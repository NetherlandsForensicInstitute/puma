# Installation

## Installation scripts

The scripts in the [install folder](../install) install everything Puma needs, and create a
[Python venv](https://docs.python.org/3/library/venv.html) named `venv` in the root of this repository with the
requirements of Puma. Run them as your own user, outside any venv. You can run them again at any time: they skip what is
already installed.

On Windows 10 or 11, in PowerShell:

```shell
powershell -ExecutionPolicy Bypass -File install\install_windows.ps1
```

On macOS, or on Linux with apt (Debian, Ubuntu, Kali):

```shell
bash install/install_macos_linux.sh
```

Open a new terminal afterwards, so it picks up the new environment variables.

## What the scripts install

The scripts use the package manager of your system: winget on Windows, Homebrew on macOS (they install Homebrew when it
is missing) and apt on Linux.

| Dependency | Why Puma needs it | Windows | macOS | Linux |
|------------|-------------------|---------|-------|-------|
| Python 3.10 or newer | Runs Puma | winget, 3.12 | Homebrew, 3.12 | apt, the version of the distribution |
| adb | Talks to Android devices | Download from Google | Download from Google | Download from Google |
| Node.js | Runs Appium | winget, unless Node.js is installed | Homebrew | [nvm](https://github.com/nvm-sh/nvm) |
| Appium, with the UiAutomator2 driver | Operates the apps | npm | npm | npm |
| Appium XCUITest driver | Operates iOS apps | - | appium | - |
| Tesseract | OCR, which some apps need | winget | Homebrew | apt |
| ffmpeg | Screen recordings on iOS and `video_utils.py` | winget | Homebrew | apt |

Appium needs the environment variable `ANDROID_HOME` to point to an Android SDK folder that contains
`platform-tools/adb`. When `ANDROID_HOME` is not set, the scripts install adb in the default folder of Android Studio
(`%LOCALAPPDATA%\Android\Sdk` on Windows, `~/Library/Android/sdk` on macOS, `~/Android/Sdk` on Linux) and set
`ANDROID_HOME` and `ANDROID_SDK_ROOT` to it. They add adb to the `PATH`. On Windows they set these as user environment
variables, on macOS and Linux they add them to the profile of your shell (`~/.zshrc`, `~/.bashrc` or
`~/.bash_profile`).

The scripts do not install:

- Xcode, which you need to automate iOS devices. Install it from the App Store. See [setting up iOS devices](setup-ios.md).
- Android Studio, which you only need to run an emulator. See
  [setting up Android devices](setup-android.md#optional-android-studio-for-running-an-emulator).
- [Appium Inspector](https://github.com/appium/appium-inspector/releases), which helps you write Puma code for new apps.

## Installing Puma

Install Puma with pip. We recommend installing packages within [a Python venv](https://docs.python.org/3/library/venv.html).

```shell
pip install pumapy
```

Puma needs a running Appium server. Start it in a separate terminal, and keep it running while you use Puma:

```shell
appium
```

## Optional: OCR module

Puma has an OCR module which is required for some apps. See the documentation of the apps you want ot use whether you
need OCR.

Top use the OCR module you need to install Tesseract:

```shell
sudo apt install tesseract-ocr
# or on macOS
brew install tesseract
```

Or use the Windows installer.

## Optional: FFMPEG

To use `video_utils.py`, or to record the screen of an iOS device, you need to install ffmpeg:

```shell
sudo apt install ffmpeg
# or on macOS
brew install ffmpeg
```

This utils code offers a way to process screen recordings (namely concatenating videos and stitching them together
horizontally).
