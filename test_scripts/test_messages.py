import unittest

from puma.apps.ios.messages.messages import LiveLocationDuration, Messages, MessagesError, Reaction, Service
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
# Real devices only: an iMessage conversation with someone who shares read receipts, to test replying, read receipts,
# editing, unsending and forwarding. These are not available on the simulator. The other person has to read the message
# during the test. Forwarding is tested by forwarding a message to this same conversation.
REPLY_CONVERSATION = ""
# Real devices only: at least three other people with iMessage, to test group conversations. Removing people and leaving
# a group is only possible in groups of at least four people, including yourself. The name of the test group is
# GROUP_NAME. Note that all members receive the test messages.
GROUP_MEMBERS = []
GROUP_NAME = "Puma test group"


class TestMessages(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Messages on iOS.
    The test can only be run manually, as you need an iOS device or simulator.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - An iOS simulator running iOS 26, with the two conversations a simulator starts with. On a real device, replace
      these by two conversations of your own.
    - At least one photo in the photo library, e.g. added with `xcrun simctl addmedia <udid> <photo>` on a simulator.
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Messages(device_udids["Alice"])

    def test_send_message(self):
        self.alice.send_message("Puma test, with a comma", conversation=CONVERSATION_A)
        sent = self.alice.get_messages(CONVERSATION_A)[-1]
        self.assertEqual((None, "Puma test, with a comma", Service.IMESSAGE), (sent.sender, sent.text, sent.service))
        self.assertTrue(sent.sent_by_me)
        # without a conversation, the conversation that is open is used
        self.alice.send_message("Puma test, same conversation")
        self.assertEqual("Puma test, same conversation", self.alice.get_messages()[-1].text)
        self.assertEqual(Service.IMESSAGE, self.alice.get_service())

    def test_start_conversation_with_unreachable_recipient(self):
        # a simulator cannot send messages to new recipients
        with self.assertRaises(MessagesError):
            self.alice.start_conversation("+15551234567", "Puma test")
        self.assertTrue(self.alice.go_to_state(self.alice.conversations_state))

    def test_delete_conversation(self):
        self.alice.delete_conversation(CONVERSATION_A)
        self.assertFalse(self.alice.driver.is_present(conversation_row(CONVERSATION_A)))
        # sending a message from the other conversation brings the deleted conversation back for the other tests
        self.alice.send_message("Puma test, are you there?", conversation=CONVERSATION_B)
        self.assertTrue(self.alice.go_to_state(self.alice.conversations_state))
        self.assertTrue(self.alice.driver.is_present(conversation_row(CONVERSATION_A), implicit_wait=10))


    def test_search_conversations(self):
        if self.alice.driver.is_simulator() or not SEARCH_CONVERSATION:
            self.skipTest('Searching needs a real device, and SEARCH_CONVERSATION configured at the top of the script')
        self.assertIn(SEARCH_CONVERSATION, self.alice.search_conversations(SEARCH_CONVERSATION))
        # conversations that are not shown in the overview are opened by searching for them
        self.alice.get_messages(SEARCH_CONVERSATION)
        self.assertTrue(self.alice.go_to_state(self.alice.conversations_state))


    def test_reactions(self):
        self.alice.send_message("Puma test, react to me", conversation=CONVERSATION_A)
        self.alice.react_to_message("Puma test, react to me", Reaction.HEART)
        self.assertEqual([(None, Reaction.HEART)], self.alice.get_messages()[-1].reactions)
        # a new reaction replaces the previous one
        self.alice.react_to_message("Puma test, react to me", Reaction.THUMBS_UP)
        self.assertEqual([(None, Reaction.THUMBS_UP)], self.alice.get_messages()[-1].reactions)

    def test_delivered(self):
        self.alice.send_message("Puma test, delivered?", conversation=CONVERSATION_A)
        self.assertTrue(self.alice.is_message_marked_delivered("Puma test, delivered?"))
        self.assertFalse(self.alice.is_message_marked_not_delivered("Puma test, delivered?"))
        self.alice.send_message("Puma test, newer message")
        # the status is only shown for the last message sent from this device
        self.assertIsNone(self.alice.is_message_marked_delivered("Puma test, delivered?", implicit_wait=0))

    def test_reply_and_read(self):
        if self.alice.driver.is_simulator() or not REPLY_CONVERSATION:
            self.skipTest('Replying needs a real device, and REPLY_CONVERSATION configured at the top of the script')
        self.alice.send_message("Puma test, please read this", conversation=REPLY_CONVERSATION)
        self.assertTrue(self.alice.is_message_marked_read("Puma test, please read this", implicit_wait=60))
        self.alice.reply_to_message("Puma test, please read this", "Puma test, a reply")
        reply = self.alice.get_messages()[-1]
        self.assertEqual(("Puma test, a reply", True, "Puma test, please read this"),
                         (reply.text, reply.is_reply, reply.reply_to))


    def test_delete_message(self):
        self.alice.send_message("Puma test, delete me", conversation=CONVERSATION_A)
        self.alice.send_message("Puma test, keep me")
        self.alice.delete_message("Puma test, delete me")
        texts = [message.text for message in self.alice.get_messages()]
        self.assertNotIn("Puma test, delete me", texts)
        self.assertEqual("Puma test, keep me", texts[-1])

    def test_edit_unsend_and_forward(self):
        if self.alice.driver.is_simulator() or not REPLY_CONVERSATION:
            self.skipTest('Editing, unsending and forwarding need a real device, and REPLY_CONVERSATION configured at '
                          'the top of the script')
        self.alice.send_message("Puma test, edit me", conversation=REPLY_CONVERSATION)
        self.alice.edit_message("Puma test, edit me", "Puma test, edited")
        edited = self.alice.get_messages()[-1]
        self.assertEqual(("Puma test, edited", True), (edited.text, edited.edited))
        self.alice.send_message("Puma test, unsend me")
        self.alice.delete_message_for_everyone("Puma test, unsend me")
        self.assertNotIn("Puma test, unsend me", [message.text for message in self.alice.get_messages()])
        # forward to the same conversation, so no one else receives test messages
        self.alice.forward_message(REPLY_CONVERSATION, "Puma test, edited", REPLY_CONVERSATION)
        forwarded = self.alice.get_messages()[-1]
        self.assertEqual(("Puma test, edited", False), (forwarded.text, forwarded.edited))


    def test_send_media_and_voice_message(self):
        self.alice.send_media(1, conversation=CONVERSATION_A, caption="Puma test, a photo")
        photo, caption = self.alice.get_messages()[-2:]
        self.assertEqual(("", "Puma test, a photo"), (photo.text, caption.text))
        self.assertIsNotNone(photo.attachment)
        self.alice.send_voice_message(2)
        self.assertIn("Audio", self.alice.get_messages()[-1].attachment)

    def test_live_location(self):
        if self.alice.driver.is_simulator() or not REPLY_CONVERSATION:
            self.skipTest('Sharing the location needs a real device, and REPLY_CONVERSATION configured at the top of '
                          'the script')
        self.alice.send_live_location(LiveLocationDuration.ONE_HOUR, conversation=REPLY_CONVERSATION)
        self.assertEqual("Location", self.alice.get_messages()[-1].attachment)
        self.assertTrue(self.alice.stop_live_location())
        self.assertFalse(self.alice.stop_live_location())


    def test_groups(self):
        if self.alice.driver.is_simulator() or len(GROUP_MEMBERS) < 3:
            self.skipTest('Groups need a real device, and three GROUP_MEMBERS configured at the top of the script')
        self.alice.create_group(GROUP_MEMBERS[:2], "Puma test, a group", group_name=GROUP_NAME)
        self.assertTrue(self.alice.group_exists(GROUP_NAME, GROUP_MEMBERS[:2]))
        self.alice.add_members([GROUP_MEMBERS[2]], conversation=GROUP_NAME)
        self.assertTrue(self.alice.group_exists(GROUP_NAME, GROUP_MEMBERS))
        self.alice.edit_group_name(GROUP_NAME, f"{GROUP_NAME} renamed")
        self.alice.remove_member(GROUP_MEMBERS[2], conversation=f"{GROUP_NAME} renamed")
        self.assertFalse(self.alice.group_exists(f"{GROUP_NAME} renamed", GROUP_MEMBERS))
        self.alice.leave_group(f"{GROUP_NAME} renamed")


if __name__ == '__main__':
    unittest.main()
