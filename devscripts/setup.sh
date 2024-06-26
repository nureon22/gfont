#!/bin/bash

# Setup Development Environment

python3 -m venv .

. bin/activate

pip install -U pip

pip install -U poetry

poetry install --no-root

pre-commit install
