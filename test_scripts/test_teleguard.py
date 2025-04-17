from puma.apps.android.teleguard.teleguard import TeleguardActions
# Fill in the udids below. Run ADB devices to see the udids.
import unittest

device_udids = {
    "Alice": "",
    "Bob": ""
}

teleguard_ids = {
    "Bob": ""
}

class TestTeleguard(unittest.TestCase):
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
                print(f"No udid was configured for {udid_key}. Please add at the top of the script.\nExiting....")
                exit(1)
        if not teleguard_ids["Bob"]:
            print("No TeleGuard ID was configured for Bob. Please add at the top of the script.\nExiting....")

        self.alice = TeleguardActions(device_udids["Alice"])
        self.bob = TeleguardActions(device_udids["Bob"])

        self.contact_alice = "Alice"
        self.contact_bob = "Bob"

        self.alice.add_contact(teleguard_ids["Bob"])
        self.bob.accept_invite()

    def test_select_chat_send_message(self):
        self.alice.select_chat("Bob")
        self.alice.send_message("Test message from Alice to Bob")

    def test_send_message(self):
        self.alice.return_to_homescreen()
        self.alice.send_message("Test message and selecting Bob chat in one go", "Bob")



