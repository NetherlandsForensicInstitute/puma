import unittest

from puma.apps.android


# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Alice": "32131JEHN38079"
}


class TestPlayStore(unittest.TestCase):
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
    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = SnapchatActions(device_udids["Alice"])
        self.contact_bob = "Bob"
        self.contact_charlie = "Charlie"