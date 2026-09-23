from enum import Enum
from time import sleep, time

from puma.apps.ios.apple_maps.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.puma_driver import PumaDriver, Platform, supported_version
from puma.state_graph.state import SimpleState, compose_clicks
from puma.state_graph.state_graph import StateGraph
from puma.utils.route_simulator import RouteSimulator

APPLE_MAPS_BUNDLE_ID = 'com.apple.Maps'


class TransportType(Enum):
    CAR = 'Drive'
    WALK = 'Walk'
    TRANSIT = 'Transit'
    BIKE = 'Cycle'


def _search(driver: PumaDriver, search_string: str):
    """
    Searches for a place and opens it. Apple Maps decides which place matches the search best. When searching for a
    category of places (such as 'coffee'), the first search result is opened.
    """
    driver.send_keys(SEARCH_FIELD, search_string)
    # wait for the suggestions to be loaded, otherwise Apple Maps sometimes opens an older suggestion
    _wait_for(driver, SEARCH_SUGGESTION)
    sleep(1)
    driver.press_enter()
    _wait_for(driver, DIRECTIONS_BUTTON, FIRST_SEARCH_RESULT, timeout=10)
    if not driver.is_present(DIRECTIONS_BUTTON):
        driver.click(FIRST_SEARCH_RESULT)
        sleep(2)


def _wait_for(driver: PumaDriver, *xpaths: str, timeout: float = 6):
    start = time()
    while time() - start < timeout:
        if any(driver.is_present(xpath) for xpath in xpaths):
            return
        sleep(0.3)


@supported_version("26.2")
class AppleMaps(StateGraph):
    """
    A class representing the Apple Maps application on iOS.

    Apple Maps needs to know the location of the device to plan routes. On a simulator, the location can be set using
    the route simulator (see get_route_simulator()), or with `xcrun simctl location`.
    """
    platform = Platform.IOS

    # States
    home_state = SimpleState(xpaths=[SEARCH_FIELD, PROFILE_BUTTON], initial_state=True)
    place_state = SimpleState(xpaths=[DIRECTIONS_BUTTON, CLOSE_CARD_BUTTON],
                              parent_state=home_state,
                              parent_state_transition=compose_clicks([CLOSE_CARD_BUTTON], 'close_place'))
    directions_state = SimpleState(xpaths=[TRANSPORT_TYPE_PICKER, WAYPOINT_LIST, CLOSE_CARD_BUTTON],
                                   parent_state=place_state,
                                   parent_state_transition=compose_clicks([CLOSE_CARD_BUTTON], 'close_directions'))

    # Transitions
    home_state.to(place_state, _search)
    place_state.to(directions_state, compose_clicks([DIRECTIONS_BUTTON], 'open_directions'))

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Apple Maps with a device UDID.

        :param device_udid: The unique device identifier of the iOS device or simulator.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, APPLE_MAPS_BUNDLE_ID, **kwargs)
        self.add_popup_handler(PopUpHandler([GETTING_THERE_SAFELY_ALERT], [GETTING_THERE_SAFELY_OK]))
        self.route_simulator = RouteSimulator(self, 0)

    def get_route_simulator(self) -> RouteSimulator:
        """
        :return: A route simulator, which can be used to spoof the location of the device along a route.
        """
        return self.route_simulator

    @action(home_state, end_state=place_state)
    def search_place(self, search_string: str):
        """
        Searches for a place, and opens the first result.

        :param search_string: The place to search for.
        """
        _search(self.driver, search_string)

    @action(home_state, end_state=directions_state)
    def get_directions(self, search_string: str, transport_type: TransportType = TransportType.CAR):
        """
        Searches for a place, and shows the directions from the current location of the device to that place.

        :param search_string: The place to search for.
        :param transport_type: The type of transport to use.
        """
        _search(self.driver, search_string)
        self.driver.click(DIRECTIONS_BUTTON)
        sleep(2)
        # The first time directions are requested, Apple Maps shows a safety warning
        if self.driver.is_present(GETTING_THERE_SAFELY_OK):
            self.driver.click(GETTING_THERE_SAFELY_OK)
        self.driver.click(transport_type_button(transport_type.value))
        sleep(2)

    def start_navigation(self, search_string: str, transport_type: TransportType = TransportType.CAR):
        """
        Searches for a place, and starts navigating from the current location of the device to that place.
        Note that turn-by-turn navigation is not available on the iOS simulator, only on real devices.

        :param search_string: The place to search for.
        :param transport_type: The type of transport to use.
        """
        self.get_directions(search_string, transport_type)
        self.driver.click(GO_BUTTON)
