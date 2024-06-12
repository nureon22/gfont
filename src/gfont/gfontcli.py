import argparse

from . import gfontlibs


def search_command(args):
    installed_families = gfontlibs.get_installed_families()

    for family in gfontlibs.search_families(args.keywords):
        if family["family"] in installed_families:
            print(f"\033[34m{family['family']}\033[0m [installed]")
        else:
            print(f"\033[34m{family['family']}\033[0m")


def info_command(args):
    if args.license:
        print(gfontlibs.get_license_content(gfontlibs.resolve_family_name(args.family.replace("_", " "))))
    else:
        print(gfontlibs.get_family_info(args.family.replace("_", " "), args.raw))


def list_command(args):
    installed_families = gfontlibs.get_installed_families()

    if args.installed:
        if len(installed_families) == 0:
            print("No installed font families")
        else:
            for family in installed_families:
                print(f"\033[34m{family}\033[0m")
    else:
        for family_metadata in gfontlibs.get_families_metadata()["familyMetadataList"]:
            if family_metadata["family"] in installed_families:
                print(f"\033[34m{family_metadata['family']}\033[0m [installed]")
            else:
                print(f"\033[34m{family_metadata['family']}\033[0m")


def install_command(args):
    family = gfontlibs.resolve_family_name(args.family.replace("_", " "))
    if gfontlibs.ask_yes_no(f"Installing '{family}'"):
        gfontlibs.download_family(family)


def remove_command(args):
    family = gfontlibs.resolve_family_name(args.family.replace("_", " "))
    if gfontlibs.ask_yes_no(f"Installing '{family}'"):
        gfontlibs.remove_family(family)


def preview_command(args):
    family = gfontlibs.resolve_family_name(args.family.replace("_", " "))
    fonts = gfontlibs.get_family_fonts(family)["manifest"]["fileRefs"]

    regular_font: dict | None = None

    for font in fonts:
        if "Regular" in font["filename"]:
            regular_font = font

    if regular_font:
        gfontlibs.preview_font(regular_font, args.text if args.text else None)


def main():
    argparser = argparse.ArgumentParser(
        prog="gfont",
        description="Browse and download fonts from fonts.google.com",
    )
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
    list_parser = subparsers.add_parser("list", help="list available font families")
    list_parser.add_argument("--installed", action="store_true", help="list only installed font families")
    list_parser.set_defaults(func=list_command)

    # install sub-command
    install_parser = subparsers.add_parser("install", help="install a font family")
    install_parser.add_argument("family", help="Name of the font family (case-insensitive)")
    install_parser.set_defaults(func=install_command)

    # remove sub-command
    remove_parser = subparsers.add_parser("remove", help="remove a font family")
    remove_parser.add_argument("family", help="Name of the font family (case-insensitive)")
    remove_parser.set_defaults(func=remove_command)

    # preview sub-command
    preview_parser = subparsers.add_parser("preview", help="preview a font family")
    preview_parser.add_argument("--text", help="Write any preview text you want")
    preview_parser.add_argument("family", help="Name of the font family (case-insensitive)")
    preview_parser.set_defaults(func=preview_command)

    args = argparser.parse_args()

    if "func" in args:
        args.func(args)


if __name__ == "__main__":
    main()
