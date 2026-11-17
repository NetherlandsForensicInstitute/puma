import unittest
from time import sleep
from unittest.mock import Mock, patch, call

from geopy import Point

from puma.state_graph import puma_driver
from puma.state_graph.android_driver import AndroidPumaDriver
from puma.state_graph.ios_driver import IOSPumaDriver
from puma.utils import route_simulator
from puma.utils.route_simulator import RouteSimulator

ROUTE = [Point(48.8, 2.3), Point(48.9, 2.4)]


def _driver(udid: str = 'phone', driver_class=AndroidPumaDriver):
    """
    A PumaDriver with mocked Appium driver and logger, without connecting to a device.
    """
    driver = driver_class.__new__(driver_class)
    driver.options = Mock(udid=udid)
    driver.driver = Mock()
    driver.adb = Mock()
    driver.gtl_logger = Mock()
    return driver


class TestRouteSimulator(unittest.TestCase):
    def tearDown(self):
        for route in puma_driver._routes.values():
            route.stop_route()
        puma_driver._routes.clear()

    @patch('puma.utils.route_simulator.requests.get')
    def test_osm_route_uses_transport_mode(self, get):
        get.return_value.json.return_value = {'routes': [{'geometry': {'coordinates': [[2.3, 48.8], [2.4, 48.9]]}}]}
        points = route_simulator._get_osm_route(48.8, 2.3, 48.9, 2.4, 'bike')
        self.assertIn('/routed-bike/', get.call_args[0][0])
        self.assertIn('2.3,48.8;2.4,48.9', get.call_args[0][0])
        self.assertEqual([(48.8, 2.3), (48.9, 2.4)], [(p.latitude, p.longitude) for p in points])

    def test_unsupported_transport_mode(self):
        with self.assertRaises(ValueError):
            route_simulator.plan_route('a', 'b', 'boat')

    def test_route_starts_at_first_point_through_driver(self):
        driver = Mock()
        simulator = RouteSimulator(driver)
        simulator.execute_route_with_points(ROUTE)
        self.assertEqual(ROUTE[0], simulator._current_location)
        sleep(0.5)  # the location thread sets the location right after it starts
        simulator.stop_route()
        driver.set_location.assert_any_call(48.8, 2.3, 0, 0)

    def test_route_finished(self):
        driver = _driver()
        self.assertTrue(driver.is_route_finished())
        driver.start_route_with_points(ROUTE, 0)
        self.assertFalse(driver.is_route_finished())
        self.assertFalse(driver.wait_until_route_finished(timeout=0))
        driver.stop_route()
        self.assertTrue(driver.wait_until_route_finished(timeout=0))
        driver.adb.shell.assert_called_once_with('am stopservice io.appium.settings/.LocationService')

    def test_one_route_per_device(self):
        first = _driver()
        first.start_route_with_points(ROUTE, 0)
        with self.assertRaises(RuntimeError):
            first.start_route_with_points(ROUTE, 0)
        # also not from another driver for the same device, e.g. of another app
        with self.assertRaises(RuntimeError):
            _driver().start_route_with_points(ROUTE, 0)
        # another device is not blocked
        _driver('other phone').start_route_with_points(ROUTE, 0)
        first.stop_route(reset_location=False)
        _driver().start_route_with_points(ROUTE, 0)

    def test_new_route_after_finished_route_stops_it(self):
        driver = _driver()
        driver.start_route_with_points(ROUTE, 0)
        finished = puma_driver._routes['phone']
        finished._next_locations = []  # reached the end, still at the last location
        driver.start_route_with_points(ROUTE, 0)
        self.assertIsNone(finished._current_location)
        self.assertIsNot(finished, puma_driver._routes['phone'])

    def test_queries_route_checks_running_route_before_planning(self):
        driver = _driver()
        driver.start_route_with_points(ROUTE, 0)
        with patch('puma.state_graph.puma_driver.plan_route') as plan_route:
            with self.assertRaises(RuntimeError):
                driver.start_route_with_queries('a', 'b', 'car', 50)
            plan_route.assert_not_called()

    def test_update_speed_needs_route(self):
        driver = _driver()
        with self.assertRaises(RuntimeError):
            driver.update_route_speed(50)
        driver.start_route_with_points(ROUTE, 0)
        driver.update_route_speed(50, variance_relative=0.1)
        route = puma_driver._routes['phone']
        self.assertAlmostEqual(45, route._target_speed_lower_bound)
        self.assertAlmostEqual(55, route._target_speed_upper_bound)

    def test_reset_location_per_platform(self):
        ios = _driver(driver_class=IOSPumaDriver)
        ios.reset_location()
        ios.driver.execute_script.assert_called_once_with('mobile: resetSimulatedLocation')
        android = _driver()
        android.reset_location()
        android.adb.shell.assert_called_once_with('am stopservice io.appium.settings/.LocationService')

    def test_google_maps_route_stands_still_while_navigation_starts(self):
        from puma.apps.android.google_maps.google_maps import GoogleMaps, TransportType
        maps = Mock()
        with patch('puma.apps.android.google_maps.google_maps.sleep'):
            GoogleMaps.start_route(maps, 'a', 'b', 50, TransportType.BIKE)
        self.assertEqual([call.driver.start_route_with_queries('a', 'b', 'bike', 0),
                          call.start_navigation('b', TransportType.BIKE),
                          call.driver.update_route_speed(50)], maps.mock_calls)

    def test_google_maps_route_stops_when_navigation_fails(self):
        from puma.apps.android.google_maps.google_maps import GoogleMaps
        maps = Mock()
        maps.start_navigation.side_effect = TimeoutError()
        with patch('puma.apps.android.google_maps.google_maps.sleep'), self.assertRaises(TimeoutError):
            GoogleMaps.start_route(maps, 'a', 'b', 50)
        maps.driver.stop_route.assert_called_once()

    def test_apple_maps_route_rejects_transit(self):
        from puma.apps.ios.apple_maps.apple_maps import AppleMaps, TransportType
        maps = Mock()
        with self.assertRaises(ValueError):
            AppleMaps.start_route(maps, 'a', 'b', 50, TransportType.TRANSIT)
        maps.driver.start_route_with_queries.assert_not_called()


if __name__ == '__main__':
    unittest.main()
