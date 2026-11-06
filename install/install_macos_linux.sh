#!/usr/bin/env bash
# Installs everything Puma needs on macOS, or on Linux with apt (Debian, Ubuntu, Kali): Python, adb, Node.js, Appium
# with its drivers, Tesseract and ffmpeg. Then it creates a venv in the repository root with the requirements of Puma.
# Run it again at any time: it skips what is already installed.
#
# Usage: bash install/install_macos_linux.sh
set -euo pipefail

PUMA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OS="$(uname -s)"
MARKER="# Added by the Puma installer"

step() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

[ "$(id -u)" -ne 0 ] || die "Run this script as your own user, without sudo. It asks for your password when it needs it."
[ -z "${VIRTUAL_ENV:-}" ] || die "Deactivate your virtual environment first (run: deactivate)."

case "$OS" in
  Darwin)
    if ! have brew; then
      step "Installing Homebrew"
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    for brew in /opt/homebrew/bin/brew /usr/local/bin/brew; do
      [ -x "$brew" ] && eval "$("$brew" shellenv)" && break
    done
    have brew || die "Homebrew is not on the PATH. Open a new terminal and run this script again."

    step "Installing Python, Node.js, Tesseract and ffmpeg with Homebrew"
    brew install python@3.12 node tesseract ffmpeg
    PYTHON=python3.12
    SDK_DEFAULT="$HOME/Library/Android/sdk"
    ADB_ZIP=platform-tools-latest-darwin.zip
    PROFILE_EXTRA="eval \"\$($(command -v brew) shellenv)\""
    ;;
  Linux)
    # shortcut: apt only, add other package managers when someone needs them
    have apt-get || die "This script supports Linux distributions with apt. Install the dependencies in docs/installation.md by hand."

    step "Installing Python, Tesseract and ffmpeg with apt"
    sudo apt-get update
    sudo apt-get install -y curl unzip python3 python3-venv python3-pip tesseract-ocr ffmpeg
    PYTHON=python3
    "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 10))' \
      || die "Puma needs Python 3.10 or newer, but your distribution has $($PYTHON -V). Upgrade your distribution."

    # The Node.js of most distributions is too old for Appium, and npm needs no sudo with nvm
    step "Installing Node.js with nvm"
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] || curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
    set +eu  # nvm does not work with these options
    . "$NVM_DIR/nvm.sh"
    nvm install --lts && nvm alias default 'lts/*'
    set -eu
    have node || die "Could not install Node.js with nvm."
    SDK_DEFAULT="$HOME/Android/Sdk"
    # shortcut: Google ships these for x86_64 only; on arm64 install adb from apt and set ANDROID_HOME by hand
    ADB_ZIP=platform-tools-latest-linux.zip
    PROFILE_EXTRA=""
    ;;
  *)
    die "Unsupported operating system: $OS. Use install_windows.ps1 on Windows."
    ;;
esac

# Appium needs ANDROID_HOME to point to an Android SDK folder that contains platform-tools/adb
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$SDK_DEFAULT}}"
if [ ! -x "$SDK/platform-tools/adb" ]; then
  step "Installing adb in $SDK"
  tmp="$(mktemp -d)"
  curl -fsSL "https://dl.google.com/android/repository/$ADB_ZIP" -o "$tmp/platform-tools.zip"
  mkdir -p "$SDK"
  unzip -q -o "$tmp/platform-tools.zip" -d "$SDK"
  rm -rf "$tmp"
fi
export ANDROID_HOME="$SDK" ANDROID_SDK_ROOT="$SDK" PATH="$SDK/platform-tools:$PATH"

case "$(basename "${SHELL:-}")" in
  zsh) PROFILE="$HOME/.zshrc" ;;
  bash) [ "$OS" = Darwin ] && PROFILE="$HOME/.bash_profile" || PROFILE="$HOME/.bashrc" ;;
  *) PROFILE="$HOME/.profile" ;;
esac
if ! grep -qF "$MARKER" "$PROFILE" 2>/dev/null; then
  step "Adding ANDROID_HOME and adb to $PROFILE"
  {
    printf '\n%s\n' "$MARKER"
    [ -z "$PROFILE_EXTRA" ] || printf '%s\n' "$PROFILE_EXTRA"
    printf 'export ANDROID_HOME="%s"\n' "$SDK"
    printf 'export ANDROID_SDK_ROOT="%s"\n' "$SDK"
    printf 'export PATH="$ANDROID_HOME/platform-tools:$PATH"\n'
  } >> "$PROFILE"
fi

step "Installing Appium and its drivers"
have appium || npm install -g appium
DRIVERS=uiautomator2
[ "$OS" = Darwin ] && DRIVERS="uiautomator2 xcuitest"
INSTALLED="$(appium driver list --installed --json 2>/dev/null)"
for driver in $DRIVERS; do
  [[ "$INSTALLED" == *"\"$driver\""* ]] || appium driver install "$driver"
done

step "Creating the virtual environment in $PUMA_ROOT/venv"
[ -d "$PUMA_ROOT/venv" ] || "$PYTHON" -m venv "$PUMA_ROOT/venv"
"$PUMA_ROOT/venv/bin/python" -m pip install --upgrade pip
"$PUMA_ROOT/venv/bin/python" -m pip install -r "$PUMA_ROOT/requirements.txt"

step "Installed versions"
echo "Python:    $("$PUMA_ROOT/venv/bin/python" -V)"
echo "adb:       $(adb version | head -n 1)"
echo "Node.js:   $(node -v)"
echo "Appium:    $(appium -v)"
echo "Tesseract: $(tesseract --version 2>&1 | head -n 1)"
echo "ffmpeg:    $(ffmpeg -version | head -n 1)"
if [ "$OS" = Darwin ] && ! xcodebuild -version >/dev/null 2>&1; then
  echo
  echo "WARNING: Xcode is missing. You need it to automate iOS devices. Install it from the App Store, then run:"
  echo "  sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
fi

cat <<EOF

Puma is ready. Open a new terminal, so it picks up the new settings, and run:
  appium                              # keep this running while you use Puma
  source "$PUMA_ROOT/venv/bin/activate"   # in a second terminal
EOF
