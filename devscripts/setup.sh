#!/bin/bash

# Setup Development Environment

python3 -m venv --upgrade-deps .

. bin/activate

pip install poetry

poetry install

pre-commit install