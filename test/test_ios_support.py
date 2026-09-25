import base64
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from geopy import Point
from selenium.common import WebDriverException

from puma.state_graph.locators import Locator, accessibility_id, ios_predicate, ios_class_chain, to_by_value
from puma.state_graph.popup_handler import IOSAlertHandler, known_popups_for, known_popups, known_ios_popups
from puma.state_graph.puma_driver import PumaDriver, Platform
from puma.state_graph.state import SimpleState
from puma.state_graph.state_graph import StateGraph
from puma.state_graph.utils import is_valid_bundle_id, is_valid_app_id
from puma.utils.route_simulator import RouteSimulator


def _mock_appium_driver():
    appium_driver = Mock()
    appium_driver.capabilities = {'udid': 'mock_udid'}
    appium_driver.get_window_size.return_value = {'width': 400, 'height': 800}
    return appium_driver


def _create_driver(platform: Platform, appium_driver=None) -> PumaDriver:
    appium_driver = appium_driver or _mock_appium_driver()
    with patch('puma.state_graph.puma_driver._get_appium_driver', return_value=appium_driver), \
            patch('adb_pywrapper.adb_device.AdbDevice'):
        return PumaDriver('mock_udid', 'com.example.app', platform=platform)


class TestLocators(unittest.TestCase):
    def test_plain_string_is_xpath(self):
        self.assertEqual((AppiumBy.XPATH, '//button'), to_by_value('//button'))

    def test_locators(self):
        self.assertEqual((AppiumBy.ACCESSIBILITY_ID, 'Done'), to_by_value(accessibility_id('Done')))
        self.assertEqual((AppiumBy.IOS_PREDICATE, 'name == "Done"'), to_by_value(ios_predicate('name == "Done"')))
        self.assertEqual((AppiumBy.IOS_CLASS_CHAIN, '**/XCUIElementTypeCell'),
                         to_by_value(ios_class_chain('**/XCUIElementTypeCell')))

    def test_locator_is_a_string(self):
        # locators must be usable everywhere an XPath string is accepted
        locator = accessibility_id('Done')
        self.assertIsInstance(locator, str)
        self.assertIsInstance(locator, Locator)
        self.assertEqual('Done', locator)
        self.assertIn('Done', f'{locator}')


class TestAppIdValidation(unittest.TestCase):
    def test_bundle_ids(self):
        self.assertTrue(is_valid_bundle_id('com.apple.mobilesafari'))
        self.assertTrue(is_valid_bundle_id('com.apple.MobileAddressBook'))
        self.assertTrue(is_valid_bundle_id('net.whatsapp.WhatsApp'))
        self.assertTrue(is_valid_bundle_id('com.my-company.my-app'))
        self.assertFalse(is_valid_bundle_id('nodots'))
        self.assertFalse(is_valid_bundle_id('this is invalid'))
        self.assertFalse(is_valid_bundle_id(''))
        self.assertFalse(is_valid_bundle_id('com..app'))

    def test_app_id_per_platform(self):
        # hyphens are allowed in iOS bundle ids, but not in Android package names
        self.assertTrue(is_valid_app_id('com.my-company.app', Platform.IOS))
        self.assertFalse(is_valid_app_id('com.my-company.app', Platform.ANDROID))
        self.assertTrue(is_valid_app_id('com.android.chrome', Platform.ANDROID))


class IOSTestApp(StateGraph):
    platform = Platform.IOS
    main_state = SimpleState(['xpath'], initial_state=True)


class TestStateGraphPlatform(unittest.TestCase):
    def test_default_platform_is_android(self):
        self.assertEqual(Platform.ANDROID, StateGraph.platform)

    def test_invalid_bundle_id(self):
        with self.assertRaises(ValueError) as error:
            IOSTestApp(device_udid='mock_udid', app_package='this is invalid')
        self.assertEqual('The provided bundle id is invalid: this is invalid', str(error.exception))

    def test_ios_app_gets_ios_driver(self):
        with patch('puma.state_graph.puma_driver._get_appium_driver', return_value=_mock_appium_driver()):
            app = IOSTestApp(device_udid='mock_udid', app_package='com.my-company.app')
        self.assertEqual(Platform.IOS, app.driver.platform)
        self.assertEqual('com.my-company.app', app.driver.bundle_id)


class TestPumaDriverPlatforms(unittest.TestCase):
    def test_default_driver_is_android(self):
        driver = _create_driver(Platform.ANDROID)
        self.assertEqual('AndroidPumaDriver', type(driver).__name__)
        self.assertEqual(Platform.ANDROID, driver.platform)
        self.assertEqual('UIAutomator2', driver.options.automation_name)

    def test_ios_driver(self):
        driver = _create_driver(Platform.IOS)
        self.assertEqual('IOSPumaDriver', type(driver).__name__)
        self.assertEqual(Platform.IOS, driver.platform)
        self.assertEqual('XCUITest', driver.options.automation_name)
        self.assertEqual('iOS', driver.options.platform_name)
        self.assertEqual('com.example.app', driver.app_id)

    def test_is_present_uses_locator_strategy(self):
        appium_driver = _mock_appium_driver()
        appium_driver.find_elements.return_value = [Mock()]
        driver = _create_driver(Platform.IOS, appium_driver)
        self.assertTrue(driver.is_present(accessibility_id('Done')))
        appium_driver.find_elements.assert_called_with(by=AppiumBy.ACCESSIBILITY_ID, value='Done')
        driver.is_present('//button')
        appium_driver.find_elements.assert_called_with(by=AppiumBy.XPATH, value='//button')


class TestWdaPorts(unittest.TestCase):
    SIMULATOR = 'A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D'
    DEVICE = '00008130-001A2B3C4D5E6F70'

    def test_ports_are_stable_and_in_range(self):
        from puma.state_graph.ios_driver import wda_ports
        wda_port, mjpeg_port = wda_ports(self.DEVICE)
        self.assertEqual((wda_port, mjpeg_port), wda_ports(self.DEVICE))
        self.assertTrue(8200 <= wda_port < 9000)
        self.assertEqual(wda_port + 1000, mjpeg_port)

    def test_devices_get_different_ports(self):
        # a simulator and a real device on the same Appium server must never share a WebDriverAgent connection
        from puma.state_graph.ios_driver import wda_ports
        self.assertNotEqual(wda_ports(self.SIMULATOR), wda_ports(self.DEVICE))
        self.assertNotIn(8100, wda_ports(self.SIMULATOR) + wda_ports(self.DEVICE))

    def test_driver_uses_device_ports(self):
        from puma.state_graph.ios_driver import wda_ports
        driver = _create_driver(Platform.IOS)
        self.assertEqual(wda_ports('mock_udid'), (driver.options.wda_local_port, driver.options.mjpeg_server_port))

    def test_capabilities_override_ports(self):
        with patch('puma.state_graph.puma_driver._get_appium_driver', return_value=_mock_appium_driver()):
            driver = PumaDriver('mock_udid', 'com.example.app', platform=Platform.IOS,
                                desired_capabilities={'appium:wdaLocalPort': 8100})
        self.assertEqual(8100, driver.options.wda_local_port)


class TestIOSPumaDriver(unittest.TestCase):
    def setUp(self):
        self.appium_driver = _mock_appium_driver()
        self.driver = _create_driver(Platform.IOS, self.appium_driver)

    def test_app_open(self):
        self.appium_driver.query_app_state.return_value = 4
        self.assertTrue(self.driver.app_open())
        self.appium_driver.query_app_state.return_value = 3  # running in background
        self.assertFalse(self.driver.app_open())
        self.appium_driver.query_app_state.assert_called_with('com.example.app')

    def test_back_uses_navigation_bar_back_button(self):
        back_button = Mock()
        self.appium_driver.find_elements.return_value = [back_button]
        self.appium_driver.find_element.return_value = back_button
        self.driver.back()
        back_button.click.assert_called_once()
        self.appium_driver.execute_script.assert_not_called()

    def test_back_swipes_from_left_edge_without_back_button(self):
        self.appium_driver.find_elements.return_value = []
        self.driver.back()
        script, arguments = self.appium_driver.execute_script.call_args[0]
        self.assertEqual('mobile: dragFromToForDuration', script)
        self.assertLessEqual(arguments['fromX'], 5)
        self.assertGreater(arguments['toX'], arguments['fromX'])
        self.assertEqual(arguments['fromY'], arguments['toY'])

    def test_is_simulator(self):
        self.appium_driver.execute_script.return_value = {'isSimulator': True, 'name': 'iPhone 17 Pro'}
        self.assertTrue(self.driver.is_simulator())
        self.appium_driver.execute_script.assert_called_with('mobile: deviceInfo')
        self.appium_driver.execute_script.return_value = {'isSimulator': False}
        self.assertFalse(self.driver.is_simulator())

    def test_home(self):
        self.driver.home()
        self.appium_driver.execute_script.assert_called_with('mobile: pressButton', {'name': 'home'})

    def test_keys(self):
        self.driver.press_enter()
        self.appium_driver.switch_to.active_element.send_keys.assert_called_with('\n')
        self.driver.press_backspace()
        self.appium_driver.switch_to.active_element.send_keys.assert_called_with('\b')
        with self.assertRaises(NotImplementedError):
            self.driver.press_left_arrow()

    def test_open_url(self):
        self.driver.open_url('https://example.com')
        self.appium_driver.execute_script.assert_called_with('mobile: deepLink', {'url': 'https://example.com'})

    def test_alert_buttons(self):
        self.appium_driver.execute_script.return_value = ['Allow', 'Don’t Allow']
        self.assertEqual(['Allow', 'Don’t Allow'], self.driver.alert_buttons())
        self.appium_driver.execute_script.side_effect = WebDriverException('no alert open')
        self.assertEqual([], self.driver.alert_buttons())

    def test_click_text_ocr_converts_pixels_to_points(self):
        found_text = Mock()
        found_text.bounding_box.middle = (300, 600)
        with patch.object(self.driver, '_find_text_ocr', return_value=([found_text], 3.0)):
            self.driver.click_text_ocr('text')
        self.appium_driver.execute_script.assert_called_with('mobile: tap', {'x': 100, 'y': 200})

    def test_recording(self):
        self.appium_driver.stop_recording_screen.return_value = base64.b64encode(b'video').decode()
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(self.driver.stop_recording_and_save_video())
            self.driver.start_recording(directory)
            self.driver.start_recording(directory)  # already recording, should not restart
            self.appium_driver.start_recording_screen.assert_called_once()
            videos = self.driver.stop_recording_and_save_video()
            self.assertEqual(1, len(videos))
            with open(videos[0], 'rb') as video:
                self.assertEqual(b'video', video.read())
            self.assertEqual(directory, os.path.dirname(videos[0]))
            self.assertIsNone(self.driver.stop_recording_and_save_video())


class TestIOSPopups(unittest.TestCase):
    def _driver(self, buttons, platform=Platform.IOS):
        driver = Mock()
        driver.platform = platform
        driver.alert_buttons.return_value = buttons
        return driver

    def test_known_popups_per_platform(self):
        self.assertIs(known_popups, known_popups_for(Platform.ANDROID))
        self.assertIs(known_ios_popups, known_popups_for(Platform.IOS))

    def test_permission_alert_is_accepted(self):
        permission_handler = known_ios_popups[0]
        driver = self._driver(['Allow Once', 'Allow While Using App', 'Don’t Allow'])
        self.assertTrue(permission_handler.is_popup_window(driver))
        permission_handler.dismiss_popup(driver)
        driver.click_alert_button.assert_called_once_with('Allow While Using App')

    def test_tracking_alert_is_accepted(self):
        permission_handler = known_ios_popups[0]
        driver = self._driver(['Ask App Not to Track', 'Allow'])
        self.assertTrue(permission_handler.is_popup_window(driver))
        permission_handler.dismiss_popup(driver)
        driver.click_alert_button.assert_called_once_with('Allow')

    def test_other_alerts_are_ignored(self):
        permission_handler = known_ios_popups[0]
        self.assertFalse(permission_handler.is_popup_window(self._driver(['OK'])))
        self.assertFalse(permission_handler.is_popup_window(self._driver([])))

    def test_ios_alert_handler_ignored_on_android(self):
        handler = IOSAlertHandler(['OK'], ['OK'])
        driver = self._driver(['OK'], platform=Platform.ANDROID)
        self.assertFalse(handler.is_popup_window(driver))
        driver.alert_buttons.assert_not_called()


class TestRouteSimulator(unittest.TestCase):
    def test_unwraps_puma_objects(self):
        appium_driver = Mock(spec=WebDriver)
        puma_driver = Mock()
        puma_driver.driver = appium_driver
        app = Mock()
        app.driver = puma_driver
        self.assertIs(appium_driver, RouteSimulator(appium_driver, 0).driver)
        self.assertIs(appium_driver, RouteSimulator(puma_driver, 0).driver)
        self.assertIs(appium_driver, RouteSimulator(app, 0).driver)

    @patch('puma.utils.route_simulator.requests.get')
    def test_osm_route_uses_transport_mode(self, get):
        get.return_value.json.return_value = {'routes': [{'geometry': {'coordinates': [[2.3, 48.8], [2.4, 48.9]]}}]}
        points = RouteSimulator._get_osm_route(48.8, 2.3, 48.9, 2.4, 'bike')
        self.assertIn('/routed-bike/', get.call_args[0][0])
        self.assertIn('2.3,48.8;2.4,48.9', get.call_args[0][0])
        self.assertEqual([(48.8, 2.3), (48.9, 2.4)], [(p.latitude, p.longitude) for p in points])

    def test_unsupported_transport_mode(self):
        with self.assertRaises(ValueError):
            RouteSimulator(Mock(spec=WebDriver), 0).execute_route_with_queries('a', 'b', 'boat')

    def test_route_finished(self):
        simulator = RouteSimulator(Mock(spec=WebDriver), 0)
        self.assertTrue(simulator.is_route_finished())
        simulator._next_locations = [Point(48.8, 2.3)]
        self.assertFalse(simulator.is_route_finished())
        self.assertFalse(simulator.wait_until_route_finished(timeout=0))
        simulator.stop_route()
        self.assertTrue(simulator.wait_until_route_finished(timeout=0))

    def test_apple_maps_route_rejects_transit(self):
        from puma.apps.ios.apple_maps.apple_maps import AppleMaps, TransportType
        maps = Mock()
        with self.assertRaises(ValueError):
            AppleMaps.start_route(maps, 'a', 'b', 50, TransportType.TRANSIT)
        maps.route_simulator.execute_route_with_queries.assert_not_called()


if __name__ == '__main__':
    unittest.main()
