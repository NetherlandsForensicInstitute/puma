import unittest

from puma.apps.android.slack.slack import Slack

# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Alice": ""
}

# The conversations to use, as listed on the Slack home screen of Alice. Messages and pictures will be sent in these
# conversations, so use a test channel and a contact that does not mind. Most tests use the direct message conversation.
# A channel is written with a '#' prefix. A direct message conversation is written without a prefix here: the tests add
# the optional '@' prefix where needed.
conversations = {
    "channel": "#general",
    "direct_message": "Bob"
}


class TestSlack(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Slack.
    The test can only be run manually, as you need a phone with Slack.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - 1 phone with Slack installed and signed in to a workspace (Alice)
    - The channel and the direct message conversation configured above are listed on the home screen of the workspace
    - At least 3 pictures on the phone
    - Appium running

    The first time a picture is sent, Slack asks for permission to access the photos and videos on the device. Puma
    grants this permission.
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Slack(device_udids["Alice"])
        self.channel = conversations["channel"]
        self.direct_message = conversations["direct_message"]

    def _assert_last_message(self, text: str, conversation: str = None):
        messages = self.alice.get_messages(conversation=conversation, message_count=1)
        self.assertEqual([text], [message.text for message in messages])

    # Navigation: channels and direct message conversations only differ in how they are opened

    def test_go_to_home(self):
        self.alice.go_to_state(Slack.chat_state, conversation=self.direct_message)
        self.alice.go_to_state(Slack.home_state)

    def test_go_to_channel(self):
        self.alice.go_to_state(Slack.chat_state, conversation=self.channel)

    def test_go_to_direct_message(self):
        self.alice.go_to_state(Slack.chat_state, conversation=f"@{self.direct_message}")

    def test_go_to_direct_message_without_prefix(self):
        self.alice.go_to_state(Slack.chat_state, conversation=self.direct_message)

    def test_go_from_channel_to_direct_message_and_back(self):
        self.alice.go_to_state(Slack.chat_state, conversation=self.channel)
        self.alice.go_to_state(Slack.chat_state, conversation=self.direct_message)
        self.alice.go_to_state(Slack.chat_state, conversation=self.channel)

    # Sending messages

    def test_send_message(self):
        self.alice.send_message("Test message with a conversation", conversation=self.direct_message)
        self._assert_last_message("Test message with a conversation")
        self.alice.send_message("Test message without a conversation")
        self._assert_last_message("Test message without a conversation", conversation=self.direct_message)

    def test_send_message_in_different_conversations(self):
        self.alice.send_message("Test message in a channel", conversation=self.channel)
        self.alice.send_message("Test message in a direct message conversation", conversation=self.direct_message)
        self._assert_last_message("Test message in a direct message conversation")
        self._assert_last_message("Test message in a channel", conversation=self.channel)

    # Sending pictures

    def test_send_picture(self):
        self.alice.send_picture(conversation=self.direct_message)
        self.alice.send_picture()

    def test_send_picture_by_index(self):
        self.alice.send_picture(picture_id=1, conversation=self.direct_message)
        self.alice.send_picture(picture_id=2)
        # the third picture is not shown in the photo strip right away
        self.alice.send_picture(picture_id=3)

    def test_send_picture_with_caption(self):
        self.alice.send_picture(caption="This is a test caption", conversation=self.direct_message)
        messages = self.alice.get_messages(message_count=1)
        self.assertEqual("This is a test caption", messages[0].text)
        self.assertTrue(messages[0].attachments, "The picture is not in the attachments of the message")

    def test_send_picture_invalid_index(self):
        with self.assertRaises(ValueError):
            self.alice.send_picture(picture_id=0, conversation=self.direct_message)

    # Getting messages

    def test_get_messages(self):
        # Getting all messages scrolls through the whole conversation, which takes a while in a long conversation
        self.alice.send_message("Test message to get", conversation=self.direct_message)
        messages = self.alice.get_messages()
        self.assertEqual("Test message to get", messages[-1].text)
        for message in messages:
            self.assertTrue(message.sender, f"Message without sender: {message}")
            if message.time:
                self.assertRegex(message.time, r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$')
        self.assertTrue(any(message.time for message in messages), "No message with a time was found")
        # the last messages are the end of all messages
        message_count = min(5, len(messages))
        self.assertEqual(messages[-message_count:], self.alice.get_messages(message_count=message_count))

    def test_get_last_messages(self):
        for text in ("First test message", "Second test message", "Third test message"):
            self.alice.send_message(text, conversation=self.direct_message)
        messages = self.alice.get_messages(message_count=3)
        self.assertEqual(["First test message", "Second test message", "Third test message"],
                         [message.text for message in messages])
        # consecutive messages have no header in Slack, the sender is found by scrolling up
        for message in messages:
            self.assertTrue(message.sender, f"Message without sender: {message}")

    def test_get_last_messages_with_conversation(self):
        self.alice.send_message("Test message to get from home", conversation=self.direct_message)
        self.alice.go_to_state(Slack.home_state)
        messages = self.alice.get_messages(conversation=self.direct_message, message_count=1)
        self.assertEqual(["Test message to get from home"], [message.text for message in messages])

    def test_get_messages_invalid_message_count(self):
        with self.assertRaises(ValueError):
            self.alice.get_messages(conversation=self.direct_message, message_count=0)


if __name__ == '__main__':
    unittest.main()
