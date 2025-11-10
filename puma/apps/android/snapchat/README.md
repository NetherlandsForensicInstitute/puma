# Snapchat - Android

Snapchat is an American messaging app developed by Snap Inc.
Puma supports has limited support for Snapchat.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.snapchat.android).

## Prerequisites

- The application installed on your device
- Registration with a phone number

## Initialization

Initialization is standard:

```python
from puma.apps.android.snapchat.snapchat import Snapchat

phone = Snapchat("emulator-5444")
```

### Sending a message

We can send a simple text message:

```python
# Send a message to a recipient
phone.send_message(msg="Hi charlie!", recipients="Charlie")
phone.send_message(msg="Hi charlie!", recipients="Charlie")
```

### Send a Snap

We can send a snap to specific people, or post it to My Story:

```python
phone.toggle() # changes the direction of the camera
phone.take_photo(caption="Hi Charlie!") # takes a photo and puts a caption on it
phone.send_snap_to(recipients=["Charlie"]) # sends the previously taken photo with caption to a recipient
phone.take_photo() # takes a photo
phone.send_snap_to(recipients=["Charlie", "Alice iPhone"]) # sends the previously taken photo to multiple recipients
```
