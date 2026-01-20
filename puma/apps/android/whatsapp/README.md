# WhatsApp Messenger - Android

WhatsApp Messenger is an instant messaging VoIP service owned by Meta.
Puma supports a wide range of actions in WhatsApp, listed below. Registration with a phone number is required.
For detailed information on each method, see the method its PyDoc documentation.

Actions can also be verified. For more information, see examples below 
and the [action](../../../../puma/state_graph/action.py) documentation. 

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.whatsapp.w4b&hl=nl).

## Deprecation

This class does not use `StateGraph` as its base class, and has therefore been deprecated since Puma 3.0.0. It can still
be used, but it will not be maintained. If you want to add functionality, please rewrite this class using `StateGraph`
as the abstract base class. Also see the [CONTRIBUTING.md](../../../../CONTRIBUTING.md).

### Prerequisites

- The application installed on your device
- Registration with a phone number

### Initialization

Initialization is standard:

```python
from puma.apps.android.whatsapp.whatsapp import WhatsApp
phone = WhatsApp("emulator-5444", "com.whatsapp")
```

### Account actions

Some account properties can be set:

```python
# this method takes the first picture in the provided folder name
phone.change_profile_picture(1, 'Downloads')
# add a WhatsApp status
phone.add_status("This is my new status!")
# set the about text on your WhatsApp profile
phone.set_about("I'm just a developer")
```

### Navigating the UI

You can go to the WhatsApp start screen (the screen you see when opening the app), and opening a specific conversation:

```python
# returns to the WhatsApp home screen
phone.go_to_state(WhatsApp.conversations_state)
# opens the conversation with Bob
phone.go_to_state(WhatsApp.chat_state, conversation="Bob")
# this call will automatically go back to the home screen first, then open the other conversation
phone.go_to_state(WhatsApp.chat_state, conversation="Cool Kidz")
```

### Sending text messages

Of course, you can send text messages:

```python
# Send Bob a message
phone.send_message("Hi Bob!", "Bob")
# but this can be done in one call:
# The above code will not work if these contacts aren't in the list of WhatsApp conversations
# In that case, a new conversation needs to be created to send a message:
phone.create_new_chat("Dave", "Hi there Dave")
# WhatsApp also has broadcast messages, which are sent to at least 2 other contacts:
phone.send_broadcast(["Bob", "Charlie", "Dana"], "Thinking about you!")
# Forwards a messages containing `important message!` from Bob to Charlie
phone.forward_message("Bob", "important message!", "Charlie")
```

Sending messages can also be verified, depending on the expected result:

```python
# verify the message ended up in state 'sent'
phone.send_message("Hi Bob!", "Bob", verify_with=phone.is_message_marked_sent)
# verify the message ended up in state 'delivered'
phone.send_message("Hi Bob!", "Bob", verify_with=phone.is_message_marked_delivered)
# verify the message ended up in state 'read'
phone.send_message("Hi Bob!", "Bob", verify_with=phone.is_message_marked_read)
```

### Sending media

Sending a picture or video is supported, but since the UI doesn't show full paths or filenames, you are required to know
which folder your desired picture or video is in. Puma will pick the first file in that folder and send it.

```python
# sends the first picture or video in the folder "Bird"
phone.send_media(1, conversation="Bob", directory_name="Bird")
# sends the first picture or video in the folder "Horse"
phone.send_media(1, conversation="Charlie", directory_name="Horse")
# send media from folder "Fish" at index 2, with a caption
phone.send_media(index=2, conversation="Bob", directory_name="Fish", caption="look at this cool fish!")
# activate the 'view once' option. The conversation does not have to be specified if the previous message was also sent to Bob.
phone.send_media(1, directory_name="Turtle", view_once=True)
```

### Other chat functions

Many other functions are supported:

```python
# Replies to a given message
phone.reply_to_message(conversation="Bob", message_to_reply_to="Hi Alice!", reply_text="Who dis? New phone")
# send a sticker. It will simply pick the first sticker.
phone.send_sticker(conversation="Bob")
# Sending voice recordings
phone.send_voice_message(conversation="Bob", duration=2000)  # duration in ms
# sending location, either the current or a live location
phone.send_current_location(conversation="Bob")
phone.send_live_location(conversation="Bob")
# stops live location sharing. The conversation does not have to be specified, since the previous message was also sent to Bob.
phone.stop_live_location()
# contacts can also be sent
phone.send_contact(contact_name="Auntie Flo", conversation="Bob")
# delete a message in the conversation. You need to input the full message
phone.delete_message_for_everyone(message_text="Curpuceeno", conversation="Bob")
# activate or deactivate automatically disappearing messages in a conversation
phone.activate_disappearing_messages(conversation="Bob")
phone.deactivate_disappearing_messages(conversation="Bob")
```

### Calls

We can start, end, and refuse calls:

```python
# calls Bob
phone_alice.start_voice_call("Bob")
# answers incoming call
phone_bob.answer_call()
# ends current call (can be called before other party answered the call)
phone_alice.end_voice_call("Bob")
# video alls are also supported:
phone.start_video_call("Bob")
# declining incoming calls is also possible:
phone.decline_call()
```

You can also verify that answering a call succeeded:

```python
# calls Bob
phone_alice.start_voice_call("Bob")
# answers incoming call
phone_bob.answer_call()
# now verify we are in a call
if not phone_bob.in_connected_call():
    logger.warning('Connecting to call failed!')
```

### WhatsApp group chats

Many group management actions are also supported:

```python
# creates a group with a few participants
phone.create_group("Best friends since 2013", ["Bob", "Charlie"])
phone.set_group_description(description="we go way back!", conversation="Best friends since 2013")
# leaves and deletes a group
phone.delete_group("Some group")
# just leaves a group
phone.leave_group("Some other group")
# removes a person from a group
phone.remove_member_from_group("Friends", "Donald")
```

You can also verify that a group was correctly created:

```python
phone.create_group("Best friends since 2013", ["Bob", "Charlie"], verify_with=phone.group_exists)
```