import time
import unittest

from puma.apps.android.telegram.telegram import Telegram

# Fill in the udids below. Run ADB devices to see the udids.
device_udids = {
    "Alice": "",
    "Bob": ""
}
ALICE_NAME = "Alice"
BOB_NAME = "Bob"
GALLERY_FOLDER_NAME = "Screenshots"  # a directory containing pictures of videos that can be sent for this test


class TestTelegram(unittest.TestCase):
    """
    With this test, you can check whether all functionality works for the current version of Telegram.
    The test can only be run manually, as you need a setup with at least one but preferably two phones.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - 2 phones with Telegram installed and registered:
        - Alice:
            - Have Bob in contacts
            - Have Bob in the conversation overview (start chatting with Bob manually to ensure this)
        - Bob: (If this device is not configured, you can still run most tests, but the lower ones will fail).
            - Have Alice in contacts.
    - Appium running
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Telegram(device_udids["Alice"])

        self.bob_configured = bool(device_udids["Bob"])
        if self.bob_configured:
            self.bob = Telegram(device_udids["Bob"])
        else:
            print("WARNING: No udid configured for Bob. Some tests will fail as a result")

    def setUp(self):
        """
        Return to start screen of telegram before each test
        """
        self.alice.go_to_state(Telegram.conversations_state)
        if self.bob_configured:
            self.bob.go_to_state(Telegram.conversations_state)

    def test_send_message(self):
        self.alice.send_message("Hello Bob!", conversation=BOB_NAME)
        self.alice.send_message("Hello again")

    def test_send_voice_and_video_message(self):
        self.alice.send_voice_message(duration=2, conversation=BOB_NAME)
        self.alice.send_voice_message(duration=1)
        self.alice.send_video_message(duration=3)
        self.alice.send_video_message(duration=1, conversation=BOB_NAME)

    def test_send_from_gallery(self):
        self.alice.send_media_from_gallery(conversation=BOB_NAME, media_index=1)
        self.alice.send_media_from_gallery(media_index=[2,4])
        self.alice.send_media_from_gallery(conversation=BOB_NAME, media_index=3, caption="This is a caption")
        self.alice.send_media_from_gallery(conversation=BOB_NAME, media_index=1, folder=GALLERY_FOLDER_NAME)

    def test_calls(self):
        self.alice.start_call(conversation=BOB_NAME)
        self.bob.answer_call()
        time.sleep(2)
        self.bob.mute_mic()
        time.sleep(2)
        self.bob.mute_mic()
        time.sleep(1)
        self.alice.end_call()

    def test_group_management(self):
        group_name = 'Puma test group'
        new_group_name = 'New puma test group'
        self.alice.create_new_group(group_name=group_name, members=[BOB_NAME])
        self.bob.send_message(conversation=group_name, message='Hi there Alice!')
        self.alice.remove_member(conversation=group_name, member=BOB_NAME)
        self.alice.add_members(conversation=group_name, new_members=[BOB_NAME])
        self.bob.edit_group_name(conversation=group_name, new_group_name=new_group_name)
        self.bob.delete_and_leave_group(conversation=new_group_name)
        self.alice.delete_and_leave_group(conversation=new_group_name)
