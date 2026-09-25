import unittest

from puma.apps.ios.safari.safari import Safari
from puma.apps.ios.safari.xpaths import ADDRESS_BAR, bookmark

# Fill in the udid below. Run `xcrun simctl list devices booted` (simulators) or `xcrun xctrace list devices`
# (real devices) to see the udids.
device_udids = {
    "Alice": ""
}


class TestSafari(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Safari on iOS.
    The test can only be run manually, as you need an iOS device or simulator.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - An iOS device or simulator running iOS 26
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Safari(device_udids["Alice"])

    def _address(self) -> str:
        return self.alice.driver.get_element(ADDRESS_BAR).get_attribute('value')

    def test_visit_url_new_tab(self):
        self.alice.visit_url_new_tab("example.com")
        self.assertIn("example.com", self._address())

    def test_visit_url(self):
        self.alice.visit_url_new_tab("example.com")
        self.alice.visit_url("example.org")
        self.assertIn("example.org", self._address())

    def test_visit_url_private(self):
        self.alice.visit_url_private("example.net")
        self.assertIn("example.net", self._address())

    def test_bookmarks(self):
        self.alice.visit_url_new_tab("example.com")
        # Clean up at the start, so we can be sure that both saving and deleting are properly tested.
        while self.alice.delete_bookmark("Example Domain"):
            pass
        self.alice.go_to_state(self.alice.current_tab_state)
        self.alice.bookmark_page()
        self.alice.load_bookmark("Example Domain")
        self.assertIn("example.com", self._address())
        self.assertTrue(self.alice.delete_bookmark("Example Domain"))
        self.assertFalse(self.alice.driver.is_present(bookmark("Example Domain")))


if __name__ == '__main__':
    unittest.main()
