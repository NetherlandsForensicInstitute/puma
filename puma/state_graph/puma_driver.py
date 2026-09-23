import os
import time
from abc import abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict
from uuid import uuid4

from PIL import Image
from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver import WebElement
from appium.webdriver.webdriver import WebDriver
from selenium.webdriver import ActionChains
from urllib3.exceptions import MaxRetryError

from puma.computer_vision import ocr
from puma.computer_vision.ocr import RecognizedText
from puma.state_graph import logger
from puma.state_graph.locators import to_by_value
from puma.utils import CACHE_FOLDER
from puma.utils.gtl_logging import create_gtl_logger

# Android keycode constants, found at https://developer.android.com/reference/android/view/KeyEvent
KEYCODE_LEFT_ARROW = 21
KEYCODE_ENTER = 66
KEYCODE_BACKSPACE = 67


class Platform(Enum):
    """
    The mobile platforms supported by Puma.
    """
    ANDROID = 'Android'
    IOS = 'iOS'


class PumaClickException(Exception):
    """
    Custom exception for handling errors related to clicking actions in the PumaDriver.
    """
    pass


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
    A driver class for interacting with mobile applications using Appium.

    This class provides methods to interact with an app, such as activating, terminating, and interacting with UI
    elements. It uses Appium's WebDriver for remote control of the application.

    PumaDriver is the platform-independent base class. Creating a PumaDriver returns the driver for the requested
    platform: an AndroidPumaDriver by default, or an IOSPumaDriver when passing `platform=Platform.IOS`.

    All methods that take an XPath also accept a Locator (see puma.state_graph.locators), which allows using other
    locator strategies such as iOS predicate strings.
    """
    platform: Platform = None

    def __new__(cls, *args, platform: Platform = Platform.ANDROID, **kwargs):
        if cls is PumaDriver:
            if platform == Platform.IOS:
                from puma.state_graph.ios_driver import IOSPumaDriver
                cls = IOSPumaDriver
            else:
                from puma.state_graph.android_driver import AndroidPumaDriver
                cls = AndroidPumaDriver
        return super().__new__(cls)

    def __init__(self, udid: str, app_package: str, implicit_wait: int = 1, appium_server: str = 'http://localhost:4723', desired_capabilities: Dict[str, str] = None, platform: Platform = None):
        """
        Initializes the PumaDriver with device and application details.

        :param udid: The unique device identifier of the device.
        :param app_package: The identifier of the application to interact with: the package name on Android, the bundle
        id on iOS.
        :param implicit_wait: The implicit wait time for element searches, defaults to 1 second.
        :param appium_server: The address of the Appium server, defaults to 'http://localhost:4723'.
        :param desired_capabilities: The desired capabilities as passed to the Appium webdriver.
        :param platform: The platform of the device. Only used when instantiating PumaDriver directly, to choose the
        platform specific driver. Defaults to Android.
        """
        self.options = self._default_options()
        self.options.udid = udid
        self._set_device_options(udid)
        self.app_package = app_package
        if desired_capabilities:
            self.options.load_capabilities(desired_capabilities)
        logger.info("Connecting to Appium driver...")
        self.driver = _get_appium_driver(appium_server, udid, self.options)
        self.implicit_wait = implicit_wait
        self.driver.implicitly_wait(implicit_wait)
        self.udid = self.driver.capabilities.get("udid")
        self._screen_recorder_output_directory = None
        self.gtl_logger = create_gtl_logger(udid)

    @property
    def app_id(self) -> str:
        """
        The identifier of the application: the package name on Android, the bundle id on iOS.
        """
        return self.app_package

    @staticmethod
    @abstractmethod
    def _default_options() -> AppiumOptions:
        """
        :return: The default Appium options for this platform.
        """
        pass

    def _set_device_options(self, udid: str):
        """
        Sets Appium options that depend on the device. Desired capabilities passed by the user take precedence.

        :param udid: The unique device identifier of the device.
        """
        pass

    def is_present(self, xpath: str, implicit_wait: float = 0) -> bool:
        """
        Checks if an element is present on the screen.

        :param xpath: The XPath (or Locator) of the element to check.
        :param implicit_wait: The time to wait for the element to be present.
        :return: True if the element is present, False otherwise.
        """
        self.driver.implicitly_wait(implicit_wait)
        by, value = to_by_value(xpath)
        found = self.driver.find_elements(by=by, value=value)
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

    @abstractmethod
    def app_open(self) -> bool:
        """
        Checks if the application is currently open.

        :return: True if the application is open, False otherwise.
        """
        pass

    @abstractmethod
    def back(self):
        """
        Navigates back. On Android this presses the back button, on iOS (which has no back button) this uses the back
        button in the navigation bar, or a swipe from the left edge of the screen.
        """
        pass

    @abstractmethod
    def home(self):
        """
        Simulates pressing the home button on the device.
        """
        pass

    def click(self, xpath: str, width_ratio:float=0.5, height_ratio:float=0.5):
        """
        Clicks on an element specified by its XPath.

        By default, this method clicks in the center of the element selected by the given XPath.
        If you want to click off-center, you can use the width and heigh ratio.
        The ratios are values between 0 and 1 that determine where the element needs to be clicked, where (0,0)
        corresponds to the top-left and (1,1) corresponds to the bottom right.
        The width_ratio determines the x coordinate, the height_ratio the y coordinate.

        :param xpath: The XPath (or Locator) of the element to click.
        :param width_ratio: Optional. Determines the x coordinate, relative within the element, from 0 to 1 (left to right).
        :param height_ratio: Optional. Determines the y coordinate, relative within the element, from 0 to 1 (top to bottom).
        :raises PumaClickException: If the element cannot be clicked after multiple attempts.
        """
        for attempt in range(3):
            if self.is_present(xpath, self.implicit_wait):
                if (width_ratio, height_ratio) == (0.5, 0.5):
                    by, value = to_by_value(xpath)
                    self.driver.find_element(by=by, value=value).click()
                else:
                    element = self.get_element(xpath)
                    top_left = element.location['x'], element.location['y']
                    size = element.size['height'], element.size['width']
                    location = int(top_left[0] + width_ratio * size[1]), int(top_left[1] + height_ratio * size[0])
                    self.tap(location)
                return
        raise PumaClickException(f'Could not click on non present element with xpath {xpath}')

    def tap(self, coords: tuple[int, int], duration: int = None):
        """
        Taps on the screen at the specified coordinates.

        :param coords: A tuple (x, y) representing the coordinates to tap.
        """
        self.gtl_logger.info(f'Tapping on coordinates {coords}')
        self.driver.tap([coords], duration=duration)

    def long_click_element(self, xpath: str, duration: int = 2, width_ratio:float=0.5, height_ratio:float=0.5):
        """
        Clicks on a certain element, and hold for a given duration (in seconds)

        :param xpath: The XPath (or Locator) of the element to click.
        :param duration: how many seconds to hold the element before releasing
        :raises PumaClickException: If the element cannot be found after multiple attempts.
        """
        element = self.get_element(xpath)
        if (width_ratio, height_ratio) == (0.5, 0.5):
            actions = ActionChains(self.driver)
            actions.move_to_element(element).click_and_hold().pause(duration).release().perform()
        else:
            element = self.get_element(xpath)
            top_left = element.location['x'], element.location['y']
            size = element.size['height'], element.size['width']
            location = int(top_left[0] + width_ratio * size[1]), int(top_left[1] + height_ratio * size[0])
            self.tap(location, duration=duration)

    def get_element(self, xpath: str):
        """
        Retrieves an element specified by its XPath.

        :param xpath: The XPath (or Locator) of the element to retrieve.
        :return: The WebElement corresponding to the XPath.
        :raises PumaClickException: If the element cannot be found after multiple attempts.
        """
        for attempt in range(3):
            if self.is_present(xpath, self.implicit_wait):
                by, value = to_by_value(xpath)
                return self.driver.find_element(by=by, value=value)
        raise PumaClickException(f'Could not find element with xpath {xpath}')

    def get_elements(self, xpath: str) -> list[WebElement]:
        """
        Retrieves all elements matching the specified XPath.

        :param xpath: The XPath (or Locator) of the elements to retrieve.
        :return: A list of WebElements corresponding to the XPath.
        :raises PumaClickException: If no elements can be found after multiple attempts.
        """
        for attempt in range(3):
            if self.is_present(xpath, self.implicit_wait):
                by, value = to_by_value(xpath)
                return self.driver.find_elements(by=by, value=value)
        raise PumaClickException(f'Could not find elements with xpath {xpath}')

    def _scroll_down(self):
        """
        Moves/scrolls down a screen by simulating a 'swipe up' gesture.
        """
        window_size = self.driver.get_window_size()
        start_x = window_size['width'] / 2
        start_y = window_size['height'] * 0.8
        end_y = window_size['height'] * 0.2
        self.driver.swipe(start_x, start_y, start_x, end_y, 500)
        time.sleep(0.5)

    def _scroll_up(self):
        """
        Moves/scrolls up a screen by simulating a 'swipe down' gesture.
        """
        window_size = self.driver.get_window_size()
        start_x = window_size['width'] / 2
        start_y = window_size['height'] * 0.2
        end_y = window_size['height'] * 0.8
        self.driver.swipe(start_x, start_y, start_x, end_y, 500)
        time.sleep(0.5)

    def swipe_to_find_element(self, xpath: str, max_swipes: int = 10, swipe_down: bool = True):
        """
        Swipes up or down to find an element specified by its XPath. This is necessary when the element you want to click on
        is out of view.

        :param xpath: The XPath (or Locator) of the element to find.
        :param max_swipes: The maximum number of swipe attempts to find the element.
        :param swipe_down: If the element can be found below, True, otherwise False.
        :raises PumaClickException: If the element cannot be found after the maximum number of swipes.
        """
        for attempt in range(max_swipes):
            if self.is_present(xpath):
                return self.get_element(xpath)
            else:
                self.gtl_logger.warning(f"Attempt {attempt + 1}: Element not found, swiping")
                if swipe_down:
                    self._scroll_down()
                else:
                    self._scroll_up()
        raise PumaClickException(f'After {max_swipes} swipes, cannot find element with xpath {xpath}')

    def swipe_to_find_elements(self, xpath: str, num_swipes: int = 10):
        """
        Collects all elements matching given XPath. Next, swipes down a number of times and collects
        all new elements matching given XPath in each resulting view.

        :param xpath: the xpath (or Locator) of the elements to find
        :param num_swipes: the number of swipes to execute
        :raises PumaClickException: if no matching element can be found after given number of swipes
        """
        seen_elements = set()
        results = []

        for attempt in range(num_swipes):
            try:
                found_elements = self.get_elements(xpath)
            except PumaClickException as e:
                self.gtl_logger.info(f'Unable to get elements with XPath {xpath}, reason: {str(e)}')
                self.gtl_logger.info(f'Swiping down')
            else:
                for element in found_elements:
                    if element not in seen_elements:
                        seen_elements.add(element)
                        results.append(element)

            self._scroll_down()

        if not results:
            raise PumaClickException(f'After {num_swipes} swipes, no element with xpath {xpath} found')

        return results

    def swipe_to_click_element(self, xpath: str, max_swipes: int = 10):
        """
        Swipes down to find and click an element specified by its XPath. This is necessary when the element you want to
        click on is out of view.

        :param xpath: The XPath (or Locator) of the element to find and click.
        :param max_swipes: The maximum number of swipe attempts to find the element.
        :raises PumaClickException: If the element cannot be found after the maximum number of swipes.
        """
        self.swipe_to_find_element(xpath, max_swipes).click()

    def send_keys(self, xpath: str, text: str):
        """
        Sends keys to an element specified by its XPath.

        :param xpath: The XPath (or Locator) of the element to send keys to.
        :param text: The text to send to the element.
        """
        self.gtl_logger.info(f'Entering text "{text}" in text box')
        element = self.get_element(xpath)
        element.click() # TODO check all usages
        time.sleep(0.5)
        # The element has changed after clicking due to the keyboard appearing, so find it again.
        element = self.get_element(xpath)
        element.clear()
        element.send_keys(text)

    @abstractmethod
    def press_enter(self):
        """
        Presses the ENTER key.
        """
        pass

    @abstractmethod
    def press_backspace(self):
        """
        Presses the BACKSPACE key.
        """
        pass

    @abstractmethod
    def press_left_arrow(self):
        """
        Presses the LEFT ARROW key.
        """
        pass

    @abstractmethod
    def open_url(self, url: str):
        """
        Opens a given URL. The URl will open in the default app configured for that URL.
        """
        pass

    @abstractmethod
    def open_notifications(self):
        """
        Opens the notifications panel.
        """
        pass

    @abstractmethod
    def start_recording(self, output_directory: str):
        """
        Starts a screen recording.

        :param output_directory: The directory the screen recording should be stored in.
        """
        pass

    @abstractmethod
    def stop_recording_and_save_video(self) -> list[str] | None:
        """
        Stops the screen recording, and saves the video to the output directory passed to start_recording.

        :return: The paths of the stored video files, or None if no recording was active.
        """
        pass

    def _new_screenshot_name(self):
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        device_name = self.options.device_name
        return Path(CACHE_FOLDER) / f'{now}-{device_name}-{uuid4()}.png'

    def _find_text_ocr(self, text_to_find: str) -> tuple[list[RecognizedText], float]:
        """
        Takes a screenshot and uses OCR to find the given text.

        :param text_to_find: The text to find.
        :return: The found text, and the ratio between screenshot pixels and screen coordinates. On iOS, screenshots are
        taken in pixels while the screen coordinates are in points, so the ratio is 2 or 3 depending on the device.
        """
        path = self._new_screenshot_name()
        screenshot_taken = False
        try:
            screenshot_taken = self.driver.get_screenshot_as_file(path)
            if not screenshot_taken:
                raise Exception(f'Screenshot could not be stored to {path}')
            with Image.open(path) as screenshot:
                screenshot_width = screenshot.size[0]
            scale = screenshot_width / self.driver.get_window_size()['width']
            self.gtl_logger.info(f'Using OCR to find text "{text_to_find}"')
            found_text = ocr.find_text(str(path), text_to_find)
            return found_text, scale
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
        found_text, scale = self._find_text_ocr(text_to_click)
        if len(found_text) == 0:
            msg = f'Could not find text "{text_to_click}" on screen so could not click it'
            raise PumaClickException(msg)
        if len(found_text) > 1:
            msg = f'Found multiple occurrences of text "{text_to_click}" on screen so could not determine what to click'
            if not click_first_when_multiple:
                raise PumaClickException(msg)
            else:
                self.gtl_logger.warning(f'Found multiple occurrences of text "{text_to_click}" on screen, clicking first one')
        x = round(found_text[0].bounding_box.middle[0] / scale)
        y = round(found_text[0].bounding_box.middle[1] / scale)
        self.gtl_logger.info(f'Clicking found text "{found_text}" at coordinates {(x,y)}')
        self._click_coordinates(x, y)

    @abstractmethod
    def _click_coordinates(self, x: int, y: int):
        """
        Clicks on the given screen coordinates using the platform specific gesture.
        """
        pass

    def set_idle_timeout(self, timeout: int):
        """
        Sets a maximum time to wait while idle.
        Note that the unit differs per platform: milliseconds on Android (UiAutomator2), seconds on iOS (XCUITest).

        :param timeout: The maximum time to wait.
        """
        # https://github.com/appium/appium-uiautomator2-driver#poor-elements-interaction-performance
        # https://github.com/appium/appium-uiautomator2-driver#settings-api
        # https://appium.github.io/appium-xcuitest-driver/latest/reference/settings/
        settings = self.driver.get_settings()
        settings.update({"waitForIdleTimeout": timeout})
        self.driver.update_settings(settings)

    def execute_script(self, script: str, *args):
        return self.driver.execute_script(script, *args)

    def __repr__(self):
        """
        Returns a string representation of the PumaDriver instance.

        :return: A string describing the PumaDriver instance.
        """
        return f"Puma {self.platform.value if self.platform else ''} Driver {self.options.udid} for app {self.app_package}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._is_recording():
            self.stop_recording_and_save_video()
        self.driver.__exit__(exc_type, exc_val, exc_tb)

    def _is_recording(self) -> bool:
        return self._screen_recorder_output_directory is not None
