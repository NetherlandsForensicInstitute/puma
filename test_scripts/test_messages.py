import unittest

from puma.apps.ios.messages.messages import Messages, MessagesError, Service
from puma.apps.ios.messages.xpaths import conversation_row

# Fill in the udid below. Run `xcrun simctl list devices booted` (simulators) or `xcrun xctrace list devices`
# (real devices) to see the udids.
device_udids = {
    "Alice": ""
}

# The two conversations a simulator starts with. Messages sent in one of them are received in the other.
CONVERSATION_A = "+1 (888) 555-1212"
CONVERSATION_B = "+1 (555) 564-8583"
# Real devices only: the name of a conversation on the device that is not shown in the overview without scrolling, to
# test searching. The simulator does not index messages, so searching finds nothing there.
SEARCH_CONVERSATION = ""


class TestMessages(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Messages on iOS.
    The test can only be run manually, as you need an iOS device or simulator.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - An iOS simulator running iOS 26, with the two conversations a simulator starts with. On a real device, replace
      these by two conversations of your own.
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Messages(device_udids["Alice"])

    def test_send_and_receive(self):
        self.alice.send_message("Puma test, with a comma", conversation=CONVERSATION_A)
        sent = self.alice.get_messages(CONVERSATION_A)[-1]
        self.assertEqual((None, "Puma test, with a comma", Service.IMESSAGE), (sent.sender, sent.text, sent.service))
        self.assertTrue(sent.sent_by_me)
        # without a conversation, the conversation that is open is used
        self.alice.send_message("Puma test, same conversation")
        self.assertEqual("Puma test, same conversation", self.alice.get_messages()[-1].text)
        # on a simulator, the messages are received in the other conversation
        received = self.alice.get_messages(CONVERSATION_B)[-1]
        self.assertEqual((CONVERSATION_B, "Puma test, same conversation", Service.IMESSAGE),
                         (received.sender, received.text, received.service))
        self.assertEqual(Service.IMESSAGE, self.alice.get_service())

    def test_start_conversation_with_unreachable_recipient(self):
        # a simulator cannot send messages to new recipients
        with self.assertRaises(MessagesError):
            self.alice.start_conversation("+15551234567", "Puma test")
        self.assertTrue(self.alice.go_to_state(self.alice.conversations_state))

    def test_delete_conversation(self):
        self.alice.delete_conversation(CONVERSATION_A)
        self.assertFalse(self.alice.driver.is_present(conversation_row(CONVERSATION_A)))
        # sending a message from the other conversation brings the deleted conversation back
        self.alice.send_message("Puma test, are you there?", conversation=CONVERSATION_B)
        received = self.alice.get_messages(CONVERSATION_A)[-1]
        self.assertEqual((CONVERSATION_A, "Puma test, are you there?"), (received.sender, received.text))


    def test_search_conversations(self):
        if self.alice.driver.is_simulator() or not SEARCH_CONVERSATION:
            self.skipTest('Searching needs a real device, and SEARCH_CONVERSATION configured at the top of the script')
        self.assertIn(SEARCH_CONVERSATION, self.alice.search_conversations(SEARCH_CONVERSATION))
        # conversations that are not shown in the overview are opened by searching for them
        self.alice.get_messages(SEARCH_CONVERSATION)
        self.assertTrue(self.alice.go_to_state(self.alice.conversations_state))


if __name__ == '__main__':
    unittest.main()
