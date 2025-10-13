# Google camera - Android

Google Camera is the camera application that is preinstalled on Google Pixel devices.

Currently, it is only possible to take a picture and to switch between the front and rear camera.

The app can be installed on Pixel phones
through [the Play Store](https://play.google.com/store/apps/details?id=com.google.android.GoogleCamera).

## Deprecation

This class does not use `StateGraph` as its base class, and has therefore been deprecated since Puma 3.0.0. It can still
be used, but it will not be maintained. If you want to add functionality, please rewrite this class using `StateGraph`
as the abstract base class. Also see the [CONTRIBUTING.md](../../../../CONTRIBUTING.md).

## Prerequisites

- The application is installed on your device

### Initialization is standard:

```python
from puma.apps.android.google_camera.google_camera import GoogleCameraActions

phone = GoogleCameraActions("emulator-5554")
```

### Using the camera

You can take pictures, and switch from front to back:

```python
# simply take a picture
phone.take_picture()
# switch to the front camera to take a picture
phone.switch_camera()
phone.take_picture()
# switch back to the rear camera to take a picture
phone.switch_camera()
phone.take_picture()
```