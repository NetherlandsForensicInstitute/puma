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

## Sending messages

Conversations are identified by their name as shown in the overview: the name of the contact, the phone number or email
address, or the name of the group.

```python
phone.start_conversation("Bob Jansen", "Hi Bob!")          # a contact, phone number or email address
phone.send_message("How are you?", conversation="Bob Jansen")
```

When a message cannot be sent to a recipient, `start_conversation` raises a `MessagesError`.

## Reading messages

```python
phone.get_messages("Bob Jansen")
# [('Your iMessage', 'Hi Bob!'), ('Your iMessage', 'How are you?'), ('Bob Jansen', 'Fine, thanks!')]
```

`get_messages` returns the text messages shown on the screen, with their sender. Messages sent from the device have
`'Your iMessage'` as sender (`CONVERSATION_SENT_BY_ME` in `xpaths.py`). Photos and other attachments are not included,
and in long conversations only the most recent messages are returned.

## Deleting conversations

```python
phone.delete_conversation("Bob Jansen")
```

Deleted conversations are moved to Recently Deleted, where iOS keeps them for 30 days.
