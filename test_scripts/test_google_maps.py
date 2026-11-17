import unittest
from time import sleep

from puma.apps.android.google_maps.google_maps import GoogleMaps, TransportType

# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Alice": ""
}


class TestGoogleMaps(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Google Maps.
    The test can only be run manually, as you need a phone.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - Phone with Google Maps installed, with location services on and location access granted to Google Maps
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = GoogleMaps(device_udids["Alice"])

    def test_search(self):
        self.alice.search_place('Eiffel Tower')
        self.alice.search_place('Laan van Ypenburg 6, The Hague')
        self.alice.search_place('52°35\'05.6"N 5°22\'53.2"E')

    def test_directions(self):
        self.alice.get_directions('Tower Bridge, London')
        self.alice.get_directions('Atomium', transport_type=TransportType.BIKE)

    def test_navigation(self):
        self.alice.start_navigation('Tower Bridge, London')
        self.alice.start_navigation('Eiffel Tower', transport_type=TransportType.BIKE)
        self.alice.start_navigation('Atomium', time_to_wait=5)
        self.alice.end_navigation()

    def test_route(self):
        driver = self.alice.driver
        self.alice.start_route(from_query='Laan van Ypenburg 6, The Hague', to_query='Eiffel Tower', speed=100)
        with self.assertRaises(RuntimeError):
            driver.start_route_with_queries('Eiffel Tower', 'Laan van Ypenburg 6, The Hague', 'car', 50)
        sleep(10)
        driver.update_route_speed(50)
        sleep(10)
        driver.update_route_speed(0)
        sleep(5)
        driver.update_route_speed(100, variance_absolute=10)
        sleep(10)
        self.assertFalse(driver.is_route_finished())
        self.alice.stop_route()
        self.assertTrue(driver.is_route_finished())


if __name__ == '__main__':
    unittest.main()
