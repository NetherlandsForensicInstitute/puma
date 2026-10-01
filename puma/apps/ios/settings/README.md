# Settings - iOS

Settings is the settings application built into iOS, developed by Apple.
Puma supports part of the features of Settings.
For detailed information on each method, see the method its PyDoc documentation.

Settings is part of iOS, so its version is the iOS version.

## Prerequisites

- A real iOS device running iOS 26, set up as described in [Setting up iOS](../../../../docs/setup-ios.md).
  Simulators have fewer settings: there is for example no Auto-Lock setting, as simulators do not lock.
- Device language needs to be set to English

## Initialization

Initialization is standard:

```python
from puma.apps.ios.settings.settings import Settings

phone = Settings("00008110-000A1B2C3D4E5F6G")
```

On a real device, also pass the signing settings for WebDriverAgent as `desired_capabilities`, see
[Setting up iOS](../../../../docs/setup-ios.md).

## Auto-Lock

You can read and change after how long the screen locks automatically (Auto-Lock). This is useful when running Puma on
a real device, as iOS does not start apps on a locked device:

```python
original = phone.get_auto_lock()   # the number of seconds, e.g. 30, or None for Never
phone.set_auto_lock(None)          # never lock the screen
...                                # run your Puma script
phone.set_auto_lock(original)      # restore the original setting
```

The options are 30, 60, 120, 180, 240 and 300 seconds, or None for Never.
