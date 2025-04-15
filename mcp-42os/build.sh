#!/usr/bin/env bash
set -e

echo "===== Verifying Python version ====="
# Use python3 explicitly; check for version 3.10 or above.
python3 -c 'import sys; version = sys.version_info; assert version >= (3,10), f"Python 3.10 or above is required; found {version.major}.{version.minor}"'

echo "===== Creating virtual environment ====="
# Create the virtual environment in a folder called "venv"
python3 -m venv venv

echo "===== Activating virtual environment ====="
# Activate the venv
source venv/bin/activate

echo "===== Upgrading pip ====="
pip install --upgrade pip

echo "===== Installing dependencies from requirements.txt ====="
pip install -r requirements.txt

echo "===== Build process complete ====="