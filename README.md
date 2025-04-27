# Puma - Programmable Utility for Mobile Automation
![](images/Logo.svg)
Puma is a Python library for executing app-specific actions on mobile devices such as sending a message or starting a
call. The goal is that you can focus on *what* should happen rather than *how* this should happen, so rather than write
code to "tap on Bob's conversation on Alice's phone, enter the message, and press send", you can simply write "send a
Telegram message to Bob from Alice's phone".

To execute actions on the mobile device, Puma uses [Appium](https://appium.io/), and open-source project for UI
automation.

Puma was created at the NFI to improve our process of creating test and reference datasets. Our best practices on
creating test data can be found [here](docs/TESTDATA_GUIDELINES.md). If you are wondering whether you should make your
own test data, or whether you should use Puma for it, [this document](docs/TESTDATA_WHY.md) goes into the advantages of
doing so.

Puma is an open-source non-commercial project, and community contributions to add support for apps, or improve support
of existing apps are welcome! If you want to contribute, please read [CONTRIBUTING.md](CONTRIBUTING.md).

> :no_mobile_phones: Puma currently only supports Android apps. iOS apps are on our to-do list!

## Getting started

1. Install all required software (see the [requirements](#requirements) section).
2. Connect your Android device (or start an emulator), make sure it is connected properly over ADB (See the section on
   [troubleshooting](#Troubleshooting) if you encounter problems).
    - :warn: Make sure the phone is set to English, and [all other requirements](#android-devices-or-emulators) are met!
3. Get the UDID of your device by running `adb devices` (in the example below `954724ertyui74125` is the UDID of the
   device):

```shell
$ adb devices
> List of devices attached
954724ertyui74125  device
```

4. Install Puma. We recommend installing packages within [a Python venv](https://docs.python.org/3/library/venv.html).

```shell
pip install pumapy
```

5. Run Appium. This starts the Appium server, a process that needs to run while you use Puma.

```shell
appium
```

### Examples

If everything is setup correctly, you can now use Puma! Below are a few small examples to get started. If you want a
more extensive step-by-step guide on how to use (and develop) Puma, please refer to the
[Puma Tutorial](tutorial/exercises).

The code below shows a small example on how to search for the Eiffel Tower in Google Maps.

```python
from puma.apps.android.google_maps.google_maps import GoogleMapsActions

phone = GoogleMapsActions("emulator-5444")
phone.search_place('eiffel tower')
```

This is a rather simple application, in the sense that it can be used without any form of registration. Other
applications
need some additional preparation, such as WhatsApp. For this application, you first need to register with a phone
number.
These kind of prerequisites are also described in the application README. The first time you use an application, there
might be pop-ups explaining the app that Puma does not take into account, as these need to be confirmed only once. You
need
to do this manually the first time while running Puma. After registering, you can send a WhatsApp message to a contact
with the code below:

```python
from puma.apps.android.whatsapp.whatsapp import WhatsappActions

alice = WhatsappActions("<INSERT UDID HERE>")  # Initialize a connection with device
alice.create_new_chat(contact="<Insert the contact name>",
                      first_message="Hello world!")  # Send a message to contact in your contact list
alice.send_message("Sorry for the spam :)")  # we can send a second message in the open conversation
```

Congratulations, you just did a search query in Google Maps and/or sent a WhatsApp message without touching your phone!
You can now explore what other functions are possible with Puma in [WhatsApp](puma/apps/android/whatsapp/README.md), or
try a
[different application](#supported-apps). You could even start working
on [adding support for a new app](CONTRIBUTING.md).

## Supported apps

The following apps are supported by Puma. Each app has its own documentation page detailing the supported actions with
example implementations:

* [Google Camera](puma/apps/android/google_camera/google_camera.py)
* [Google Chrome](puma/apps/android/google_chrome/README.md)
* [Google Maps](puma/apps/android/google_maps/README.md)
* [Open Camera](puma/apps/android/open_camera/README.md)
* [Snapchat](puma/apps/android/snapchat/README.md)
* [Telegram](puma/apps/android/telegram/README.md)
* [TeleGuard](puma/apps/android/teleguard/README.md)
* [WhatsApp](puma/apps/android/whatsapp/README.md)

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

If you are running your script on a newer app version than the tag, it is advised to first run the test script of your
app (can be found in the [test scripts directory](test_scripts)). This test script includes each action that can be
performed on the phone, and running these first will inform you if all actions are still supported, without messing up
your experiment.

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

## Install dependencies

First off, run the installation scripts in the `install` folder.
See [the installation manual](install/README_INSTALLATION.md) for more details.

### Android Device(s) or Emulators

You can either use a physical Android device or an Android emulator.
See [Optional: Android Studio](#optional--android-studio--for-running-an-emulator-) for instructions on installing
Android Studio and running an emulator

- Have the Android device(s) or emulator(s) connected to the system where Puma runs, configured as follows:
    - Connected to the Internet
    - Language set to English
    - File transfer enabled
    - (Root access is not needed)

You can check if the device is connected:

  ```shell
  adb devices
    > List of devices attached
  894759843jjg99993  device
  ```

If the status says `device`, the device is connected and available.

### Optional: Android Studio (for running an emulator)

For more information about Android Emulators, refer
to [the Android developer website](https://developer.android.com/studio/run/managing-avds#about)
Follow these steps to create and start an Android emulator:

1. [Install Android Studio](https://developer.android.com/studio/run/managing-avds#createavd).
2. [Create an Android Virtual Device (avd)](https://developer.android.com/studio/run/managing-avds) We recommend a Pixel
   with the Playstore enabled, and a recent Android version. For running 1 or a few apps, the default configuration can
   be used.
3. [Start the emulator](https://developer.android.com/studio/run/managing-avds#emulator).

If you want to run the emulator from the commandline, refer
to [Start the emulator from the command line](https://developer.android.com/studio/run/emulator-commandline).

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

This happens when you did not allow data transfer via usb. Tap on the charging popup or go to
`settings > USB preferences` and select `File Transfer`.

### Adb device cannot connect

If the status of your device is `unauthorized`, make sure USB debugging is enabled in developer options:

- [Enable developer options](https://developer.android.com/studio/debug/dev-options)
- [Enable USB debugging](https://developer.android.com/studio/debug/dev-options#Enable-debugging)
- Connect your device to your computer, open a terminal and run `adb devices`
- Your device should now show a popup to allow USB debugging. Press always allow.

If you do not get the pop-up, reset USB debugging authorisation in `Settings > Developer options > Revoke USB debugging
authorisations` and reconnect the device and run `adb devices` again.

### Android Emulator won't start in Android Studio

We have encountered this in MacOS, but it could also occor on other platforms.
If you encounter an issue where the Android Emulator won't start, it might be due to the location where Android Studio
installs system images. By default, Android Studio installs system images in the `$HOME/Library/Android/Sdk` directory.
However, our configuration may expect the SDK to be located in a different directory, such as
`$HOME/Android/Sdk`.

A workaround is to create a symbolic link:

```bash
ln -s $HOME/Library/Android/Sdk/system-images $HOME/Android/Sdk/system-images
```

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
download [Appium Desktop](https://github.com/appium/appium-desktop/releases/), make the binary executable and start it
manually before running Puma.

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

### My application is not present on the device

Install the APK on the device you want to use.
When using an emulator, this can be done by dragging the APK file onto the emulator, this automatically installs the APK
on the device.
For physical devices as well as emulators, you could use `adb install`. See
the [developer docs](https://developer.android.com/tools/adb#move)

### Pop-ups break my code!

Some applications have pop-ups which appear the first time that the application is opened.
Puma does not handle these pop-ups, these should be manually clicked once to remove them.
The same holds for pop-ups that request permissions, these should be manually clicked.
Note: If your app has other pop-ups that happen regularly, Puma should support these.