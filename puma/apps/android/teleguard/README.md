# TeleGuard Messenger - Android

TeleGuard Messenger is a messaging app developed by Swisscows.
Puma supports part of the features of TeleGuard.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded in 
[the Google PlayStore](https://play.google.com/store/apps/details?id=ch.swisscows.messenger.teleguardapp).

### Prerequisites

- The application installed on your device
- Registration (no personal information such as a phone number is required)

### Initialization

Initialization is done in the following way:

```python
from puma.apps.android.teleguard.teleguard import TeleGuard

phone = TeleGuard("emulator-5444")
```

### Navigating the UI

You can go to the TeleGuard start screen (the screen you see when opening the app), and opening a specific conversation:

```python
# 1-on-1 conversation
phone.go_to_state(phone.chat_state, conversation="Bob")
# Group chat
phone.go_to_state(phone.chat_state, conversation="Guys")
# Channel
phone.go_to_state(phone.chat_state, conversation="News")
```

### Adding a contact
You can add a contact of by TeleGuard ID:
```python
phone.add_contact("INSERT THE CONTACT's ID HERE")
```

### Accepting an invite
If you were added by someone else, you can accept their invite. 
:warn: Note that if you have multiple invites, only the top one will be accepted. Run this again to accept any
additional invites. 
```python
phone.accept_invite()
```

### Sending a message

You can send messages. As opposed to adding a contact, you should now use their username.

```python
from puma.apps.android.teleguard.teleguard import TeleGuard
phone = TeleGuard("emulator-5444")

# Send Bob a message
phone.send_message("Hi Bob!", "Bob")
# Alternatively, use:
phone.send_message("Hi Charlie", conversation="Charlie")
# A second message can be sent without supplying the conversation again:
phone.send_message("Hi Charlie, please reply!")
```
### Sending a picture

You can also send pictures, either from the device or by taking a new picture with the camera. 

```python
from puma.apps.android.teleguard.teleguard import TeleGuard
phone = TeleGuard("emulator-5444")

# Send Bob a picture, picture_id=1 will send the first picture that pops up the media picker, so this will be the latest picture on device. 
phone.send_picture(picture_id=1, caption="Hey bob, look at this cool picture!", conversation="Bob")
# caption is optional, and the conversation argument is not needed when already in a conversation 
phone.send_picture(picture_id=2)
# if we do not provide a picture_id, a  picture will be taken using the camera
phone.send_picture(caption="You want me to buy this?")
# so when in a conversation, you can leave out all arguments and a picture will be taken and sent without caption
phone.send_picture()
```

### clearing history

The conversation history can be cleared. In Teleguard, this only affects one user: the other user still has the entire
chat history.

```python
from puma.apps.android.teleguard.teleguard import TeleGuard

phone_alice = TeleGuard("emulator-5444")
phone_bob = TeleGuard("emulator-5446")

phone_alice.clear_history(conversation="Bob")
phone_bob.clear_history(conversation="Alice")
```