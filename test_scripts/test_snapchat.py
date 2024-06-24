import unittest

from puma.apps.android.snapchat.snapchat import SnapchatActions


# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Alice": ""
}


class TestSnapchat(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Snapchat.
    The test can only be run manually, as you need a setup with at least one but preferably two phones.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - 1 registered Snapchat account for Bob
    - 1 phone with:
        - Snapchat installed and registered for Alice
        - Bob and Charlie in contacts
        - An existing conversation for Bob and Charlie (TODO: do this automatically)
    - Appium running
    """

    def setUp(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = SnapchatActions(device_udids["Alice"])
        self.contact_bob = "Bob"
        self.contact_charlie = "Charlie"

    def test_navigation(self):
        self.alice.go_to_conversation_tab()
        self.alice.go_to_camera_tab()
        self.alice.select_chat(self.contact_bob)

    def test_send_message(self):
        self.alice.select_chat(self.contact_bob)
        self.alice.send_message("Hi Bob!")
        self.alice.send_message("Hi charlie!", chat=self.contact_charlie)

    def test_send_snap(self):
        self.alice.send_snap(recipients=[self.contact_bob, self.contact_charlie])
        self.alice.send_snap(recipients=[self.contact_bob], caption="Hi bob!")
        self.alice.send_snap(caption="This is nice for my story!", front_camera=True)
        # no arguments: post to story without caption
        self.alice.send_snap()


if __name__ == '__main__':
    unittest.main()
