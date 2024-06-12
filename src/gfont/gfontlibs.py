import json
import os
import shutil
import sys
import time

import requests

# fonts_metadata.json will be refreshed every 24 hours
families_metadata_file = os.path.expandvars("$HOME/.cache/gfont/families_metadata.json")
fonts_dir = os.path.expandvars("$HOME/.local/share/fonts/gfont")

IS_ASSUME_YES = False

LOG_COLORS = {
    "DEBUG": "\033[34m",  # Blue
    "INFO": "\033[0m",  # Default
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Purple
    "RESET": "\033[0m",
}


def log(level, message, **kwargs):
    level = level.upper()
    print(f"{LOG_COLORS[level]}{message}{LOG_COLORS['RESET']}", **kwargs)


def ask_yes_no(question):
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


def download_families_metadata():
    "Download metadata of all available font families to specified filepath"

    res = requests.get(url="https://fonts.google.com/metadata/fonts")

    if res.status_code != 200:
        log("error", f"Request to '{res.url}' failed. {res.reason}")
        sys.exit(1)

    os.makedirs(os.path.dirname(families_metadata_file), exist_ok=True)

    with open(families_metadata_file, "w") as file:
        file.write(res.text)


def get_family_fonts(family):
    "Get list of files (including manifest files) contains in a font family"

    res = requests.get(f"https://fonts.google.com/download/list?family={family}")

    if res.status_code != 200:
        log("error", f"Request to '{res.url}' failed. {res.reason}")
        sys.exit()

    # https://fonts.google.com/download/list?family={family} return )]}' at the
    # beginning of the response. I don't know why. But this will make json parser
    # to fail.
    return json.loads(res.text[4:] if res.text.find(")]}'") == 0 else res.text)


def download_font(font, filepath, retries=5):
    """Download the given font, not complete set of font family.

    :param font: dictionary that hold information of a font, much contains 'filename' and 'url' properties.
    :param retries: number of retries if downloading the font failed
    """

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


def get_families_metadata():
    """Get metadata of all available font families"""

    if os.path.isfile(families_metadata_file):
        age = time.time() - os.stat(families_metadata_file).st_mtime

        # if fonts_metadata_file is older than 24 hours, download again.
        if age > 3600 * 24:
            download_families_metadata()
    else:
        download_families_metadata()

    return json.loads(open(families_metadata_file, "r").read())


def search_families(keywords, exact=False):
    """Search font families contain given keywords.

    :param exact: if True, given keywords will be directly compare to name of the font family. But still case-insensitive.
    """

    families_metadata = get_families_metadata()
    family_metadata_list = families_metadata["familyMetadataList"]

    results = []

    for family_metadata in family_metadata_list:
        family = family_metadata["family"].lower()

        not_found = False

        for keyword in keywords:
            keyword = keyword.replace("  ", "").strip().lower()

            if exact:
                if family != keyword:
                    not_found = True
            else:
                if family.find(keyword) == -1:
                    not_found = True

        if not not_found:
            results.append(family_metadata)

    return results


def get_family_metadata(family_name):
    """Get metadata of a specific font family"""

    families = search_families([family_name], True)

    if len(families) == 0:
        __family_not_found(family_name, True)

    return families[0]


def resolve_family_name(family_name):
    return get_family_metadata(family_name)["family"]


def get_family_info(family_name, isRaw=False):
    """Get metadata of a specific font family in pretty print format

    :param isRaw: if True, return is raw json format (contains extra informations)
    """

    family_metadata = get_family_metadata(family_name)

    if family_metadata is None:
        __family_not_found(family_name, True)

    content = ""

    if isRaw:
        content = json.dumps(family_metadata, indent=2)
    else:
        content = f"""
            \r\033[32m{family_metadata['family']}\033[0m
            \r------------
            \r\033[32mCategory\033[0m   : {family_metadata['category']}
            \r\033[32mSubsets\033[0m    : {', '.join(family_metadata['subsets'])}
            \r\033[32mFonts\033[0m      : {', '.join(list(family_metadata['fonts'].keys()))}
            \r\033[32mDesigners\033[0m  : {', '.join(family_metadata['designers'])}
            \r\033[32mOpenSource\033[0m : {family_metadata['isOpenSource']}
        \r"""

    return content


def download_family(unsafe_family_name):
    """Download complete set of given font family"""

    family_metadata = get_family_metadata(unsafe_family_name)

    if family_metadata is None:
        __family_not_found(unsafe_family_name, True)

    family = family_metadata["family"]

    dir = os.path.join(fonts_dir, family.replace(" ", "_"))
    os.makedirs(dir, exist_ok=True)

    family_fonts = get_family_fonts(family)
    manifest_files = family_fonts["manifest"]["files"]
    font_files = family_fonts["manifest"]["fileRefs"]

    successed = []
    cached = []
    failed = []

    for manifest in manifest_files:
        with open(os.path.join(dir, manifest["filename"]), "w") as file:
            file.write(manifest["contents"])

    current = 1
    total = len(font_files)
    for font in font_files:
        log("info", f"({current}/{total}) Downloading {font['filename']}")

        status = download_font(font, os.path.join(dir, font["filename"]))

        if status == "success":
            successed.append(font)
        elif status == "cached":
            cached.append(font)
        else:
            failed.append(font)

        current = current + 1

    if shutil.which("fc-cache"):
        os.system("fc-cache")

    log("info", f"Success {len(successed) + len(cached)} Failed {len(failed)} Cached {len(cached)}")
    log("info", "Installation finish.")


def remove_family(family):
    """Remove already installed font family. If given font family wasn't installed yet, do nothing."""

    family = resolve_family_name(family)
    dir = os.path.join(fonts_dir, family.replace(" ", "_"))

    if os.path.isdir(dir):
        os.removedirs(dir)
        if shutil.which("fc-cache"):
            os.system("fc-cache")


def get_installed_families():
    """Get installed font families"""

    families = []

    for dir in os.listdir(fonts_dir) if os.path.isdir(fonts_dir) else []:
        if not dir.startswith("."):
            family = dir.replace("_", " ")
            families.append(family)

    return families


def get_license_content(family):
    """
    Get license of a font family. Not just license name, including its contents.
    """
    family_fonts = get_family_fonts(family)

    for manifest in family_fonts["manifest"]["files"]:
        if manifest["filename"] == "LICENSE.txt" or manifest["filename"] == "OFL.txt":
            return manifest["contents"]

    return "License not found"


def preview_font(font, preview_text=None, font_size=48):
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


def split_long_text(text, max_words_count):
    """
    Add line break at every {max_words_count} words
    """

    result = ""

    words = text.split(" ")
    for index in range(0, len(words), max_words_count):
        end = index + max_words_count
        result = result + " ".join(words[index:end]) + "\n"

    return result
