import sys, os, requests, json, time, argparse

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
        raise Exception(
            f"Downloading {res.url} failed with status code {res.status_code}"
        )

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
    except:
        if retries:
            return __download_font(font, filepath, retries - 1)
        else:
            print(f"\033[31mFailed {font['filename']}\033[0m")
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

    if family_metadata == None:
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

    if family_metadata == None:
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
            families.append(dir)

    return families


def search_command(args):
    for family in search_families(args.keywords):
        print("\033[94m{}\033[0m".format(family["family"]))


def info_command(args):
    print(get_family_info(args.family.replace("_", " "), args.raw))


def list_command(args):
    if args.installed:
        installed_families = get_installed_families()

        if len(installed_families) == 0:
            print("No installed font families")
        else:
            print(installed_families)
    else:
        for family_metadata in get_families_metadata()["familyMetadataList"]:
            print(family_metadata["family"])


def install_command(args):
    download_family(args.family.replace("_", " "))

def remove_command(args):
    remove_family(args.family.replace("_", " "))

def main():
    argparser = argparse.ArgumentParser(
        prog="gfont",
        description="Browse and download fonts from fonts.google.com",
        exit_on_error=True,
    )
    subparsers = argparser.add_subparsers(title="commands")

    # search sub-command
    search_parser = subparsers.add_parser(
        "search", help="search available font families"
    )
    search_parser.add_argument(
        "keywords",
        nargs="+",
        help="Enter the keywords to search available font families",
    )
    search_parser.set_defaults(func=search_command)

    # info sub-command
    info_parser = subparsers.add_parser(
        "info", help="show informations of a font family"
    )
    info_parser.add_argument(
        "--raw", action="store_true", help="print information in raw json format"
    )
    info_parser.add_argument("family", help="Name of font family (case-insensitive)")
    info_parser.set_defaults(func=info_command)

    # list sub-command
    list_parser = subparsers.add_parser("list", help="list available font families")
    list_parser.add_argument("--installed", action="store_true", help="list only installed font families")
    list_parser.set_defaults(func=list_command)

    # install sub-command
    install_parser = subparsers.add_parser("install", help="install a font family")
    install_parser.add_argument(
        "family", help="Name of the font family (case-insensitive)"
    )
    install_parser.set_defaults(func=install_command)

    # remove sub-command
    remove_parser = subparsers.add_parser("remove", help="remove a font family")
    remove_parser.add_argument(
        "family", help="Name of the font family (case-insensitive)"
    )
    remove_parser.set_defaults(func=remove_command)

    args = argparser.parse_args()
    args.func(args)