#!/bin/bash
set -e

echo "Installing NVM..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "Installing Node.js 22 (LTS)..."
nvm install 22
nvm use 22
nvm alias default 22

if ! command -v appium &> /dev/null; then
  echo "Installing Appium..."
  npm install -g appium
else
  echo "Appium is already installed"
fi

# Install the driver only if it isn't already there
if ! appium driver list --installed 2>&1 | grep -q uiautomator2; then
  appium driver install uiautomator2
fi

appium --version