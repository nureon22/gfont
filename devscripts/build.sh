#!/bin/bash

# Build wheel package

python3 -m venv --upgrade-deps .

. bin/activate

pip install poetry

poetry build