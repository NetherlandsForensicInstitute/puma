import time

from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from appium import webdriver
from appium.webdriver.extensions.android.nativekey import AndroidKey


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
# TODO the PumaDriver misses some functionality compared to the driver initialisation part of appium actions, such as
# logging that appium is not running., or adding desired capabilities. make sure we have the same functionality as
# before!
class PumaDriver:
    """
    A driver class for interacting with Android applications using Appium.

    This class provides methods to interact with an Android app, such as activating,
    terminating, and interacting with UI elements. It uses Appium's WebDriver for
    remote control of the application.
    """

    def __init__(self, udid: str, app_package: str, implicit_wait: int = 1, appium_server: str = 'http://localhost:4723'):
        """
        Initializes the PumaDriver with device and application details.

        :param udid: The unique device identifier for the Android device.
        :param app_package: The package name of the application to interact with.
        :param implicit_wait: The implicit wait time for element searches, defaults to 1 second.
        :param appium_server: The address of the Appium server, defaults to 'http://localhost:4723'.
        """
        self.options = _get_android_default_options()
        self.options.udid = udid
        self.implicit_wait = implicit_wait
        self.app_package = app_package
        self.driver = webdriver.Remote(appium_server, options=self.options)

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
        self.driver.activate_app(self.app_package)

    def terminate_app(self):
        """
        Terminates the application on the device.
        """
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
        self.driver.press_keycode(AndroidKey.BACK)

    def home(self):
        """
        Simulates pressing the home button on the device.
        """
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
                print(f"Attempt {attempt + 1}: Element not found, swiping down")
                window_size = self.driver.get_window_size()
                start_x = window_size['width'] / 2
                start_y = window_size['height'] * 0.8
                end_y = window_size['height'] * 0.2
                self.driver.swipe(start_x, start_y, start_x, end_y, 500)
                time.sleep(0.5)
        raise PumaClickException(f'After {max_swipes} swipes, cannot find element with xpath {xpath}')

    def send_keys(self, xpath: str, keys: str):
        """
        Sends keys to an element specified by its XPath.

        :param xpath: The XPath of the element to send keys to.
        :param keys: The keys to send to the element.
        """
        element = self.get_element(xpath)
        element.send_keys(keys)

    def __repr__(self):
        """
        Returns a string representation of the PumaDriver instance.

        :return: A string describing the PumaDriver instance.
        """
        return f"Puma Driver {self.options.udid} for app package {self.app_package}"
