import os
import re
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from requests import request

from .. import utils
from ..constants import FONTS_DIR, LICENSES, REQUEST_TIMEOUT


class GFontPluginBase(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def plugin_id(self) -> str:
        pass

    @abstractmethod
    def get_families(self, refresh: bool = False) -> List[str]:
        """
        Get a list of families
        """
        pass

    @abstractmethod
    def get_metadata(self, family: str, extra: bool = False) -> Dict[str, Any]:
        """
        Get metadata of given family
        """
        pass

    def get_printable_info(self, family: str, raw: bool = False):
        """
        Get metadata of given family in printable format
        """

        metadata = self.get_metadata(family, True)

        max_length = os.get_terminal_size().columns
        line_breaker = "\n            "
        axes = [f"@{x['tag']}={x['min']}>{x['max']}" for x in metadata["axes"]]

        content = ""
        content += f"\033[01;34m{metadata['family']}\033[0m\n"
        content += "------------\n"
        content += f"\033[34mVersion\033[0m   : {metadata['version']}\n"
        content += f"\033[34mCategory\033[0m  : {metadata['category']}\n"
        content += utils.split_long_text(f"\033[34mSubsets\033[0m   : {', '.join(metadata['subsets'])}\n", max_length, ", ", line_breaker)
        content += utils.split_long_text(f"\033[34mVariants\033[0m  : {', '.join(metadata['variants'])}\n", max_length, ", ", line_breaker)
        content += utils.split_long_text(f"\033[34mAxes\033[0m      : {', '.join(axes) if axes else 'None'}\n", max_length, ", ", line_breaker)
        content += utils.split_long_text(f"\033[34mDesigners\033[0m : {', '.join(metadata['designers'])}\n", max_length, ", ", line_breaker)
        content += utils.split_long_text(f"\033[34mLicense\033[0m   : {LICENSES[metadata['license']][0]}", max_length, ", ", line_breaker)

        return content

    def get_installed_families(self):
        """
        Get a list already installed families
        """

        available_families = self.get_families()
        installed_families = []
        subdir = os.path.join(FONTS_DIR, self.plugin_id())

        if os.path.isdir(subdir):
            for family in os.listdir(subdir):
                family = family.replace("_", " ")
                if family in available_families:
                    installed_families.append(family)

        return installed_families

    def get_available_updates(self) -> List[str]:
        """
        Get a list of families available to update
        """

        # Force to refresh metadata cache file
        self.get_families(True)

        families = []

        for family in self.get_installed_families():
            lastModified = datetime.fromisoformat(self.get_metadata(family)["lastModified"])

            if lastModified.timestamp() > time.time():
                families.append(family)

        return families

    def install_family(self, family: str, nocache: bool = False):
        """
        Install the given family
        """

        metadata = self.get_metadata(family)

        subdir = os.path.join(FONTS_DIR, self.plugin_id(), family.replace(" ", "_"))
        fonts = []

        for [variant, url] in metadata["files"].items():
            filename = family.replace(" ", "_")
            filename = filename + "-" + utils.resolve_variant(variant, False)  # Convert to standard font variant
            filename = filename + os.path.splitext(url)[1]  # Add file extension
            fonts.append({"filename": filename, "url": url})

        lastModified = datetime.fromisoformat(metadata["lastModified"])
        self.download_fonts(family, fonts, subdir, nocache or lastModified.timestamp() > time.time())

        if shutil.which("fc-cache"):
            subprocess.call("fc-cache")

        print(f"Installation '{family}' finished.")

    def remove_family(self, family: str):
        """
        Remove the already installed family
        """

        subdir = os.path.join(FONTS_DIR, self.plugin_id(), family.replace(" ", "_"))

        if os.path.isdir(subdir):
            shutil.rmtree(subdir)

            if shutil.which("fc-cache"):
                subprocess.call("fc-cache")

            print("Removing '{}' finished".format(family))

    def resolve_family(self, family: str, exact: bool = False) -> str:
        """
        Resolve the family name that contains (case-insensitive, underscore) to valid one
        """

        _family = family
        family = re.sub(r"[-_\+]", " ", family)
        families = self.get_families()

        if family in families:
            return family

        for x in families:
            if x.lower() == family:
                return x

        utils.log("Error", f"Family '{_family}' cannot be found")
        sys.exit(1)

    def search_families(self, keywords: List[str], exact: bool = False) -> List[str]:
        """
        Search font families contain given keywords.

        :param exact -
            if True, given keywords will be directly compare to name
            of the font family. But still case-insensitive.
        :return - Return a list contains font family names
        """

        results = []

        for family in self.get_families():
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

    def download_fonts(self, family: str, fonts: List[Dict], dir: str, nocache: bool = False):
        """
        Download the given font, not complete set of font family.

        :param fonts: List of dictionary that hold information of a font, should contains 'filename' and 'url' properties.
        """

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

        utils.need_internet_connection()
        utils.thread_pool_loop(_download, fonts)

    def pack_webfonts(self, family: str, dir: str, clean: bool, styles: str = "", **parameters: Optional[str]):
        """Pack a font family to use in websites as self-hosted fonts"""

        family = self.resolve_family(family)
        family_kebab = utils.kebab_case(family)

        webfonts_css = self.get_webfonts_css(family, True, styles, **parameters)
        subdir = os.path.join(dir, family_kebab)

        fonts = list(set(re.findall(r"url\(([^\)]+)\)", webfonts_css)))
        fonts = [{"url": font, "filename": f"{utils.unique_name()}.woff2"} for font in fonts]

        if clean:
            utils.empty_directory(subdir)
        self.download_fonts(family, fonts, subdir, True)

        for font in fonts:
            webfonts_css = webfonts_css.replace(font["url"], f"{family_kebab}/" + font["filename"])
        utils.write_file(f"{dir}/{family_kebab}.css", webfonts_css)

        print(f"Packing '{family}' webfonts finished.")
