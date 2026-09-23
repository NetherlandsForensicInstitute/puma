import unittest

from puma.apps.ios.contacts.contacts import Contacts
from puma.apps.ios.contacts.xpaths import contact_cell

# Fill in the udid below. Run `xcrun simctl list devices booted` (simulators) or `xcrun devicectl list devices`
# (real devices) to see the udids.
device_udids = {
    "Alice": ""
}


class TestContacts(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Contacts on iOS.
    The test can only be run manually, as you need an iOS device or simulator.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - An iOS device or simulator running iOS 26
    - No existing contact named 'Bob Puma'
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Contacts(device_udids["Alice"])

    def test_add_and_delete_contact(self):
        self.alice.add_contact("Bob", "Puma", phone_number="+31687654321", email="bob@example.com", company="NFI")
        details = self.alice.get_contact_details("Bob Puma")
        self.assertIn("home, bob@example.com", details)
        self.assertTrue(any(detail.startswith("mobile") for detail in details))
        self.alice.delete_contact("Bob Puma")
        self.assertFalse(self.alice.driver.is_present(contact_cell("Bob Puma")))


if __name__ == '__main__':
    unittest.main()
