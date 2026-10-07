import logging
import os
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from selenium.common import WebDriverException

from puma.apps.android.google_play_store.google_play_store import GooglePlayStore
from puma.state_graph.ios_driver import VERSION_ATTRIBUTE, APPLICATION_TYPE_ATTRIBUTE
from puma.state_graph.puma_driver import PumaDriver, Platform, AppVersionUnavailable, supported_version
from puma.state_graph.state import SimpleState
from puma.state_graph.state_graph import StateGraph

IOS_VERSION = '26.6'


def _mock_appium_driver(device_info: dict = None):
    appium_driver = Mock()
    appium_driver.capabilities = {'udid': 'mock_udid'}
    if device_info is not None:
        appium_driver.execute_script.return_value = device_info
    return appium_driver


def _create_driver(platform: Platform, appium_driver=None, app_package: str = 'com.example.app') -> PumaDriver:
    with patch('puma.state_graph.puma_driver._get_appium_driver', return_value=appium_driver or _mock_appium_driver()), \
            patch('adb_pywrapper.adb_device.AdbDevice'):
        return PumaDriver('mock_udid', app_package, platform=platform)


def _adb_result(stdout: str = '', stderr: str = '', success: bool = True) -> Mock:
    return Mock(stdout=stdout, stderr=stderr, success=success)


class TestAndroidAppVersion(unittest.TestCase):
    def setUp(self):
        self.driver = _create_driver(Platform.ANDROID)

    def test_version(self):
        self.driver.adb.shell.return_value = _adb_result('Packages:\n  Package [com.example.app]\n    versionName=2.26.2.70\n')
        self.assertEqual('2.26.2.70', self.driver.get_app_version())
        self.driver.adb.shell.assert_called_with('dumpsys package com.example.app')

    def test_first_version_is_used_when_there_are_multiple(self):
        self.driver.adb.shell.return_value = _adb_result('    versionName=2.26.2.70\nHidden system packages:\n    versionName=1.0.0\n')
        self.assertEqual('2.26.2.70', self.driver.get_app_version())

    def test_version_name_is_not_cut_off(self):
        self.driver.adb.shell.return_value = _adb_result('    versionName=48.3.25-31 [0] [PR] 123456789\n')
        self.assertEqual('48.3.25-31 [0] [PR] 123456789', self.driver.get_app_version())

    def test_other_app(self):
        self.driver.adb.shell.return_value = _adb_result('    versionName=1.2.3\n')
        self.assertEqual('1.2.3', self.driver.get_app_version('com.other.app'))
        self.driver.adb.shell.assert_called_with('dumpsys package com.other.app')

    def test_not_installed(self):
        self.driver.adb.shell.return_value = _adb_result('')
        self.assertIsNone(self.driver.get_app_version())

    def test_adb_failure_is_not_the_same_as_not_installed(self):
        self.driver.adb.shell.return_value = _adb_result(stderr='/bin/sh: adb: command not found', success=False)
        with self.assertRaisesRegex(AppVersionUnavailable, 'adb: command not found'):
            self.driver.get_app_version()


class TestIOSRealDeviceAppVersion(unittest.TestCase):
    def setUp(self):
        self.apps = {}
        self.appium_driver = _mock_appium_driver()
        self.appium_driver.execute_script.side_effect = self._execute_script
        self.driver = _create_driver(Platform.IOS, self.appium_driver)

    def _execute_script(self, script, args=None):
        if script == 'mobile: deviceInfo':
            return {'isSimulator': False, 'lockdownInfo': {'ProductVersion': IOS_VERSION}}
        self.assertEqual('mobile: listApps', script)
        self.assertEqual({'applicationType': 'Any', 'returnAttributes': [VERSION_ATTRIBUTE, APPLICATION_TYPE_ATTRIBUTE]}, args)
        return self.apps

    def _scripts_called(self) -> list[str]:
        return [call.args[0] for call in self.appium_driver.execute_script.call_args_list]

    def test_user_app(self):
        self.apps = {'com.example.app': {VERSION_ATTRIBUTE: '1.2.3', APPLICATION_TYPE_ATTRIBUTE: 'User'}}
        self.assertEqual('1.2.3', self.driver.get_app_version())

    def test_app_bundled_with_ios_has_the_ios_version(self):
        # Built-in apps report a version of their own, which differs from the iOS version
        self.apps = {'com.apple.Preferences': {VERSION_ATTRIBUTE: '1', APPLICATION_TYPE_ATTRIBUTE: 'System'}}
        self.assertEqual(IOS_VERSION, self.driver.get_app_version('com.apple.Preferences'))

    def test_app_from_apple_with_its_own_version(self):
        self.apps = {'com.apple.TestFlight': {VERSION_ATTRIBUTE: '3.9.2', APPLICATION_TYPE_ATTRIBUTE: 'User'}}
        self.assertEqual('3.9.2', self.driver.get_app_version('com.apple.TestFlight'))

    def test_not_installed(self):
        self.assertIsNone(self.driver.get_app_version())

    def test_app_without_version(self):
        self.apps = {'com.example.app': {APPLICATION_TYPE_ATTRIBUTE: 'User'}}
        with self.assertRaises(AppVersionUnavailable):
            self.driver.get_app_version()

    def test_appium_failure_is_not_the_same_as_not_installed(self):
        self.appium_driver.execute_script.side_effect = WebDriverException('device is locked')
        with self.assertRaisesRegex(AppVersionUnavailable, 'device is locked'):
            self.driver.get_app_version()

    def test_device_info_and_apps_are_looked_up_once_per_call(self):
        self.apps = {'com.apple.Preferences': {VERSION_ATTRIBUTE: '1', APPLICATION_TYPE_ATTRIBUTE: 'System'}}
        self.driver.get_app_version('com.apple.Preferences')
        self.driver.get_app_version('com.apple.Preferences')
        self.assertEqual(['mobile: deviceInfo', 'mobile: listApps', 'mobile: listApps'], self._scripts_called())


class TestIOSSimulatorAppVersion(unittest.TestCase):
    RUNTIME_APPS = '/Library/Developer/CoreSimulator/Profiles/Runtimes/iOS 26.2.simruntime/Contents/Resources/RuntimeRoot/Applications'
    USER_APPS = '/Users/me/Library/Developer/CoreSimulator/Devices/mock_udid/data/Containers/Bundle/Application/ABC'

    def setUp(self):
        self.driver = _create_driver(Platform.IOS, _mock_appium_driver({'isSimulator': True}))
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        which = patch('shutil.which', return_value='/usr/bin/xcrun')
        which.start()
        self.addCleanup(which.stop)

    def _app_dir(self, parent: str, version: str) -> str:
        app_dir = os.path.join(self.tempdir.name, parent)
        os.makedirs(app_dir, exist_ok=True)
        with open(os.path.join(app_dir, 'Info.plist'), 'wb') as info_plist:
            plistlib.dump({VERSION_ATTRIBUTE: version}, info_plist)
        return app_dir

    @staticmethod
    def _simctl_result(stdout: str = '', stderr: str = '', returncode: int = 0) -> Mock:
        return Mock(stdout=stdout, stderr=stderr, returncode=returncode)

    def test_user_app(self):
        app_dir = self._app_dir(self.USER_APPS.lstrip('/'), '4.5.6')
        with patch('subprocess.run', return_value=self._simctl_result(app_dir + '\n')) as run:
            self.assertEqual('4.5.6', self.driver.get_app_version())
        run.assert_called_once()
        self.assertEqual(['xcrun', 'simctl', 'get_app_container', 'mock_udid', 'com.example.app', 'app'],
                         run.call_args.args[0])

    def test_app_bundled_with_ios_has_the_ios_version(self):
        app_dir = self._app_dir(self.RUNTIME_APPS.lstrip('/') + '/Preferences.app', '1')
        with patch('subprocess.run', side_effect=[self._simctl_result(app_dir + '\n'),
                                                  self._simctl_result('26.2\n')]) as run:
            self.assertEqual('26.2', self.driver.get_app_version('com.apple.Preferences'))
        self.assertEqual(['xcrun', 'simctl', 'getenv', 'mock_udid', 'SIMULATOR_RUNTIME_VERSION'],
                         run.call_args.args[0])

    def test_not_installed(self):
        error = 'An error was encountered processing the command (domain=NSPOSIXErrorDomain, code=2)'
        with patch('subprocess.run', return_value=self._simctl_result(stderr=error, returncode=2)):
            self.assertIsNone(self.driver.get_app_version())

    def test_simctl_failure_is_not_the_same_as_not_installed(self):
        with patch('subprocess.run', return_value=self._simctl_result(stderr='Unable to lookup in current state: Shutdown', returncode=405)):
            with self.assertRaisesRegex(AppVersionUnavailable, 'Shutdown'):
                self.driver.get_app_version()

    def test_simctl_timeout(self):
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('simctl', 30)):
            with self.assertRaises(AppVersionUnavailable):
                self.driver.get_app_version()

    def test_without_xcrun(self):
        with patch('shutil.which', return_value=None), patch('subprocess.run') as run:
            with self.assertRaisesRegex(AppVersionUnavailable, 'same Mac'):
                self.driver.get_app_version()
        run.assert_not_called()


@supported_version('2.0')
class VersionedApp(StateGraph):
    platform = Platform.ANDROID
    main_state = SimpleState(['xpath'], initial_state=True)


class UnversionedApp(StateGraph):
    platform = Platform.ANDROID
    main_state = SimpleState(['xpath'], initial_state=True)


class TestCheckSupportedVersion(unittest.TestCase):
    def _create_app(self, app_class=VersionedApp, installed_version=None, error: Exception = None, **kwargs):
        with patch('puma.state_graph.puma_driver._get_appium_driver', return_value=_mock_appium_driver()), \
                patch('adb_pywrapper.adb_device.AdbDevice'), \
                patch('puma.state_graph.android_driver.AndroidPumaDriver.get_app_version',
                      return_value=installed_version, side_effect=error) as get_app_version:
            # The driver logs while connecting, so there are always log records. Only those of the check are returned
            with self.assertLogs('puma.state_graph', level=logging.INFO) as logs:
                app_class('mock_udid', 'com.example.app', **kwargs)
        self.get_app_version = get_app_version
        return [record for record in logs.records if record.filename == 'state_graph.py']

    def test_supported_version_does_not_warn(self):
        self.assertEqual([], self._create_app(installed_version='2.0'))

    def test_different_version_warns(self):
        records = self._create_app(installed_version='3.1')
        self.assertEqual([logging.WARNING], [record.levelno for record in records])
        self.assertIn('3.1', records[0].getMessage())
        self.assertIn('2.0', records[0].getMessage())

    def test_not_installed_warns(self):
        records = self._create_app(installed_version=None)
        self.assertEqual([logging.WARNING], [record.levelno for record in records])
        self.assertIn('not installed', records[0].getMessage())

    def test_unavailable_version_does_not_warn(self):
        records = self._create_app(error=AppVersionUnavailable('xcrun is not available'))
        self.assertEqual([logging.INFO], [record.levelno for record in records])
        self.assertIn('xcrun is not available', records[0].getMessage())

    def test_unexpected_error_warns_and_does_not_raise(self):
        records = self._create_app(error=RuntimeError('boom'))
        self.assertEqual([logging.WARNING], [record.levelno for record in records])
        self.assertIn('boom', records[0].getMessage())

    def test_app_without_supported_version_is_not_checked(self):
        self.assertEqual([], self._create_app(UnversionedApp, installed_version='3.1'))
        self.get_app_version.assert_not_called()

    def test_check_can_be_turned_off(self):
        self.assertEqual([], self._create_app(installed_version='3.1', check_version=False))
        self.get_app_version.assert_not_called()

    def test_check_can_be_turned_off_for_an_app_class(self):
        class UncheckedApp(VersionedApp):
            main_state = SimpleState(['xpath'], initial_state=True)
            check_version = False

        self.assertEqual([], self._create_app(UncheckedApp, installed_version='3.1'))
        self.get_app_version.assert_not_called()
        self.assertEqual([], self._create_app(UncheckedApp, installed_version='3.1', check_version=False))

    def test_app_can_override_how_versions_are_compared(self):
        class PrefixApp(VersionedApp):
            main_state = SimpleState(['xpath'], initial_state=True)

            def is_supported_version(self, installed_version, supported_version):
                return installed_version.startswith(supported_version)

        self.assertEqual([], self._create_app(PrefixApp, installed_version='2.0.1'))
        self.assertEqual(1, len(self._create_app(VersionedApp, installed_version='2.0.1')))

    def test_google_play_store_ignores_version_name_suffix(self):
        play_store = object.__new__(GooglePlayStore)
        self.assertTrue(play_store.is_supported_version('48.3.25-31 [0] [PR] 123456789', '48.3.25-31'))
        self.assertFalse(play_store.is_supported_version('48.4.1-31 [0] [PR] 123456789', '48.3.25-31'))


if __name__ == '__main__':
    unittest.main()
