import unittest
from datetime import datetime, timedelta

from puma.apps.ios.reminders.reminders import Reminders

# Fill in the udid below. Run `xcrun simctl list devices booted` (simulators) or `xcrun xctrace list devices`
# (real devices) to see the udids.
device_udids = {
    "Alice": ""
}


class TestReminders(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Reminders on iOS.
    The test can only be run manually, as you need an iOS device or simulator.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - An iOS device or simulator running iOS 26
    - No existing reminders named 'Puma buy milk', 'Puma dentist', and no list named 'Puma groceries'
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Reminders(device_udids["Alice"])

    def test_reminders(self):
        due = (datetime.now() + timedelta(days=5)).replace(hour=9, minute=30)
        self.alice.add_reminder("Puma buy milk")
        self.alice.add_reminder("Puma dentist", notes="Bring insurance card", due=due, due_time=True)
        self.assertEqual(["Puma buy milk", "Puma dentist"], [r for r in self.alice.get_reminders() if r.startswith("Puma")])
        self.assertIn("09:30", self.alice.get_reminder_details("Puma dentist"))
        self.alice.complete_reminder("Puma buy milk")
        self.assertNotIn("Puma buy milk", self.alice.get_reminders())
        self.alice.delete_reminder("Puma dentist")
        self.assertNotIn("Puma dentist", self.alice.get_reminders())

    def test_lists(self):
        self.alice.add_list("Puma groceries")
        self.alice.add_reminder("Puma apples", list_name="Puma groceries")
        self.assertEqual(["Puma apples"], self.alice.get_reminders(list_name="Puma groceries"))
        self.alice.delete_list("Puma groceries")


if __name__ == '__main__':
    unittest.main()
