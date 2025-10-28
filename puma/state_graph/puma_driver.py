import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict
from uuid import uuid4

from adb_pywrapper.adb_device import AdbDevice
from adb_pywrapper.adb_screen_recorder import AdbScreenRecorder
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from appium import webdriver
from appium.webdriver.extensions.android.nativekey import AndroidKey
from appium.webdriver.webdriver import WebDriver
from selenium.webdriver import ActionChains
from urllib3.exceptions import MaxRetryError

from puma.computer_vision import ocr
from puma.computer_vision.ocr import RecognizedText
from puma.state_graph import logger
from puma.utils import CACHE_FOLDER
from puma.utils.gtl_logging import create_gtl_logger

KEYCODE_ENTER = 66

class PumaClickException(Exception):
    """
    Custom exception for handling errors related to clicking actions in the PumaDriver.
    """
    pass

def _get_android_default_options() -> UiAutomator2Options:
    """
    Creates and configures default options for an Android UiAutomator2 driver.

    This function sets up the default options required for initializing an Android
    UiAutomator2 driver, including platform name and command timeout settings.

    :return: Configured UiAutomator2Options instance.
    """
    options = UiAutomator2Options()
    options.no_reset = True
    options.platform_name = 'Android'
    options.new_command_timeout = 1200
    return options


__drivers: dict[str, WebDriver] = {}

def _get_appium_driver(appium_server: str, udid: str, options) -> WebDriver:
    key = f"{appium_server}${udid}"
    if key not in __drivers.keys():
        try:
            __drivers[key] = webdriver.Remote(appium_server, options=options)
        except MaxRetryError:
            logger.error("Connecting to the Appium server has failed.\n"
                         "Make sure that the appium server is running!\n"
                         "This can be done by running the `appium` command from the command line.")
            exit(1)
    else:
        logger.warning(f'WARNING: There already was an initialized driver for appium server {appium_server} and udid {udid}. '
                       'This driver will be used, which might mean your Appium capabilities are ignored as these cannot be'
                       'altered for a driver that has already been initialized. If you need specific capabilities, please '
                       'rewrite your Puma code to ensure the correct capabilities are loaded the first time you connect to '
                       f'server {appium_server} and device {udid}.')
    return __drivers[key]

def supported_version(version: str):
    def decorator(class_or_function):
        class_or_function.supported_version = version
        return class_or_function

    return decorator

class PumaDriver:
    """
    A driver class for interacting with Android applications using Appium.

    This class provides methods to interact with an Android app, such as activating,
    terminating, and interacting with UI elements. It uses Appium's WebDriver for
    remote control of the application.
    """

    def __init__(self, udid: str, app_package: str, implicit_wait: int = 1, appium_server: str = 'http://localhost:4723', desired_capabilities: Dict[str, str] = None):
        """
        Initializes the PumaDriver with device and application details.

        :param udid: The unique device identifier for the Android device.
        :param app_package: The package name of the application to interact with.
        :param implicit_wait: The implicit wait time for element searches, defaults to 1 second.
        :param appium_server: The address of the Appium server, defaults to 'http://localhost:4723'.
        :param desired_capabilities: The desired capabilities as passed to the Appium webdriver.
        """
        self.options = _get_android_default_options()
        self.options.udid = udid
        self.app_package = app_package
        if desired_capabilities:
            self.options.load_capabilities(desired_capabilities)
        logger.info("Connecting to Appium driver...")
        self.driver = _get_appium_driver(appium_server, udid, self.options)
        self.implicit_wait = implicit_wait
        self.driver.implicitly_wait(implicit_wait)
        self.udid = self.driver.capabilities.get("udid")
        self.adb = AdbDevice(self.udid)
        self._screen_recorder = None
        self._screen_recorder_output_directory = None
        self.gtl_logger = create_gtl_logger(udid)

    def is_present(self, xpath: str, implicit_wait: int = 0) -> bool:
        """
        Checks if an element is present on the screen.

        :param xpath: The XPath of the element to check.
        :param implicit_wait: The time to wait for the element to be present.
        :return: True if the element is present, False otherwise.
        """
        self.driver.implicitly_wait(implicit_wait)
        found = self.driver.find_elements(by=AppiumBy.XPATH, value=xpath)
        self.driver.implicitly_wait(self.implicit_wait)
        return len(found) > 0

    def activate_app(self):
        """
        Activates the application on the device.
        """
        self.gtl_logger.info(f'Activating app {self.app_package}')
        self.driver.activate_app(self.app_package)

    def terminate_app(self):
        """
        Terminates the application on the device.
        """
        self.gtl_logger.info(f'Terminating app {self.app_package}')
        self.driver.terminate_app(self.app_package)

    def restart_app(self):
        """
        Restarts the application by terminating and then activating it.
        """
        self.terminate_app()
        self.activate_app()

    def app_open(self) -> bool:
        """
        Checks if the application is currently open.

        :return: True if the application is open, False otherwise.
        """
        return str(self.driver.current_package) == self.app_package

    def back(self):
        """
        Simulates pressing the back button on the device.
        """
        self.gtl_logger.info(f'Pressing back button')
        self.driver.press_keycode(AndroidKey.BACK)

    def home(self):
        """
        Simulates pressing the home button on the device.
        """
        self.gtl_logger.info(f'Pressing home button')
        self.driver.press_keycode(AndroidKey.HOME)

    def click(self, xpath: str):
        """
        Clicks on an element specified by its XPath.

        :param xpath: The XPath of the element to click.
        :raises PumaClickException: If the element cannot be clicked after multiple attempts.
        """
        for attempt in range(3):
            if self.is_present(xpath, self.implicit_wait):
                self.driver.find_element(by=AppiumBy.XPATH, value=xpath).click()
                return
        raise PumaClickException(f'Could not click on non present element with xpath {xpath}')

    def click_within(self, xpath:str, width_ratio:float=0.5, height_ratio:float=0.5):
        """
        Clicks on a location within a given element, based on a specified width and height ratio.
        While the click() method will always click in the middle, this method can be used to click off-center.

        The ratios are values between 0 and 1 that determine where the element needs to be clicked, where (0,0)
        corresponds to the top-left and (1,1) corresponds to the bottom right.
        The width_ratio determines the x coordinate, the height_ratio the y coordinate.

        :param xpath: The XPath of the element to click.
        :param width_ratio: Determines the x coordinate, relative within the element, from 0 to 1 (left to right).
        :param height_ratio: Determines the y coordinate, relative within the element, from 0 to 1 (top to bottom).
        :raises PumaClickException: If the element cannot be found after multiple attempts.
        """
        send_button = self.get_element(xpath)
        top_left = send_button.location['x'], send_button.location['y']
        size = send_button.size['height'], send_button.size['width']
        location = int(top_left[0] + width_ratio * size[1]), int(top_left[1] + height_ratio * size[0])
        self.driver.tap([(location)])

    def long_click(self, xpath:str):
        """
        Triggers a long_press on an element specified by its XPath.
        This method uses press_and_hold with a duration of 1 second.

        :param xpath: The XPath of the element to click.
        :raises PumaClickException: If the element cannot be clicked after multiple attempts.
        """
        self.press_and_hold(xpath, 1)

    def press_and_hold(self, xpath: str, duration: int):
        """
        Clicks on a certain element, and hold for a given duration (in seconds)

        :param xpath: The XPath of the element to click.
        :param duration: how many seconds to hold the element before releasing
        :raises PumaClickException: If the element cannot be found after multiple attempts.
        """
        element = self.get_element(xpath)
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().pause(duration).release().perform()

    def get_element(self, xpath: str):
        """
        Retrieves an element specified by its XPath.

        :param xpath: The XPath of the element to retrieve.
        :return: The WebElement corresponding to the XPath.
        :raises PumaClickException: If the element cannot be found after multiple attempts.
        """
        for attempt in range(3):
            if self.is_present(xpath, self.implicit_wait):
                return self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        raise PumaClickException(f'Could not find element with xpath {xpath}')

    def swipe_to_click_element(self, xpath: str, max_swipes: int = 10):
        """
        Swipes down to find and click an element specified by its XPath. This is necessary when the element you want to
        click on is out of view.

        :param xpath: The XPath of the element to find and click.
        :param max_swipes: The maximum number of swipe attempts to find the element.
        :raises PumaClickException: If the element cannot be found after the maximum number of swipes.
        """
        for attempt in range(max_swipes):
            if self.is_present(xpath):
                self.click(xpath)
                return
            else:
                self.gtl_logger.warning(f"Attempt {attempt + 1}: Element not found, swiping down")
                window_size = self.driver.get_window_size()
                start_x = window_size['width'] / 2
                start_y = window_size['height'] * 0.8
                end_y = window_size['height'] * 0.2
                self.driver.swipe(start_x, start_y, start_x, end_y, 500)
                time.sleep(0.5)
        raise PumaClickException(f'After {max_swipes} swipes, cannot find element with xpath {xpath}')

    def send_keys(self, xpath: str, text: str):
        """
        Sends keys to an element specified by its XPath.

        :param xpath: The XPath of the element to send keys to.
        :param text: The text to send to the element.
        """
        self.gtl_logger.info(f'Entering text "{text}" in text box')
        element = self.get_element(xpath)
        element.send_keys(text)

    def press_enter(self):
        """
        Presses the ENTER key.
        """
        self.driver.press_keycode(KEYCODE_ENTER)

    def open_url(self, url: str, package_name:str=None):
        """
        Opens a given URL. A package name can be opened to define an app to open the link with.
        If not, the URl will open in the default app configured for that URL.
        """
        self.adb.open_intent(url, package_name)

    def start_recording(self, output_directory: str):
        """
        Starts a screen recording.

        :param output_directory: The directory the screen recording should be stored in.
        """
        if self._screen_recorder is None:
            self._screen_recorder_output_directory = output_directory
            self._screen_recorder = AdbScreenRecorder(self.adb)
            self.gtl_logger.info('Starting screen recording')
            self._screen_recorder.start_recording()

    def stop_recording_and_save_video(self) -> list[str] | None:
        if self._screen_recorder is None:
            return None
        self.gtl_logger.info('Ending screen recording')
        video_files = self._screen_recorder.stop_recording(self._screen_recorder_output_directory)
        self._screen_recorder.__exit__(None, None, None)
        self._screen_recorder = None
        return video_files

    def _new_screenshot_name(self):
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        device_name = self.options.device_name
        return Path(CACHE_FOLDER) / f'{now}-{device_name}-{uuid4()}.png'

    def _find_text_ocr(self, text_to_find: str) -> list[RecognizedText]:
        path = self._new_screenshot_name()
        screenshot_taken = False
        try:
            screenshot_taken = self.driver.get_screenshot_as_file(path)
            if not screenshot_taken:
                raise Exception(f'Screenshot could not be stored to {path}')
            self.gtl_logger.info(f'Using OCR to find text {text_to_find}')
            found_text = ocr.find_text(str(path), text_to_find)
            return found_text
        finally:
            if screenshot_taken:
                os.remove(path)

    def click_text_ocr(self, text_to_click: str, click_first_when_multiple: bool = False):
        """
        Clicks a text if it can be found on a screen using OCR.

        :param text_to_click: The text to click.
        :param click_first_when_multiple: If True, the first occurrence of the string will be clicked if multiple are found.
        If False, raises an PumaClickException if multiple occurrences are found. Defaults to False.
        """
        self.gtl_logger.info(f'Using OCR to click on text "{text_to_click}"')
        found_text = self._find_text_ocr(text_to_click)
        if len(found_text) == 0:
            msg = f'Could not find text {text_to_click} on screen so could not click it'
            raise PumaClickException(msg)
        if len(found_text) > 1:
            msg = f'Found multiple occurrences of text {text_to_click} on screen so could not determine what to click'
            if not click_first_when_multiple:
                raise PumaClickException(msg)
            else:
                logger.warning(f'Found multiple occurrences of text {text_to_click} on screen, clicking first one')
        x = found_text[0].bounding_box.middle[0]
        y = found_text[0].bounding_box.middle[1]
        self.gtl_logger.info(f'Clicking found text {found_text} at coordinates {(x,y)}')
        self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})

    def set_idle_timeout(self, timeout: int):
        """
        Sets a maximum time to wait while idle.

        :param timeout: The maximum time to wait.
        """
        # https://github.com/appium/appium-uiautomator2-driver#poor-elements-interaction-performance
        # https://github.com/appium/appium-uiautomator2-driver#settings-api
        settings = self.driver.get_settings()
        settings.update({"waitForIdleTimeout": timeout})
        self.driver.update_settings(settings)

    def __repr__(self):
        """
        Returns a string representation of the PumaDriver instance.

        :return: A string describing the PumaDriver instance.
        """
        return f"Puma Driver {self.options.udid} for app package {self.app_package}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._screen_recorder is not None:
            self.stop_recording_and_save_video()
        self.driver.__exit__(exc_type, exc_val, exc_tb)