import argparse
import json
import logging
import os
import sys
import time

import requests

# fonts_metadata.json will be refreshed every 24 hours
families_metadata_file = os.path.expandvars("$HOME/.cache/gfont/families_metadata.json")
fonts_dir = os.path.expandvars("$HOME/.local/share/fonts/gfont")


def __family_not_found(family_name, exit=False):
    print("\033[31m'{}' not found\033[0m".format(family_name))

    if exit:
        sys.exit(1)


def __download_families_metadata():
    res = requests.get(url="https://fonts.google.com/metadata/fonts")

    if res.status_code != 200:
        print(f"Fetching {res.url} failed with status code {res.status_code}")
        sys.exit(1)

    os.makedirs(os.path.dirname(families_metadata_file), exist_ok=True)

    with open(families_metadata_file, "w") as file:
        file.write(res.text)


def __get_family_fonts(family: str):
    res = requests.get(f"https://fonts.google.com/download/list?family={family}")

    if res.status_code != 200:
        raise Exception(f"Downloading {res.url} failed with status code {res.status_code}")

    # https://fonts.google.com/download/list?family={family} return )]}' at the
    # beginning of the response. I don't know why. But this will make json parser
    # to fail.
    return json.loads(res.text[4:] if res.text.find(")]}'") == 0 else res.text)


def __download_font(font: dict, filepath: str, retries=5):
    print(f"Downloading {font['filename']}")

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    content: bytes

    try:
        res = requests.get(font["url"], timeout=5)

        if res.status_code != 200:
            raise Exception(res)

        content = res.content
    except Exception as ex:
        if retries:
            return __download_font(font, filepath, retries - 1)
        else:
            print(f"\033[31mFailed {font['filename']}\033[0m")
            logging.error(ex)
            return False

    with open(filepath, "wb") as file:
        file.write(content)

    return True


def get_families_metadata():
    if os.path.isfile(families_metadata_file):
        age = time.time() - os.stat(families_metadata_file).st_mtime

        # if fonts_metadata_file is older than 24 hours, download again.
        if age > 3600 * 24:
            __download_families_metadata()
    else:
        __download_families_metadata()

    return json.loads(open(families_metadata_file, "r").read())


def search_families(keywords: list[str], exact: bool = False):
    families_metadata = get_families_metadata()
    family_metadata_list = families_metadata["familyMetadataList"]

    results = []

    for family_metadata in family_metadata_list:
        family = family_metadata["family"].lower()

        is_found = False

        for keyword in keywords:
            keyword = keyword.replace("  ", "").strip().lower()

            if exact:
                if family == keyword:
                    is_found = True
            else:
                if family.find(keyword) == 0:
                    is_found = True

        if is_found:
            results.append(family_metadata)

    return results


def get_family_metadata(family_name: str) -> dict:
    families = search_families([family_name], True)

    if len(families) == 0:
        __family_not_found(family_name, True)

    return families[0]


def resolve_family_name(family_name: str):
    return get_family_metadata(family_name)["family"]


def get_family_info(family_name: str, isRaw: bool = False):
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
            \r\033[32mCategory\033[0m  : {family_metadata['category']}
            \r\033[32mSubsets\033[0m   : {', '.join(family_metadata['subsets'])}
            \r\033[32mFonts\033[0m     : {', '.join(list(family_metadata['fonts'].keys()))}
            \r\033[32mDesigners\033[0m : {', '.join(family_metadata['designers'])}
        \r"""

    return content


def download_family(unsafe_family_name: str):
    family_metadata = get_family_metadata(unsafe_family_name)

    if family_metadata is None:
        __family_not_found(unsafe_family_name, True)

    family = family_metadata["family"]

    dir = os.path.join(fonts_dir, family.replace(" ", "_"))
    os.makedirs(dir, exist_ok=True)

    print("Downloading '{}'".format(family))

    family_fonts = __get_family_fonts(family)
    manifest_files = family_fonts["manifest"]["files"]
    font_files = family_fonts["manifest"]["fileRefs"]

    successed = []
    failed = []

    for manifest in manifest_files:
        with open(os.path.join(dir, manifest["filename"]), "w") as file:
            file.write(manifest["contents"])

    for font in font_files:
        if __download_font(font, os.path.join(dir, font["filename"])):
            successed.append(font)
        else:
            failed.append(font)

    if len(failed) > 0:
        print("\nRetrying failed downloads")

        for font in failed:
            __download_font(font, os.path.join(dir, font["filename"]))

    print("Success {}. Failed {}.".format(len(successed), len(failed)))
    print("Installation finish.")


def remove_family(family):
    family = resolve_family_name(family)
    dir = os.path.join(fonts_dir, family.replace(" ", "_"))

    if os.path.isdir(dir):
        os.removedirs(dir)


def get_installed_families():
    families = []

    for dir in os.listdir(fonts_dir) if os.path.isdir(fonts_dir) else []:
        if not dir.startswith("."):
            family = dir.replace("_", " ")
            families.append(family)

    return families