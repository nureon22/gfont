#!/bin/python3

import json
import os

from requests import request


def resolve_variants(variants):
    result = []

    for variant in variants:
        if variant == "regular":
            result.append("400")
        elif variant == "italic":
            result.append("400i")
        else:
            result.append(variant.replace("italic", "i"))

    return result


res = request("GET", f"https://www.googleapis.com/webfonts/v1/webfonts?key={os.environ['API_KEY']}")
res.raise_for_status()

families = {}

for item in res.json()["items"]:
    del item["menu"]
    del item["kind"]
    item["variants"] = resolve_variants(item["variants"])

    if item["family"].startswith("Material"):
        item["designers"] = ["Google"]
        item["isOpenSource"] = True
        item["isBrandFont"] = False

    families[item["family"]] = item


res = request("GET", "https://fonts.google.com/metadata/fonts")
res.raise_for_status()

for item in res.json()["familyMetadataList"]:
    family = families[item["family"]]
    for prop in ["designers", "isOpenSource", "isBrandFont"]:
        if prop not in family:
            family[prop] = item[prop]

with open(os.path.join(os.path.dirname(__file__), "../src/gfont/data/families.json"), "w") as file:
    file.write(json.dumps(families, indent=4) + "\n")
    file.close()
