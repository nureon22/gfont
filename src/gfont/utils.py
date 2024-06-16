import os
import sys
import time

import requests

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
    print(f"{LOG_COLORS[level.upper()]}{message}{LOG_COLORS['RESET']}", **kwargs)


def ask_yes_no(question: str) -> bool:
    isinstance_check(question, str, "First argument 'question' must be 'str'")

    while True:
        answer = input(f"{question} [y|N] ").upper().strip()[0]
        if answer == "":
            return False
        elif answer == "N":
            return False
        elif answer == "Y":
            return True


def family_not_found(family_name, exit=True):
    log("error", f"'{family_name}' cannot be found")

    if exit:
        sys.exit(1)


def split_long_text(text: str, max_words_count: int):
    """
    Add line break at every {max_words_count} words
    """

    isinstance_check(text, str, "First argument 'text' must be 'str'")
    isinstance_check(max_words_count, int, "Second argument 'max_words_count' must be 'int'")

    result = ""

    words = text.split(" ")
    for index in range(0, len(words), max_words_count):
        end = index + max_words_count
        result = result + " ".join(words[index:end]) + "\n"

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


def download_file(url: str, filepath: str, retries: int = 5, cache_age: int = 0):
    isinstance_check(url, str, "First argument 'url' must be 'str'")
    isinstance_check(filepath, str, "Second argument 'filepath' must be 'str'")
    isinstance_check(retries, int, "Third argument 'retries' must be 'int'")
    isinstance_check(cache_age, int, "Fourth argument 'cache_age' must be 'int'")

    if os.path.isfile(filepath):
        if cache_age > time.time() - os.path.getmtime(filepath):
            time.sleep(0.1)
            return "cached"

    need_retry = False

    try:
        res = requests.get(url, timeout=10)

        if res.status_code == 200:
            write_bytes_file(filepath, res.content)
        else:
            log("error", f"Downloading '{url}' failed. {res.reason}")
            need_retry = True

    except Exception as exception:
        log("error", f"Downloading '{url}' failed. {exception} ")
        need_retry = True

    if need_retry:
        if retries > 0:
            log("warning", f"Retrying '{url}'")
            download_file(url, filepath, retries - 1, cache_age)
        else:
            log("warning", f"Skipping '{url}'")
            return "failed"

    return "successed"
