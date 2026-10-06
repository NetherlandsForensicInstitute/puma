# Slack - Android

Slack is a messaging app for teams and workspaces, developed by Slack Technologies (Salesforce).
Puma has limited support for Slack.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.Slack).

## Prerequisites

- The application installed on your device
- Being signed in to a Slack workspace

## Initialization

Initialization is standard:

```python
from puma.apps.android.slack.slack import Slack

phone = Slack("emulator-5444")
```

### Navigating the UI

You can go to the Slack home screen (the screen you see when opening the app), and open a specific channel or direct
message conversation:

```python
# Go to the home screen
phone.go_to_state(phone.home_state)
# Open a channel
phone.go_to_state(phone.channel_state, channel="general")
# Open a direct message conversation
phone.go_to_state(phone.channel_state, direct_message="Bob")
```

The channel or direct message conversation needs to be listed on the home screen of the active workspace. If it is out
of view, Puma will scroll the home screen to find it. Matching of channel and conversation names is case-insensitive.

### Sending a message

You can send a text message to a channel or in a direct message conversation:

```python
# Send a message in a channel
phone.send_message("Hi everyone!", channel="general")
# Send a direct message
phone.send_message(message="Hi Bob!", direct_message="Bob")
# A second message can be sent without supplying the channel or conversation again:
phone.send_message("How are you doing?")
```

### Sending a picture

You can send a picture from the device, optionally with a caption. Pictures are selected by their index, where
`picture_id=1` is the most recent picture on the device.

```python
# Send the most recent picture in a channel
phone.send_picture(channel="general")
# Send the third most recent picture with a caption in a direct message conversation
phone.send_picture(picture_id=3, caption="Look at this!", direct_message="Bob")
```

The first time a picture is sent, Slack asks for permission to access the photos and videos on the device. Puma grants
this permission automatically.
