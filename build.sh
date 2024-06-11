#!/bin/sh

python3 -m venv .

. bin/activate

pip install -r requirements.txt

poetry install

python3 -m build
