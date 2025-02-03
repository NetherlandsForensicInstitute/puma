import time
import unittest

from puma.apps.android.telegram.telegram import TelegramActions


# Fill in the udids below. Run ADB devices to see the udids.
device_udids = {
    "Alice": "",
    "Bob": ""
}


class TestTelegram(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Telegram.
    The test can only be run manually, as you need a setup with at least one but preferably two phones.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - 2 phones with Telegram isntalled and registered:
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
        self.alice = TelegramActions(device_udids["Alice"])

        self.bob_configured = bool(device_udids["Bob"])
        if self.bob_configured:
            self.bob = TelegramActions(device_udids["Bob"])
        else:
            print("WARNING: No udid configured for Bob. Some tests will fail as a result")

        self.contact_alice = "Alice"
        self.contact_bob = "Bob"

    def test_navigation(self):
        self.alice.return_to_homescreen()
        self.alice.select_chat(self.contact_bob)
        self.alice.return_to_homescreen()

    def test_send_message(self):
        self.alice.send_message("Hello Bob!", chat=self.contact_bob)
        self.alice.send_message("Hello again!")

    def test_reply_to_message(self):
        original_message = "test123"
        self.alice.send_message(original_message, chat=self.contact_bob)
        self.alice.reply_to_message(original_message, reply="This is a first reply")
        self.alice.return_to_homescreen()
        self.alice.reply_to_message(original_message, reply="this is a second reply", chat=self.contact_bob)

    def test_emoji_reply_to_message(self):
        original_message = "test123"
        self.alice.send_message(original_message, chat=self.contact_bob)
        self.alice.emoji_reply_to_message(original_message)
        self.alice.emoji_reply_to_message(original_message, emoji_to_respond_with="👎")
        self.alice.return_to_homescreen()
        self.alice.emoji_reply_to_message(original_message, chat=self.contact_bob)

    def test_take_and_send_picture(self):
        self.alice.take_and_send_picture(chat=self.contact_bob)
        self.alice.take_and_send_picture(caption="test caption!")
        self.alice.take_and_send_picture(front_camera=True)
        time_to_sleep = 2
        start = time.time()
        self.alice.take_and_send_picture(wait_time=time_to_sleep)
        end = time.time()
        if end - start < time_to_sleep:
            self.fail("phone.take_and_send_picture did not wait long enough")

    def test_calls_abort_call(self):
        self.alice.start_call(self.contact_bob)
        time.sleep(2)
        self.alice.end_call()
        self.alice.start_call(self.contact_bob, video=True)
        time.sleep(2)
        self.alice.end_call()

    def test_get_call_status(self):
        self.assertIsNone(self.alice.get_call_status())
        self.alice.start_call(self.contact_bob)
        self.assertIsNotNone(self.alice.get_call_status())
        self.alice.end_call()

    # Call related tests. Note that you need two phones for these tests, otherwise these tests will fail
    def assert_bob_configured(self):
        self.assertTrue(self.bob_configured, "Bob is not configured. This test cannot be executed.")

    def test_calls_decline_call(self):
        self.assert_bob_configured()
        self.alice.start_call(self.contact_bob)
        time.sleep(2)
        self.bob.decline_call()

    def test_calls_answer_and_end_call(self):
        self.assert_bob_configured()
        self.alice.start_call(self.contact_bob)
        time.sleep(2)
        self.bob.answer_call()
        time.sleep(2)
        self.bob.end_call()

    def test_calls_change_video(self):
        self.assert_bob_configured()
        self.alice.start_call(self.contact_bob)
        time.sleep(2)
        self.bob.answer_call()
        time.sleep(1)
        self.alice.toggle_video_in_call()
        time.sleep(1)
        self.alice.flip_video_in_call()
        time.sleep(1)
        self.alice.flip_video_in_call()
        time.sleep(1)
        self.alice.toggle_video_in_call()
        time.sleep(1)
        self.bob.end_call()


if __name__ == '__main__':
    unittest.main()
