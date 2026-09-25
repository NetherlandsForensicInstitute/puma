# Setting up iOS devices

Automating iOS requires a Mac with [Xcode](https://developer.apple.com/xcode/) installed, and the Appium XCUITest driver
(`appium driver install xcuitest`, the macOS installation script does this for you). You can use an iOS simulator or a
physical device. The device should be connected to the Internet and have its language set to English.

The first time Puma connects to an iOS device, Appium builds and installs WebDriverAgent on the device, which can take a
few minutes.

## Simulators

**Simulators** work out of the box. List the available simulators with `xcrun simctl list devices`, and start one with
`xcrun simctl boot <udid>` or from Xcode. Note that the App Store is not available on simulators, so only apps that are
preinstalled or that you build yourself can be automated.

Get the UDID of a running simulator, which is what you pass to Puma:

```shell
xcrun simctl list devices booted
```

## Physical devices

**Physical devices** need some preparation:

1. Connect the device to your Mac with a cable, unlock it and tap **Trust** when asked to trust the computer.
2. Open Xcode (Window > Devices and Simulators) so the device is paired with Xcode. This makes the Developer Mode setting
   appear on the device.
3. Enable [Developer Mode](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device)
   (Settings > Privacy & Security > Developer Mode). The device restarts.
4. Enable UI Automation (Settings > Developer > Enable UI Automation).
5. Add your Apple ID to Xcode (Settings > Accounts), and create an **Apple Development** certificate
   (Manage Certificates... > + > Apple Development). A free Apple ID is enough.
6. Get the UDID of the device. Note that `xcrun devicectl list devices` shows a different identifier, which Appium does
   not accept:

   ```shell
   xcrun xctrace list devices
   ```

7. Appium installs WebDriverAgent on the device, which needs to be signed with your Apple developer account. Pass your
   team id and signing identity as desired capabilities, see
   [the Appium documentation on real device configuration](https://appium.github.io/appium-xcuitest-driver/latest/preparation/real-device-config/).
   With a free Apple ID, WebDriverAgent also needs a bundle id of your own:

   ```python
   from puma.apps.ios.safari.safari import Safari

   phone = Safari("00008110-000A1B2C3D4E5F6G", desired_capabilities={
       "appium:xcodeOrgId": "<your team id>",
       "appium:xcodeSigningId": "Apple Development",
       "appium:updatedWDABundleId": "com.<your name>.WebDriverAgentRunner",  # free Apple ID only
   })
   ```

   Your team id is the `OU` of your certificate, shown in Xcode (Settings > Accounts), or with
   `security find-certificate -c "Apple Development" -p | openssl x509 -noout -subject`.
8. The first connection installs WebDriverAgent. With a free Apple ID, iOS then refuses to start it until you trust your
   developer certificate on the device: Settings > General > VPN & Device Management > your Apple ID > Trust.
9. Keep the device unlocked while Puma runs: iOS does not start apps on a locked device. Setting Auto-Lock to Never
   (Settings > Display & Brightness) helps.

Devices managed by an organization (MDM) can be configured to refuse pairing with a computer, or to block Developer Mode.
In that case, only the administrator of the device can allow this.

See [troubleshooting](troubleshooting.md#ios) if the device does not connect.

## Multiple devices

Puma gives each iOS device its own WebDriverAgent ports (derived from its UDID), so multiple devices and simulators can
safely share one Appium server. You can override these with the `appium:wdaLocalPort` and `appium:mjpegServerPort`
capabilities.

## iOS specifics

Some iOS specifics to be aware of:

- iOS has no back button. Puma navigates back using the back button in the navigation bar, or by swiping from the left
  edge of the screen.
- System pop-ups such as permission requests are handled automatically, by granting the permission.
- Screen recording (`start_recording()`) requires [ffmpeg](installation.md#optional-ffmpeg) on the Mac running Appium.
- Apps built into iOS (Safari, Contacts, Apple Maps) change with iOS updates, so their supported version is the iOS
  version.
