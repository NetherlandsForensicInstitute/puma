import unittest

from puma.apps.android.google_chrome.google_chrome import GoogleChromeActions
from test_scripts.test_google_maps import device_udids

# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Alice": ""
}


class TestGoogleChrome(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Google Chrome.
    The test can only be run manually, as you need a setup with at least one but preferably two phones.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - Phone or emulator with Google Chrome installed
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Pleas add at the top of the script.\nExiting....")
            exit(1)
        self.alice = GoogleChromeActions(device_udids["Alice"])

    def test_go_to(self):
        self.alice.go_to("www.wikipedia.com")

    def test_new_tab(self):
        self.alice.go_to("www.google.com", new_tab=True)

    def test_save_bookmark(self):
        self.alice.bookmark_page()

    def test_load_bookmark(self):
        self.alice.load_bookmark()

    def test_incognito(self):
        self.alice.go_to_incognito("www.wikipedia.com")


if __name__ == '__main__':
    unittest.main()