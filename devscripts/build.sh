#!/bin/bash

# Build wheel package

python3 -m venv .

. bin/activate

pip install -U pip

pip install -U poetry

poetry build
