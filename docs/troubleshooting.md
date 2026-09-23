# Troubleshooting

* [General](#general)
* [Appium](#appium)
* [Android](#android)
* [iOS](#ios)

## General

### Appium Action fails due to popup

When first using the app, sometimes you get popups the first time you do a specific action, for instance when sending
a view-once photo.
Because this only occurs the first time, it is not handled by the code. The advice is when running into this problem,
manually click `Ok` on the pop-up and try again. To ensure this does not happen in the middle of your test data script,
first do a test run by executing the test script for your application.

### Pop-ups break my code!

Some applications have pop-ups which appear the first time that the application is opened.
Puma does not handle these pop-ups, these should be manually clicked once to remove them.
The same holds for pop-ups that request permissions, these should be manually clicked.
Note: If your app has other pop-ups that happen regularly, Puma should support these.

## Appium

### ConnectionRefusedError: [Errno 111] Connection refused

This error is probably caused by Appium not running. Start Appium first and try again.

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

## Android

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

### My application is not present on the device

Install the APK on the device you want to use.
When using an emulator, this can be done by dragging the APK file onto the emulator, this automatically installs the APK
on the device.
For physical devices as well as emulators, you could use `adb install`. See
the [developer docs](https://developer.android.com/tools/adb#move)

## iOS

### iOS: WebDriverAgent fails to start

The first connection to an iOS device builds WebDriverAgent with Xcode. If this fails:

- Check that Xcode and its command line tools are installed and selected: `xcode-select -p` should point to
  `/Applications/Xcode.app/Contents/Developer`.
- On real devices, check the signing capabilities (see [setting up iOS devices](setup-ios.md#physical-devices)), and
  that UI Automation is enabled in the developer settings on the device.
- Check the Appium server output for the `xcodebuild` error. The most common errors are described below.

### iOS: "The application could not be launched because the Developer App Certificate is not trusted"

WebDriverAgent was built and installed, but iOS does not trust the certificate it is signed with. On the device, go to
Settings > General > VPN & Device Management, select your Apple ID under "Developer App", and tap Trust.

### iOS: No valid signing identities, although a certificate is present in Xcode

`security find-identity -v -p codesigning` shows `0 valid identities found`, although Xcode created an Apple Development
certificate. This happens when the intermediate certificate that issued your certificate is missing from the keychain.
Current certificates are issued by the **Apple Worldwide Developer Relations G3** intermediate: download it from
[Apple's certificate authority page](https://www.apple.com/certificateauthority/) (`AppleWWDRCAG3.cer`), and add it to
your login keychain:

```shell
security add-certificates -k ~/Library/Keychains/login.keychain-db ~/Downloads/AppleWWDRCAG3.cer
```

If adding the certificate by double-clicking it fails with error -25294, the keychain chosen in the dialog does not
exist: use the command above instead.

### iOS: "The device is configured to reject new pairings"

The device is managed by an organization (MDM), which does not allow pairing the device with a computer. Without
pairing, Developer Mode cannot be enabled and WebDriverAgent cannot be installed. Only the administrator of the device
can allow this.

### iOS: "Unable to launch ... because the device was not, or could not be, unlocked"

iOS does not start apps on a locked device. Unlock the device, and consider setting Auto-Lock to Never (Settings >
Display & Brightness) while running Puma.

### iOS: Developer Mode is not shown in the settings

The Developer Mode setting only appears after the device has been paired with Xcode: connect the device, trust the
computer, and open Window > Devices and Simulators in Xcode. On devices managed by an organization, Developer Mode can
also be blocked by the administrator.

### iOS: Private tabs in Safari cannot be opened

On real devices, Safari locks private browsing with Face ID after leaving Safari. Puma cannot unlock it, and raises a
`PrivateBrowsingLockedError`. To use private tabs, turn off "Require Face ID to Unlock Private Browsing" in Settings >
Apps > Safari.
