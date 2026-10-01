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
phone.start_conversation("Bob Jansen", "Hi Bob!")          # a contact, phone number or email address
phone.send_message("How are you?", conversation="Bob Jansen")
phone.send_message("Any plans this weekend?")              # without a conversation, the open conversation is used
```

When a message cannot be sent to a recipient, `start_conversation` raises a `MessagesError`.

## Reading messages

```python
from puma.apps.ios.messages.messages import Service

messages = phone.get_messages("Bob Jansen")
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

## Deleting conversations

```python
phone.delete_conversation("Bob Jansen")
```

Deleted conversations are moved to Recently Deleted, where iOS keeps them for 30 days.
