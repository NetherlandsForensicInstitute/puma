# Messages - iOS

Messages is the messaging application built into iOS, used for iMessage and SMS.
Messages is part of iOS, so its version is the iOS version.

## Prerequisites
- An iOS device or simulator running iOS 26
- To send and receive messages, a real device signed in to iMessage. On a simulator, messages cannot be sent to new
  recipients. The simulator does start with two conversations, which can be used for testing: messages sent in one of
  them are received in the other.

### Initialization is standard:

```python
from puma.apps.ios.messages.messages import Messages
phone = Messages("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
```

### Navigating the UI

Conversations are identified by their name as shown in the overview: the name of the contact, the phone number or email
address, or the name of the group.

```python
phone.start_conversation("Bob Jansen", "Hi Bob!")          # a contact, phone number or email address
phone.send_message("How are you?", conversation="Bob Jansen")
phone.get_messages("Bob Jansen")
# [('Your iMessage', 'Hi Bob!'), ('Your iMessage', 'How are you?'), ('Bob Jansen', 'Fine, thanks!')]
phone.delete_conversation("Bob Jansen")
```

`get_messages` returns the text messages shown on the screen, with their sender. Messages sent from the device have
`'Your iMessage'` as sender (`SENT_BY_ME` in `xpaths.py`). This text depends on the language of the device. Photos and
other attachments are not included, and in long conversations only the most recent messages are returned.

When a message cannot be sent to a recipient, `start_conversation` raises a `MessagesError`.

Deleted conversations are moved to Recently Deleted, where iOS keeps them for 30 days.
