import os
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from puma.state_graph.puma_driver import PumaDriver, Platform


def _mock_appium_driver(**capabilities):
    appium_driver = Mock()
    appium_driver.capabilities = {'udid': 'mock_udid', **capabilities}
    return appium_driver


def _create_driver(platform: Platform, app_package: str = 'com.example.app', **capabilities) -> PumaDriver:
    appium_driver = _mock_appium_driver(**capabilities)
    with patch('puma.state_graph.puma_driver._get_appium_driver', return_value=appium_driver), \
            patch('adb_pywrapper.adb_device.AdbDevice'):
        driver = PumaDriver('mock_udid', app_package, platform=platform)
    return driver


class TestAndroidAppVersion(unittest.TestCase):
    def setUp(self):
        self.driver = _create_driver(Platform.ANDROID)

    def test_version(self):
        self.driver.adb.package_versions.return_value = ['2.26.2.70']
        self.assertEqual('2.26.2.70', self.driver.get_app_version())
        self.driver.adb.package_versions.assert_called_with('com.example.app')

    def test_first_version_is_used_when_there_are_multiple(self):
        self.driver.adb.package_versions.return_value = ['2.26.2.70', '1.0.0']
        self.assertEqual('2.26.2.70', self.driver.get_app_version())

    def test_other_app(self):
        self.driver.adb.package_versions.return_value = ['1.2.3']
        self.assertEqual('1.2.3', self.driver.get_app_version('com.other.app'))
        self.driver.adb.package_versions.assert_called_with('com.other.app')

    def test_not_installed(self):
        self.driver.adb.package_versions.side_effect = Exception('not installed')
        self.assertIsNone(self.driver.get_app_version())
        self.driver.adb.package_versions.side_effect = None
        self.driver.adb.package_versions.return_value = []
        self.assertIsNone(self.driver.get_app_version())


class TestIOSAppVersion(unittest.TestCase):
    def _real_device_driver(self, **capabilities):
        driver = _create_driver(Platform.IOS, **capabilities)
        self.apps = {}

        def execute_script(script, args=None):
            if script == 'mobile: deviceInfo':
                return {'isSimulator': False}
            self.assertEqual('mobile: listApps', script)
            self.assertEqual(['CFBundleShortVersionString'], args['returnAttributes'])
            return self.apps.get(args['applicationType'], {})

        driver.driver.execute_script.side_effect = execute_script
        return driver

    def test_real_device_user_app(self):
        driver = self._real_device_driver()
        self.apps = {'User': {'com.example.app': {'CFBundleShortVersionString': '1.2.3'}}}
        self.assertEqual('1.2.3', driver.get_app_version())

    def test_real_device_falls_back_to_system_apps(self):
        driver = self._real_device_driver()
        self.apps = {'System': {'com.apple.Preferences': {'CFBundleShortVersionString': '26.6'}}}
        self.assertEqual('26.6', driver.get_app_version('com.apple.Preferences'))

    def test_real_device_not_installed(self):
        driver = self._real_device_driver()
        self.assertIsNone(driver.get_app_version())

    def test_simulator(self):
        driver = _create_driver(Platform.IOS)
        driver.driver.execute_script.return_value = {'isSimulator': True}
        with tempfile.TemporaryDirectory() as app_path:
            with open(os.path.join(app_path, 'Info.plist'), 'wb') as info_plist:
                plistlib.dump({'CFBundleShortVersionString': '4.5.6'}, info_plist)
            with patch('subprocess.run', return_value=Mock(stdout=app_path + '\n')) as run:
                self.assertEqual('4.5.6', driver.get_app_version())
        run.assert_called_with(['xcrun', 'simctl', 'get_app_container', 'mock_udid', 'com.example.app', 'app'],
                               capture_output=True, text=True, check=True, timeout=30)

    def test_simulator_not_installed(self):
        driver = _create_driver(Platform.IOS)
        driver.driver.execute_script.return_value = {'isSimulator': True}
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'xcrun')):
            self.assertIsNone(driver.get_app_version())


class TestCheckSupportedVersion(unittest.TestCase):
    def setUp(self):
        self.driver = _create_driver(Platform.ANDROID)

    def _check(self, supported: str = '2.26.2.70'):
        with self.assertLogs('puma.state_graph', level='WARNING') as logs:
            self.driver.check_supported_version(supported)
            # assertLogs needs at least one record, so log a marker the test can ignore
            from puma.state_graph import logger
            logger.warning('marker')
        return [record.getMessage() for record in logs.records if record.getMessage() != 'marker']

    def test_matching_version_does_not_warn(self):
        self.driver.adb.package_versions.return_value = ['2.26.2.70']
        self.assertEqual([], self._check())

    def test_different_version_warns(self):
        self.driver.adb.package_versions.return_value = ['2.26.3.1']
        messages = self._check()
        self.assertEqual(1, len(messages))
        self.assertIn('2.26.3.1', messages[0])
        self.assertIn('2.26.2.70', messages[0])

    def test_unknown_version_warns(self):
        self.driver.adb.package_versions.side_effect = Exception('not installed')
        self.assertEqual(1, len(self._check()))

    def test_failure_does_not_raise(self):
        with patch.object(self.driver, 'get_app_version', side_effect=RuntimeError('boom')):
            self.assertEqual(1, len(self._check()))

    def test_apple_app_is_compared_to_ios_version(self):
        driver = _create_driver(Platform.IOS, 'com.apple.Preferences', platformVersion='26.6')
        with patch.object(driver, 'get_app_version') as get_app_version, \
                self.assertNoLogs('puma.state_graph', level='WARNING'):
            driver.check_supported_version('26.6')
        get_app_version.assert_not_called()


if __name__ == '__main__':
    unittest.main()
