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
MAX_WORKERS = 10
FONT_CACHE_AGE = 3600 * 24 * 30
BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0"
VERSION = "0.7.3"
