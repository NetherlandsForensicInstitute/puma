# Fill in the udids below. Run ADB devices to see the udids.
import unittest

from puma.apps.android.teleguard.teleguard import TeleGuard

device_udids = {
    "Alice": "",
    "Bob": ""
}

teleguard_ids = {
    "Bob": ""
}

class TestTeleGuard(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of TeleGuard.
    The test can only be run manually, as you need a setup with at least one but preferably two phones.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - 2 phones with TeleGuard installed and registered, with usernames Alice and Bob. Find the TeleGuard IDs and fill them
    in above in `teleguard_ids`.
    - Alice and Bob should not already have a conversation or be in each other's contacts TODO note how
    - Appium running
    """
    @classmethod
    def setUpClass(self):
        for udid_key in ("Alice", "Bob"):
            if not device_udids[udid_key]:
                print(f"No udid was configured for {udid_key}. Please add at the top of the script.")
                print("Exiting....")
                exit(1)
        if not teleguard_ids["Bob"]:
            print("No TeleGuard ID was configured for Bob. Please add at the top of the script.")
            print("Exiting....")
            exit(1)

        self.alice = TeleGuard(device_udids["Alice"])
        self.bob = TeleGuard(device_udids["Bob"])

        self.contact_alice = "Alice"
        self.contact_bob = "Bob"

        self.alice.add_contact(teleguard_ids["Bob"])
        self.bob.accept_invite()

    def test_select_chat_send_message(self):
        self.alice.send_message("Test message from Alice to Bob", conversation="Bob")

