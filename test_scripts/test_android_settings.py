import unittest

from puma.apps.android.settings.settings import Settings

# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Alice": ""
}
# A Wi-Fi network in range of the device and its password, to test connecting to a network.
# The Wi-Fi test is skipped when no network is configured.
WIFI_SSID = ""
WIFI_PASSWORD = ""


class TestAndroidSettings(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Settings on Android.
    The test can only be run manually, as you need a real device.
    The brightness and screen timeout are restored at the end of each test.

    Prerequisites:
    - All prerequisites mentioned in the README.
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Settings(device_udids["Alice"])

    def test_brightness(self):
        original = self.alice.get_brightness()
        try:
            for percentage in [0, 50, 100]:
                self.alice.set_brightness(percentage)
                # Adaptive brightness can change the brightness level a bit
                self.assertAlmostEqual(percentage, self.alice.get_brightness(), delta=5)
            with self.assertRaises(ValueError):
                self.alice.set_brightness(101)
        finally:
            self.alice.set_brightness(original)

    def test_screen_timeout(self):
        original = self.alice.get_screen_timeout()
        try:
            self.alice.set_screen_timeout(15)
            self.assertEqual(15, self.alice.get_screen_timeout())
            self.alice.set_screen_timeout(600)
            self.assertEqual(600, self.alice.get_screen_timeout())
            with self.assertRaises(ValueError):
                self.alice.set_screen_timeout(45)
        finally:
            self.alice.set_screen_timeout(original)

    @unittest.skipUnless(WIFI_SSID, 'No Wi-Fi network configured')
    def test_connect_to_wifi(self):
        self.assertTrue(self.alice.connect_to_wifi(WIFI_SSID, WIFI_PASSWORD))
        # Connecting again does nothing
        self.assertTrue(self.alice.connect_to_wifi(WIFI_SSID, WIFI_PASSWORD))

    def test_transitions(self):
        for state in Settings.states:
            self.alice.go_to_state(state)


if __name__ == '__main__':
    unittest.main()
