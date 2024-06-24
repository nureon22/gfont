import os
import platform

system_platform = platform.system()

if system_platform == "Linux":
    FONTS_DIR = os.path.expanduser("~/.local/share/fonts/gfont")
    CACHE_DIR = os.path.expanduser("~/.cache/gfont")
    CACHE_FILE = os.path.join(CACHE_DIR, "families.json")
elif system_platform == "Darwin":
    FONTS_DIR = os.path.expanduser("~/Library/Fonts/gfont")
    CACHE_DIR = os.path.expanduser("~/Library/Caches/gfont")
    CACHE_FILE = os.path.join(CACHE_DIR, "families.json")
else:
    raise Exception("You system is not supported yet")


REQUEST_TIMEOUT = 10
MAX_WORKERS = 4
FONT_CACHE_AGE = 3600 * 24 * 30
METADATA_CACHE_AGE = 3600 * 24 * 7
BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0"
VERSION = "0.8.1"

# Note: Please don't you my API_KEY outside this application
API_KEY = "AIzaSyDBVcn95JW2QN7Ttm5CfP_R7qRewHJa074"
API_URL = f"https://www.googleapis.com/webfonts/v1/webfonts?key={API_KEY}"

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
