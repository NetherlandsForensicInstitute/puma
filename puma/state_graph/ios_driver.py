import base64
import os
import plistlib
import subprocess
import zlib
from datetime import datetime
from typing import Dict

from appium.options.ios import XCUITestOptions
from appium.webdriver.applicationstate import ApplicationState
from selenium.common import WebDriverException

from puma.state_graph.locators import ios_class_chain, to_by_value
from puma.state_graph.puma_driver import PumaDriver, Platform

# The back button in a UINavigationBar. Depending on the iOS version it is named 'BackButton' or 'Back'
NAVIGATION_BAR_BACK_BUTTON = ios_class_chain(
    '**/XCUIElementTypeNavigationBar/XCUIElementTypeButton[`name == "BackButton" OR name == "Back"`]')


# Keys of a hardware keyboard, as HID usages on the keyboard page. See the Keyboard/Keypad Page in the HID Usage Tables,
# https://usb.org/document-library/hid-usage-tables-15
HID_PAGE_KEYBOARD = 0x07
HID_KEY_RETURN = 0x28
HID_KEY_DELETE = 0x2A
HID_KEY_LEFT_ARROW = 0x50
# The duration of a single key press, as used by XCTest
HID_KEY_PRESS_DURATION = 0.005
# The Info.plist key holding the version of an app, as shown to users
VERSION_ATTRIBUTE = 'CFBundleShortVersionString'

def wda_ports(udid: str) -> tuple[int, int]:
    """
    Returns the local ports used to connect to WebDriverAgent on a device: one for the WebDriverAgent server, one for the
    screen streaming (MJPEG) server.

    By default, Appium uses the same ports (8100 and 9100) for every device. When multiple devices are used on the same
    Appium server, Appium can then reuse the connection to one device for another device, sending commands to the wrong
    device. Therefore, each device gets its own ports, derived from its udid, so the ports are the same every time the
    same device is used.

    :param udid: The unique device identifier of the device.
    :return: The WebDriverAgent port (8200-8999) and the MJPEG server port (9200-9999).
    """
    offset = zlib.crc32(udid.encode()) % 800
    return 8200 + offset, 9200 + offset


def get_ios_default_options() -> XCUITestOptions:
    """
    Creates and configures default options for an iOS XCUITest driver.

    No bundle id is set, as a single Appium session per device is shared between all apps (see _get_appium_driver).
    Apps are started with activate_app instead.

    :return: Configured XCUITestOptions instance.
    """
    options = XCUITestOptions()
    options.no_reset = True
    options.platform_name = Platform.IOS.value
    options.new_command_timeout = 1200
    # The first time WebDriverAgent needs to be built and installed on a device, which can take a few minutes
    options.wda_launch_timeout = 300_000
    return options


class IOSPumaDriver(PumaDriver):
    """
    A driver class for interacting with iOS applications using Appium and XCUITest.

    iOS differs from Android in a few ways that are relevant to Puma:
    - There is no back button. back() uses the back button in the navigation bar when present, and otherwise swipes
      from the left edge of the screen. States that cannot be left this way (e.g. modal sheets) should define a
      `parent_state_transition`.
    - System pop-ups (such as permission requests) are shown as alerts, which are handled through the Appium alert API
      (see puma.state_graph.popup_handler.IOSAlertHandler).
    - XPath lookups are relatively slow. Consider using Locators (puma.state_graph.locators) such as ios_predicate or
      ios_class_chain for elements that are looked up often.
    """
    platform = Platform.IOS

    def __init__(self, udid: str, app_package: str, implicit_wait: int = 1, appium_server: str = 'http://localhost:4723', desired_capabilities: Dict[str, str] = None, platform: Platform = None):
        """
        Initializes the IOSPumaDriver with device and application details.

        :param udid: The unique device identifier of the iOS device or simulator.
        :param app_package: The bundle id of the application to interact with.
        :param implicit_wait: The implicit wait time for element searches, defaults to 1 second.
        :param appium_server: The address of the Appium server, defaults to 'http://localhost:4723'.
        :param desired_capabilities: The desired capabilities as passed to the Appium webdriver. For real devices, this
        typically contains the signing settings for WebDriverAgent (xcodeOrgId and xcodeSigningId). Each device gets its
        own WebDriverAgent ports (see wda_ports), which can be overridden with wdaLocalPort and mjpegServerPort.
        """
        super().__init__(udid, app_package, implicit_wait=implicit_wait, appium_server=appium_server, desired_capabilities=desired_capabilities)
        self._back_buttons = []

    def _set_device_options(self, udid: str):
        self.options.wda_local_port, self.options.mjpeg_server_port = wda_ports(udid)

    @property
    def bundle_id(self) -> str:
        return self.app_package

    def is_simulator(self) -> bool:
        """
        :return: True if the device is a simulator, False if it is a real device.
        """
        return bool(self.execute_script('mobile: deviceInfo').get('isSimulator'))

    @staticmethod
    def _default_options() -> XCUITestOptions:
        return get_ios_default_options()

    def get_app_version(self, app_id: str = None) -> str | None:
        """
        Returns the version (CFBundleShortVersionString) of an installed app.

        On real devices this uses Appium. Appium cannot list apps on simulators, so there the Info.plist of the app is
        read using `xcrun simctl`, which only works if Puma runs on the same machine as the simulator.

        :param app_id: The bundle id of the app. Defaults to the app of this driver.
        :return: The version, or None if the app is not installed or its version cannot be determined.
        """
        bundle_id = app_id or self.app_package
        if self.is_simulator():
            return self._simulator_app_version(bundle_id)
        for application_type in ('User', 'System'):
            apps = self.execute_script('mobile: listApps', {
                'applicationType': application_type, 'returnAttributes': [VERSION_ATTRIBUTE]})
            version = (apps or {}).get(bundle_id, {}).get(VERSION_ATTRIBUTE)
            if version:
                return version
        return None

    def _simulator_app_version(self, bundle_id: str) -> str | None:
        try:
            app_path = subprocess.run(['xcrun', 'simctl', 'get_app_container', self.udid, bundle_id, 'app'],
                                      capture_output=True, text=True, check=True, timeout=30).stdout.strip()
            with open(os.path.join(app_path, 'Info.plist'), 'rb') as info_plist:
                return plistlib.load(info_plist).get(VERSION_ATTRIBUTE)
        except (OSError, subprocess.SubprocessError, plistlib.InvalidFileException):
            return None

    def _version_for_supported_check(self) -> str | None:
        # Apple's own apps are versioned with iOS, so the supported version of those is an iOS version
        if self.app_package.startswith('com.apple.'):
            return self.driver.capabilities.get('platformVersion')
        return self.get_app_version()

    def app_open(self) -> bool:
        return self.driver.query_app_state(self.app_package) == ApplicationState.RUNNING_IN_FOREGROUND

    def add_back_button(self, back_button: str):
        """
        Registers the back button of an application, for applications that do not use the standard back button of iOS.
        back() uses the registered back buttons before the standard one.

        :param back_button: The XPath (or Locator) of the back button.
        """
        self._back_buttons.append(back_button)

    def back(self):
        """
        Navigates back. iOS has no back button, so this clicks the back button in the navigation bar if present, and
        otherwise performs a swipe from the left edge of the screen, which is the standard back gesture on iOS.
        Back buttons registered by the application (see add_back_button) are tried before the standard back button.
        """
        for back_button in self._back_buttons + [NAVIGATION_BAR_BACK_BUTTON]:
            if self.is_present(back_button):
                self.gtl_logger.info('Pressing back button in navigation bar')
                self.driver.find_element(*to_by_value(back_button)).click()
                return
        self.gtl_logger.info('Swiping from left edge to go back')
        window_size = self.driver.get_window_size()
        y = window_size['height'] / 2
        self.driver.execute_script('mobile: dragFromToForDuration', {
            'fromX': 1, 'fromY': y, 'toX': window_size['width'] * 0.8, 'toY': y, 'duration': 0.3})

    def home(self):
        """
        Simulates pressing the home button on the device.
        """
        self.gtl_logger.info(f'Pressing home button')
        self.driver.execute_script('mobile: pressButton', {'name': 'home'})

    def _press_key(self, usage: int):
        """
        Presses a key of a hardware keyboard, as if a keyboard is connected to the device (e.g. over bluetooth). Unlike
        typing text, this triggers the action of the key, e.g. the return key submits a search field.

        :param usage: The HID usage of the key, see the HID_KEY constants.
        """
        self.driver.execute_script('mobile: performIoHidEvent', {
            'page': HID_PAGE_KEYBOARD, 'usage': usage, 'durationSeconds': HID_KEY_PRESS_DURATION})

    def press_enter(self):
        """
        Presses the return key of a hardware keyboard.
        """
        self._press_key(HID_KEY_RETURN)

    def press_backspace(self):
        """
        Presses the delete key of a hardware keyboard.
        """
        self._press_key(HID_KEY_DELETE)

    def press_left_arrow(self):
        """
        Presses the left arrow key of a hardware keyboard.
        """
        self._press_key(HID_KEY_LEFT_ARROW)

    def open_url(self, url: str):
        """
        Opens a given URL. The URl will open in the default app configured for that URL.
        """
        self.gtl_logger.info(f'Opening url {url}')
        self.driver.execute_script('mobile: deepLink', {'url': url})

    def open_notifications(self):
        """
        Opens the iOS notification center by swiping down from the top left of the screen.
        """
        self.gtl_logger.info('Opening notification center')
        window_size = self.driver.get_window_size()
        x = window_size['width'] * 0.25
        self.driver.execute_script('mobile: dragFromToForDuration', {
            'fromX': x, 'fromY': 1, 'toX': x, 'toY': window_size['height'] * 0.6, 'duration': 0.3})

    def alert_buttons(self) -> list[str]:
        """
        Returns the labels of the buttons of the alert currently shown, including system alerts such as permission
        requests.

        :return: The button labels, or an empty list if no alert is shown.
        """
        try:
            return self.driver.execute_script('mobile: alert', {'action': 'getButtons'}) or []
        except WebDriverException:
            return []

    def click_alert_button(self, button_label: str):
        """
        Clicks a button in the alert currently shown.

        :param button_label: The label of the button to click.
        """
        self.gtl_logger.info(f'Clicking alert button "{button_label}"')
        self.driver.execute_script('mobile: alert', {'action': 'accept', 'buttonLabel': button_label})

    def start_recording(self, output_directory: str):
        """
        Starts a screen recording. On real devices, this requires ffmpeg to be installed on the machine running Appium.

        :param output_directory: The directory the screen recording should be stored in.
        """
        if not self._is_recording():
            self._screen_recorder_output_directory = output_directory
            self.gtl_logger.info('Starting screen recording')
            self.driver.start_recording_screen(forceRestart=True, timeLimit=1800)

    def stop_recording_and_save_video(self) -> list[str] | None:
        if not self._is_recording():
            return None
        self.gtl_logger.info('Ending screen recording')
        video = self.driver.stop_recording_screen()
        os.makedirs(self._screen_recorder_output_directory, exist_ok=True)
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(self._screen_recorder_output_directory, f'{now}-{self.udid}.mp4')
        with open(path, 'wb') as video_file:
            video_file.write(base64.b64decode(video))
        self._screen_recorder_output_directory = None
        return [path]

    def _click_coordinates(self, x: int, y: int):
        self.driver.execute_script('mobile: tap', {'x': x, 'y': y})

