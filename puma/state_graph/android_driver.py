from typing import Dict

from appium.options.android import UiAutomator2Options
from appium.webdriver.extensions.android.nativekey import AndroidKey

from puma.state_graph.puma_driver import PumaDriver, Platform, KEYCODE_ENTER, KEYCODE_BACKSPACE, KEYCODE_LEFT_ARROW


def get_android_default_options() -> UiAutomator2Options:
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


class AndroidPumaDriver(PumaDriver):
    """
    A driver class for interacting with Android applications using Appium and UiAutomator2.
    """
    platform = Platform.ANDROID

    def __init__(self, udid: str, app_package: str, implicit_wait: int = 1, appium_server: str = 'http://localhost:4723', desired_capabilities: Dict[str, str] = None, platform: Platform = None):
        """
        Initializes the AndroidPumaDriver with device and application details.

        :param udid: The unique device identifier for the Android device.
        :param app_package: The package name of the application to interact with.
        :param implicit_wait: The implicit wait time for element searches, defaults to 1 second.
        :param appium_server: The address of the Appium server, defaults to 'http://localhost:4723'.
        :param desired_capabilities: The desired capabilities as passed to the Appium webdriver.
        """
        super().__init__(udid, app_package, implicit_wait=implicit_wait, appium_server=appium_server, desired_capabilities=desired_capabilities)
        # adb_pywrapper is imported here, as importing it logs errors when adb is not installed (e.g. for iOS users)
        from adb_pywrapper.adb_device import AdbDevice
        self.adb = AdbDevice(self.udid)
        self._screen_recorder = None

    @staticmethod
    def _default_options() -> UiAutomator2Options:
        return get_android_default_options()

    def app_open(self) -> bool:
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

    def press_enter(self):
        self.driver.press_keycode(KEYCODE_ENTER)

    def press_backspace(self):
        self.driver.press_keycode(KEYCODE_BACKSPACE)

    def press_left_arrow(self):
        self.driver.press_keycode(KEYCODE_LEFT_ARROW)

    def open_url(self, url: str):
        """
        Opens a given URL. The URl will open in the default app configured for that URL.
        """
        self.adb.open_intent(url)

    def open_notifications(self):
        """
        Opens the Android notifications panel.
        """
        self.gtl_logger.info('Opening notifications panel')
        self.driver.open_notifications()

    def start_recording(self, output_directory: str):
        """
        Starts a screen recording using adb.

        :param output_directory: The directory the screen recording should be stored in.
        """
        if self._screen_recorder is None:
            from adb_pywrapper.adb_screen_recorder import AdbScreenRecorder
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
        self._screen_recorder_output_directory = None
        return video_files

    def _is_recording(self) -> bool:
        return self._screen_recorder is not None

    def _click_coordinates(self, x: int, y: int):
        self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
