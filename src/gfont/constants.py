import os
import platform

system_platform = platform.system()

if system_platform == "Linux":
    FONTS_DIR = os.path.expanduser("~/.local/share/fonts/gfont")
    CACHE_DIR = os.path.expanduser("~/.cache/gfont")
elif system_platform == "Darwin":
    FONTS_DIR = os.path.expanduser("~/Library/Fonts/gfont")
    CACHE_DIR = os.path.expanduser("~/Library/Caches/gfont")
else:
    raise Exception("You system is not supported yet")

CACHE_FILE = os.path.join(CACHE_DIR, "families.json")

REQUEST_TIMEOUT = 10
MAX_WORKERS = 4
BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
VERSION = "0.13.1"

FONT_VARIANT_STANDARD_NAMES = {
    "100": "Thin",
    "100i": "ThinItalic",
    "200": "ExtraLight",
    "200i": "ExtraLightItalic",
    "300": "Light",
    "300i": "LightItalic",
    "400": "Regular",
    "400i": "RegularItalic",
    "500": "Medium",
    "500i": "MediumItalic",
    "600": "SemiBold",
    "600i": "SemiBoldItalic",
    "700": "Bold",
    "700i": "BoldItalic",
    "800": "ExtraBold",
    "800i": "ExtraBoldItalic",
    "900": "Black",
    "900i": "BlackItalic",
}

LICENSES = {
    "apache2": ["Apache-2.0", "https://opensource.org/license/apache-2-0"],
    "ofl": ["OFL-1.1", "https://opensource.org/license/ofl-1-1"],
    "ufl": ["UFL-1.0", "http://font.ubuntu.com/ufl/"],
}
