import unittest

from puma.apps.android.state_graph.snapchat.snapchat import Snapchat

# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Bob": "34281JEHN03866"
}

class TestSnapchat(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Snapchat.
    The test can only be run manually, as you need a setup with at least one but preferably two phones.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - 1 registered Snapchat account for Alice
    - 1 phone with:
        - Snapchat installed and registered for Bob
        - Alice and Charlie in contacts
        - An existing conversation for Bob and Charlie (TODO: do this automatically)
    - Appium running
    """
    @classmethod
    def setUpClass(self):
        if not device_udids["Bob"]:
            print("No udid was configured for Bob. Please add at the top of the script.\nExiting....")
            exit(1)
        self.bob = Snapchat(device_udids["Bob"])

        self.contact_alice = "Alice iPhone"
        self.contact_charlie = "Charlie"

    def setUp(self):
        """
        Return to start screen of snapchat before each test
        """
        self.bob.go_to_state(Snapchat.camera_state)

    def test_send_message(self):
        self.bob.send_message(msg="Hi Charlie!", conversation=self.contact_charlie)

    def test_send_snap(self):
        self.bob.toggle_camera()
        self.bob.take_photo(caption="Hi Charlie!")
        self.bob.send_snap_to(recipients=[self.contact_charlie])
        self.bob.take_photo()
        self.bob.send_snap_to(recipients=[self.contact_alice, self.contact_charlie])

if __name__ == '__main__':
    unittest.main()
