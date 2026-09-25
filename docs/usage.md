# Using Puma

This page explains how to use Puma once your device is set up. See the [README](../README.md) for a quickstart.

## Examples

If everything is setup correctly, you can now use Puma! Below are a few small examples to get started. If you want a
more extensive step-by-step guide on how to use (and develop) Puma, please refer to the
[Puma Tutorial](../tutorial/2026/exercises.md).

The code below shows a small example on how to search for the Eiffel Tower in Google Maps.

```python
from puma.apps.android.google_maps.google_maps import GoogleMapsActions
from puma.utils import configure_default_logging

configure_default_logging()# Use Puma's logging configuration. You can also implement your own

phone = GoogleMapsActions("emulator-5444")
phone.search_place('eiffel tower')
```

This is a rather simple application, in the sense that it can be used without any form of registration. Other
applications
need some additional preparation, such as WhatsApp. For this application, you first need to register with a phone
number.
These kind of prerequisites are also described in the application README. The first time you use an application, there
might be pop-ups explaining the app that Puma does not take into account, as these need to be confirmed only once. You
need
to do this manually the first time while running Puma. After registering, you can send a WhatsApp message to a contact
with the code below:

```python
from puma.apps.android.whatsapp.whatsapp import WhatsApp
from puma.utils import configure_default_logging

configure_default_logging() # Use Puma's logging configuration. You can also implement your own

alice = WhatsApp("<INSERT UDID HERE>", "com.whatsapp")  # Initialize a connection with device
alice.create_new_chat(conversation="<Insert the contact name>",
                      first_message="Hello world!")  # Send a message to contact in your contact list
alice.send_message("Sorry for the spam :)")  # we can send a second message in the open conversation
```

An action might not always execute properly. If you want to verify that the action succeeded, you can add a special
named argument to the action, which points to the function you want to verify the action with. We supply some
commonly used verifications for users to use.

For example, verifying a Whatsapp message has been sent:

```python
from puma.apps.android.whatsapp.whatsapp import WhatsApp

app = WhatsApp('<INSERT UDID HERE>', 'com.whatsapp')
app.send_message(conversation='Bob', message_text='Sorry for the spam :)', verify_with=app.is_message_marked_sent)
```

This will verify if the expected message has indeed been sent. If not, it will log this using the Ground Truth logger.
It will not stop the execution of the following steps. For more information, see the [action](../puma/state_graph/action.py) documentation.

Congratulations, you just did a search query in Google Maps and/or sent a WhatsApp message without touching your phone!
You can now explore what other functions are possible with Puma in [WhatsApp](../puma/apps/android/whatsapp/README.md), or
try a
[different application](../README.md#supported-apps). You could even start working
on [adding support for a new app](../CONTRIBUTING.md).

## Exploring the functionality of an app

To get a full overview of all functionality and pydoc of a specific app, run

```bash
# Example for WhatsApp
python -m pydoc puma/apps/android/whatsapp/whatsapp.py
```

## Supported versions

The currently supported version of each app is mentioned in the documentation above (and in the source code). When Puma
code breaks due to UI changes (for example when app Xyz updates from v2 to v3), Puma will be updated to support Xyz v3.
This new version of Puma does will **only** be tested against Xyz v3: if you still want to use Xyz v2, you simply have
to use an older release of Puma.

To make it easy for users to lookup older versions, git tags will be used to tag app versions. So in the above example
you'd simply have to look up the tag `Xyz_v2`.

If you are running your script on a newer app version than the tag, it is advised to first run the test script of your
app (can be found in the [test scripts directory](../test_scripts)). This test script includes each action that can be
performed on the phone, and running these first will inform you if all actions are still supported, without messing up
your experiment.

## Navigation

You need to be careful about navigation. For example, some methods require you to already be in a conversation. However,
most methods give you the option to navigate to a specific conversation. 2 examples:

### Example 1

```python
from puma.apps.android.whatsapp.whatsapp import WhatsApp
from puma.utils import configure_default_logging

configure_default_logging() # Use Puma's logging configuration. You can also implement your own
alice = WhatsApp("emulator-5554")  # initialize a connection with device emulator-5554
alice.go_to_state(WhatsApp.chat_state, conversation="Bob")
alice.send_message("message_text")
```

In this example, the message is sent to the conversation with "Bob", by selecting the conversation manually. The second
example below automates this step.

### Example 2

```python
from puma.apps.android.whatsapp.whatsapp import WhatsApp
from puma.utils import configure_default_logging

configure_default_logging() # Use Puma's logging configuration. You can also implement your own
alice = WhatsApp("emulator-5554")  # initialize a connection with device emulator-5554
alice.send_message("message_text", conversation="Bob")
alice.send_message("message_text2")
```

In the second example, the chat conversation to send the message in is supplied as a parameter. Before the message is
sent, there will be navigated to the home screen first, and then the chat "Bob" will be selected.

Note that the second message is sent to the current chat conversation. Puma will detect that a conversation was
already opened, so it will not navigate back to the main screen and reopen the same conversation.
