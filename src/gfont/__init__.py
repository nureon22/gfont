import argparse

from . import gfontlibs


def search_command(args):
    for family in gfontlibs.search_families(args.keywords):
        print("\033[94m{}\033[0m".format(family["family"]))


def info_command(args):
    print(gfontlibs.get_family_info(args.family.replace("_", " "), args.raw))


def list_command(args):
    if args.installed:
        installed_families = gfontlibs.get_installed_families()

        if len(installed_families) == 0:
            print("No installed font families")
        else:
            print(installed_families)
    else:
        for family_metadata in gfontlibs.get_families_metadata()["familyMetadataList"]:
            print(family_metadata["family"])


def install_command(args):
    gfontlibs.download_family(args.family.replace("_", " "))


def remove_command(args):
    gfontlibs.remove_family(args.family.replace("_", " "))


def main():
    argparser = argparse.ArgumentParser(
        prog="gfont",
        description="Browse and download fonts from fonts.google.com",
        exit_on_error=True,
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

    args = argparser.parse_args()
    args.func(args)
