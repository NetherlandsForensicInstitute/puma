# Snapchat - Android

Snapchat is an American messaging app developed by Snap Inc.
Puma supports sending messages and snaps to friends in Snapchat.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.snapchat.android).

## Prerequisites

- The application installed on your device
- Registration with a phone number
- The people you want to send messages or snaps to are your friends in Snapchat

## Initialization

Initialization is standard:

```python
from puma.apps.android.snapchat.snapchat import Snapchat

phone = Snapchat("emulator-5444")
```

Puma allows Snapchat to use the camera and microphone when it asks for it, and declines sharing the location.

### Sending a message

We can send a simple text message to a friend. Puma opens the chat through the search screen, so this also works for
friends you have not chatted with yet:

```python
phone.send_message(message="Hi Charlie!", conversation="Charlie")
phone.send_message(message="How are you?")  # in the current chat
```

### Sending a snap

A snap is a photo taken with the camera of the phone. We can send a snap to one friend from the chat with that friend,
or to several friends at once from the camera tab. From the camera tab, the snap can also be posted to My Story, which is
visible to friends only, or to the public story, which is visible to everyone. Snaps can have a caption:

```python
phone.send_snap(conversation="Charlie", caption="Hi Charlie!")  # takes a photo in the chat with Charlie and sends it
phone.send_snap_to(recipients=["Charlie", "Bob"], caption="Hi!")  # takes a photo on the camera tab and sends it to both
phone.send_snap_to(my_story=True, caption="Hello!")  # posts the snap to My Story, visible to friends only
phone.send_snap_to(recipients=["Charlie"], my_story=True)  # sends the snap to Charlie and posts it to My Story
phone.send_snap_to(public_story=True)  # posts the snap to the public story, visible to everyone
phone.flip_camera()  # switches between the front and the rear camera
```
