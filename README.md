# Puma - Programmable Utility for Mobile Automation

Puma is a Python library for executing app-specific actions on mobile devices. The goal is that you can focus on *what*
should happen rather than *how* this should happen, so rather than write code to "tap on Bob's conversation on Alice's
phone, enter the message, and press send", you can simply write "send a Telegram message to Bob from Alice's phone".

To execute actions on the mobile device, Puma uses [Appium](https://appium.io/), and open-source project for UI
automation.

Puma is an open-source non-commercial project, and community contributions to add apps, or improve support of existing
apps are welcome! If you want to contribute, please read [CONTRIBUTING.md](CONTRIBUTING.md).

> :no_mobile_phones: Puma currently only supports Android apps. iOS apps are on our to-do list!
## Installation
```bash
pip install pumapy
# Example import for WhatsApp
from puma.apps.android.whatsapp.whatsapp import WhatsappActions
```

## Example usage

The following code is an example on how to easily execute a series of actions on multiple devices:

```python
from puma.apps.android.whatsapp.whatsapp import WhatsappActions

alice = WhatsappActions("emulator-5554")  # initialize a connection with device emulator-5554
bob = WhatsappActions("emulator-5556")  # initialize a connection with device emulator-5556
# Now chatting is very easy
alice.create_new_chat("Bob", "Hi Bob, how are you?")
bob.select_chat("Alice")
bob.send_message("Hi Alice, I'm great, are we still on for the 12th Avengers movie next weekend?")
alice.send_message("Shoot, I totally forgot. Wait, I'm calling you!")
# we can even make calls
alice.call_contact()
bob.answer_call()
time.sleep(5)
bob.end_call()
```

## Supported apps

The following apps are supported by Puma. each app has its own documentation page detailing the supported actions with
example implementations:

* [WhatsApp](apps/android/whatsapp/README)
* [Telegram](apps/android/telegram/README)
* [Snapchat](apps/android/snapchat/README)

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


Although the latter one is the safest, _ie_ it will always handle navigation correctly regardless of your position, it is not very efficient. When
you send multiple messages in the same conversation consecutively, this will result in going to the home screen and
into the conversation each time you send a message. Thus, it is advised to use the first example when sending multiple
messages in the same conversation, and use the second one if you only send one message in the conversation.


## Requirements

### OS

Puma is developed and tested on Linux and Windows. MacOS is not tested by us, but might work.

### Python

Puma is tested on Python 3.10 and 3.11, we haven't tested other versions.

### ADB

Puma uses ADB to connect to Android devices for some features. [Install ADB](https://developer.android.com/tools/adb)
and ensure it's on your PATH.

### Appium

Apps are controlled through Appium. See the [Appium website](https://appium.io/docs/en/2.0/quickstart/install/) or below
how to install Appium, Appium v2.0 or greater is needed to run Puma.

```bash
sudo apt install curl
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.3/install.sh | bash
nvm install 19.0.0
npm install -g appium
appium driver install uiautomator2
```
_See [troubleshooting](#installing-appium-with-npm-fails) if installing Appium or npm fails._

- Android SDK platform tools ([Download here](https://developer.android.com/studio/releases/platform-tools)) or with the following commands:
```bash
cd /path/of/your/choosing
sudo mkdir -p android-sdk-linux/cmdline-tools
cd android-sdk-linux/cmdline-tools/ || exit
sudo wget https://dl.google.com/android/repository/commandlinetools-linux-9123335_latest.zip
sudo unzip commandlinetools-linux-9123335_latest.zip
sudo mv cmdline-tools latest
```

- `ANDROID_SDK_ROOT` environment variable set:
```bash
$ export ANDROID_SDK_ROOT={/path/to/android-sdk-linux} >> ~/.bashrc
$ source ~/.bashrc
```

- ADB (Possibly installed with platform tools, export env variable)
- One of the following browsers: Google Chrome, Chromium, updated to a relatively new version
- 1 or more Android devices connected to the system where Puma runs, with:
    - The Google Play Store installed
    - Logged in to a Google account
    - Internet connection
    - USB debugging enabled
    - Language set to English
    - Device is not secured (e.g. with a password, pattern, or fingerprint)
    - (Root access is not needed)
  - You can check if the device is connected:
    ```bash
    $ adb devices
    > List of devices attached
    847734hfdjkd93937  device
    ```
If the status says `device`, the device is connected and available.

### OCR module

If you wish to use the OCR module, you need to have tesseract installed:

```shell
sudo apt install tesseract-ocr
```

Or use the Windows installer.

### FFMPEG

To use `video_utils.py` you need to install ffmpeg:

```shell
sudo apt install ffmpeg
```

This utils code offers a way to process screen recordings (namely concatenating videos and stitching them together
horizontally).

## Troubleshooting

### Installing Appium with npm fails
If you are behind a proxy and the appium install hangs, make sure to configure your `~/.npmrc` with the following settings.
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