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
from puma.apps.android.teleguard.teleguard import TeleguardActions

phone = TeleguardActions("emulator-5444")
```

### Navigating the UI

You can go to the Teleguard start screen (the screen you see when opening the app), and opening a specific conversation:

```python
phone.return_to_homescreen()  # returns to the WhatsApp home screen
phone.select_chat("Bob")  # opens the conversation with Bob
# this method doesn't require you to be at the home screen
phone.select_group("Guys")  # this call will first go back to the home screen, then open the other conversation
phone.select_channel("News")
```

### Adding a contact
You can add a contact of by Teleguard ID:
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
phone.select_chat("Bob")  # open the conversation with Bob 
phone.send_message("Hi Bob!")  # Send Bob a message
# but this can be done in one call:
phone.send_message("Hi Charlie", chat="Charlie")  # This will open the charlie conversation, then send the message
# !!! Only use the `chat` argument the first time! If not, each send_message call will first exit the current
# conversation, and then open the conversation again. This happens because Puma cannot detect whether you're already
# in the desired conversation
```
