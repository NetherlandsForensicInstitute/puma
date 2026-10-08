# App Store - iOS

The App Store is the app store built into iOS, developed by Apple.
Puma supports the basic features of the App Store to install and manage apps.
For detailed information on each method, see the method its PyDoc documentation.

The App Store is part of iOS, so its version is the iOS version.

## Prerequisites

- A real iOS device, set up for Puma as described in
  [Using Puma apps on iOS](../../../../docs/setup-ios.md#using-puma-apps-on-ios). Simulators have no App Store.
- The device is signed in with an Apple Account
- The machine running Puma has an internet connection. Puma uses it to look up the App Store id of an app, which it
  needs to open the page of the app.
- Puma cannot enter a password, or confirm with the side button, Face ID or Touch ID. Turn these off for free
  downloads, so Puma can install apps without being stopped by a confirmation:
  1. Open Settings, tap your name (Apple Account) at the top, tap Media & Purchases, and tap Password Settings. Turn
     off the toggle next to *Require Password* under *Free Downloads*.
  2. Settings > Face ID & Passcode (or Touch ID & Passcode), and turn off *iTunes & App Store*.

  The first time an app is downloaded, iOS shows a sheet to confirm the download. With step 2, it has an *Install*
  button, which Puma clicks. Without step 2, the sheet asks to *Double Click to Install* with the side button. If iOS
  still asks for the password of your Apple Account after the Install button (check step 1), Puma cannot continue: it
  closes the sheet and raises an `AppStoreError`. Apps that were downloaded before (shown as *Redownload*) are
  installed without a sheet. Paid apps always need a confirmation, so Puma cannot install them.

## Initialization

Apps are not available in every country, so the two-letter country code of the App Store of your device is required.
Puma looks up apps in that App Store. An app that is not in it cannot be installed, and Puma raises an `AppStoreError`:

```python
from puma.apps.ios.app_store.app_store import AppStore

phone = AppStore("00008110-000A1B2C3D4E5F6G", country="nl")
```

On a real device, also pass the signing settings, see
[Using Puma apps on iOS](../../../../docs/setup-ios.md#using-puma-apps-on-ios).

## Managing specific apps

Puma supports installing, uninstalling, and updating specific apps. The bundle id of the app is required:
```python
# we can install multiple apps
phone.install_app('com.duolingo.DuolingoMobile')
phone.install_app('net.whatsapp.WhatsApp')
# installing an app that is already installed will do nothing
phone.install_app('net.whatsapp.WhatsApp')

# we can remove apps. As with installing, this won't raise an error if the app was already uninstalled.
# The App Store cannot remove apps, so Puma removes the app without using the App Store, which also works for apps
# that are not in the App Store
phone.uninstall_app('com.duolingo.DuolingoMobile')

# if an update is available we can install it. As with other methods, this method does not raise an error if there was no update available
phone.update_app('net.whatsapp.WhatsApp')
```

Aside from executing actions, you can also look up the state of an app:
```python
state = phone.get_app_state('net.whatsapp.WhatsApp')
```

This state can have the following values:
1. `NOT_INSTALLED`: the app is not yet installed
2. `INSTALLED`: the app is installed and has no update available
3. `UPDATE_AVAILABLE`: the app is installed and has an update available
4. `INSTALLING`: the app is being installed or updated. The App Store does not show which of the two.
5. `UNKNOWN`: An unknown state Puma does not recognize

`install_app` and `update_app` wait until the app is really installed or updated, which can take a while. If this takes
longer than `timeout` seconds (default 120), a `TimeoutError` is raised. Puma tries a failed action a second time, so
it can take twice as long before the error reaches you. Use a larger timeout for big apps or a slow connection:
```python
phone.install_app('com.duolingo.DuolingoMobile', timeout=300)
```
If the app is already being installed, they wait for that installation to finish. `update_all_apps` does not wait.

### Updating all apps

Aside from managing specific apps, Puma can also trigger an update for all apps in the App Store:
```python
phone.update_all_apps()
```
