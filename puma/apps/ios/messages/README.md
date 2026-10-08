# Messages - iOS

Messages is the messaging application built into iOS, developed by Apple, used for iMessage and SMS.
Puma supports part of the features of Messages.
For detailed information on each method, see the method its PyDoc documentation.

Messages is part of iOS, so its version is the iOS version.

## Prerequisites

- An iOS device or simulator running iOS 26, set up as described in [Setting up iOS](../../../../docs/setup-ios.md)
- Device language needs to be set to English
- To send and receive messages, a real device signed in to iMessage. On a simulator, messages cannot be sent
  to new recipients. The simulator does start with two conversations, which can be used for testing: messages sent in
  one of them are received in the other.

## Initialization

Initialization is standard:

```python
from puma.apps.ios.messages.messages import Messages

phone = Messages("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
```

On a real device, also pass the signing settings for WebDriverAgent as `desired_capabilities`, see
[Setting up iOS](../../../../docs/setup-ios.md).

## Opening and searching conversations

Conversations are identified by their name as shown in the overview: the name of the contact, the phone number or email
address, or the name of the group. Conversations that are not shown in the overview without scrolling are opened by
searching for them. Names are case-sensitive, as conversations can have names that only differ in case, e.g. `Bank`
and `bank`.

```python
phone.search_conversations("Bank")      # ['Bank', 'bank', 'Bank Alerts']
```

Searching only works on real devices: the simulator does not index messages, so searching finds nothing there.

## Sending messages

```python
phone.start_conversation("Bob", "Hi Bob!")                 # a contact, phone number or email address
phone.send_message("How are you?", conversation="Bob")
phone.send_message("Any plans this weekend?")              # without a conversation, the open conversation is used
```

When a message cannot be sent to a recipient, `start_conversation` raises a `MessagesError`.

## Reading messages

```python
from puma.apps.ios.messages.messages import Service

messages = phone.get_messages("Bob")
# [Message(sender=None, text='Hi Bob!', time='14:45', service=Service.IMESSAGE),
#  Message(sender='Bob Jansen', text='Fine, thanks!', time='14:46', service=Service.IMESSAGE)]
messages[0].sent_by_me                   # True
phone.get_service("Bank")                # Service.SMS: the service of the next message
```

`get_messages` returns the text messages shown on the screen. Messages sent from the device have `None` as sender.
Photos and other attachments are not included, and in long conversations only the most recent messages are returned.

Each message has the service it was sent with: iMessage or SMS. For messages sent from the device, the service is part
of the message. For received messages, the service is shown in the conversation only when it changes. When that is no
longer on the screen, the service of the conversation (see `get_service`) is used. RCS messages are not recognized yet.

## Replying and reacting

```python
from puma.apps.ios.messages.messages import Reaction

phone.reply_to_message("Any plans this weekend?", "Perhaps a movie?", conversation="Bob")
phone.react_to_message("Perhaps a movie?", Reaction.HEART)   # HEART, THUMBS_UP, THUMBS_DOWN, HAHA, EMPHASIZE, QUESTION
```

Messages are identified by their text. When multiple messages contain the text, the last one is used. Older messages are
scrolled to. Replies and reactions are included in the messages returned by `get_messages`:

```python
reply = phone.get_messages()[-1]
reply.is_reply, reply.reply_to     # True, 'Any plans this weekend?'
reply.reactions                    # [(None, Reaction.HEART)]: reactions from this device have None as who
```

A person can give one reaction to a message: a new reaction replaces the previous one. Replying is only available for
iMessage, and not on a simulator.

## Editing, unsending, deleting and forwarding

```python
phone.edit_message("Perhaps a movie?", "Perhaps a movie tonight?")
phone.get_messages()[-1].edited                              # True
phone.delete_message_for_everyone("Perhaps a movie tonight?")  # Undo Send: removes it for everyone
phone.delete_message("Any plans this weekend?")              # deletes the message from this device only
phone.forward_message("Bob", "Any plans", "Alice")           # forwards the last message containing 'Any plans'
```

Only messages sent from the device with iMessage can be edited (up to 15 minutes after sending) and unsent (up to 2
minutes after sending). These are not available on a simulator, where a `MessagesError` is raised. Deleted messages are
moved to Recently Deleted.

## Photos, audio and location

```python
from puma.apps.ios.messages.messages import LiveLocationDuration

phone.send_media(1, conversation="Bob", caption="Look!")          # the most recent photo or video
phone.send_voice_message(duration=3)                             # records 3 seconds with the microphone
phone.send_live_location(LiveLocationDuration.ONE_HOUR)          # ONE_HOUR, END_OF_DAY or INDEFINITELY
phone.stop_live_location()
```

Photos, audio messages and locations are included in `get_messages`, with an empty text and a description in
`attachment`, e.g. `'Includes picture'` or `'Location'`.

- The photo picker shows the newest photos first: `send_media(1)` sends the most recent one. On a simulator, add
  photos with `xcrun simctl addmedia <udid> <photo>`.
- On a simulator, audio messages are recorded without sound.
- Sharing the location is only available on real devices. To share another location than the real location of the
  device, set the location first, e.g. with `set_location()` of the Appium driver. Sending a
  fixed location (instead of sharing it for a while) is not available in Messages on iOS 26.

## Delivery status

```python
phone.is_message_marked_delivered("Perhaps a movie?")       # True when delivered or read
phone.is_message_marked_read("Perhaps a movie?")            # only when the recipient shares read receipts
phone.is_message_marked_not_delivered("Perhaps a movie?")   # e.g. an SMS that could not be delivered
```

iOS only shows the status of the last message sent from the device. For other messages, these methods return `None`.

## Groups

> **TODO:** most group actions have not been verified on a device yet, as that needs a group of people with iMessage
> that can receive test messages. Verified on a device: selecting multiple recipients for a new group (without sending),
> and reading the messages of a group conversation, with the sender of each message. They are built on the standard texts of iOS 26 (e.g. "Change Name and Photo" and
> "Leave this Conversation"), and raise a `MessagesError` when an element is not found. Run `test_groups` in
> `test_scripts/test_messages.py` with three test contacts to verify them, and adjust the locators marked with TODO in
> `locators.py` where needed.

```python
phone.create_group(["Bob", "Alice"], "Hi both!", group_name="Weekend")
phone.add_members(["Charlie"], conversation="Weekend")
phone.edit_group_name("Weekend", "Weekend trip")
phone.remove_member("Charlie", conversation="Weekend trip")
phone.group_exists("Weekend trip", ["Bob", "Alice"])          # True
phone.leave_group("Weekend trip")
```

Only group conversations with iMessage users can be named and have people added or removed. Removing people and
leaving a group is only possible in groups of at least four people, including yourself. `group_exists` searches for the
conversation, which only works on real devices.

## Deleting conversations

```python
phone.delete_conversation("Bob")
```

Deleted conversations are moved to Recently Deleted, where iOS keeps them for 30 days.
