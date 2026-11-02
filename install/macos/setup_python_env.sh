#!/bin/bash

# Exit on error
set -e
CURRENT_DIR=$(dirname "$(realpath "$0")")
PUMA_ROOT="$CURRENT_DIR/../.."

# Install Brew
"$CURRENT_DIR"/install_brew.sh

# Install Python3.10
brew install python@3.12

cd "$PUMA_ROOT"

echo "Setting up a virtual environment..."
python3.12 -m venv venv

source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Puma setup completed"
