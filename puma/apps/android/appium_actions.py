import os
from datetime import datetime
from pathlib import Path
from typing import Dict
from uuid import uuid4

from adb_pywrapper.adb_device import AdbDevice
from adb_pywrapper.adb_screen_recorder import AdbScreenRecorder
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver import WebElement
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.common.touch_action import TouchAction
from appium.webdriver.extensions.android.nativekey import AndroidKey

from puma.apps.android import logger
from puma.computer_vision import ocr
from puma.utils.video_utils import CACHE_FOLDER, log_error_and_raise_exception


def _get_android_default_options():
    options = UiAutomator2Options()
    options.no_reset = True
    options.platform_name = 'Android'
    options.new_command_timeout = 1200
    return options


def supported_version(version: str):
    def decorator(class_or_function):
        class_or_function.supported_version = version
        return class_or_function

    return decorator


class AndroidAppiumActions:
    def __init__(self,
                 udid: str,
                 app_package: str,
                 app_activity: str,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait: int = 1,
                 appium_server: str = 'http://localhost:4723'):
        """
        Class with a generic API for Appium scripting on an Android device.
        Can be used with an emulator or real device attached to the computer.
        :param desired_capabilities: desired capabilities as passed to the Appium webdriver
        :param implicit_wait: how long Appium will look for an element (you can look for an element before it is
                              rendered). Default 1 second
        :param appium_server: url of the appium server
        """
        # prepare options
        self.options = _get_android_default_options()
        self.options.udid = udid
        self.options.app_package = app_package
        self.options.app_activity = app_activity
        if desired_capabilities:
            self.options.load_capabilities(desired_capabilities)
        # connect to appium server
        self.driver = webdriver.Remote(appium_server, options=self.options)

        # the implicit wait time is how long appium looks for an element (you can try to find an element before it is rendered)
        self.implicit_wait = implicit_wait
        self.driver.implicitly_wait(implicit_wait)
        self.udid = self.driver.capabilities.get("udid")
        self.adb = AdbDevice(self.udid)

        # screen recorder
        self._screen_recorder = None

        # start app
        self.activate_app()

    def activate_app(self):
        self.driver.activate_app(self.options.app_package)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._screen_recorder is not None:
            self._screen_recorder.__exit__(None, None, None)
        self.driver.__exit__(exc_type, exc_val, exc_tb)

    def back(self):
        self.driver.press_keycode(AndroidKey.BACK)

    def home(self):
        self.driver.press_keycode(AndroidKey.HOME)

    def open_notifications(self):
        self.driver.open_notifications()

    def scroll_to_find_element(self, resource_id: str = None, text_equals: str = None,
                               text_contains: str = None) -> WebElement:
        """
        This code will scroll in the current view until a certain element is found, and then return that element.
        The element can be searched for by resource-id and/or the text in that element.
        When defining the text of the element either an exact match or a textContains match can be used. These two can
        of course not be used at the same time.
        The method will keep scrolling until the element is found. If you look for something that doesn't exist you
        will have a bad time.
        The first matching element is returned when found.
        :param resource_id: the resource id of the element to look for.
        :param text_equals: the exact text of the element to look for. Cannot be used in combination with text_contains.
        :param text_contains: part of the text of the element to look for. Cannot be used in combination with
        text_equals.
        :return: The element when found.
        """
        if text_equals is not None and text_contains is not None:
            raise ValueError('text_equals and text_contains can not be used at the same time')
        if resource_id is None and text_contains is None and text_equals is None:
            raise ValueError('resource_id, text_equals and text_contains cannot all be None')

        resource_id_part = '' if resource_id is None else f'.resourceIdMatches("{resource_id}")'
        text_part = '' if text_equals is None else f'.text("{text_equals}")'
        text_contains_part = '' if text_contains is None else f'.textContains("{text_contains}")'

        java_code = f'new UiScrollable(new UiSelector().scrollable(true).instance(0)).scrollIntoView(new UiSelector(){resource_id_part}{text_part}{text_contains_part}.instance(0))'
        return self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value=java_code)

    def is_present(self, xpath: str, implicit_wait: int = 0) -> bool:
        self.driver.implicitly_wait(implicit_wait)
        found = self.driver.find_elements(by=AppiumBy.XPATH, value=xpath)
        self.driver.implicitly_wait(self.implicit_wait)
        return len(found) > 0

    def start_recording(self):
        if self._screen_recorder is None:
            self._screen_recorder = AdbScreenRecorder(self.adb)
            self._screen_recorder.start_recording()

    def stop_recording_and_save_video(self, output_directory: str) -> [str]:
        if self._screen_recorder is None:
            return None
        video_files = self._screen_recorder.stop_recording(output_directory)
        self._screen_recorder.__exit__(None, None, None)
        self._screen_recorder = None
        return video_files

    def new_screenshot_name(self):
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        device_name = self.options.device_name
        return Path(CACHE_FOLDER) / f'{now}-{device_name}-{uuid4()}.png'

    def find_text_ocr(self, text_to_find: str) -> [ocr.RecognizedText]:
        path = self.new_screenshot_name()
        screenshot_taken = False
        try:
            screenshot_taken = self.driver.get_screenshot_as_file(path)
            if not screenshot_taken:
                raise Exception(f'Screenshot could not be stored to {path}')
            found_text = ocr.find_text(str(path), text_to_find)
            return found_text
        finally:
            if screenshot_taken:
                os.remove(path)

    def click_text_ocr(self, text_to_click: str, click_first_when_multiple: bool = False):
        found_text = self.find_text_ocr(text_to_click)
        if len(found_text) == 0:
            msg = f'Could not find text {text_to_click} on screen so could not click it'
            log_error_and_raise_exception(logger, msg)
        if len(found_text) > 1:
            msg = f'Found multiple occurrences of text {text_to_click} on screen so could not determine what to click'
            if not click_first_when_multiple:
                log_error_and_raise_exception(logger, msg)
            else:
                logger.warning(f'Found multiple occurrences of text {text_to_click} on screen, clicking first one')
        TouchAction(self.driver) \
            .tap(None, found_text[0].bounding_box.middle[0], found_text[0].bounding_box.middle[1], 1) \
            .perform()
