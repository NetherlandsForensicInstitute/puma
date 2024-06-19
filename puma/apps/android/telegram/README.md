# Telegram Messenger - Android

Telegram Messenger is a messaging app developed by Telegram Messenger Inc.
Puma supports part of the features of Telegram.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=org.telegram.messenger).

### Initialization

Initialization is standard:

```python
from puma.apps.android.telegram.telegram import TelegramActions
phone = TelegramActions("emulator-5444")
```

### Navigating the UI

You can go to the Telegram start screen (the screen you see when opening the app), and opening a specific conversation:

```python
phone.return_to_homescreen()  # returns to the WhatsApp home screen
phone.select_chat("Bob")  # opens the conversation with Bob
# this method doesn't require you to be at the home screen
phone.select_group("Guys")  # this call will first go back to the home screen, then open the other conversation
phone.select_channel("News")
```


### Sending a message

Of course, you can send text messages:

```python
phone.select_chat("Bob")  # open the conversation with Bob 
phone.send_message("Hi Bob!")  # Send Bob a message
# but this can be done in one call:
phone.send_message("Hi Charlie", chat="Charlie")  # This will open the charlie conversation, then send the message
# !!! Only use the `chat` argument the first time! If not, each send_message call will first exit the current
# conversation, and then open the conversation again. This happens because Puma cannot detect whether you're already
# in the desired conversation
# Telegram allows you to reply to messages:
phone.reply_to_message("Hi Alice!", reply="Hi bob, what's up!")  # replies with a new message
phone.emoji_reply_to_message("Finished laundry", reply="👍")  # replies with an emoji reaction on the message itself
```

### Sending Pictures

For Telegram, Puma currently only supports taking and sending a picture with the embedded camera in the Telegram app.

```python
phone.take_and_send_picture(chat="bob")  # Sends a picture with the rear camera
phone.take_and_send_picture(caption="Look where I am!")  # Captions can be included
phone.take_and_send_picture(front_camera=True)  # You can also use the front camera
```

## Calls

We can make (videO) calls using telegram:

```python
phone_alice.start_call()  # start call in the current conversation
phone_bob.answer_call()  # answer an incoming call
phone_alice.end_call()  # ends current call (can be called before other party answered the call)
phone_alice.start_call("Charlie", video=True)  # starts a video call
phone_charlie.decline_call()  # decline an incoming call
# when a call is active, we can toggle between a video call and a voice call:
phone.toggle_video_in_call()
# when in a video call, we can switch between the front and read camera:
phone.flip_video_in_call()
```