# Settings - iOS

Settings is the settings application built into iOS.
Settings is part of iOS, so its version is the iOS version.

## Prerequisites
- A real iOS device running iOS 26. Simulators have fewer settings: there is for example no Auto-Lock setting, as
  simulators do not lock.

### Initialization is standard:

```python
from puma.apps.ios.settings.settings import Settings
phone = Settings("00008110-000A1B2C3D4E5F6G")
```

### Navigating the UI

You can read and change after how long the screen locks automatically (Auto-Lock). This is useful when running Puma on
a real device, as iOS does not start apps on a locked device:

```python
original = phone.get_auto_lock()   # the number of seconds, e.g. 30, or None for Never
phone.set_auto_lock(None)          # never lock the screen
...                                # run your Puma script
phone.set_auto_lock(original)      # restore the original setting
```

The options are 30, 60, 120, 180, 240 and 300 seconds, or None for Never.
