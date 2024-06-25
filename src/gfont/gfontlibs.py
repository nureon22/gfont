import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from typing import (
    Dict,
    List,
    Optional,
)

from requests import request

from . import utils
from .constants import *

IS_ASSUME_YES = False
IS_NO_CACHE = False

__families: Dict[str, Dict] = {}


def get_families() -> Dict[str, Dict]:
    """Get families and its metadata as a dict"""

    global __families

    if __families:
        return __families

    if os.path.isfile(CACHE_FILE):
        refresh = (time.time() - os.path.getmtime(CACHE_FILE)) > METADATA_CACHE_AGE
    else:
        refresh = True

    if refresh:
        res = request("GET", "https://fonts.google.com/metadata/fonts", timeout=REQUEST_TIMEOUT)
        res.raise_for_status()

        for item in res.json()["familyMetadataList"]:
            __families[item["family"]] = item

        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        utils.write_file(CACHE_FILE, json.dumps(__families, indent=4))
    else:
        __families = json.loads(utils.read_file(CACHE_FILE))  # type: ignore

    return __families


def get_files(family: str) -> Dict[str, List]:
    "Get manifest and fonts files for the family"

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family)

    res = request("GET", f"https://fonts.google.com/download/list?family={family}", timeout=REQUEST_TIMEOUT)
    res.raise_for_status()

    # https://fonts.google.com/download/list?family={family} return )]}' at the
    # beginning of the response. I don't know why. But this will make json parser
    # to fail.
    data = json.loads(res.text[4:] if res.text.startswith(")]}'") else res.text)

    return {"manifest": data["manifest"]["files"], "fonts": data["manifest"]["fileRefs"]}


def get_webfonts_css(family: str, woff2: bool = False, variants: Optional[List[str]] = None, text: Optional[str] = None) -> str:
    """Return CSS content of a font family"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(woff2, bool, "Second argument 'woff2' must be 'bool'")

    if variants is not None:
        utils.isinstance_check(variants, List, "Third argument 'variants' must be 'List'")

    family = resolve_family_name(family)

    url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}"

    if variants:
        all_variants = list(get_families()[family]["fonts"].keys())  # type: ignore

        for variant in variants:
            if variant not in all_variants:
                utils.log("error", f"Font variant '{variant}' is not available for '{family}'")
                sys.exit(1)

        finalvariants = [f"1,{x[:-1]}" if x.startswith("i") else f"0,{x}" for x in variants]
        finalvariants.sort()
        url = url + ":ital,wght@" + ";".join(finalvariants)

    if text:
        url = url + "&text=" + text

    # User-Agent is specified to make sure woff2 fonts are returned instead of ttf fonts
    headers = {"User-Agent": BROWSER_USER_AGENT} if woff2 else {}
    res = request("GET", url, headers=headers, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()

    return res.text


def search_families(keywords: List[str], exact: bool = False) -> List[str]:
    """Search font families contain given keywords.

    :param exact - if True, given keywords will be directly compare to name of the font family. But still case-insensitive.
    :return - Return a list contains font family names
    """

    utils.isinstance_check(keywords, List, "First argument 'keywords' must be 'List'")
    utils.isinstance_check(exact, bool, "Second argument 'exact' must be 'bool'")

    results = []

    for family in get_families():
        not_found = False
        family_lower = family.lower()

        for keyword in keywords:
            utils.isinstance_check(keyword, str, "First argument 'keywords' must be 'List[str]'")

            keyword = keyword.replace("  ", "").strip().lower()

            if exact:
                if family_lower != keyword:
                    not_found = True
            else:
                if family_lower.find(keyword) == -1:
                    not_found = True

        if not not_found:
            results.append(family)

    return results


def resolve_family_name(family: str, exact: bool = False) -> str:
    """Resolve a font family name contains (case-insensitive,underscore) to valid name"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(exact, bool, "Second argument 'exact' must be 'bool'")

    if family in get_families():
        return family

    families = search_families([family.replace("_", " ")], exact)

    if len(families) == 0:
        utils.family_not_found(family, True)

    return families[0]


def get_printable_info(family: str, isRaw: bool = False) -> str:
    """Get metadata of a specific font family in pretty print format

    :param isRaw: if True, return is raw json format (contains extra informations)
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(isRaw, bool, "Second argument 'isRaw' must be 'bool'")

    metadata = get_families()[family]

    content = ""

    if isRaw:
        content = json.dumps(metadata, indent=4)
    else:
        content = f"""
            \r\033[01;34m{metadata['family']}\033[0m
            \r------------
            \r\033[34mCategory\033[0m   : {metadata['category']}
            \r\033[34mSubsets\033[0m    : {', '.join(metadata['subsets'])}
            \r\033[34mFonts\033[0m      : {', '.join(list(metadata['fonts'].keys()))}
            \r\033[34mDesigners\033[0m  : {', '.join(metadata['designers'])}
            \r\033[34mOpenSource\033[0m : {metadata['isOpenSource']}
        \r"""

    return content


def download_fonts(fonts: List[Dict], dir: str, nocache: bool = False):
    """Download the given font, not complete set of font family.

    :param font: dictionary that hold information of a font, should contains 'filename' and 'url' properties.
    """

    utils.isinstance_check(fonts, List, "First argument 'fonts' must be 'List'")
    utils.isinstance_check(dir, str, "Second argument 'dir' must be 'str'")

    total = len(fonts)
    total_width = len(str(total))

    def _download(font):
        utils.log("info", f"({str(fonts.index(font) + 1).rjust(total_width, '0')}/{total}) Downloading {font['filename']}")

        utils.download_file(font["url"], f"{dir}/{font['filename']}", (0 if nocache or IS_NO_CACHE else FONT_CACHE_AGE))

    utils.thread_pool_loop(_download, fonts)


def download_family(family: str):
    """Download complete set of given font family"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family)
    files = get_files(family)

    subdir = os.path.join(FONTS_DIR, family.replace(" ", "_"))

    for manifest in files["manifest"]:
        utils.write_file(os.path.join(FONTS_DIR, subdir, manifest["filename"]), manifest["contents"])

    lastModified = datetime.fromisoformat(get_families()[family]['lastModified'])
    download_fonts(files["fonts"], subdir, lastModified.timestamp() > time.time())

    if shutil.which("fc-cache"):
        os.system("fc-cache")

    utils.log("info", "Installation '{}' finished.".format(family))


def remove_family(family: str):
    """Remove already installed font family. If given font family wasn't installed yet, do nothing."""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family)
    dir = os.path.join(FONTS_DIR, family.replace(" ", "_"))

    if os.path.isdir(dir):
        shutil.rmtree(dir)

        if shutil.which("fc-cache"):
            os.system("fc-cache")

        utils.log("info", "Removing '{}' finished".format(family))


def get_installed_families() -> List[str]:
    """Get installed font families"""

    families = []

    for dir in os.listdir(FONTS_DIR) if os.path.isdir(FONTS_DIR) else []:
        if not dir.startswith("."):
            families.append(dir.replace("_", " "))

    return families


def get_license_content(family: str) -> str:
    """
    Get license of a font family. Not just license name, including its contents.
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    for manifest in get_files(family)["manifest"]:
        if manifest["filename"] == "LICENSE.txt" or manifest["filename"] == "OFL.txt":
            return manifest["contents"]

    return "License not found"


def preview_family(family: str, preview_text: Optional[str] = None, font_size: int = 48):
    """
    Preview the given font using imagemagick
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family, True)

    if preview_text is None:
        res = request("GET", f"https://fonts.google.com/sampletext?family={family.replace(' ', '+')}")
        res.raise_for_status()

        preview_text = str(json.loads(res.text[4:])["sampleText"]["specimen48"])
    else:
        utils.isinstance_check(preview_text, str, "Second argument 'preview_text' must be 'None' or 'str'")

    utils.isinstance_check(font_size, int, "Third argument 'font_size' must be 'int'")

    preview_text = utils.split_long_text(preview_text, 32)

    webfonts_css = get_webfonts_css(family, woff2=False, text=preview_text)
    font = re.findall(r"https://fonts.gstatic.com/[^\)]+", webfonts_css)[0]

    if shutil.which("convert") and shutil.which("display"):
        fontfile = os.path.join(CACHE_DIR, "preview.ttf")
        imagefile = os.path.join(CACHE_DIR, "preview.png")

        utils.download_file(font, fontfile)

        os.system(
            f'convert -background "#101010" -fill "#ffffff" -font "{fontfile}" -pointsize {font_size} label:"{preview_text}" {imagefile}'
        )
        os.system(f"display {imagefile}")

        os.remove(fontfile)
        os.remove(imagefile)
    else:
        utils.log("warning", "Cannot preview the font, because imagemagick isn't installed")


def pack_webfonts(family: str, dir: str, variants: Optional[List[str]] = None):
    """Pack a font family to use in websites as self-hosted fonts"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(dir, str, "Second argument 'dir' must be 'str'")

    if variants is not None:
        utils.isinstance_check(variants, List, "Third argument 'variants' must be 'List'")

    family = resolve_family_name(family)

    webfonts_css = get_webfonts_css(family, woff2=True, variants=variants)

    subdir = os.path.join(dir, family.replace(" ", "_"))

    woff_fonts = list(set(re.findall(r"https://fonts.gstatic.com/.+\.woff2?", webfonts_css)))
    fonts = [{"url": font, "filename": os.path.basename(font)} for font in woff_fonts]

    download_fonts(fonts, f"{subdir}/fonts")

    webfonts_css = re.sub(r"https://fonts.gstatic.com/.+/", "fonts/", webfonts_css)
    utils.write_file(f"{subdir}/{family.replace(' ', '_')}.css", webfonts_css)

    utils.log("info", "Packing webfonts finished.")
