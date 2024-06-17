import json
import os
import platform
import re
import shutil
import sys
import time
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


def get_available_families(refresh: bool = False) -> List[str]:
    """Get all available font family names

    :param refresh - Refresh from internet instead of local cache
    """

    utils.isinstance_check(refresh, bool, "First argument 'refresh' must be 'bool'")

    if refresh is False:
        if os.path.isfile(CACHE_FILE):
            # if fonts_metadata_file is older than 30 days, refresh it
            refresh = (time.time() - os.path.getmtime(CACHE_FILE)) > METADATA_CACHE_AGE
        else:
            refresh = True

    families = None

    if refresh:
        res = request("GET", "https://fonts.google.com/metadata/fonts", timeout=REQUEST_TIMEOUT)

        if res.status_code != 200:
            utils.log("error", f"Request to '{res.url}' failed. {res.reason}")
            sys.exit(1)

        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)

        families = [family_metadata["family"] for family_metadata in json.loads(res.text)["familyMetadataList"]]

        utils.write_file(CACHE_FILE, json.dumps(families))
    else:
        families = json.loads(utils.read_file(CACHE_FILE))  # type: ignore

    return families


def get_family_files(family: str) -> List[List[Dict]]:
    "Get list of files (including manifest files) contains in a font family"

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family)

    res = request("GET", f"https://fonts.google.com/download/list?family={family}", timeout=REQUEST_TIMEOUT)

    if res.status_code != 200:
        utils.log("error", f"Request to '{res.url}' failed. {res.reason}")
        sys.exit(1)

    # https://fonts.google.com/download/list?family={family} return )]}' at the
    # beginning of the response. I don't know why. But this will make json parser
    # to fail.
    data = json.loads(res.text[4:] if res.text.find(")]}'") == 0 else res.text)

    return [data["manifest"]["files"], data["manifest"]["fileRefs"]]


def get_family_webfonts_css(family: str) -> str:
    """Return CSS content of a font family"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family)
    metadata = get_family_metadata(family)

    url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}"

    if "fonts" in metadata:
        fonts = metadata["fonts"].keys()
        finalfonts = []

        for font in fonts:
            if font.endswith("i"):
                finalfonts.append("1," + font[:-1])
            else:
                finalfonts.append("0," + font)

        finalfonts.sort()

        url = url + ":ital,wght@" + ";".join(finalfonts)

    # User-Agent is specified to make sure woff2 fonts are returned instead of ttf fonts
    res = request("GET", url, headers={"User-Agent": BROWSER_USER_AGENT}, timeout=REQUEST_TIMEOUT)

    if res.status_code != 200:
        utils.log("error", f"Request to {res.url} failed. {res.reason}")
        sys.exit(1)

    return res.text


def search_families(keywords: List[str], exact: bool = False) -> List[str]:
    """Search font families contain given keywords.

    :param exact - if True, given keywords will be directly compare to name of the font family. But still case-insensitive.
    :return - Return a list contains font family names
    """

    utils.isinstance_check(keywords, List, "First argument 'keywords' must be 'List'")
    utils.isinstance_check(exact, bool, "Second argument 'exact' must be 'bool'")

    results = []

    for family in get_available_families():
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


def refresh_all_metadata():
    families = get_available_families()

    utils.log("info", "\rRefreshing families metadata", end="")

    def _func(family):
        utils.log("info", f"\rRefreshing families metadata ({families.index(family)} / {len(families)})", end="")
        get_family_metadata(family, True)

    utils.thread_pool_loop(_func, families)
    utils.log("info", "")


def get_family_metadata(family: str, refresh: bool = False) -> Dict:
    """Get metadata of a specific font family

    :param refresh - Refresh metadata from internet instead of local cache
    :return - Return a dict contains metadata of a font family
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(refresh, bool, "Second argument 'refresh' must be 'bool'")

    family = resolve_family_name(family)

    filepath = os.path.join(CACHE_DIR, "families", family + ".json")

    if refresh:
        res = request("GET", f"https://fonts.google.com/metadata/fonts/{family}", timeout=REQUEST_TIMEOUT)

        if res.status_code != 200:
            utils.log("error", f"Request to '{res.url}' failed. {res.reason}")
            sys.exit(1)

        # "https://fonts.google.com/metadata/fonts/{family}" return )]}' at the
        # beginning of the response. I don't know why. But this will make json parser
        # to fail.
        metadata = json.loads(res.text[4:] if res.text.find(")]}'") == 0 else res.text)

        utils.write_file(filepath, json.dumps(metadata))

        return metadata
    else:
        if os.path.isfile(filepath) and time.time() - os.path.getmtime(filepath) < METADATA_CACHE_AGE:
            return json.loads(utils.read_file(filepath))  # type: ignore

        return get_family_metadata(family, True)


def resolve_family_name(family: str, exact: bool = False) -> str:
    """Resolve a font family name contains (case-insensitive,underscore) to valid name"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(exact, bool, "Second argument 'exact' must be 'bool'")

    if family in get_available_families():
        return family

    families = search_families([family.replace("_", " ")], exact)

    if len(families) == 0:
        utils.family_not_found(family, True)

    return families[0]


def get_printable_family_info(family: str, isRaw: bool = False) -> str:
    """Get metadata of a specific font family in pretty print format

    :param isRaw: if True, return is raw json format (contains extra informations)
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(isRaw, bool, "Second argument 'isRaw' must be 'bool'")

    family_metadata = get_family_metadata(family)

    content = ""

    if isRaw:
        content = json.dumps(family_metadata, indent=2)
    else:
        content = f"""
            \r\033[01;34m{family_metadata['family']}\033[0m
            \r------------
            \r\033[34mCategory\033[0m   : {family_metadata['category']}
            \r\033[34mSubsets\033[0m    : {', '.join(family_metadata['coverage'].keys())}
            \r\033[34mFonts\033[0m      : {', '.join(list(family_metadata['fonts'].keys()))}
            \r\033[34mDesigners\033[0m  : {', '.join([designer["name"] for designer in family_metadata['designers']])}
            \r\033[34mLicense\033[0m    : {family_metadata['license']}
            \r\033[34mOpenSource\033[0m : {family_metadata['isOpenSource']}
        \r"""

    return content


def download_fonts(fonts: List[Dict], dir: str):
    """Download the given font, not complete set of font family.

    :param font: dictionary that hold information of a font, should contains 'filename' and 'url' properties.
    """

    utils.isinstance_check(fonts, List, "First argument 'font' must be 'List'")
    utils.isinstance_check(dir, str, "Second argument 'dir' must be 'str'")

    def _download(font):
        utils.log("info", f"({fonts.index(font) + 1}/{len(fonts)}) Downloading {font['url']}")

        utils.download_file(font["url"], f"{dir}/{font['filename']}", (0 if IS_NO_CACHE else FONT_CACHE_AGE))

    utils.thread_pool_loop(_download, fonts)


def download_family(family: str):
    """Download complete set of given font family"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family)
    [manifest_files, font_files] = get_family_files(family)

    dir = os.path.join(FONTS_DIR, family.replace(" ", "_"))

    for manifest in manifest_files:
        utils.write_file(f"{dir}/{manifest['filename']}", manifest["contents"])

    download_fonts(font_files, dir)

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
            family = dir.replace("_", " ")
            families.append(family)

    return families


def get_license_content(family: str) -> str:
    """
    Get license of a font family. Not just license name, including its contents.
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    for manifest in get_family_files(family)[0]:
        if manifest["filename"] == "LICENSE.txt" or manifest["filename"] == "OFL.txt":
            return manifest["contents"]

    return "License not found"


def preview_font(font: Dict, preview_text: Optional[str] = None, font_size: int = 48):
    """
    Preview the given font using imagemagick
    """

    utils.isinstance_check(font, Dict, "First argument 'font' must be 'Dict'")

    if preview_text is None:
        preview_text = "Whereas disregard and contempt\nfor human rights have resulted "
    else:
        utils.isinstance_check(preview_text, str, "Second argument 'preview_text' must be None or type 'str'")

    utils.isinstance_check(font_size, int, "Third argument 'font_size' must be 'int'")

    preview_text = utils.split_long_text(preview_text, 8)

    if shutil.which("convert") and shutil.which("display"):
        fontfile = os.path.expandvars(f"$HOME/.cache/gfont/{font['filename']}")
        imagefile = os.path.expandvars("$HOME/.cache/gfont/preview.png")

        utils.download_file(font["url"], fontfile)

        os.system(
            f'convert -background "#101010" -fill "#ffffff" -font "{fontfile}" -pointsize {font_size} label:"{preview_text}" {imagefile}'
        )
        os.system(f"display {imagefile}")

        os.remove(fontfile)
    else:
        utils.log("warning", "Cannot preview the font, because imagemagick isn't installed")


def pack_webfonts(family: str, dir: str):
    """Pack a font family to use in websites as self-hosted fonts"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(dir, str, "Second argument 'dir' must be 'str'")

    family = resolve_family_name(family)
    webfonts_css = get_family_webfonts_css(family)

    subdir = os.path.join(dir, family.replace(" ", "_"))

    woff_fonts = list(set(re.findall(r"https://fonts.gstatic.com/.+\.woff2?", webfonts_css)))
    fonts = [{"url": font, "filename": os.path.basename(font)} for font in woff_fonts]

    download_fonts(fonts, f"{subdir}/fonts")

    webfonts_css = re.sub(r"https://fonts.gstatic.com/.+/", "fonts/", webfonts_css)
    utils.write_file(f"{subdir}/{family.replace(' ', '_')}.css", webfonts_css)

    utils.log("info", "Packing webfonts finished.")
