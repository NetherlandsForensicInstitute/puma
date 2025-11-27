# Google camera - Android

Google Camera is the camera application that is preinstalled on Google Pixel devices.

Currently, it is only possible to take a picture and to switch between the front and rear camera.

The app can be installed on Pixel phones
through [the Play Store](https://play.google.com/store/apps/details?id=com.google.android.GoogleCamera).

## Prerequisites

- The application is installed on your device

### Initialization is standard:

```python
from puma.apps.android.google_camera.google_camera import GoogleCamera

phone = GoogleCamera("emulator-5554")
```

### Using the camera

You can take pictures, and switch from front to back:

```python
# simply take a picture
phone.take_picture()
# switch to the front camera to take a picture
phone.take_picture(front_camera=True)
# switch back to the rear camera to take a picture
phone.take_picture(front_camera=False)

# take a 5-second video with the back camera
phone.record_video(5)
# take a 5-second video with the front camera
phone.record_video(5, front_camera=True)
```