import sys
from typing import Dict, List, Optional, Tuple

from .. import utils
from .base import GFontPluginBase


class GFontPluginManager():
    def __init__(self, plugins: Tuple[GFontPluginBase]):
        self.plugins = plugins

    def find_plugin(self, family):
        for plugin in self.plugins:
            if family in plugin.get_families():
                return plugin

        utils.log("ERROR", "Family '{}' cannot be found".format(family))
        sys.exit(1)

    def info(self, family: str, raw: bool = False) -> str:
        plugin = self.find_plugin(family)
        return plugin.get_printable_info(family, raw)

    def install(self, family: str, nocache: bool = False):
        plugin = self.find_plugin(family)
        plugin.install_family(family, nocache)

    def remove(self, family: str):
        plugin = self.find_plugin(family)
        plugin.remove_family(family)

    def pack_webfonts(self, family: str, dir: str, clean: bool, styles: str = "", **parameters: Optional[str]):
        plugin = self.find_plugin(family)
        plugin.pack_webfonts(family, dir, clean, styles, **parameters)

    def search(self, keywords: List[str], exact: bool = False) -> List[str]:
        result = []

        for plugin in self.plugins:
            families = plugin.search_families(keywords, exact)
            families = utils.format_families_by_plugin(plugin.plugin_id(), families)
            result.extend(families)

        return result

    def get_families(self) -> List[str]:
        result = []

        for plugin in self.plugins:
            families = plugin.get_families()
            families = utils.format_families_by_plugin(plugin.plugin_id(), families)
            result.extend(families)

        return result

    def get_installed_families(self) -> List[str]:
        result = []

        for plugin in self.plugins:
            families = plugin.get_installed_families()
            families = utils.format_families_by_plugin(plugin.plugin_id(), families)
            result.extend(families)

        return result

    def get_available_updates(self) -> List[str]:
        result = []

        for plugin in self.plugins:
            families = plugin.get_available_updates()
            families = utils.format_families_by_plugin(plugin.plugin_id(), families)
            result.extend(families)

        return result

    def resolve_family(self, family: str) -> str:
        for plugin in self.plugins:
            resolved_family = plugin.resolve_family(family, False)

            if resolved_family:
                return resolved_family

        utils.log("ERROR", f"Family {family} cannot be found")
        sys.exit(1)
