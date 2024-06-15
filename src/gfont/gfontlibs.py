import json
import os
import platform
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import (
    Dict,
    List,
    Optional,
)

import requests

system_platform = platform.system()

if system_platform == "Linux":
    cache_file = os.path.expanduser("~/.cache/gfont/families.json")
    fonts_dir = os.path.expanduser("~/.local/share/fonts/gfont")
elif system_platform == "Darwin":
    cache_file = os.path.expanduser("~/Library/Caches/gfont/families.json")
    fonts_dir = os.path.expanduser("~/Library/Fonts/gfont")
else:
    raise Exception("You system is not supported yet")


IS_ASSUME_YES = False
IS_NO_CACHE = False

LOG_COLORS = {
    "DEBUG": "\033[34m",  # Blue
    "INFO": "\033[0m",  # Default
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Purple
    "RESET": "\033[0m",
}

max_workers = 5


def log(level: str, message: str, **kwargs):
    print(f"{LOG_COLORS[level.upper()]}{message}{LOG_COLORS['RESET']}", **kwargs)


def ask_yes_no(question: str) -> bool:
    while True:
        answer = input(f"{question} [y|N] ").upper().strip()[0]
        if answer == "":
            return False
        elif answer == "N":
            return False
        elif answer == "Y":
            return True


def __family_not_found(family_name, exit=True):
    log("error", f"'{family_name}' cannot be found")

    if exit:
        sys.exit(1)


def get_available_families() -> List[str]:
    """Get all available font family names"""

    refresh = False

    if os.path.isfile(cache_file):
        # if fonts_metadata_file is older than 30 days, refresh it
        refresh = (time.time() - os.path.getmtime(cache_file)) > 3600 * 24 * 30
    else:
        refresh = True

    families = None

    if refresh:
        res = requests.get(url="https://fonts.google.com/metadata/fonts")

        if res.status_code != 200:
            log("error", f"Request to '{res.url}' failed. {res.reason}")
            sys.exit(1)

        os.makedirs(os.path.dirname(cache_file), exist_ok=True)

        families = [family_metadata["family"] for family_metadata in json.loads(res.text)["familyMetadataList"]]

        with open(cache_file, "w") as file:
            file.write(json.dumps(families))
            file.close()
    else:
        with open(cache_file, "r") as file:
            families = json.loads(file.read())
            file.close()

    return families


def get_family_fonts(unsafe_family_name: str) -> Dict[str, List[Dict]]:
    "Get list of files (including manifest files) contains in a font family"

    family = resolve_family_name(unsafe_family_name)

    res = requests.get(f"https://fonts.google.com/download/list?family={family}")

    if res.status_code != 200:
        log("error", f"Request to '{res.url}' failed. {res.reason}")
        sys.exit()

    # https://fonts.google.com/download/list?family={family} return )]}' at the
    # beginning of the response. I don't know why. But this will make json parser
    # to fail.
    data = json.loads(res.text[4:] if res.text.find(")]}'") == 0 else res.text)

    return {
        "manifest_files": data["manifest"]["files"],
        "font_files": data["manifest"]["fileRefs"],
    }


def get_family_webfonts_css(unsafe_family_metadata: str) -> str:
    """Return CSS content of a font family"""

    family_metadata = get_family_metadata(unsafe_family_metadata)

    url = f"https://fonts.googleapis.com/css2?family={family_metadata['family'].replace(' ', '+')}"

    if "fonts" in family_metadata:
        fonts = family_metadata["fonts"].keys()
        finalfonts = []

        for font in fonts:
            if font.endswith("i"):
                finalfonts.append("1," + font[:-1])
            else:
                finalfonts.append("0," + font)

        finalfonts.sort()

        url = url + ":ital,wght@" + ";".join(finalfonts)

    # User-Agent is specified to make sure woff2 fonts are returned instead of ttf fonts
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0"})

    if res.status_code != 200:
        log("error", f"Request to {res.url} failed. {res.reason}")
        sys.exit(1)

    return res.text


def search_families(keywords: List[str], exact: bool = False) -> List[str]:
    """Search font families contain given keywords.

    :param exact - if True, given keywords will be directly compare to name of the font family. But still case-insensitive.
    :return - Return a list contains font family names
    """

    results = []

    for family in get_available_families():
        not_found = False
        family_lower = family.lower()

        for keyword in keywords:
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


def get_family_metadata(unsafe_family_name: str) -> Dict:
    """Get metadata of a specific font family

    :return - Return a dict contains metadata of a font family
    """

    family = resolve_family_name(unsafe_family_name)

    res = requests.get(f"https://fonts.google.com/metadata/fonts/{family}")

    if res.status_code != 200:
        log("error", f"Request to '{res.url}' failed. {res.reason}")
        sys.exit()

    # "https://fonts.google.com/metadata/fonts/{family}" return )]}' at the
    # beginning of the response. I don't know why. But this will make json parser
    # to fail.
    return json.loads(res.text[4:] if res.text.find(")]}'") == 0 else res.text)


def resolve_family_name(unsafe_family_name: str, exact: bool = False) -> str:
    """Resolve a font family name contains (case-insensitive,underscore) to valid name"""

    if unsafe_family_name in get_available_families():
        return unsafe_family_name

    families = search_families([unsafe_family_name.replace("_", " ")], exact)

    if len(families) == 0:
        __family_not_found(unsafe_family_name, True)

    return families[0]


def get_family_info(unsafe_family_name: str, isRaw: bool = False) -> str:
    """Get metadata of a specific font family in pretty print format

    :param isRaw: if True, return is raw json format (contains extra informations)
    """

    family_metadata = get_family_metadata(unsafe_family_name)

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


def download_font(font: Dict, filepath: str, retries: int = 5):
    """Download the given font, not complete set of font family.

    :param font: dictionary that hold information of a font, should contains 'filename' and 'url' properties.
    :param retries: number of retries if downloading the font failed
    """

    if not IS_NO_CACHE:
        if os.path.isfile(filepath):
            age = time.time() - os.stat(filepath).st_mtime

            # if download font file is older than 30 days, download it again
            if age < 3600 * 24 * 30:
                time.sleep(0.1)
                return "cached"

    need_retry = False

    try:
        res = requests.get(font["url"], timeout=10)

        if res.status_code == 200:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as file:
                file.write(res.content)
                file.close()
        else:
            log("error", f"Downloading {font['url']} -> {font['filename']} failed. {res.reason}")
            need_retry = True

    except Exception as exception:
        log("error", f"Downloading {font['url']} -> {font['filename']} failed. {exception} ")
        need_retry = True

    if need_retry:
        if retries > 0:
            log("warning", f"Retrying {font['url']} -> {font['filename']}")
            download_font(font, filepath, retries - 1)
        else:
            log("warning", f"Skipping {font['url']} -> {font['filename']}")
            return "failed"

    return "success"


def download_family(unsafe_family_name: str):
    """Download complete set of given font family"""

    family_metadata = get_family_metadata(unsafe_family_name)

    family = family_metadata["family"]

    dir = os.path.join(fonts_dir, family.replace(" ", "_"))
    os.makedirs(dir, exist_ok=True)

    family_fonts = get_family_fonts(family)

    successed = []
    cached = []
    failed = []

    for manifest in family_fonts["manifest_files"]:
        with open(os.path.join(dir, manifest["filename"]), "w") as file:
            file.write(manifest["contents"])
            file.close()

    total = len(family_fonts["font_files"])

    def _download(font):
        log("info", "({}/{}) Downloading {}".format(family_fonts["font_files"].index(font) + 1, total, font['filename']))

        status = download_font(font, os.path.join(dir, font["filename"]))

        if status == "success":
            successed.append(font)
        elif status == "failed":
            failed.append(font)
        elif status == "cached":
            cached.append(font)

    with ThreadPoolExecutor(max_workers) as executor:
        futures = [executor.submit(_download, font) for font in family_fonts["font_files"]]
        [future.result() for future in as_completed(futures)]

    if shutil.which("fc-cache"):
        os.system("fc-cache")

    log("info", f"Success {len(successed) + len(cached)} Failed {len(failed)} Cached {len(cached)}")
    log("info", "Installation '{}' finished.".format(family))


def remove_family(unsafe_family_name: str):
    """Remove already installed font family. If given font family wasn't installed yet, do nothing."""

    family = resolve_family_name(unsafe_family_name)
    dir = os.path.join(fonts_dir, family.replace(" ", "_"))

    if os.path.isdir(dir):
        shutil.rmtree(dir)

        if shutil.which("fc-cache"):
            os.system("fc-cache")

        log("info", "Removing '{}' finished".format(family))


def get_installed_families() -> List[str]:
    """Get installed font families"""

    families = []

    for dir in os.listdir(fonts_dir) if os.path.isdir(fonts_dir) else []:
        if not dir.startswith("."):
            family = dir.replace("_", " ")
            families.append(family)

    return families


def get_license_content(unsafe_family_name: str) -> str:
    """
    Get license of a font family. Not just license name, including its contents.
    """
    family_fonts = get_family_fonts(unsafe_family_name)

    for manifest in family_fonts["manifest__files"]:
        if manifest["filename"] == "LICENSE.txt" or manifest["filename"] == "OFL.txt":
            return manifest["contents"]

    return "License not found"


def preview_font(font: Dict, preview_text: Optional[str] = None, font_size: int = 48):
    """
    Preview the given font using imagemagick
    """

    if not preview_text:
        preview_text = "Whereas disregard and contempt\nfor human rights have resulted "

    preview_text = split_long_text(preview_text, 8)

    if shutil.which("convert") and shutil.which("display"):
        fontfile = os.path.expandvars(f"$HOME/.cache/gfont/{font['filename']}")
        imagefile = os.path.expandvars("$HOME/.cache/gfont/preview.png")

        download_font(font, fontfile)

        os.system(
            f'convert -background "#101010" -fill "#ffffff" -font "{fontfile}" -pointsize {font_size} label:"{preview_text}" {imagefile}'
        )
        os.system(f"display {imagefile}")

        os.remove(fontfile)
    else:
        log("warning", "Cannot preview the font, because imagemagick isn't installed")


def split_long_text(text: str, max_words_count: int):
    """
    Add line break at every {max_words_count} words
    """

    result = ""

    words = text.split(" ")
    for index in range(0, len(words), max_words_count):
        end = index + max_words_count
        result = result + " ".join(words[index:end]) + "\n"

    return result


def pack_webfonts(unsafe_family_name: str, dir: str):
    family_metadata = get_family_metadata(unsafe_family_name)
    webfonts_css = get_family_webfonts_css(family_metadata["family"])
    nospace_family_name = family_metadata["family"].replace(" ", "_")

    fonts = re.findall(r"https://fonts.gstatic.com/.+\.woff2?", webfonts_css)
    fonts = list(set(fonts))

    total = len(fonts)

    successed = []
    failed = []
    cached = []

    def _download(font):
        nonlocal webfonts_css

        filename = os.path.basename(font)
        filepath = os.path.join(dir, nospace_family_name, "fonts", filename)
        webfonts_css = webfonts_css.replace(font, f"fonts/{filename}")

        log("info", "({}/{}) Downloading {}".format(fonts.index(font) + 1, total, font))

        status = download_font({"filename": filename, "url": font}, filepath)

        if status == "success":
            successed.append(font)
        elif status == "failed":
            failed.append(font)
        elif status == "cached":
            cached.append(font)

    with ThreadPoolExecutor(max_workers) as executor:
        futures = [executor.submit(_download, font) for font in fonts]
        [future.result() for future in as_completed(futures)]

    with open(os.path.join(dir, nospace_family_name, nospace_family_name + ".css"), "w") as file:
        file.write(webfonts_css)
        file.close()

    log("info", f"Success {len(successed) + len(cached)} Failed {len(failed)} Cached {len(cached)}")
    log("info", "Packing webfonts finished.")
