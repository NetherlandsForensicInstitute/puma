from time import sleep
from typing import Optional

from puma.apps.ios.settings import logger
from puma.apps.ios.settings.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, Platform, supported_version
from puma.state_graph.state import SimpleState
from puma.state_graph.state_graph import StateGraph

SETTINGS_BUNDLE_ID = 'com.apple.Preferences'
# The Auto-Lock options, in seconds. None means the screen never locks.
AUTO_LOCK_OPTIONS = [30, 60, 120, 180, 240, 300, None]
_NEVER = -1


def _open(cell: str, name: str):
    """
    Creates a transition that opens a cell in a settings screen, scrolling down to it if needed.
    """
    def _open_cell(driver: PumaDriver):
        driver.swipe_to_find_element(cell, max_swipes=5).click()
        sleep(1)
    _open_cell.__name__ = name
    return _open_cell


@supported_version("26.6")
class Settings(StateGraph):
    """
    A class representing the Settings application on iOS.

    Note that the settings available differ between devices and simulators. Simulators for example have no Display &
    Brightness settings, and therefore no Auto-Lock.
    """
    platform = Platform.IOS

    # States. The parent transitions are the default back action, which uses the back button in the navigation bar
    settings_state = SimpleState(xpaths=[SETTINGS_NAVIGATION_BAR, GENERAL_CELL], initial_state=True)
    display_state = SimpleState(xpaths=[DISPLAY_NAVIGATION_BAR], parent_state=settings_state)
    auto_lock_state = SimpleState(xpaths=[AUTO_LOCK_NAVIGATION_BAR], parent_state=display_state)

    # Transitions
    settings_state.to(display_state, _open(DISPLAY_CELL, 'open_display_and_brightness'))
    display_state.to(auto_lock_state, _open(AUTO_LOCK_CELL, 'open_auto_lock'))

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Settings with a device UDID.

        :param device_udid: The unique device identifier of the iOS device or simulator.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, SETTINGS_BUNDLE_ID, **kwargs)

    @action(auto_lock_state)
    def get_auto_lock(self) -> Optional[int]:
        """
        Returns after how long the screen locks automatically. Only available on real devices.

        :return: The number of seconds, or None if the screen never locks.
        """
        seconds = int(self.driver.get_element(SELECTED_AUTO_LOCK_OPTION).get_attribute('name'))
        return None if seconds == _NEVER else seconds

    @action(auto_lock_state)
    def set_auto_lock(self, seconds: Optional[int]):
        """
        Sets after how long the screen locks automatically. Only available on real devices.

        :param seconds: The number of seconds (30, 60, 120, 180, 240 or 300), or None to never lock the screen.
        """
        if seconds not in AUTO_LOCK_OPTIONS:
            raise ValueError(f'Auto-Lock cannot be set to {seconds}, the options are {AUTO_LOCK_OPTIONS}')
        self.driver.click(auto_lock_option(_NEVER if seconds is None else seconds))
        sleep(1)
        logger.info(f'Set Auto-Lock to {"Never" if seconds is None else f"{seconds} seconds"}')
