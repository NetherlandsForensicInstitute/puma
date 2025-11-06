import unittest
from time import sleep

from puma.apps.android.whatsapp.whatsapp import WhatsApp
from puma.apps.android.whatsapp.xpaths import CONVERSATIONS_ROW_BY_SUBJECT

# Fill in the udids below. Run ADB devices to see the udids.
device_udids = {
    "Alice": "",
    "Bob": ""
}


class TestWhatsapp(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Whatsapp. The test
    can only be run manually, as you need a setup with two phones

    Prerequisites:
    - All prerequisites mentioned in the README.
    - 2 phones with WhatsApp registered:
        - Alice:
            - Have Bob and Charlie in contacts
            - Have a folder named "photos" with at least 1 photo on the location WhatsApp looks for media (for
            example create the folder in Google Photos or the gallery app)
        - Bob: (If this device is not configured, you can still run most tests, but the lower ones will fail).
            - Have Alice in contacts.
    - Appium running
    - A 3rd registered WhatsApp account Charlie (for some tests this is required)
    """
    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = WhatsApp(device_udids["Alice"], "com.whatsapp") # Assuming Phone class is already defined

        self.bob_configured = bool(device_udids["Bob"])
        if self.bob_configured:
            self.bob = WhatsApp(device_udids["Bob"], "com.whatsapp")
        else:
            print("WARNING: No udid configured for Bob. Some tests will fail as a result")

        self.contact_alice = "Alice"
        self.contact_bob = "Bob"
        self.contact_charlie = "Charlie"
        self.photo_directory_name = "photos"

    def conversation_present(self, subject):
        return self.alice.driver.is_present(CONVERSATIONS_ROW_BY_SUBJECT.format(conversation=subject))

    def ensure_bob_conversation_present(self):
        if not self.conversation_present(self.contact_bob):
            self.alice.create_new_chat(self.contact_bob, "create new chat, first message")

    def test_change_profile_picture(self):
        self.alice.change_profile_picture("Screenshots")

    def test_set_about(self):
        self.alice.set_about("about text")

    def test_set_status(self):
        self.alice.add_status("caption")

    def test_create_new_chat(self):
        self.alice.create_new_chat(self.contact_bob, "create new chat, first message")

    def test_activate_and_deactivate_disappearing_messages(self):
        self.ensure_bob_conversation_present()
        self.alice.activate_disappearing_messages(self.contact_bob)
        self.alice.deactivate_disappearing_messages(self.contact_bob)

    def test_send_and_delete_message_for_everyone(self):
        self.ensure_bob_conversation_present()
        self.alice.send_message(self.contact_bob, "message to delete")
        self.alice.delete_message_for_everyone(self.contact_bob, "message to delete")

    def test_forward_message(self):
        self.ensure_bob_conversation_present()
        message_to_forward = "message to forward"
        self.alice.send_message(self.contact_bob, message_to_forward, True)
        self.alice.forward_message(self.contact_bob, message_to_forward, self.contact_bob)

    def test_reply_to_message(self):
        self.ensure_bob_conversation_present()
        message = "message to reply to"
        self.alice.send_message(self.contact_bob, message, True)
        self.alice.reply_to_message(self.contact_bob, message, "reply")

    def test_send_media(self):
        self.alice.send_media(self.contact_bob, "Screenshots", caption="caption", view_once=False)

    def test_send_media_view_once(self):
        self.alice.send_media(self.contact_bob, 'Screenshots', caption="caption", view_once=True)

    def test_send_sticker(self):
        self.alice.send_sticker(self.contact_bob)

    def test_send_emoji(self):
        self.alice.send_emoji(self.contact_bob)

    def test_send_contact(self):
        self.ensure_bob_conversation_present()
        self.alice.send_contact(self.contact_bob, self.contact_bob)

    def test_send_current_location(self):
        self.ensure_bob_conversation_present()
        self.alice.send_current_location(self.contact_bob)

    def test_send_and_stop_live_location(self):
        self.ensure_bob_conversation_present()
        self.alice.send_live_location(self.contact_bob, "caption")
        self.alice.stop_live_location(self.contact_bob)

    def test_send_voice_recording(self):
        self.ensure_bob_conversation_present()
        self.alice.send_voice_recording(self.contact_bob)

    # Group related tests
    def test_set_group_description(self):
        description_group = "description group"
        self.alice.create_group(description_group, self.contact_bob)
        self.alice.set_group_description(description_group, "group description")

    def test_archive_group(self):
        archive_group = "archive group"
        self.alice.create_group(archive_group, self.contact_bob)
        self.alice.archive_conversation(archive_group)

    def test_leave_group(self):
        leave_group = "leave group"
        self.alice.create_group(leave_group, self.contact_bob)
        self.alice.leave_group(leave_group)

    def test_delete_group(self):
        delete_group = "delete group"
        self.alice.create_group(delete_group, self.contact_bob)
        self.alice.delete_group(delete_group)

    def test_remove_participant_from_group(self):
        group = "remove bob group"
        self.alice.create_group(group, self.contact_bob)
        self.alice.remove_participant_from_group(group, self.contact_bob)

    # Call related tests. Note that you need two phones for these tests, otherwise these tests will fail
    def assert_bob_configured(self):
        self.assertTrue(self.bob_configured, "Bob is not configured. This test cannot be executed.")

    # TODO Call Bob and hang up immediately (voice and video)

    def test_answer_end_voice_call(self):
        self.assert_bob_configured()
        self.alice.voice_call_contact(self.contact_bob)
        self.bob.answer_call()
        sleep(2)
        self.alice.end_voice_call(self.contact_bob)

    def test_answer_end_video_call(self):
        self.assert_bob_configured()
        self.alice.video_call_contact(self.contact_bob)
        self.bob.answer_call()
        sleep(2)
        self.alice.end_video_call(self.contact_bob)

    def test_decline_voice_call(self):
        self.assert_bob_configured()
        self.alice.voice_call_contact(self.contact_bob)
        self.bob.decline_call()

    def test_decline_video_call(self):
        self.assert_bob_configured()
        self.alice.video_call_contact(self.contact_bob)
        self.bob.decline_call()

    def test_open_view_once_photo(self):
        self.assert_bob_configured()
        self.alice.send_media(self.contact_bob, self.photo_directory_name, view_once=True)
        sleep(1)
        self.bob.open_view_once_photo(self.contact_alice)

    # For this test, both Bob and Charlie need to be in Alice's contacts
    def test_send_broadcast(self):
        message = "broadcast message"
        self.alice.send_broadcast([self.contact_bob, self.contact_charlie], message)


if __name__ == '__main__':
    unittest.main()

