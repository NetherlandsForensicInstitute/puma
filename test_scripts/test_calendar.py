import unittest
from datetime import datetime, timedelta

from puma.apps.ios.calendar.calendar import Calendar

# Fill in the udid below. Run `xcrun simctl list devices booted` (simulators) or `xcrun xctrace list devices`
# (real devices) to see the udids.
device_udids = {
    "Alice": ""
}


class TestCalendar(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Calendar on iOS.
    The test can only be run manually, as you need an iOS device or simulator.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - An iOS device or simulator running iOS 26
    - No existing events named 'Puma meeting' or 'Puma day off'
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Calendar(device_udids["Alice"])

    def test_event(self):
        start = (datetime.now() + timedelta(days=40)).replace(hour=14, minute=5, second=0, microsecond=0)
        self.alice.add_event("Puma meeting", start, start + timedelta(hours=2), location="NFI The Hague")
        details = self.alice.get_event_details("Puma meeting")
        self.assertEqual(["Puma meeting", "NFI The Hague"], details[:2])
        self.assertIn("14:05", details[3])
        self.alice.delete_event("Puma meeting")

    def test_all_day_event(self):
        day = datetime.now() + timedelta(days=2)
        self.alice.add_event("Puma day off", day, all_day=True)
        details = self.alice.get_event_details("Puma day off", date=day)
        self.assertEqual("Puma day off", details[0])
        self.assertIn("All-day", details)
        self.alice.delete_event("Puma day off", date=day)


if __name__ == '__main__':
    unittest.main()
