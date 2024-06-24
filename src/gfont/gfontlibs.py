import json
import os
import re
import shutil
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


def get_families(refresh: bool = False) -> Dict[str, Dict]:
    """Get all font families

    :param refresh - Force to refresh from internet instead of local cache
    """

    utils.isinstance_check(refresh, bool, "First argument 'refresh' must be 'bool'")

    if refresh is False:
        if os.path.isfile(CACHE_FILE):
            refresh = (time.time() - os.path.getmtime(CACHE_FILE)) > METADATA_CACHE_AGE
        else:
            refresh = True

    families = {}

    if refresh:
        res = request("GET", f"{API_URL}", timeout=REQUEST_TIMEOUT)
        res.raise_for_status()

        for item in res.json()["items"]:
            families[item["family"]] = item

        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        utils.write_file(CACHE_FILE, json.dumps(families, indent=4))
    else:
        families = json.loads(utils.read_file(CACHE_FILE))  # type: ignore

    return families


def get_manifest_files(family: str) -> List[Dict]:
    "Get list of manifest files for the family"

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family)

    res = request("GET", f"https://fonts.google.com/download/list?family={family}", timeout=REQUEST_TIMEOUT)
    res.raise_for_status()

    # https://fonts.google.com/download/list?family={family} return )]}' at the
    # beginning of the response. I don't know why. But this will make json parser
    # to fail.
    data = json.loads(res.text[4:] if res.text.find(")]}'") == 0 else res.text)

    return data["manifest"]["files"]


def get_family_webfonts_css(family: str, woff2: bool = False, variants: Optional[List[str]] = None) -> str:
    """Return CSS content of a font family"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family)
    metadata = get_family_metadata(family)

    if variants:
        variants = [x for x in variants if x in metadata["fonts"]]
    else:
        variants = metadata["fonts"]

    url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}"

    if "fonts" in metadata:
        finalfonts = []

        for font in variants:  # type: ignore
            if font.endswith("i"):
                finalfonts.append("1," + font[:-1])
            else:
                finalfonts.append("0," + font)

        finalfonts.sort()

        url = url + ":ital,wght@" + ";".join(finalfonts)

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


def refresh_all_metadata():
    families = list(get_families().keys())

    utils.log("info", "\rRefreshing families metadata", end="")

    def _func(family):
        utils.log("info", f"\rRefreshing families metadata ({families.index(family)} / {len(families)})", end="")
        get_family_metadata(family, False)

    utils.thread_pool_loop(_func, families)
    utils.log("info", "")


def get_family_metadata(family: str, refresh: bool = False) -> Dict:
    """Get metadata of a specific font family

    :param refresh - Refresh metadata from internet instead of local cache
    :return - Return a dict contains following fields of the font family
            family: The name of the family
            subsets: A list of scripts supported by the family
            menu: A url to the family subset covering only the name of the family.
            variants: The different styles available for the family
            version: The font family version.
            axes: Axis range, Present only upon request for variable fonts.
            lastModified: The date (format "yyyy-MM-dd") the font family was modified for the last time.
            files: The font family files (with all supported scripts) for each one of the available variants.
            designers: A list of designers of the family
            license: Shorten license name of the family
            isOpenSource: A bool whether the family is open-source or not
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(refresh, bool, "Second argument 'refresh' must be 'bool'")

    family = resolve_family_name(family)

    filepath = os.path.join(CACHE_DIR, "families", family.replace(" ", "_") + ".json")

    if refresh:
        res = request("GET", f"https://fonts.google.com/metadata/fonts/{family}", timeout=REQUEST_TIMEOUT)
        res.raise_for_status()

        # "https://fonts.google.com/metadata/fonts/{family}" return )]}' at the
        # beginning of the response. I don't know why. But this will make json parser
        # to fail.
        original_extrametadata = json.loads(res.text[4:] if res.text.find(")]}'") == 0 else res.text)
        extrametadata = {}

        # Copy only specific fields
        for key in ["designers", "license", "isOpenSource"]:
            extrametadata[key] = original_extrametadata[key]

        # Place before merging statement to make sure only required information are cached
        utils.write_file(filepath, json.dumps(extrametadata))

        return {**extrametadata, **get_families()[family]}
    else:
        if os.path.isfile(filepath) and time.time() - os.path.getmtime(filepath) < METADATA_CACHE_AGE:
            extrametadata = json.loads(utils.read_file(filepath))  # type: ignore
            return {**extrametadata, **get_families()[family]}

        return get_family_metadata(family, True)


def resolve_variant_name(variant: str, shorten: bool = True) -> str:
    """Resolve font variant to shorten or long standard format"""

    if variant == "regular":
        variant = "400"
    elif variant == "italic":
        variant = "400i"

    variant = variant.replace("italic", "i")

    if not shorten:
        variant = FONT_VARIANT_STANDARD_NAMES[variant]

    return variant


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
            \r\033[34mSubsets\033[0m    : {', '.join(family_metadata['subsets'])}
            \r\033[34mVariants\033[0m   : {', '.join([resolve_variant_name(x) for x in family_metadata['variants']])}
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

    total = len(fonts)
    total_width = len(str(total))

    def _download(font):
        utils.log("info", f"({str(fonts.index(font) + 1).rjust(total_width, '0')}/{total}) Downloading {font['filename']}")

        utils.download_file(font["url"], f"{dir}/{font['filename']}", (0 if IS_NO_CACHE else FONT_CACHE_AGE))

    utils.thread_pool_loop(_download, fonts)


def download_family(family: str):
    """Download complete set of given font family"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family)
    font_files = get_families()[family]["files"]

    subdir = family.replace(" ", "_")

    for manifest in get_manifest_files(family):
        utils.write_file(os.path.join(FONTS_DIR, subdir, manifest["filename"]), manifest["contents"])

    fonts = [
        {
            "filename": f"{subdir}-{resolve_variant_name(key, False)}{os.path.splitext(font_files[key])[1]}",
            "url": font_files[key],
        }
        for key in font_files
    ]

    download_fonts(fonts, os.path.join(FONTS_DIR, subdir))

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

    for manifest in get_manifest_files(family):
        if manifest["filename"] == "LICENSE.txt" or manifest["filename"] == "OFL.txt":
            return manifest["contents"]

    return "License not found"


def preview_font(family: str, preview_text: Optional[str] = None, font_size: int = 48):
    """
    Preview the given font using imagemagick
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family_name(family, True)

    if preview_text is None:
        res = request("GET", f"https://fonts.google.com/sampletext?family={family.replace(' ', '+')}")
        res.raise_for_status()

        preview_text = re.sub(r"(\\n|\n|\")", "", json.loads(res.text[4:])["sampleText"]["specimen48"])
    else:
        utils.isinstance_check(preview_text, str, "Second argument 'preview_text' must be None or type 'str'")

    utils.isinstance_check(font_size, int, "Third argument 'font_size' must be 'int'")

    preview_text = utils.split_long_text(preview_text, 32)

    font_files = get_family_metadata(family)["files"]

    font = None

    # Choose one of these variants in specified order
    for variant in ["400", "500", "600", "700", "300", "400i", "500i", "600i", "700i", "300i"]:
        if variant in font_files:
            font = {"filename": os.path.basename(font_files[variant]), "url": font_files[variant]}
            break

    if font is None:
        raise Exception(f"Cannot preview {family}")

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


def pack_webfonts(family: str, dir: str, variants: Optional[List[str]] = None):
    """Pack a font family to use in websites as self-hosted fonts"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(dir, str, "Second argument 'dir' must be 'str'")

    family = resolve_family_name(family)
    family_metadata = get_family_metadata(family)

    variants = variants or family_metadata["fonts"]
    webfonts_css = get_family_webfonts_css(family, woff2=True, variants=variants)

    subdir = os.path.join(dir, family.replace(" ", "_"))

    woff_fonts = list(set(re.findall(r"https://fonts.gstatic.com/.+\.woff2?", webfonts_css)))
    fonts = [{"url": font, "filename": os.path.basename(font)} for font in woff_fonts]

    download_fonts(fonts, f"{subdir}/fonts")

    webfonts_css = re.sub(r"https://fonts.gstatic.com/.+/", "fonts/", webfonts_css)
    utils.write_file(f"{subdir}/{family.replace(' ', '_')}.css", webfonts_css)

    utils.log("info", "Packing webfonts finished.")
