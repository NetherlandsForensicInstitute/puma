import base64
import os
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
    options.platform_name = 'iOS'
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
      parent_state_transition.
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

    def _set_device_options(self, udid: str):
        self.options.wda_local_port, self.options.mjpeg_server_port = wda_ports(udid)

    @property
    def bundle_id(self) -> str:
        return self.app_package

    @staticmethod
    def _default_options() -> XCUITestOptions:
        return get_ios_default_options()

    def app_open(self) -> bool:
        return self.driver.query_app_state(self.app_package) == ApplicationState.RUNNING_IN_FOREGROUND

    def back(self):
        """
        Navigates back. iOS has no back button, so this clicks the back button in the navigation bar if present, and
        otherwise performs a swipe from the left edge of the screen, which is the standard back gesture on iOS.
        """
        if self.is_present(NAVIGATION_BAR_BACK_BUTTON):
            self.gtl_logger.info('Pressing back button in navigation bar')
            self.driver.find_element(*to_by_value(NAVIGATION_BAR_BACK_BUTTON)).click()
        else:
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

    def press_enter(self):
        """
        Presses the return key on the keyboard, by typing a newline in the focused element.
        """
        self.driver.switch_to.active_element.send_keys('\n')

    def press_backspace(self):
        """
        Presses the delete key on the keyboard, by typing a backspace in the focused element.
        """
        self.driver.switch_to.active_element.send_keys('\b')

    def press_left_arrow(self):
        """
        Not supported: the iOS keyboard has no arrow keys.
        """
        raise NotImplementedError('The iOS keyboard has no arrow keys, pressing the left arrow is not supported on iOS')

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

