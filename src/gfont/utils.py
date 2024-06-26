import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from requests import request

from .constants import *

LOG_COLORS = {
    "DEBUG": "\033[34m",  # Blue
    "INFO": "\033[0m",  # Default
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Purple
    "RESET": "\033[0m",
}


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


def family_not_found(family_name, exit=True):
    log("error", f"Family '{family_name}' cannot be found")

    if exit:
        sys.exit(1)


def split_long_text(text: str, max_length: int):
    """
    Add line break at every {max_length} words
    """

    isinstance_check(text, str, "First argument 'text' must be 'str'")
    isinstance_check(max_length, int, "Second argument 'max_length' must be 'int'")

    result = ""

    for index in range(0, len(text), max_length):
        end = index + max_length
        result = result + text[index:end] + "\n"

    return result


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
            return time.sleep(0.1)

    res = request("GET", url, timeout=10)
    res.raise_for_status()

    write_bytes_file(filepath, res.content)


def thread_pool_loop(func, items, *args):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(func, item, *args) for item in items]
        return [future.result() for future in as_completed(futures)]
