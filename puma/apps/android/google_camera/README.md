# Google camera - Android

Google Camera is a the camera application that is preinstalled on Google Pixel devices.

Currently, it is only possible to take a picture and to switch between the front and rear camera.

The app can be installed on Pixel phones
through [the Play Store](https://play.google.com/store/apps/details?id=com.google.android.GoogleCamera).

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