import unittest

from puma.apps.ios.messages.messages import Messages, MessagesError
from puma.apps.ios.messages.xpaths import SENT_BY_ME, conversation_row

# Fill in the udid below. Run `xcrun simctl list devices booted` (simulators) or `xcrun xctrace list devices`
# (real devices) to see the udids.
device_udids = {
    "Alice": ""
}

# The two conversations a simulator starts with. Messages sent in one of them are received in the other.
CONVERSATION_A = "+1 (888) 555-1212"
CONVERSATION_B = "+1 (555) 564-8583"


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
        self.assertEqual((SENT_BY_ME, "Puma test, with a comma"), self.alice.get_messages(CONVERSATION_A)[-1])
        # on a simulator, the message is received in the other conversation
        self.assertEqual((CONVERSATION_B, "Puma test, with a comma"), self.alice.get_messages(CONVERSATION_B)[-1])

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
        self.assertEqual((CONVERSATION_A, "Puma test, are you there?"), self.alice.get_messages(CONVERSATION_A)[-1])


if __name__ == '__main__':
    unittest.main()
