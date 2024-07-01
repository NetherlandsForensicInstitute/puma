# Puma - Programmable Utility for Mobile Automation

Puma is a Python library for executing app-specific actions on mobile devices such as sending a message or starting a 
call. The goal is that you can focus on *what* should happen rather than *how* this should happen, so rather than write
code to "tap on Bob's conversation on Alice's phone, enter the message, and press send", you can simply write "send a
Telegram message to Bob from Alice's phone".

To execute actions on the mobile device, Puma uses [Appium](https://appium.io/), and open-source project for UI
automation.

Puma is an open-source non-commercial project, and community contributions to add apps, or improve support of existing
apps are welcome! If you want to contribute, please read [CONTRIBUTING.md](CONTRIBUTING.md).

> :no_mobile_phones: Puma currently only supports Android apps. iOS apps are on our to-do list!
## Getting started
1. Install all required software (see the [requirements](#requirements) section).
    - install [ADB](#ADB)
    - install [Appium](#Appium)
2. Connect your Android device (or start an emulator), make sure it is connected properly over ADB (See the 
[troubleshooting](#Troubleshooting) if you encounter problems).
    - :warn: Make sure the phone is set to English, and [all other requirements](#Android-Devices-or-Emulators) are met!
3. Get the UDID of your device by running `adb devices` (in the example below `954724ertyui74125` is the UDID of the device):
```shell
$ adb devices
> List of devices attached
954724ertyui74125  device
```
4. Install Puma. We recommend always installing packages within [a Python venv](https://docs.python.org/3/library/venv.html).
```shell
pip install pumapy
```
5. Run Appium. This starts the Appium server, a process that needs to run while you use Puma.
```shell
appium
```
Now you can use Puma! The code below is a small example on how to send a WhatsApp message, you can run this on a phone
that has WhatsApp installed and has a registered WhatsApp account:
```python
from puma.apps.android.whatsapp.whatsapp import WhatsappActions

alice = WhatsappActions("<INSERT UDID HERE>")  # Initialize a connection with device
alice.create_new_chat(contact="<Insert the contact name>", first_message="Hello world!")  # Send a message to contact in your contact list
alice.send_message("Sorry for the spam :)")  # we can send a second message in the open conversation
```
Congratulations, you just sent a WhatsApp message without touching your phone!
You can now explore what other function are possible with Puma in [WhatsApp](puma/apps/android/whatsapp/README.md), or
try a [different application](#supported-apps). Or you could even start working on [adding support for aa new app](CONTRIBUTING.md).

## Supported apps

The following apps are supported by Puma. each app has its own documentation page detailing the supported actions with
example implementations:

* [WhatsApp](puma/apps/android/whatsapp/README.md)
* [Telegram](puma/apps/android/telegram/README.md)
* [Snapchat](puma/apps/android/snapchat/README.md)

Right now only Android is supported.

To get a full overview of all functionality and pydoc of a specific app, run

```bash
# Example for WhatsApp
python -m pydoc puma/apps/android/whatsapp/whatsapp.py
```

### Supported versions

The currently supported version of each app is mentioned in the documentation above (and in the source code). When Puma
code breaks due to UI changes (for example when app Xyz updates from v2 to v3), Puma will be updated to support Xyz v3.
This new version of Puma does will **only** be tested against Xyz v3: if you still want to use Xyz v2, you simply have
to use an older release of Puma.

To make it easy for users to lookup older versions, git tags will be used to tag app versions. So in the above example
you'd simply have to look up the tag `Xyz_v2`.

If you are running your script on a newer app version that the tag, it is advised to first run the test script of your
app (can be found in the [test scripts directory](test_scripts)). This test script includes each action that can be performed on the phone, and first running these will inform
you if all actions are still supported, without messing up your experiment.

#### Navigation
You need to be careful about navigation. For example, some methods require you to already be in a conversation. However,
most methods give you the option to navigate to a specific conversation. 2 examples:

##### Example 1
```python
from puma.apps.android.whatsapp.whatsapp import WhatsappActions

alice = WhatsappActions("emulator-5554")  # initialize a connection with device emulator-5554
alice.select_chat("Bob")
alice.send_message("message_text")
```
In this example, the message is sent in the current conversation. It is the responsibility of the user to make sure you
are in the correct conversation. So, you will have to have called `select_chat` first.

##### Example 2
```python
from puma.apps.android.whatsapp.whatsapp import WhatsappActions

alice = WhatsappActions("emulator-5554")  # initialize a connection with device emulator-5554
alice.send_message("message_text", chat="Bob")
```
In the second example, the chat conversation to send the message in is supplied as a parameter. Before the message is
sent, there will be navigated to the home screen first, and then the chat "Bob" will be selected.


Although the latter one is the safest, it is slower as it will always do some navigation before sending the message.
When you send multiple messages in the same conversation consecutively, this will result in going to the home screen and
into the conversation each time you send a message. Therefore, it is advised to use `select_chat` or the optional `chat`
argument only once, and then sticking to `send_message` without the secondary argument.


## Requirements

### OS

Puma is developed and tested on Linux and Windows. MacOS is not tested by us, but might work.

### Python

Puma is tested on Python 3.10 and 3.11, we haven't tested other versions.
Download Python [here](https://www.python.org/downloads/) or install it using apt:
```shell
sudo apt install python3.11
```

### ADB

Puma uses ADB to connect to Android devices for some features, both directly and through Appium.
To install ADB, download [the Android Sdk Platform Tools](https://developer.android.com/tools/releases/platform-tools).
Create the directory `~/Android/Sdk/` and unzip the platform-tools in this folder, so the absolute path to adb becomes `~/Android/Sdk/platform-tools/adb`. 
Then create the environmental value `ANDROID_SDK_ROOT` with the value `~/Android/Sdk/`:

```shell
$ echo 'export ANDROID_SDK_ROOT="$HOME/Android/Sdk/"' >> ~/.bashrc
$ source ~/.bashrc
```
> :warning: When running your Appium script from an IDE, you might get the error `Could not determine ANDROID_SDK_ROOT.`
> This is because the IDE might not load the environment variables correctly. Since Puma then defaults to ~/Android/Sdk,
> you will not need to do anything if you followed the steps above, and you can ignore this message. If you really want 
> to use another location, please refer to you IDE specific documentation how to set environment variables.

### Appium

Apps are controlled through Appium. See the [Appium website](https://appium.io/docs/en/2.0/quickstart/install/) or below
how to install Appium, Appium v2.0 or greater is needed to run Puma.

Appium is a NodeJS application which can be installed through NPM.
If you don't have NPM isntalled, we recommend installing NPM and Node using NVM, an application to manage your NodeJS
installation.

```shell
sudo apt install curl
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 19.0.0
```

If you have NPM installed you can install Appium:

```shell
npm install -g appium
appium driver install uiautomator2
```
_See [troubleshooting](#installing-appium-with-npm-fails) if installing Appium or npm fails._ 

### Android Device(s) or Emulators
- 1 or more Android devices or emulators connected to the system where Puma runs, with:
  - Internet connection
  - Language set to English
  - File transfer enabled
  - Recommended: disable 
  - (Root access is not needed)

You can check if the device is connected:
  ```shell
  adb devices
    > List of devices attached
  894759843jjg99993  device
  ```
If the status says `device`, the device is connected and available.

### Optional: OCR module

Puma has an OCR module which is required for some apps. See the documentation of the apps you want ot use whether you
need OCR.

Top use the OCR module you need to install Tesseract:

```shell
sudo apt install tesseract-ocr
```

Or use the Windows installer.

### Optional: FFMPEG
 
To use `video_utils.py` you need to install ffmpeg:

```shell
sudo apt install ffmpeg
```

This utils code offers a way to process screen recordings (namely concatenating videos and stitching them together
horizontally).

## Troubleshooting
### ADB shows status unauthorized
This happens when you did not allow data transfer via usb. Tap on the charging popup or go to `settings > USB preferences` and select `File Transfer`.

### Adb device cannot connect
If the status of your device is `unauthorized`, make sure USB debugging is enabled in developer options:

- [Enable developer options](https://developer.android.com/studio/debug/dev-options)
- [Enable USB debugging](https://developer.android.com/studio/debug/dev-options#Enable-debugging)
- Connect your device to your computer, open a terminal and run `adb devices`
- Your device should now show a popup to allow USB debugging. Press always allow.

If you do not get the pop-up, reset USB debugging authorisation in `Settings > Developer options > Revoke USB debugging
authorisations` and reconnect the device and run `adb devices` again.

### Installing Appium with npm fails
If you are behind a proxy and the appium install hangs, make sure to configure your `~/.npmrc` with the following
settings.
Fill in the values, restart terminal and try again:

```text
registry=<your organization registry>
proxy=<organization proxy>
https-proxy=<organization proxy>
http-proxy=<organization proxy>
strict-ssl=false
```

Alternatively, you can also
download [Appium Desktop](https://github.com/appium/appium-desktop/releases/), make the binary executable and start it manually before running Puma.

```bash
sudo chmod +x Appium-Server-GUI-*.AppImage
./Appium-Server-GUI-*.AppImage
```

- Do not change the default settings
- Click the startServer button
- Now you can run Puma

### ConnectionRefusedError: [Errno 111] Connection refused
This error is probably caused by Appium not running. Start Appium first and try again.

### Appium Action fails due to popup
When first using the app, sometimes you get popups the first time you do a specific action, for instance when sending
a view-once photo.
Because this only occurs the first time, it is not handled by the code. The advice is when running into this problem,
manually click `Ok` on the pop-up and try again. To ensure this does not happen in the middle of your test data script,
first do a test run by executing the test script for your application.