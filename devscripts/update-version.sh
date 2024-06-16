#!/bin/sh

if [ -z "$1" ]; then
    echo -e "\033[31mYou didn't provide any version number\033[0m"
    exit 1
fi

sed -i -E "s/^version = .+/version = \"$1\"/" pyproject.toml
sed -i -E "s/^VERSION = .+/VERSION = \"$1\"/" src/gfont/constants.py
