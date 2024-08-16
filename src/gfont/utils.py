import os
import random
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from requests import request

from .constants import FONT_VARIANT_STANDARD_NAMES, MAX_WORKERS

LOG_COLORS = {
    "DEBUG": "\033[34m",  # Blue
    "INFO": "\033[0m",  # Default
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Purple
    "RESET": "\033[0m",
}

__generated_unique_name = []
__is_online: None | bool = None


def check_internet_connection(host, port):
    global __is_online

    if __is_online is not None:
        return __is_online

    try:
        sock = socket.create_connection((host, port), 5)
        sock.close()
        __is_online = True
        return __is_online
    except OSError:
        pass

    __is_online = False
    return __is_online


def need_internet_connection():
    if not check_internet_connection("8.8.8.8", 53):
        log("ERROR", "No Internet Connection")
        sys.exit(1)


def isinstance_check(value, instance, message):
    if not isinstance(value, instance):
        raise TypeError(message)


def log(level: str, message: str, **kwargs):
    print(f"{LOG_COLORS[level.upper()]}{level.upper()}: {message}{LOG_COLORS['RESET']}", **kwargs)


def ask_yes_no(question: str, default: str = "yes") -> bool:
    isinstance_check(question, str, "First argument 'question' must be 'str'")

    if default == "yes":
        return (input(f"{question} [Y|n] ") or "Y").upper().strip()[0] == "Y"
    else:
        return (input(f"{question} [y|N] ") or "N").upper().strip()[0] == "Y"


def split_long_text(text: str, max_length: int, separator: str = " ", line_breaker: str = "\n"):
    """
    Add line break at every {max_length} words
    """

    isinstance_check(text, str, "First argument 'text' must be 'str'")
    isinstance_check(max_length, int, "Second argument 'max_length' must be 'int'")

    result = [""]

    for word in text.split(separator):
        last_result = result[-1]

        if last_result != "":
            result[-1] = last_result = last_result + separator

        if len(last_result + word) > max_length:
            result.append(line_breaker + word)
        else:
            result[-1] = last_result + word

    return "".join(result)


def read_file(filepath: str):
    isinstance_check(filepath, str, "First argument 'filepath' must be 'str'")

    if not os.path.isfile(filepath):
        return None

    with open(filepath, "r") as file:
        content = file.read()
        file.close()

    return content


def write_file(filepath: str, content: str):
    isinstance_check(filepath, str, "First argument 'filepath' must be 'str'")
    isinstance_check(content, str, "Second argument 'content' must be 'str'")

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as file:
        file.write(content)
        file.close()


def write_bytes_file(filepath: str, content: bytes):
    isinstance_check(filepath, str, "First argument 'filepath' must be 'str'")
    isinstance_check(content, bytes, "Second argument 'content' must be 'bytes'")

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as file:
        file.write(content)
        file.close()


def download_file(url: str, filepath: str, cache_age: int = 0):
    isinstance_check(url, str, "First argument 'url' must be 'str'")
    isinstance_check(filepath, str, "Second argument 'filepath' must be 'str'")
    isinstance_check(cache_age, int, "Third argument 'cache_age' must be 'int'")

    if os.path.isfile(filepath):
        if cache_age > time.time() - os.path.getmtime(filepath):
            return

    res = request("GET", url, timeout=10)
    res.raise_for_status()

    write_bytes_file(filepath, res.content)


def thread_pool_loop(func, items, *args):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(func, item, *args) for item in items]
        return [future.result() for future in as_completed(futures)]


def resolve_variant(variant: str, short: bool):
    _variant = variant

    if variant == "regular":
        variant = "400"
    if variant == "italic":
        variant = "400i"

    variant = variant.replace("italic", "i")

    if variant not in FONT_VARIANT_STANDARD_NAMES:
        log("ERROR", f"Font variant '{_variant}' is not valid")
        sys.exit(1)

    return variant if short else FONT_VARIANT_STANDARD_NAMES[variant]


def resolve_variants(variants: List[str], short: bool):
    return [resolve_variant(x, short) for x in variants]


def kebab_case(text: str):
    return text.lower().replace(" ", "-")


def snake_case(text: str):
    return text.lower().replace(" ", "_")


def unique_name():
    chars = "abcdefghijklmnopqrstuvwxyz"
    result = "".join([random.choice(chars) for _i in range(16)])

    if result in __generated_unique_name:
        return unique_name()
    else:
        __generated_unique_name.append(result)
        return result


def empty_directory(dir: str):
    if not os.path.isdir(dir):
        return

    for filename in os.listdir(dir):
        filepath = os.path.join(dir, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)


def format_families_by_plugin(plugin_id, families):
    return ["{} - {}".format(plugin_id, family) for family in families]
