# Telegram - iOS

Telegram is a cloud-based messaging app. Puma supports part of the features of Telegram on iOS.
For detailed information on each method, see the method its PyDoc documentation.

The supported version is Telegram 13.0 on iOS 26. Telegram draws most of its own interface, so Puma has to work with the
few elements it exposes, and an update of Telegram can break actions.

## Prerequisites

- An iOS device, set up for Puma as described in
  [Using Puma apps on iOS](../../../../docs/setup-ios.md#using-puma-apps-on-ios). Telegram cannot be installed on a
  simulator.
- Telegram is installed and logged in, and the chat you use exists. Puma finds chats by searching, so the chat does not
  have to be on the screen.
- To send media, Telegram has access to (some of) the photos, and to send the location it has access to the location.
  These permissions are asked when first used. Puma does not grant them: when Telegram has limited access to the photos,
  iOS regularly asks whether to select more photos, which Puma answers with 'Keep Current Selection'.

## Initialization

Initialization is standard:

```python
from puma.apps.ios.telegram.telegram import Telegram

phone = Telegram("00008130-000C70C42811401C")
```

On a real device, also pass the signing settings, see
[Using Puma apps on iOS](../../../../docs/setup-ios.md#using-puma-apps-on-ios).

## Conversations

Conversations are identified by their name as shown in the overview: the name of the contact, or the name of the group.
Names are case-sensitive. A conversation that does not exist raises a `TelegramError`.

## Sending messages

```python
phone.send_message("Hi Alice!", conversation="Alice")
phone.send_message("Any plans this weekend?")      # without a conversation, the open conversation is used
phone.send_media_from_gallery(1, caption="Look at this!", conversation="Alice")
phone.send_media_from_gallery([1, 2])              # more than one photo
phone.send_current_location(conversation="Alice")
```

The indices of `send_media_from_gallery` are the 1-based positions of the photos in the gallery picker of Telegram,
after the camera. Folders (albums) are not supported. When one of the photos is not shown in the picker, a
`TelegramError` is raised before anything is selected or sent, so none of the photos is sent.

## Reading messages

```python
phone.get_messages("Alice")
# [Message(sender=None, text='Hi Alice!', time='14 Oct 2026 at 13:01', status='Seen by recipient', kind='message'),
#  Message(sender=None, text='Look at this!', time='14 Oct 2026 at 13:06', status='', kind='photo')]
```

`get_messages` returns the messages shown on the screen, so in long conversations only the most recent messages.
Messages sent from the device have `None` as sender. The text of a photo is its caption, and a shared location is a
message with the text `Location`. The date and the status are shown as Telegram shows them, in English.

## Screens and recovery

Puma recognizes four screens (states), with the same names as Telegram on Android: `conversations_state` (the Chats
list), `search_state`, `chat_state` and `send_media_state` (the sheet of the attach button, with the gallery and the
location). The Contacts tab has a search field just like the Chats list, so the Chats list is recognized by the unnamed
button of its title as well. Tested on a device, for each screen exactly one state is recognized, or none:

| Screen                                        | Recognized as        |
|-----------------------------------------------|----------------------|
| Chats list, and the Chats list in Edit mode   | `conversations_state` |
| Contacts, Calls and Settings tab              | none                 |
| Info of a contact                             | none                 |
| Search (empty and with results)               | `search_state`       |
| An open chat                                  | `chat_state`         |
| Attach sheet (gallery and location tab)       | `send_media_state`   |

When Telegram is on a screen that is not recognized, Puma restarts the app once for each action. If Telegram is still on
an unknown screen after the restart, for example because of a passcode lock, an update screen or an alert that Puma does
not know, the action raises a `ValueError`. Puma does not tap the Chats tab instead, as the tab bar is not in the
element tree, so that tap could press something else on an unknown screen. Telegram always starts on the Chats list
after a restart: this was tested after leaving the app in an open chat, on the search screen, in the attach sheet, and
on the Contacts, Calls and Settings tab. Telegram does not restore the last tab or chat.

Not tested, or not recognized:

- The Edit mode of the Chats list is not in the element tree, so it is not told apart from the Chats list. Leave it
  before using Puma.
- A Telegram passcode lock was not tested. Puma does not enter passcodes, so Telegram should be unlocked.
- Archived chats, chat folders and a chat with someone else than the test contact were not tested.

## Not supported yet

Compared to [Telegram on Android](../../android/telegram/README.md), these are missing:

- Voice and video messages, calls, and live location. These were not tested on a device.
- Groups: creating them, and changing their members, name and description.
- Selecting a folder in the gallery, and deleting groups.
- The other states of Telegram on Android: `chat_settings_state` (the info of a chat, with the call button, which was
  seen but not used), `call_state` and `new_message_state`. A group needs more than one contact to be tested.
- Android has a `send_from_gallery_state` for the gallery. On iOS the gallery is one of the tabs of the sheet of the
  attach button, so it is part of `send_media_state`, as the sheet is closed after sending.
- Reading received messages: the messages of the other person could not be tested, as that needs a second device. They
  are returned with their name as sender, which is probably not what Telegram shows.

## Known limitations

- The buttons in the navigation bar and the tab bar of Telegram are not in the element tree. Puma avoids them by
  searching for chats. Where Puma has to tap an element that is not in the element tree (the close button of the search
  field, the circle to select a photo and the caption field), it taps relative to a neighbouring element, as described
  in `locators.py`. The tab bar is only tapped by the test script, for the recovery tests.
- The option to send the current location is the first of two unnamed rows. When there are not exactly two rows, for
  example when the live location is already shared, `send_current_location` raises an error instead of guessing, as the
  second row starts sharing the live location. After sending, Puma checks that a new location message appeared, ignoring the status of messages that
  changes in the meantime, and logs a warning if it did not. It never raises after the location was sent, as the
  framework repeats an action that raises, which would send the location twice. Two locations in the same minute are
  only recognized while the first is still on the screen.
- Only messages of today have been seen. Dates in another format are expected to show up as the second last line of the
  value of a sent message, which is how the date of other days is read.
- Searching also suggests public channels and other accounts. Puma only opens the result with exactly the name of the
  conversation.
