import json
import os
from typing import Dict, List

from requests import request

from .. import utils
from ..constants import CACHE_DIR, REQUEST_TIMEOUT
from .base import GFontPluginBase


class GFontPluginGoogle(GFontPluginBase):
    __families_metadata: Dict[str, Dict] = {}
    __families: List[str] = []

    def __init__(self):
        super().__init__()

        self.API_KEY = os.getenv("GOOGLE_FONTS_API_KEY")

    def plugin_id(self):
        return "GOOGLE"

    def get_families(self, refresh: bool = False):
        if self.API_KEY:
            url = "https://www.googleapis.com/webfonts/v1/webfonts?key=" + self.API_KEY
        else:
            url = "https://raw.githubusercontent.com/nureon22/gfont/main/data/webfonts.json"

        cache_file = os.path.join(CACHE_DIR, self.plugin_id()) + ".json"

        if refresh:
            utils.need_internet_connection()
            print("Rrefreshing families metadata", end="\033[K\r")

            res = request("GET", url, timeout=REQUEST_TIMEOUT)
            res.raise_for_status()

            self.__families_metadata = {}
            self.__families = []

            for item in res.json()["items"]:
                self.__families_metadata[item["family"]] = item
                self.__families.append(item["family"])

            utils.write_file(cache_file, json.dumps(self.__families_metadata, indent=4))

            print("", end="\033[K\r")
        else:
            if os.path.isfile(cache_file) and not self.__families_metadata and not self.__families:
                cached_content = utils.read_file(cache_file)

                if cached_content:
                    self.__families_metadata = json.loads(cached_content)
                    self.__families = list(self.__families_metadata.keys())
                else:
                    return self.get_families(True)
            else:
                return self.get_families(True)

        return self.__families

    def get_metadata(self, family, extra: bool = False):
        family_snake = utils.snake_case(family)

        if family_snake in self.__families_metadata:
            metadata = self.__families_metadata[family_snake]
        else:
            metadata = self.__families_metadata[family]

        if not extra:
            return metadata

        if "axes" not in metadata or "designers" not in metadata or "license" not in metadata:
            if family.startswith("Material Icons"):
                metadata["designers"] = ["Google"]
                metadata["axes"] = []
                metadata["license"] = "apache2"

            elif family.startswith("Material Symbols"):
                metadata["axes"] = [
                    {"tag": "opsz", "min": 20, "max": 48},
                    {"tag": "wght", "min": 100, "max": 700},
                    {"tag": "FILL", "min": 0, "max": 1},
                    {"tag": "GRAD", "min": -50, "max": 200},
                ]
                metadata["designers"] = ["Google"]
                metadata["license"] = "apache2"
            else:
                utils.need_internet_connection()
                url = f"https://fonts.google.com/metadata/fonts/{family}"
                res = request("GET", url, timeout=REQUEST_TIMEOUT)
                res.raise_for_status()
                data = json.loads(res.text.replace(")]}'", "", 1))
                metadata["designers"] = [x["name"] for x in data["designers"]]
                metadata["license"] = data["license"]
                metadata["axes"] = data["axes"]

            utils.write_file(os.path.join(CACHE_DIR, self.plugin_id()) + ".json", json.dumps(self.__families_metadata, indent=4))

        return metadata
