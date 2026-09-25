#!/bin/bash
CURRENT_DIR=$(dirname "$(realpath "$0")")

# Exit on error
set -e

echo "Starting setup of Android SDK Platform Tools, Node.js, Appium, iOS tools, and Git for macOS..."
now=$(date +"%Y%m%d_%H:%M:%S")
mkdir -p "$CURRENT_DIR/logs"
log_path="$CURRENT_DIR/logs/$now.log"
touch "$log_path"

"$CURRENT_DIR"/macos/install_adb.sh | tee -a "$log_path"
"$CURRENT_DIR"/macos/install_node_appium.sh | tee -a "$log_path"
"$CURRENT_DIR"/macos/install_ios_tools.sh | tee -a "$log_path"
"$CURRENT_DIR"/macos/install_appium_inspector.sh | tee -a "$log_path"
"$CURRENT_DIR"/macos/setup_python_env.sh | tee -a "$log_path"

#TODO actually check instead of print
echo "Installation complete!"
echo "To verify the installation, please open a new terminal and run:"
echo "- adb version (to check Android SDK Platform Tools)"
echo "- node -v (to check Node.js version - should be v19.x.x)"
echo "- appium -v (to check Appium version)"
echo "- appium driver list --installed (should list uiautomator2 and xcuitest)"
echo "- xcodebuild -version (to check Xcode, needed for iOS)"
echo "- open -a 'Appium Inspector' (to launch Appium Inspector)"
echo "- git --version (to check Git version)"
