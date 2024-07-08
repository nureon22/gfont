import json
import os
import re
import shutil
import sys
import time
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional

from requests import request

from . import utils
from .constants import (
    BROWSER_USER_AGENT,
    CACHE_DIR,
    CACHE_FILE,
    FONTS_DIR,
    LICENSES,
    REQUEST_TIMEOUT,
)

__families: Dict[str, Dict] = {}
__families_list: List[str] = []


def get_families(refresh: bool = False) -> List[str]:
    """Get a list of all families"""

    global __families
    global __families_list

    if refresh:
        __families = {}
        __families_list = []
    elif not os.path.isfile(CACHE_FILE):
        refresh = True

    if __families_list:
        return __families_list

    API_KEY = os.getenv("GOOGLE_FONTS_API_KEY")

    if API_KEY:
        url = "https://www.googleapis.com/webfonts/v1/webfonts?key=" + API_KEY
    else:
        url = "https://raw.githubusercontent.com/nureon22/gfont/main/data/webfonts.json"

    if refresh:
        print("Refreshing families metadata")
        res = request("GET", url, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()

        for item in res.json()["items"]:
            item["variants"] = utils.resolve_variants(item["variants"], True)
            __families[utils.snake_case(item["family"])] = item

        utils.write_file(CACHE_FILE, json.dumps(__families, indent=4))
    else:
        __families = json.loads(utils.read_file(CACHE_FILE))  # type: ignore

    __families = dict(sorted(__families.items()))
    __families_list = [__families[x]["family"] for x in __families]

    return __families_list


def get_metadata(family: str):
    """Get metadata of the family"""

    family = resolve_family(family)
    family_snake = utils.snake_case(family)

    if family_snake in __families:
        metadata = __families[family_snake]
    else:
        metadata = __families[family]

    if "designers" not in metadata or "license" not in metadata or "axes" not in metadata:
        if family.startswith("Material Icons"):
            metadata["designers"] = ["Google"]
            metadata["license"] = "apache2"
            metadata["axes"] = []

        elif family.startswith("Material Symbols"):
            metadata["designers"] = ["Google"]
            metadata["license"] = "apache2"
            metadata["axes"] = [
                {"tag": "opsz", "min": 20, "max": 48},
                {"tag": "wght", "min": 100, "max": 700},
                {"tag": "FILL", "min": 0, "max": 1},
                {"tag": "GRAD", "min": -50, "max": 200},
            ]

        else:
            url = f"https://fonts.google.com/metadata/fonts/{family}"
            res = request("GET", url, timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            data = json.loads(res.text.replace(")]}'", "", 1))
            metadata["designers"] = [x["name"] for x in data["designers"]]
            metadata["license"] = data["license"]
            metadata["axes"] = data["axes"]

        utils.write_file(CACHE_FILE, json.dumps(__families, indent=4))

    return metadata


def get_webfonts_css(
    family: str,
    woff2: bool,
    styles: str = "",
    display: Optional[str] = None,
    text: Optional[str] = None,
) -> str:
    """Return CSS content of a font family"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(woff2, bool, "Second argument 'woff2' must be 'bool'")
    utils.isinstance_check(styles, str, "Third argument 'styles' must be 'str'")

    api_version = "css2" if "@" in styles else "css"

    url = f"https://fonts.googleapis.com/{api_version}?family=" + family.replace(" ", "+")

    if styles:
        url = url + ":" + styles

    if display:
        url = url + f"&display={urllib.parse.quote(display)}"

    if text:
        url = url + f"&text={urllib.parse.quote(text)}"

    # User-Agent is specified to make sure woff2 fonts are returned instead of ttf fonts
    headers = {"User-Agent": BROWSER_USER_AGENT} if woff2 else {}
    res = request("GET", url, headers=headers, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()

    return f"/* original-url: {url} */\n\n{res.text}"


def get_installed_families() -> List[str]:
    """Get installed font families"""

    all_families = get_families()
    installed_families = []

    for dir in os.listdir(FONTS_DIR) if os.path.isdir(FONTS_DIR) else []:
        family = dir.replace("_", " ")
        if family in all_families:
            installed_families.append(family)

    installed_families.sort()
    return installed_families


def get_printable_info(family: str, isRaw: bool = False) -> str:
    """Get metadata of a specific font family in pretty print format

    :param isRaw: if True, return is raw json format (contains extra informations)
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(isRaw, bool, "Second argument 'isRaw' must be 'bool'")

    metadata = get_metadata(family)

    content = ""

    if isRaw:
        content = json.dumps(metadata, indent=4)
    else:
        axes = [f"@{x['tag']}={x['min']}>{x['max']}" for x in metadata["axes"]]

        content = ""
        content += f"\033[01;34m{metadata['family']}\033[0m\n"
        content += "------------\n"
        content += f"\033[34mVersion\033[0m   : {metadata['version']}\n"
        content += f"\033[34mCategory\033[0m  : {metadata['category']}\n"
        content += f"\033[34mSubsets\033[0m   : {', '.join(metadata['subsets'])}\n"
        content += f"\033[34mVariants\033[0m  : {', '.join(metadata['variants'])}\n"
        content += f"\033[34mAxes\033[0m      : {', '.join(axes) if axes else 'None'}\n"
        content += f"\033[34mDesigners\033[0m : {', '.join(metadata['designers'])}\n"
        content += f"\033[34mLicense\033[0m   : {LICENSES[metadata['license']][0]}"

    return content


def search_families(keywords: List[str], exact: bool = False) -> List[str]:
    """Search font families contain given keywords.

    :param exact -
        if True, given keywords will be directly compare to name
        of the font family. But still case-insensitive.
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


def resolve_family(family: str, exact: bool = False) -> str:
    """Resolve a font family name contains (case-insensitive,underscore) to valid name"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(exact, bool, "Second argument 'exact' must be 'bool'")

    _family = family
    family = re.sub(r"[-_]", " ", family)
    families = get_families()

    if family in families:
        return family

    for x in families:
        if x.lower() == family:
            return x

    utils.log("Error", f"Family '{_family}' cannot be found")
    sys.exit(1)


def download_fonts(family: str, fonts: List[Dict], dir: str, nocache: bool = False):
    """Download the given font, not complete set of font family.

    :param fonts: List of dictionary that hold information of a font, should contains 'filename' and 'url' properties.
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(fonts, List, "Second argument 'fonts' must be 'List'")
    utils.isinstance_check(dir, str, "Third argument 'dir' must be 'str'")

    total = len(fonts)
    total_width = len(str(total))

    def _download(font):
        filepath = os.path.join(dir, font["filename"])
        current = str(fonts.index(font) + 1).rjust(total_width, "0")

        print(f"Downloading '{family}' ({current}/{total})", end="\033[K\r")

        if os.path.isfile(filepath) and not nocache:
            return

        res = request("GET", font["url"], timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        utils.write_bytes_file(filepath, res.content)

    utils.thread_pool_loop(_download, fonts)


def install_family(family: str, nocache: bool = False):
    """Download complete set of given font family"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family(family)
    metadata = get_metadata(family)

    subdir = os.path.join(FONTS_DIR, family.replace(" ", "_"))

    fonts = [
        {
            "filename": f"{family.replace(' ', '_')}-{utils.resolve_variant(variant, False)}{os.path.splitext(url)[1]}",
            "url": url,
        }
        for [variant, url] in metadata["files"].items()
    ]

    lastModified = datetime.fromisoformat(metadata["lastModified"])
    download_fonts(family, fonts, subdir, nocache or lastModified.timestamp() > time.time())

    if shutil.which("fc-cache"):
        os.system("fc-cache")

    print(f"Installation '{family}' finished.")


def remove_family(family: str):
    """Remove already installed font family. If given font family wasn't installed yet, do nothing."""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family(family)
    dir = os.path.join(FONTS_DIR, family.replace(" ", "_"))

    if os.path.isdir(dir):
        shutil.rmtree(dir)

        if shutil.which("fc-cache"):
            os.system("fc-cache")

        print("Removing '{}' finished".format(family))


def update_families():
    # Force to refresh metadata cache file
    get_families(True)

    for family in get_installed_families():
        family = resolve_family(family)

        print(f"Updating '{family}'", end="\033[K\r")
        lastModified = datetime.fromisoformat(get_metadata(family)["lastModified"])
        if lastModified.timestamp() > time.time():
            install_family(family, True)
        else:
            print(f"No updates '{family}'")


def preview_family(family: str, preview_text: Optional[str] = None, font_size: int = 48):
    """
    Preview the given font using imagemagick
    """

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")

    family = resolve_family(family, True)

    if preview_text is None:
        url = f"https://fonts.google.com/sampletext?family={family.replace(' ', '+')}"
        res = request("GET", url, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        preview_text = str(json.loads(res.text.replace(")]}'", ""))["sampleText"]["specimen48"])
    else:
        utils.isinstance_check(
            preview_text, str, "Second argument 'preview_text' must be 'None' or 'str'"
        )

    utils.isinstance_check(font_size, int, "Third argument 'font_size' must be 'int'")

    preview_text = utils.split_long_text(preview_text, 32)

    webfonts_css = get_webfonts_css(family, woff2=False, text=preview_text)
    font = re.findall(r"url\(([^\)]+)\)", webfonts_css)[0]

    if shutil.which("convert") and shutil.which("display"):
        now = time.time()
        fontfile = os.path.join(CACHE_DIR, str(now) + ".ttf")
        imagefile = os.path.join(CACHE_DIR, str(now) + ".png")

        utils.download_file(font, fontfile)

        cmd = 'convert -background "#101010" -fill "#ffffff" -font "{}" -pointsize {} label:"{}" {}'
        os.system(cmd.format(fontfile, font_size, preview_text, imagefile))
        os.system(f"display {imagefile}")

        os.remove(fontfile)
        os.remove(imagefile)
    else:
        utils.log("warning", "Cannot preview the font, because imagemagick isn't installed")


def pack_webfonts(
    family: str,
    dir: str,
    clean: bool,
    styles: str = "",
    display: Optional[str] = None,
    text: Optional[str] = None,
):
    """Pack a font family to use in websites as self-hosted fonts"""

    utils.isinstance_check(family, str, "First argument 'family' must be 'str'")
    utils.isinstance_check(dir, str, "Second argument 'dir' must be 'str'")
    utils.isinstance_check(clean, bool, "Third argument 'clean' must be 'bool'")

    family = resolve_family(family)
    family_kebab = utils.kebab_case(family)

    webfonts_css = get_webfonts_css(family, True, styles, display=display, text=text)
    subdir = os.path.join(dir, family_kebab)

    fonts = list(set(re.findall(r"url\(([^\)]+)\)", webfonts_css)))
    fonts = [{"url": font, "filename": f"{utils.unique_name()}.woff2"} for font in fonts]

    utils.empty_directory(f"{subdir}/fonts")
    download_fonts(family, fonts, f"{subdir}/fonts", True)

    for font in fonts:
        webfonts_css = webfonts_css.replace(font["url"], font["filename"])
    utils.write_file(f"{subdir}/{family_kebab}.css", webfonts_css)

    print(f"Packing '{family}' webfonts finished.")
