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
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = GoogleChrome(device_udids["Alice"])

    def test_go_to(self):
        self.alice.go_to("www.google.com", 2)

    def test_new_tab(self):
        self.alice.go_to_new_tab("wikipedia.org")

    def test_bookmark_page(self):
        self.alice.bookmark_page(1)

    def test_delete_bookmark_page(self):
        #TODO make sure there already is a bookmark
        self.alice.delete_bookmark(1)

    def test_bookmarks(self):
        self.alice.go_to("www.wikipedia.com", False)
        # Clean up at the start, so we can be sure that both saving and deleting are properly tested.
        # self.alice.delete_bookmark()

        # self.assertTrue(self.alice.bookmark_page())
        # self.assertFalse(self.alice.bookmark_page())
        self.alice.load_first_bookmark(1)
        # self.assertTrue(self.alice.delete_bookmark())
        # self.assertFalse(self.alice.delete_bookmark())

    def test_incognito(self):
        self.alice.go_to_incognito("www.wikipedia.com")


if __name__ == '__main__':
    unittest.main()
