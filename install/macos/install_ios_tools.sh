#!/bin/bash

# Exit on error
set -e
CURRENT_DIR=$(dirname "$(realpath "$0")")

# Load NVM, so the appium installed in install_node_appium.sh is available
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "Setting up iOS automation..."

# Xcode cannot be installed from the command line, it needs to be installed from the App Store
if ! xcodebuild -version &> /dev/null; then
  echo "WARNING: Xcode is not installed (or not selected). Xcode is required to automate iOS devices."
  echo "Install Xcode from the App Store, then run: sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
else
  echo "Found $(xcodebuild -version | head -n 1)"
fi

if appium driver list --installed 2>&1 | grep -q "xcuitest"; then
  echo "Appium XCUITest driver is already installed"
else
  echo "Installing Appium XCUITest driver..."
  appium driver install xcuitest
fi

# ffmpeg is needed for screen recordings on iOS
if ! command -v ffmpeg &> /dev/null; then
  "$CURRENT_DIR"/install_brew.sh
  # install_brew.sh runs in a subshell, so load brew in case it was just installed
  command -v brew &> /dev/null || eval "$(/opt/homebrew/bin/brew shellenv)"
  echo "Installing ffmpeg..."
  brew install ffmpeg
else
  echo "ffmpeg is already installed"
fi
