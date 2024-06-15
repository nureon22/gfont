import sys

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
