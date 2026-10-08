# Settings - Android

Settings is the settings application built into Android.
Puma supports changing the brightness and screen timeout, and connecting to a Wi-Fi network.
For detailed information on each method, see the method its PyDoc documentation.

Settings is part of Android, so its version is the Android version.

## Prerequisites

- A Google Pixel device running Android 16. Other manufacturers, such as Samsung, have their own Settings app with a
  different layout, which is not supported.
- Device language needs to be set to English

## Initialization

Initialization is standard:

```python
from puma.apps.android.settings.settings import Settings

phone = Settings("emulator-5554")
```

## Brightness and screen timeout

The brightness and screen timeout have a getter and a setter. This makes it easy to put a device in a known state before
running your Puma script, and to restore the original settings afterwards:

```python
original = phone.get_screen_timeout()   # the number of seconds, e.g. 30
phone.set_screen_timeout(1800)          # keep the screen on for 30 minutes
...                                     # run your Puma script
phone.set_screen_timeout(original)      # restore the original setting

phone.set_brightness(50)                # percentage from 0 to 100
phone.get_brightness()
```

The screen timeout options are 15, 30, 60, 120, 300, 600 and 1800 seconds. When adaptive brightness is on, Android
keeps adjusting the brightness level after it has been set.

## Wi-Fi

```python
phone.connect_to_wifi("MyNetwork", "password")  # returns whether the device is connected
```

Wi-Fi is turned on if needed. The network must be in range of the device. The password is not needed for open networks
and networks that are already saved.
