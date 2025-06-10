import time

from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from appium import webdriver
from appium.webdriver.extensions.android.nativekey import AndroidKey


def _get_android_default_options():
    options = UiAutomator2Options()
    options.no_reset = True
    options.platform_name = 'Android'
    options.new_command_timeout = 1200
    return options


class PumaDriver:

    def __init__(self, udid, app_package: str, implicit_wait: int = 1, appium_server: str = 'http://localhost:4723'):
        self.options = _get_android_default_options()
        self.options.udid = udid
        self.implicit_wait = implicit_wait
        self.app_package = app_package
        self.driver = webdriver.Remote(appium_server, options=self.options)

    def is_present(self, xpath: str, implicit_wait: int = 0) -> bool:
        self.driver.implicitly_wait(implicit_wait)
        found = self.driver.find_elements(by=AppiumBy.XPATH, value=xpath)
        self.driver.implicitly_wait(self.implicit_wait)
        return len(found) > 0

    def activate_app(self):
        self.driver.activate_app(self.app_package)

    def terminate_app(self):
        self.driver.terminate_app(self.app_package)

    def restart_app(self):
        self.terminate_app()
        self.activate_app()

    def app_open(self) -> bool:
        return str(self.driver.current_package) == self.app_package

    def back(self):
        self.driver.press_keycode(AndroidKey.BACK)

    def home(self):
        self.driver.press_keycode(AndroidKey.HOME)

    def click(self, xpath: str):
        if not self.is_present(xpath, self.implicit_wait):
            raise ValueError(f'Could not click on non present element with xpath {xpath}')
        self.driver.find_element(by=AppiumBy.XPATH, value=xpath).click()

    def get_element(self, xpath: str):
        if not self.is_present(xpath, self.implicit_wait):
            raise ValueError(f'Could not click on non present element with xpath {xpath}')
        return self.driver.find_element(by=AppiumBy.XPATH, value=xpath)

    def swipe_to_click_element(self, xpath: str, max_swipes: int = 10):
        for attempt in range(max_swipes):
            if self.is_present(xpath):
                self.click(xpath)
            else:
                # Element not found, perform swipe down
                print(f"Attempt {attempt + 1}: Element not found, swiping down")
                # Get the window size to determine the swipe dimensions
                window_size = self.driver.get_window_size()
                start_x = window_size['width'] / 2
                start_y = window_size['height'] * 0.8
                end_y = window_size['height'] * 0.2

                # Perform the swipe down
                self.driver.swipe(start_x, start_y, start_x, end_y, 500)

                # Wait a bit before the next attempt
                time.sleep(0.5)
        # If the loop completes, the element was not found
        raise ValueError(f'After {max_swipes} swipes, cannot find element with xpath {xpath}')

    def send_keys(self, xpath: str, keys: str):
        element = self.get_element(xpath)
        element.send_keys(keys)

    def __repr__(self):
        return f"Puma Driver {self.options.udid} for app package {self.app_package}"
