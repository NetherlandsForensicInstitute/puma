from time import sleep

from puma.apps.android.settings import logger
from puma.apps.android.settings.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.puma_driver import supported_version
from puma.state_graph.state import SimpleState, compose_clicks, scroll_to
from puma.state_graph.state_graph import StateGraph

SETTINGS_PACKAGE = 'com.android.settings'
# The screen timeout options in seconds, and their labels in the app
SCREEN_TIMEOUT_OPTIONS = {15: '15 seconds', 30: '30 seconds', 60: '1 minute', 120: '2 minutes', 300: '5 minutes',
                          600: '10 minutes', 1800: '30 minutes'}
# The maximum value of the brightness slider
_BRIGHTNESS_SLIDER_MAX = 65535


def _screen(title: str, *xpaths: str, parent_state: SimpleState) -> SimpleState:
    return SimpleState(xpaths=[toolbar(title), *xpaths], parent_state=parent_state)


@supported_version("16")
class Settings(StateGraph):
    """
    A class representing the Settings application on Android.

    The layout of the Settings app differs between device manufacturers. This class supports the Settings app of
    Google Pixel devices.
    """

    # States. The parent transitions are the default back action.
    main_state = SimpleState(xpaths=[MAIN_SEARCH_BAR, MAIN_HOMEPAGE], initial_state=True)
    network_state = _screen('Network & internet', parent_state=main_state)
    internet_state = _screen('Internet', list_entry(INTERNET_USE_WIFI), parent_state=network_state)
    display_state = _screen('Display & touch', parent_state=main_state)
    screen_timeout_state = _screen('Screen timeout', parent_state=display_state)

    # Transitions. The app remembers the scroll position of the main screen, the entries used are at the top of it.
    # The screens take a moment to open.
    main_state.to(network_state, compose_clicks([scroll_to(list_entry('Network & internet'), swipe_down=False)],
                                                'open_network_and_internet', wait=1))
    network_state.to(internet_state, compose_clicks([list_entry('Internet')], 'open_internet', wait=1))
    main_state.to(display_state, compose_clicks([scroll_to(list_entry('Display & touch'), swipe_down=False)],
                                                'open_display_and_touch', wait=1))
    display_state.to(screen_timeout_state, compose_clicks([list_entry('Screen timeout')], 'open_screen_timeout', wait=1))

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Settings with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, SETTINGS_PACKAGE, **kwargs)

    @action(internet_state)
    def connect_to_wifi(self, ssid: str, password: str = None) -> bool:
        """
        Connects to a Wi-Fi network that is in range. Wi-Fi is turned on if needed. Nothing happens if the device is
        already connected to the network.

        :param ssid: The name of the network.
        :param password: The password of the network. Not needed for open networks and saved networks.
        :return: True if the device is connected to the network, False if connecting did not succeed within 30 seconds.
        :raises ValueError: If the network needs a password, but no password was given.
        """
        wifi_switch = row_switch(INTERNET_USE_WIFI)
        if self.driver.get_element(wifi_switch).get_attribute('checked') != 'true':
            self.gtl_logger.info('Turning Wi-Fi on')
            self.driver.click(wifi_switch)
        self.driver.wait_until_present(INTERNET_NETWORKS_HEADER, description='Waiting for the list of networks')
        if self.driver.is_present(wifi_connected(ssid)):
            self.gtl_logger.info(f'Already connected to Wi-Fi network {ssid}')
            return True
        self.gtl_logger.info(f'Opening Wi-Fi network {ssid}')
        self.driver.swipe_to_click_element(list_entry(ssid))
        if self.driver.wait_until_present(WIFI_PASSWORD_INPUT, timeout=3):
            if password is None:
                self.driver.click(WIFI_PASSWORD_CANCEL)
                raise ValueError(f'Wi-Fi network {ssid} needs a password')
            # The password is entered directly, as PumaDriver.send_keys logs the text it enters
            self.gtl_logger.info('Entering the Wi-Fi password')
            self.driver.get_element(WIFI_PASSWORD_INPUT).click()
            self.driver.get_element(WIFI_PASSWORD_INPUT).send_keys(password)
            self.gtl_logger.info('Pressing connect')
            self.driver.click(WIFI_PASSWORD_CONNECT)
        connected = self.driver.wait_until_present(wifi_connected(ssid), timeout=30,
                                                   description=f'Waiting until connected to Wi-Fi network {ssid}')
        logger.info(f'{"Connected" if connected else "Could not connect"} to Wi-Fi network {ssid}')
        return connected

    @action(display_state)
    def get_brightness(self) -> int:
        """
        :return: The brightness level, as a percentage from 0 to 100.
        """
        return int(self.driver.get_element(summary_of(DISPLAY_BRIGHTNESS_LEVEL)).text.strip('%'))

    def set_brightness(self, percentage: int):
        """
        Sets the brightness level. Note that when adaptive brightness is on, Android keeps adjusting the brightness
        level.

        :param percentage: The brightness level, from 0 to 100.
        """
        # The arguments are checked before the action, as actions are retried when they fail
        if not 0 <= percentage <= 100:
            raise ValueError(f'Brightness must be a percentage from 0 to 100, not {percentage}')
        self._set_brightness(percentage)

    @action(display_state)
    def _set_brightness(self, percentage: int):
        self.gtl_logger.info(f'Setting brightness to {percentage}%')
        self.driver.click(list_entry(DISPLAY_BRIGHTNESS_LEVEL))
        self.driver.wait_until_present(BRIGHTNESS_SLIDER)
        self.driver.get_element(BRIGHTNESS_SLIDER).send_keys(str(round(percentage / 100 * _BRIGHTNESS_SLIDER_MAX)))
        sleep(1)
        self.gtl_logger.info('Closing the brightness slider')
        self.driver.back()
        sleep(1)
        logger.info(f'Set brightness to {self.driver.get_element(summary_of(DISPLAY_BRIGHTNESS_LEVEL)).text}')

    @action(screen_timeout_state)
    def get_screen_timeout(self) -> int:
        """
        :return: After how many seconds of inactivity the screen turns off.
        """
        label = self.driver.get_element(SCREEN_TIMEOUT_SELECTED_OPTION).text
        return next(seconds for seconds, option in SCREEN_TIMEOUT_OPTIONS.items() if option == label)

    def set_screen_timeout(self, seconds: int):
        """
        Sets after how many seconds of inactivity the screen turns off.

        :param seconds: The number of seconds: 15, 30, 60, 120, 300, 600 or 1800.
        """
        if seconds not in SCREEN_TIMEOUT_OPTIONS:
            raise ValueError(f'Screen timeout cannot be set to {seconds}, the options are {list(SCREEN_TIMEOUT_OPTIONS)}')
        self._set_screen_timeout(seconds)

    @action(screen_timeout_state)
    def _set_screen_timeout(self, seconds: int):
        self.gtl_logger.info(f'Setting screen timeout to {SCREEN_TIMEOUT_OPTIONS[seconds]}')
        self.driver.click(list_entry(SCREEN_TIMEOUT_OPTIONS[seconds]))
        sleep(1)
        logger.info(f'Set screen timeout to {SCREEN_TIMEOUT_OPTIONS[seconds]}')
