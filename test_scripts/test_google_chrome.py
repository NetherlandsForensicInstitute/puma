import unittest

from puma.apps.android.google_chrome.google_chrome import GoogleChromeActions, GoogleChrome

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
    - At least one tab with a url entered in the tab overview
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = GoogleChrome(device_udids["Alice"])


    def test_visit_url(self):
        self.alice.visit_url("www.google.com", 1)

    def test_visit_url_new_tab(self):
        self.alice.visit_url_new_tab("wikipedia.org")

    def test_bookmarks(self):
        self.alice.visit_url("www.wikipedia.com", 1)
        # Clean up at the start, so we can be sure that both saving and deleting are properly tested.
        self.alice.delete_bookmark(1)

        self.assertTrue(self.alice.bookmark_page(1))
        self.assertFalse(self.alice.bookmark_page(1))
        self.alice.load_first_bookmark("Mobile bookmarks")
        self.assertTrue(self.alice.delete_bookmark(1))
        self.assertFalse(self.alice.delete_bookmark(1))

    def test_go_to_incognito(self):
        self.alice.visit_url_incognito("www.wikipedia.com")


if __name__ == '__main__':
    unittest.main()
