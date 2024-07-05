import argparse

from . import gfontlibs as libs, utils
from .constants import VERSION

IS_ASSUME_YES = False
IS_NO_CACHE = False


def search_command(args):
    installed_families = libs.get_installed_families()

    for family in libs.search_families(args.keywords):
        if family in installed_families:
            print("\033[34m{}\033[0m [installed]".format(family))
        else:
            print("\033[34m{}\033[0m".format(family))


def info_command(args):
    print(libs.get_printable_info(libs.resolve_family(args.family, True), args.raw))


def list_command(args):
    installed_families = libs.get_installed_families()
    installed_families.sort()

    if args.all:
        for family in libs.get_families():
            if family in installed_families:
                print("\033[34m{}\033[0m [installed]".format(family))
            else:
                print("\033[34m{}\033[0m".format(family))
    else:
        if len(installed_families) == 0:
            print("No installed font families")
        else:
            for family in installed_families:
                print("\033[34m{}\033[0m".format(family))


def install_command(args):
    print("Installing:")
    for family in args.family:
        print(f"  \033[34m{libs.resolve_family(family, True)}\033[0m")

    if IS_ASSUME_YES or utils.ask_yes_no("Do you want to continue?"):
        for family in args.family:
            libs.install_family(family, IS_NO_CACHE)


def remove_command(args):
    print("Removing:")
    for family in args.family:
        print(f"  \033[34m{libs.resolve_family(family, True)}\033[0m")

    if IS_ASSUME_YES or utils.ask_yes_no("Do you want to continue?"):
        for family in args.family:
            libs.remove_family(family)


def update_command(args):
    families = libs.get_installed_families()

    print("Updating:")
    for family in families:
        print(f"  \033[34m{family}\033[0m")

    if IS_ASSUME_YES or utils.ask_yes_no("Do you want to continue?"):
        for family in families:
            libs.install_family(family, IS_NO_CACHE)


def preview_command(args):
    libs.preview_family(args.family, args.text if args.text else None)


def webfont_command(args):
    families = [family for family in args.family]

    for family in families:
        if ":" in family:
            [family, variants] = family.split(":")
            libs.pack_webfonts(libs.resolve_family(family), args.dir, variants.split(","))
        else:
            libs.pack_webfonts(libs.resolve_family(family), args.dir)


helps = {
    "search__help": "search available font families",
    "search__keywords": "enter the keywords to search available font families",
    "info__help": "show information of the font family",
    "info__raw": "show information in raw json format",
    "info__family": "name of the font family (case-insensitive)",
    "list__help": "list installed font families",
    "list__all": "list all available font families",
    "install__help": "install one or more font families",
    "install__yes": "assume 'yes' as answer to all prompts and run non-interactively",
    "install__no_cache": "download the font again, even it is already downloaded",
    "install__family": "name of the font family (case-insensitive)",
    "remove__help": "remove one or more font families",
    "remove__yes": "assume 'yes' as answer to all prompts and run non-interactively",
    "remove__family": "name of the font family (case-insensitive)",
    "update__help": "update installed font families",
    "update__yes": "assume 'yes' as answer to all prompts and run non-interactively",
    "preview__help": "preview the font families",
    "preview__text": "write any preview text you want",
    "preview__family": "name of the font family (case-insensitive)",
    "webfont__help": "pack a font family to use in websites",
    "webfont__dir": "directory to place the packed webfonts",
    "webfont__no_cache": "download the font again, even it is already downloaded",
    "webfont__family": "name of the font family (case-insensitive). To pack only specific font variants use <family>:<variant> (e.g. Roboto:400, Roboto:700,700i)",
}


def main():
    argparser = argparse.ArgumentParser(
        prog="gfont", description="Browse and download fonts from fonts.google.com"
    )
    argparser.add_argument("-v", "--version", action="store_true", help="show version and exit")

    subparsers = argparser.add_subparsers(title="commands")

    # search sub-command
    search_parser = subparsers.add_parser("search", help=helps["search__help"])
    search_parser.add_argument("keywords", nargs="+", help=helps["search__keywords"])
    search_parser.set_defaults(func=search_command)

    # info sub-command
    info_parser = subparsers.add_parser("info", help=helps["info__help"])
    info_parser.add_argument("--raw", action="store_true", help=helps["info__raw"])
    info_parser.add_argument("family", help=helps["info__family"])
    info_parser.set_defaults(func=info_command)

    # list sub-command
    list_parser = subparsers.add_parser("list", help=helps["list__help"])
    list_parser.add_argument("--all", action="store_true", help=helps["list__all"])
    list_parser.set_defaults(func=list_command)

    # install sub-command
    install_parser = subparsers.add_parser("install", help=helps["install__help"])
    install_parser.add_argument("-y", "--yes", action="store_true", help=helps["install__yes"])
    install_parser.add_argument("--no-cache", action="store_true", help=helps["install__no_cache"])
    install_parser.add_argument("family", nargs="+", help=helps["install__family"])
    install_parser.set_defaults(func=install_command)

    # remove sub-command
    remove_parser = subparsers.add_parser("remove", help=helps["remove__help"])
    remove_parser.add_argument("-y", "--yes", action="store_true", help=helps["remove__yes"])
    remove_parser.add_argument("family", nargs="+", help=helps["remove__family"])
    remove_parser.set_defaults(func=remove_command)

    # update sub-command
    update_parser = subparsers.add_parser("update", help=helps["update__help"])
    update_parser.add_argument("-y", "--yes", action="store_true", help=helps["update__yes"])
    update_parser.set_defaults(func=update_command)

    # preview sub-command
    preview_parser = subparsers.add_parser("preview", help=helps["preview__help"])
    preview_parser.add_argument("--text", help=helps["preview__text"])
    preview_parser.add_argument("family", help=helps["preview__family"])
    preview_parser.set_defaults(func=preview_command)

    # webfont sub-command
    webfont_parser = subparsers.add_parser("webfont", help=helps["webfont__help"])
    webfont_parser.add_argument("--dir", required=True, help=helps["webfont__dir"])
    webfont_parser.add_argument("--no-cache", action="store_true", help=helps["webfont__no_cache"])
    webfont_parser.add_argument("family", nargs="+", help=helps["webfont__family"])
    webfont_parser.set_defaults(func=webfont_command)

    args = argparser.parse_args()

    global IS_ASSUME_YES
    global IS_NO_CACHE

    if "version" in args and args.version:
        return print(VERSION)

    if "yes" in args and args.yes:
        IS_ASSUME_YES = True

    if "no_cache" in args and args.no_cache:
        IS_NO_CACHE = True

    if "func" in args:
        args.func(args)


if __name__ == "__main__":
    main()
