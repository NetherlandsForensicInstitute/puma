import unittest

from puma.apps.ios.apple_maps.apple_maps import AppleMaps, TransportType
from puma.apps.ios.apple_maps.xpaths import DIRECTIONS_BUTTON, TRANSPORT_TYPE_PICKER, transport_type_button

# Fill in the udid below. Run `xcrun simctl list devices booted` (simulators) or `xcrun xctrace list devices`
# (real devices) to see the udids.
device_udids = {
    "Alice": ""
}


class TestAppleMaps(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Apple Maps on iOS.
    The test can only be run manually, as you need an iOS device or simulator.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - An iOS device or simulator running iOS 26
    - The device location is set to Paris, e.g. `xcrun simctl location <udid> set 48.8606,2.3376` on a simulator
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = AppleMaps(device_udids["Alice"])

    def test_search_place(self):
        self.alice.search_place("Eiffel Tower")
        self.assertTrue(self.alice.driver.is_present(DIRECTIONS_BUTTON))

    def test_search_category(self):
        self.alice.search_place("coffee")
        self.assertTrue(self.alice.driver.is_present(DIRECTIONS_BUTTON))

    def test_get_directions(self):
        self.alice.get_directions("Eiffel Tower", TransportType.BIKE)
        self.assertTrue(self.alice.driver.is_present(TRANSPORT_TYPE_PICKER))
        selected = self.alice.driver.get_element(transport_type_button(TransportType.BIKE.value)).get_attribute('value')
        self.assertEqual('1', selected)

    def test_start_route(self):
        route = self.alice.get_route_simulator()
        try:
            self.alice.start_route("Louvre, Paris", "Eiffel Tower, Paris", 300, TransportType.BIKE)
            self.assertFalse(route.is_route_finished())
            # the route is about 4 km, which takes less than a minute at 300 km/h
            self.assertTrue(route.wait_until_route_finished(timeout=90))
        finally:
            self.alice.stop_route()


if __name__ == '__main__':
    unittest.main()
