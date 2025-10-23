# Google Play Store - Android

Google Play Store is the app store for Android developed by Google, and the default app store on most Android devices.
Puma supports the basic features of the Play Store to install and manage apps.

The Play Store is not freely available and should come pre-installed on your device.

## Prerequisites

- The application installed on your device
- A Google account is needed to use the Play Store (no payment method required for free apps)
- Device language needs to be set to English

## Initialization

Initialization is done in the following way:

```python
from puma.apps.android.google_play_store.google_play_store import PlayStore

phone = PlayStore("emulator-5444")
```

## Managing specific apps

Puma supports installing, uninstalling, and updating specific apps. The package name of the app is required:
```python
# we can install multiple apps
phone.install('com.whatsapp')
phone.install('org.telegram.messenger')
# installing an app that is already installed will do nothing
phone.install('com.whatsapp')

# we can remove apps. As with installing, this won;t raise an error if the app was already uninstalled
phone.uninstall('com.whatsapp')

# if an update is available we can install it. As with other methods, this method does not raise an error if there was no update available
phone.update_app('com.whatsapp')
```

Aside from executing actions, you can also look up the state of an app:
```python
state = phone.get_app_status('com.whatsapp')
```

This state can have the following values:
1. `NOT_INSTALLED`: the app is not yet installed
2. `INSTALLED`: the app is installed and has no update available
3. `UPDATE_AVAILABLE`: the app is installed and has an update available
4. `INSTALLING`: the app was not yet installed and is now being installed
5. `INSTALLING_UPDATE`: the app was installed and is now being updated
6. `UNKNOWN`: An unknown state Puma does not recognize

### Updating all apps

Aside from managing specific apps, Puma can also trigger an update for all apps in the Play Store:
```python
phone.update_all_apps()
```
