# Snapchat - Android

Snapchat is an American messaging app developed by Snap Inc.
Puma supports has limited support for Snapchat.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.snapchat.android).

### Initialization

Initialization is standard:

```python
from puma.apps.android.snapchat.snapchat import SnapchatActions
phone = SnapchatActions("emulator-5444")
```

### Navigating the UI

You can navigate to one of the main Snapchat tabs, or open a specific chat:

```python
phone.go_to_camera_tab() # Go to the Camera tab.
phone.go_to_conversation_tab() # Go to the Chat tab.
phone.select_chat("Bob")  # Will go to the chat tab and open the conversation with Bob
```

### Sending a message

We can send a simple text message:

```python
phone.select_chat("Bob")  # Open a conversation
phone.send_message("Hi Bob!")  # Sends a message in the current conversation
# We can do both previous actions in one call:
phone.send_message("Hi charlie!", "Charlie")
```

### Send a Snap

We can send a snap to specific people, or post it to My Story:

```python
phone.send_snap(["Bob", "Charlie"])  # takes a snap with the front camera, and sends it to the selected contacts
phone.send_snap()  # if no contacts are given, the snap will be posted to `My Story`
phone.send_snap(recipients=["Dave"], caption="Look at this!")  # optionally, a caption can be included
phone.send_snap(front_camera=False)  # you can also use the rear camera
```
