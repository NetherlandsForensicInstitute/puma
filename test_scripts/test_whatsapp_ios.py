import unittest

from puma.apps.ios.whatsapp.whatsapp import WhatsApp

# Fill in the udid below. Run `xcrun xctrace list devices` to see the udids. WhatsApp cannot be installed on a
# simulator.
device_udids = {
    "Alice": ""
}
# Real devices need the signing settings of WebDriverAgent, see docs/setup-ios.md
desired_capabilities = {
    # "appium:xcodeOrgId": "<your team id>",
    # "appium:xcodeSigningId": "Apple Development",
}

# The contact the test messages are sent to. Bob receives all test messages, and is added to a test group.
CONTACT = "Bob"
# A second contact, only for the broadcast test, as a broadcast needs at least 2 receivers. Leave empty to skip it.
SECOND_CONTACT = ""
GROUP_NAME = "Puma test group"


class TestWhatsAppIOS(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of WhatsApp on iOS.
    The test can only be run manually, as you need a real iOS device with WhatsApp.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - Alice: an iOS device with WhatsApp registered, with CONTACT in its contacts, and an existing chat with CONTACT.
    - At least one photo in the photo library of Alice.
    - Note that some tests send the location of the device, record a voice message with the microphone, post a status
      and call CONTACT. The about and the profile picture are not changed by this test.
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = WhatsApp(device_udids["Alice"], desired_capabilities=desired_capabilities)

    def test_send_and_read_messages(self):
        self.alice.send_message("Puma test, with a comma", conversation=CONTACT)
        sent = self.alice.get_messages(CONTACT)[-1]
        self.assertEqual((None, "Puma test, with a comma"), (sent.sender, sent.text))
        self.assertTrue(self.alice.is_message_marked_sent("Puma test, with a comma")
                        or self.alice.is_message_marked_delivered("Puma test, with a comma"))

    def test_quotes_and_the_newest_message(self):
        # the newest of the messages with the same text is used
        self.alice.send_message('Puma test, "quoted"', conversation=CONTACT)
        self.alice.send_message('Puma test, "quoted"')
        self.alice.reply_to_message('Puma test, "quoted"', "Puma test, reply to the newest")
        messages = self.alice.get_messages()
        self.assertEqual(('Puma test, "quoted"', "Puma test, reply to the newest"),
                         (messages[-2].text, messages[-1].text))
        self.assertTrue(self.alice.is_message_marked_sent("Puma test, reply to the newest", 10)
                        or self.alice.is_message_marked_delivered("Puma test, reply to the newest", 10))

    def test_create_new_chat(self):
        self.alice.create_new_chat(CONTACT, "Puma test, new chat")
        self.assertEqual("Puma test, new chat", self.alice.get_messages()[-1].text)

    def test_reply_forward_and_delete(self):
        self.alice.send_message("Puma test, reply to me", conversation=CONTACT)
        self.alice.reply_to_message("Puma test, reply to me", "Puma test, a reply")
        reply = self.alice.get_messages()[-1]
        self.assertEqual(("Puma test, a reply", True, "Puma test, reply to me"),
                         (reply.text, reply.is_reply, reply.reply_to))
        self.alice.forward_message(CONTACT, "Puma test, reply to me", CONTACT)
        self.assertEqual("Puma test, reply to me", self.alice.get_messages()[-1].text)
        self.alice.delete_message_for_everyone("Puma test, a reply")
        self.assertNotIn("Puma test, a reply", [message.text for message in self.alice.get_messages()])

    def test_emoji_and_sticker(self):
        self.alice.send_emoji(CONTACT)
        self.assertEqual("\U0001F44D", self.alice.get_messages()[-1].text)
        self.alice.send_sticker(CONTACT)
        self.assertEqual("sticker", self.alice.get_messages()[-1].kind)

    def test_media_voice_and_contact(self):
        self.alice.send_media(1, conversation=CONTACT, caption="Puma test, a photo")
        self.assertEqual("Puma test, a photo", self.alice.get_messages()[-1].text)
        self.alice.send_voice_message(2, conversation=CONTACT)
        self.assertEqual("voice message", self.alice.get_messages()[-1].kind)
        self.alice.send_contact(CONTACT, conversation=CONTACT)
        self.assertEqual(("contact", CONTACT), (self.alice.get_messages()[-1].kind, self.alice.get_messages()[-1].text))

    def test_locations(self):
        self.alice.send_current_location(conversation=CONTACT)
        self.assertEqual("location", self.alice.get_messages(CONTACT)[-1].kind)
        self.alice.send_live_location(caption="Puma test, live location", conversation=CONTACT)
        self.assertEqual("live location", self.alice.get_messages()[-1].kind)
        self.alice.stop_live_location(conversation=CONTACT)

    def test_chat_settings(self):
        self.alice.activate_disappearing_messages(CONTACT)
        self.alice.deactivate_disappearing_messages(CONTACT)
        self.alice.view_contact_profile_picture(CONTACT)
        self.alice.archive_conversation(CONTACT)
        self.alice.unarchive_conversation(CONTACT)

    def test_groups(self):
        self.alice.create_group(GROUP_NAME, CONTACT)
        self.alice.set_group_description(GROUP_NAME, "Puma test description")
        self.assertTrue(self.alice.group_exists(GROUP_NAME, [CONTACT]))
        self.alice.remove_member_from_group(GROUP_NAME, CONTACT)
        self.alice.leave_group(GROUP_NAME)
        self.alice.delete_group(GROUP_NAME)
        self.assertFalse(self.alice.group_exists(GROUP_NAME, [CONTACT]))

    def test_broadcast(self):
        if not SECOND_CONTACT:
            self.skipTest('A broadcast needs SECOND_CONTACT configured at the top of the script')
        self.alice.send_broadcast([CONTACT, SECOND_CONTACT], "Puma test, broadcast")
        self.assertEqual("Puma test, broadcast", self.alice.get_messages()[-1].text)

    def test_status(self):
        self.alice.add_status("Puma test, status")
        self.alice.delete_status()

    def test_calls(self):
        """
        CONTACT has to answer the call within 30 seconds.
        """
        self.alice.start_voice_call(CONTACT)
        self.assertTrue(self.alice.in_connected_call(implicit_wait=30))
        self.alice.end_voice_call()


if __name__ == '__main__':
    unittest.main()
