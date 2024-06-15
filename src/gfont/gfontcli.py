import argparse

from . import gfontlibs as libs
from .version import version


def search_command(args):
    installed_families = libs.get_installed_families()

    for family in libs.search_families(args.keywords):
        if family in installed_families:
            print("\033[34m{}\033[0m [installed]".format(family))
        else:
            print("\033[34m{}\033[0m".format(family))


def info_command(args):
    if args.license:
        print(libs.get_license_content(libs.resolve_family_name(args.family, True)))
    else:
        print(libs.get_family_info(libs.resolve_family_name(args.family, True), args.raw))


def list_command(args):
    installed_families = libs.get_installed_families()
    installed_families.sort()

    if args.all:
        for family in libs.get_available_families():
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
    families = [libs.resolve_family_name(family, True) for family in args.family[0]]

    if libs.IS_ASSUME_YES or libs.ask_yes_no('Installing "{}"\nDo you want to continue'.format('", "'.join(families))):
        for family in families:
            libs.download_family(family)


def remove_command(args):
    families = [libs.resolve_family_name(family, True) for family in args.family[0]]

    if libs.IS_ASSUME_YES or libs.ask_yes_no('Removing "{}"\nDo you want to continue'.format('", "'.join(families))):
        for family in families:
            libs.remove_family(family)


def preview_command(args):
    fonts = libs.get_family_fonts(libs.resolve_family_name(args.family, True))["font_files"]

    regular_font: dict | None = None

    for font in fonts:
        if "Regular" in font["filename"]:
            regular_font = font

    if regular_font:
        libs.preview_font(regular_font, args.text if args.text else None)


def webfont_command(args):
    families = [family for family in args.family[0]]

    for family in families:
        libs.pack_webfonts(libs.resolve_family_name(family, True), args.dir)


def main():
    argparser = argparse.ArgumentParser(
        prog="gfont",
        description="Browse and download fonts from fonts.google.com",
    )
    argparser.add_argument("-v", "--version", action="store_true", help="show version and exit")

    subparsers = argparser.add_subparsers(title="commands")

    # search sub-command
    search_parser = subparsers.add_parser("search", help="search available font families")
    search_parser.add_argument(
        "keywords",
        nargs="+",
        help="Enter the keywords to search available font families",
    )
    search_parser.set_defaults(func=search_command)

    # info sub-command
    info_parser = subparsers.add_parser("info", help="show informations of a font family")
    info_parser.add_argument("--license", action="store_true", help="print license contents of a font family")
    info_parser.add_argument("--raw", action="store_true", help="print information in raw json format")
    info_parser.add_argument("family", help="Name of font family (case-insensitive)")
    info_parser.set_defaults(func=info_command)

    # list sub-command
    list_parser = subparsers.add_parser("list", help="list installed font families")
    list_parser.add_argument("--all", action="store_true", help="list all available font families")
    list_parser.set_defaults(func=list_command)

    # install sub-command
    install_parser = subparsers.add_parser("install", help="install a font family")
    install_parser.add_argument(
        "-y", "--yes", action="store_true", help="Assume 'yes' as answer to all prompts and run non-interactively."
    )
    install_parser.add_argument("--no-cache", action="store_true", help="download the font again, even it is already downloaded")
    install_parser.add_argument("family", action="append", nargs="+", help="Name of the font family (case-insensitive)")
    install_parser.set_defaults(func=install_command)

    # remove sub-command
    remove_parser = subparsers.add_parser("remove", help="remove a font family")
    remove_parser.add_argument(
        "-y", "--yes", action="store_true", help="Assume 'yes' as answer to all prompts and run non-interactively."
    )
    remove_parser.add_argument("family", action="append", nargs="+", help="Name of the font family (case-insensitive)")
    remove_parser.set_defaults(func=remove_command)

    # preview sub-command
    preview_parser = subparsers.add_parser("preview", help="preview a font family")
    preview_parser.add_argument("--text", help="Write any preview text you want")
    preview_parser.add_argument("family", help="Name of the font family (case-insensitive)")
    preview_parser.set_defaults(func=preview_command)

    # webfont sub-command
    webfont_parser = subparsers.add_parser("webfont", help="pack a font family to use in websites")
    webfont_parser.add_argument("--dir", required=True, help="directory to place the packed webfonts")
    webfont_parser.add_argument("--no-cache", action="store_true", help="download the font again, even it is already downloaded")
    webfont_parser.add_argument("family", action="append", nargs="+", help="Name of the font family (case-insensitive)")
    webfont_parser.set_defaults(func=webfont_command)

    args = argparser.parse_args()

    if "version" in args and args.version:
        print(version)

    if "yes" in args and args.yes:
        libs.IS_ASSUME_YES = True

    if "no_cache" in args and args.no_cache:
        libs.IS_NO_CACHE = True

    if "func" in args:
        args.func(args)


if __name__ == "__main__":
    main()
