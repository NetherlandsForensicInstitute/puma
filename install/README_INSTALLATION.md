# Installation script instructions

To install all required dependencies and configure your machine to run Puma, simply run the installation script for your
operating system (`install_windows.bat`, `install_linux.sh` or `install_macos.sh`).

:warn: The installation scripts might not work properly on some systems. Use at your own risk. If some of the
dependencies could not be installed with the script, you can install them manually.

Note that the requirements for running an Android emulator are not included in the install scripts, as it is optional.
Please refer to [this section in the README](../README.md#optional-android-studio-for-running-an-emulator).

# What does the script do?

These scripts will:

1. Install ADB and setup the required environmental values
2. Install NodeJS and Appium
3. Install Python 3.12
4. Install Appium Inspector
5. Install all requirements in your python virtual environment

When software is installed (ADB, Node, Appium, Python, Appium Inspector), the scripts will only install the missing
components. Python 3.12 will not be installed if you already have python 3.10, 3.11 or 3.12 installed.

## ADB and environmental values

Puma needs ADB to be installed and either be available on your path, or on `ANDROID_SDK_ROOT/platform-tools/adb`.
Appium **requires** the environmental values `ANDROID_SDK_ROOT` or `ANDROID_HOME` to be set.

The script will set these values if they aren't already set, and download the latest Android SDK platform tools and
extract them to your home folder (`~/Android/Sdk/platform-tools/adb`) .

## NodeJS and Appium

Puma needs Appium, which is a Node.JS application.
The script will install Node.JS (through NVM on Linux and MacOS) and then use NPM to install Appium globally.

## Python

Puma is tested on Python 3.10, 3.11 and 3.12. The script will install 3.12 if none of these versions are installed.

## Appium inspector

Appium Inspector is a tool that can help you develop new Puma code, either for new apps, or to expand functionality in
existing apps.

On Windows and MacOS, it will be installed as a regular application (through an installer), on Linux a portable binary
will be placed in `~/.appium-inspector/appium-inspector.AppImage` and an alias will be made so you can run it from
the terminal using `appium_inspector`.

## Installing requirements in the python virtual environment

The script will create and activate [a python venv](https://docs.python.org/3/library/venv.html) in the root of this
repository, and then run `pip install -r requirements.txt`.
