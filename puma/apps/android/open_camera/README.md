# Open Camera - Android

Open Camera is an open source camera application for Android.

Puma supports taking pictures and video, switching between front and rear camera, and zooming.

The app can be installed from [the Play Store](https://play.google.com/store/apps/details?id=net.sourceforge.opencamera)
or [F-Droid](https://f-droid.org/packages/net.sourceforge.opencamera/).

## Prerequisites

- The application is installed on your device

### Initialization is standard:

```python
from puma.apps.android.open_camera.open_camera import OpenCamera

phone = OpenCamera("emulator-5554")
```

### Using the camera

You can take pictures, and switch from front to back:

```python
# simply take a picture
phone.take_picture()
# switch to the front camera to take a picture
phone.take_picture(front_camera=True)
# switch back to the rear camera to take a picture
phone.take_picture()
# taking video requires a duration:
phone.take_video(duration=10)  # ten seconds of recording
# We can zoom
phone.take_picture(zoom_amount=1.0)
phone.take_picture(zoom_amount=0.5)
```