# WhatsApp Messenger - Android

WhatsApp Messenger is an instant messaging VoIP service owned by Meta.
Puma supports a wide range of actions in WhatsApp, listed below.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.whatsapp).

### Initialization

Initialization is standard:

```python
from puma.apps.android.whatsapp.whatsapp import WhatsappActions
phone = WhatsappActions("emulator-5444")
```

### Account actions

Some account properties can be set:

```python
# this method assumes you have a folder named "profile_picture" on your device, containing a photo
phone.change_profile_picture()
# Set your whatsapp status
phone.set_status("This is my new status!")
# set the about text on your WhatsApp profile
phone.set_about("I'm just a developer")
```

### Navigating the UI

You can go to the WhatsApp start screen (the screen you see when opening the app), and opening a specific conversation:

```python
phone.return_to_homescreen()  # returns to the WhatsApp home screen
phone.select_chat("Bob")  # opens the conversation with Bob
# this method doesn't require you to be at the home screen
phone.select_chat("Cool Kidz")  # this call will first go back to the home screen, then open the other conversation
```

### Sending text messages

Of course, you can send text messages:

```python
phone.select_chat("Bob")  # open the conversation with Bob 
phone.send_message("Hi Bob!")  # Send Bob a message
# but this can be done in one call:
phone.send_message("Hi Charlie", chat="Charlie")  # This will open the charlie conversation, then send the message
# !!! Only use the `chat` argument the first time! If not, each send_message call will first exit the current
# conversation, and then open the conversation again. This happens because Puma cannot detect whether you're already
# in the desired conversation
# The above code will not work if these contacts aren't in the list of WhatsApp conversations
# In that case, a new conversation needs to be created to send a message:
phone.create_new_chat("Dave", "Hi there Dave")
# WhatsApp also has broadcast messages, which are sent to at least 2 other contacts:
phone.send_broadcast(["Bob", "Charlie", "Dana"], "Thinking about you!")
# We can also forward messages from one conversation to another:
phone.forward_message("Bob", "important message!",
                      "Charlie")  # forwards a messages containing `important message!` from Bob to Charlie
```

### Sending media

Sending picture or video is supported, but since the UI doesn't show full paths or filenames, you are required to know
which folder your desired picture or video is in, Puma will pick the first file in that folder and send it.

```python
phone.select_chat("Bob")  # open the conversation with Bob 
phone.send_media("Bird")  # will send the first picture or video in the folder "Bird"
phone.send_media("Horse", chat="Charlie")  # First opens the correct conversation before sending the media
phone.send_media("Fish", caption="look at this cool fish!")  # send media with a caption
phone.send_media("Turtle", view_once=True)  # activate hte 'view once' option
```

### Other chat functions

Many other functions are supported:

```python
# NOTE: all methods here have an optional argument `chat`: when used, the method will first open the given conversation
# Replies to a given message
phone.reply_to_message(message_to_reply_to="Hi Alice!", reply_text="Who dis? New phone")
# send a sticker. It will simply pick the first sticker.
phone.send_sticker()
# Sending voice recordings
phone.send_voice_recording(duration=2000)  # duration in ms
# sending location, either the current or a live location
phone.send_current_location()
phone.send_live_location()
phone.stop_livelocation()  # stops live location sharing
# contacts can also be sent
phone.send_contact(contact_name="Auntie Flo")
# delete a message in the conversation. You need to input the full message
phone.delete_message_for_everyone("Curpuceeno")
# activate or deactivate automatically disappearing messages in a conversation
phone.activate_disappearing_messages()
phone.deactivate_disappearing_messages()
```

### Calls

We can start, end, and refuse calls:

```python
phone_alice.call_contact("Bob")  # calls Bob
phone_bob.answer_call()  # answers incoming call
phone_alice.end_call()  # ends current call (can be called before other party answered the call)
# video alls are also supported:
phone.call_contact("bob", video_call=True)
# declining incoming calls is also possible:
phone.decline_call()
```

### WhatsApp group chats

Many group management actions are also supported:

```python
phone.create_group("Best friends since 2013", ["Bob", "Charlie"])  # Creates a group with a few participants
phone.set_group_description(group_name="Best friends since 2013", description="we go way back!")
phone.delete_group("Some group")  # leaves and deletes a group
phone.leave_group("Some other group")  # just leaves a group
phone.remove_participant_from_group("Friends", "Donald")  # removes a person from a group 
```