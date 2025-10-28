# Telegram Messenger - Android

Telegram Messenger is a messaging app developed by Telegram Messenger Inc.
Puma supports part of the features of Telegram.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded
in [the Google PlayStore](https://play.google.com/store/apps/details?id=org.telegram.messenger).

## Prerequisites

- The application installed on your device
- Registration with a phone number
- Device language needs to be set to English

## Initialization

Initialization is standard but has one optional parameter.
When using the most common version of Telegram (the version published to the Google Play Store) you can use standard
initialization:

```python
from puma.apps.android.telegram.telegram import Telegram

phone = Telegram("emulator-5444")
```

If you're using the Telegram apk found at [telegram.org](https://telegram.org/android), you can use the optional
parameter `telegram_web_version`:

```python
phone = Telegram("emulator-5444", telegram_web_version=True)
```

This is needed because these two versions of the Telegram Android app use different package names.

## Sending a message

Sending a message is done easily:

```python
phone.send_message("Hi Bob!", conversation='Bob')  # Send Bob a message
phone.send_message("How are you doing?")  # After the conversation is opened, the conversation parameter is not needed
phone.send_message("Any plans this weekend?", conversation='Bob')  # ...But it's not a problem
phone.send_message("Perhaps a movie?", conversation='bOB')  # conversation names need to match exactly, but are case-insensitive
```

### Sending media

Puma can send pictures and videos alreayd on the device:

```python
phone.send_media_from_gallery(media_index=1, conversation='Bob')  # this picks the first picture in the media picker
# we will ommit the conversation parameter from here, as it is not needed once we have opened a conversation
phone.send_media_from_gallery(media_index=[2,4,7])  # we can also send multiple files: the 2nd, 4th and 7th
phone.send_media_from_gallery(media_index=2, caption='cool bird, huh?')  # captions are also supported
phone.send_media_from_gallery(media_index=1, folder='screenshots')  # we can also choose media files from a specific folder
# the above command uses OCR to recognize the folder name. Since this is not 100% reliable, you can also use an index
# to open the nth folder. The index is 1-based
phone.send_media_from_gallery(media_index=1, folder=3)  # sends the first media file from the 3rd folder in the Telegram dropdown 
```
Telegram also supports voice and video messages, which are audio or video clips recorded in the app:
```python
phone.send_voice_message(10, conversation='Bob')  # sends a 10 second voice message
phone.send_video_message(5)  # sends a 5 second video message
```


## Calls

We can make (video) calls using telegram:

```python
phone_alice.start_call(conversation='Bob')  # start call with Bob
phone_bob.answer_call()  # answer an incoming call
phone_alice.end_call()  # ends current call

phone_bob.start_call()  # starts a call in the current conversation
phone_alice.answer_call()
phone_bob.mute_mic()  # mutes the microphone
phone_bob.mute_mic()  # a second call will unmute
phone_alice.end_call()
```

## Location

Puma supports sending the current location or the live location:
```python
# in all examples below, the parameter conversation is needed if you're not currently in a conversation. We omit it here.
phone.send_location()  # sends the current location
phone.send_live_location()  # sends the live location for the default duration
phone.stop_live_location_sharing()  # stops the live location sharing
phone.send_live_location(duration_option=2)  # you can use a different duration option, by using a 1-based index
phone.send_live_location(duration_option='1 hour')  # or by using part of the UI text that's in view. This is readable code but less stable
```

## Group chat management

Puma can create and manage group chats. For chatting, group chats behave like regular conversations

```python
phone.create_group('my best friends', members=['alice', 'bob'])  # Creates a group.
## A group name is required, members are optional and can be added later:
phone.add_members(conversation='my best friends', new_members=['charlie, dave'])
# members can also be removed
phone.remove_member(conversation='my best friends', member='dave')
# the group name and description can be changed:
phone.edit_group_name(conversation='my best friends', new_group_name='my good friends')
phone.edit_group_description(conversation='my good friends', description='Since 1999!')
# groups can be deleted or left. A regular user will simply leave, while the group owner will delete the group:
phone.delete_and_leave_group(conversation='my good friends')
```