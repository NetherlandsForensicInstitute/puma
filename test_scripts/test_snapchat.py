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
    - 1 registered Snapchat account for Alice
    - 1 phone with:
        - Snapchat installed and registered for Bob
        - Alice and Charlie in contacts
        - An existing conversation for Bob and Charlie (TODO: do this automatically)
    - Appium running
    """
    @classmethod
    def setUpClass(self):
        if not device_udids['Alice']:
            print('No udid was configured for Alice. Please add at the top of the script.')
            print('Exiting...')
            exit(1)
        self.alice = Snapchat(device_udids['Alice'])

        self.contact_bob = 'Bob'
        self.contact_charlie = 'Charlie'

    def setUp(self):
        """
        Return to start screen of snapchat before each test
        """
        self.alice.go_to_state(Snapchat.camera_state)

    def test_send_message(self):
        self.alice.send_message(message='Hi Charlie!', conversation=self.contact_charlie)

    def test_send_snap(self):
        self.alice.toggle_camera()
        self.alice.send_snap_to(recipients=[self.contact_charlie], caption='Hi Charlie!')
        self.alice.send_snap_to(recipients=[self.contact_bob, self.contact_charlie])

    def test_send_snap_to_my_story(self):
        self.alice.send_snap_to_my_story(caption='Hello!')

    def test_transitions(self):
        for to_state in self.alice.states:
            self.alice.go_to_state(to_state, conversation=self.contact_bob)
        self.alice.go_to_state(self.alice.initial_state)

if __name__ == '__main__':
    unittest.main()
