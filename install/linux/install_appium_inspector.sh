#!/bin/bash

# Exit on error
set -e

# Download and setup Appium Inspector
echo "Setting up Appium Inspector..."
APPIUM_INSPECTOR_DIR="$HOME/.appium-inspector"
mkdir -p $APPIUM_INSPECTOR_DIR

# Create launcher script
USER_BIN_DIR="$HOME/bin"
mkdir -p "$USER_BIN_DIR"
APPIUM_INSPECTOR_SCRIPT="$USER_BIN_DIR/appium_inspector"

if [ -f "$APPIUM_INSPECTOR_SCRIPT" ]; then
        echo "Appium Inspector is already installed."
        exit 0
fi

APPIUM_INSPECTOR_FILE="$APPIUM_INSPECTOR_DIR/appium-inspector.AppImage"
if [ -f "$CURRENT_DIR/Appium-inspector.AppImage" ]; then
   cp "$CURRENT_DIR/Appium-inspector.AppImage" APPIUM_INSPECTOR_FILE
else
  # Download Appium Inspector for Linux
  APPIUM_INSPECTOR_URL="https://github.com/appium/appium-inspector/releases/download/v2025.3.1/Appium-Inspector-2025.3.1-linux-x64.tar.gz"

  echo "Downloading Appium Inspector for Linux..."
  curl -L $APPIUM_INSPECTOR_URL -o "$APPIUM_INSPECTOR_FILE"
  chmod +x "$APPIUM_INSPECTOR_FILE"
fi


cat > $APPIUM_INSPECTOR_SCRIPT << EOF
#!/bin/bash
$APPIUM_INSPECTOR_FILE "\$@"
EOF
chmod +x "$APPIUM_INSPECTOR_SCRIPT"

source "$CURRENT_DIR"/../common/get_shell.sh
SHELL_PROFILE=$(shell_profile)

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$USER_BIN_DIR"; then
    echo "export PATH=\$PATH:$USER_BIN_DIR" >> "$SHELL_PROFILE"
    export PATH=$PATH:$USER_BIN_DIR
fi
