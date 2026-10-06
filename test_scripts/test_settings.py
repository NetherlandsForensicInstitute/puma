import unittest

from puma.apps.ios.settings.settings import Settings

# Fill in the udid below. Run `xcrun xctrace list devices` to see the udids of real devices.
device_udids = {
    "Alice": ""
}


class TestSettings(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Settings on iOS.
    The test can only be run manually, as you need a real iOS device: simulators have no Auto-Lock setting.
    The Auto-Lock setting of the device is restored at the end of the test.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - A real iOS device running iOS 26
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Settings(device_udids["Alice"])

    def test_auto_lock(self):
        original = self.alice.get_auto_lock()
        try:
            self.alice.set_auto_lock(None)
            self.assertIsNone(self.alice.get_auto_lock())
            self.alice.set_auto_lock(120)
            self.assertEqual(120, self.alice.get_auto_lock())
            with self.assertRaises(ValueError):
                self.alice.set_auto_lock(45)
        finally:
            self.alice.set_auto_lock(original)


if __name__ == '__main__':
    unittest.main()
