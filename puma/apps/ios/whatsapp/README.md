# WhatsApp Messenger - iOS

WhatsApp Messenger is an instant messaging and VoIP service owned by Meta.
Puma supports a wide range of actions in WhatsApp on iOS, listed below. The actions have the same names and parameters
as in [WhatsApp for Android](../../android/whatsapp/README.md) where possible.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded in [the App Store](https://apps.apple.com/app/whatsapp-messenger/id310633997).

## Prerequisites

- A real iOS device, set up as described in [Setting up iOS](../../../../docs/setup-ios.md). WhatsApp cannot be
  installed on a simulator, as simulators have no App Store.
- The application installed on the device, and registered with a phone number
- Device language needs to be set to English

## Initialization

Initialization is standard:

```python
from puma.apps.ios.whatsapp.whatsapp import WhatsApp

phone = WhatsApp("00008110-000A1B2C3D4E5F6G", desired_capabilities={
    "appium:xcodeOrgId": "<your team id>",
    "appium:xcodeSigningId": "Apple Development",
})
```

See [Setting up iOS](../../../../docs/setup-ios.md) for the signing settings of WebDriverAgent.

Chats are identified by their name as shown in WhatsApp: the name of the contact, or the name of the group. Chats that
are not on the screen are opened by searching for them. Messages are identified by (a part of) their text. When
multiple messages contain the text, the newest one is used. Names and texts can contain quotes, but texts used to
identify a message cannot contain newlines. With many chats and contacts, WhatsApp on iOS can be slow to
automate: an action can take up to a minute.

## Sending messages

```python
phone.create_new_chat("Bob", "Hi Bob!")                    # start a chat with a contact
phone.send_message("How are you?", conversation="Bob")
phone.send_message("Any plans this weekend?")              # without a conversation, the open chat is used
phone.reply_to_message("How are you?", "Perhaps a movie?", conversation="Bob")
phone.forward_message("Bob", "Any plans", "Alice")         # forwards the last message containing 'Any plans'
phone.delete_message_for_everyone("Perhaps a movie?", conversation="Bob")
phone.send_emoji("Bob")
phone.send_sticker("Bob")                                  # the first sticker of the sticker tray
phone.send_broadcast(["Bob", "Alice"], "Hi all!")          # at least 2 receivers
```

## Reading messages

```python
messages = phone.get_messages("Bob")
# [Message(sender='Bob', text='Hi!', time='16:05', status=None, is_reply=False, reply_to=None, kind='message'),
#  Message(sender=None, text='How are you?', time='16:08', status='Delivered', ...)]
phone.is_message_marked_sent("How are you?")
phone.is_message_marked_delivered("How are you?")
phone.is_message_marked_read("How are you?")              # only when both people have read receipts turned on
```

`get_messages` returns the messages shown on the screen, from old to new. Messages sent from the device have `None` as
sender, and a status: `Sent`, `Delivered` or `Read`. The kind of a message is `message` for text messages, and e.g.
`photo`, `voice message`, `contact`, `location`, `live location` or `sticker` for other messages.

## Media, contacts and locations

```python
phone.send_media(1, conversation="Bob", caption="Look!")   # the newest photo or video in the photo library
phone.send_media(1, conversation="Bob", view_once=True)
phone.send_media(1, conversation="Bob", directory_name="Favorites")  # the first photo or video of an album
phone.open_view_once_photo("Bob")                          # opens the last received view once photo
phone.send_voice_message(duration=3, conversation="Bob")   # records 3 seconds with the microphone
phone.send_contact("Alice", conversation="Bob")
phone.send_current_location(conversation="Bob")
phone.send_live_location(caption="On my way", conversation="Bob")  # shared for 1 hour
phone.stop_live_location(conversation="Bob")
```

## Chat settings

```python
phone.activate_disappearing_messages("Bob")               # new messages disappear after 24 hours
phone.deactivate_disappearing_messages("Bob")
phone.archive_conversation("Bob")
phone.unarchive_conversation("Bob")
phone.view_contact_profile_picture("Bob")
```

## Groups

```python
phone.create_group("Weekend", ["Bob", "Alice"])
phone.set_group_description("Weekend", "Plans for the weekend")
phone.group_exists("Weekend", ["Bob", "Alice"])            # True
phone.remove_member_from_group("Weekend", "Alice")         # only group admins can remove members
phone.leave_group("Weekend")
phone.delete_group("Weekend")                             # leaves the group first, when not left yet
```

## Profile and status

```python
phone.set_about("Available")                              # shown for 1 day, the default of WhatsApp
phone.set_about("At work", duration="1 week")             # 1 hour, 8 hours, 1 day, 2 days or 1 week
phone.change_profile_picture(1)                           # the newest photo in the photo library
phone.change_profile_picture(1, directory_name="Recently Saved")   # the first photo of an album
phone.add_status("Hello from Puma!")                      # a text status, shown to your contacts for 24 hours
phone.delete_status()                                     # deletes all your status updates
```

WhatsApp only shows an about for a limited time: an about without an end date cannot be set anymore. A status is a
text on iOS, so `add_status` needs a caption, while on Android a status without a caption is a photo taken with the
camera. For `change_profile_picture`, only the first albums of each row in the Collections of the photo library can be
chosen, as these rows scroll sideways.

## Calls

```python
phone.start_voice_call("Bob")
phone.in_connected_call(implicit_wait=30)                 # True when Bob answers
phone.end_voice_call()
phone.start_video_call("Bob")                             # uses the camera of the device
phone.end_video_call()
phone.answer_call()                                       # answers an incoming call
phone.decline_call()                                      # declines an incoming call
```

Incoming calls are shown by iOS instead of by WhatsApp. `answer_call` and `decline_call` therefore look up the buttons
in the call screen of iOS. In a video call, WhatsApp hides the buttons after a few seconds; ending the call shows them
again first.

## Verified on a device

All actions were verified on an iPhone with WhatsApp 26.38.74, except `change_profile_picture`: to keep the profile
picture of the test account, it was not run. Choosing the photo is verified, confirming the cropped photo is not.

WhatsApp spells some texts of its accessibility labels differently, e.g. 'Red' for the status Read, and
'llive location'. Puma handles these, but they may be corrected in a newer version of WhatsApp.
