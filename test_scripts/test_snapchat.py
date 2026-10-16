import unittest

from puma.apps.android.snapchat.snapchat import Snapchat

# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    'Alice': ''
}


class TestSnapchat(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Snapchat.
    The test can only be run manually, as you need a setup with at least one but preferably two phones.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - 1 phone with Snapchat installed and registered for Alice
    - Bob and Charlie are friends of Alice in Snapchat
    - Appium running
    """

    @classmethod
    def setUpClass(cls):
        if not device_udids['Alice']:
            print('No udid was configured for Alice. Please add at the top of the script.')
            print('Exiting...')
            exit(1)
        cls.alice = Snapchat(device_udids['Alice'])

        cls.contact_bob = 'Bob'
        cls.contact_charlie = 'Charlie'

    def setUp(self):
        """
        Return to start screen of snapchat before each test
        """
        self.alice.go_to_state(Snapchat.camera_state)

    def test_send_message(self):
        self.alice.send_message(message='Hi Charlie!', conversation=self.contact_charlie)
        self.alice.send_message(message='How are you?')

    def test_send_snap(self):
        self.alice.send_snap(conversation=self.contact_charlie, caption='Hi Charlie!')
        self.alice.send_snap()

    def test_send_snap_to(self):
        self.alice.send_snap_to(recipients=[self.contact_charlie], caption='Hi Charlie!')
        self.alice.send_snap_to(recipients=[self.contact_bob, self.contact_charlie])

    def test_flip_camera(self):
        self.alice.flip_camera()
        self.alice.flip_camera()

    def test_transitions(self):
        for to_state in self.alice.states:
            if not to_state.recognize_only:
                self.alice.go_to_state(to_state, conversation=self.contact_bob)
        self.alice.go_to_state(self.alice.initial_state)


if __name__ == '__main__':
    unittest.main()
