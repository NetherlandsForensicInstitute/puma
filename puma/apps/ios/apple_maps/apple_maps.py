from enum import Enum
from time import sleep, time

from puma.apps.ios.apple_maps import logger
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


# The routing profiles used by the route simulator for each transport type. Public transport cannot be simulated.
ROUTE_TRANSPORT_MODES = {
    TransportType.CAR: 'car',
    TransportType.WALK: 'foot',
    TransportType.BIKE: 'bike',
}


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


def _open_directions(driver: PumaDriver, search_string: str, transport_type: 'TransportType'):
    """
    Searches for a place, and shows the directions from the current location of the device to that place.
    """
    _search(driver, search_string)
    driver.click(DIRECTIONS_BUTTON)
    sleep(2)
    # The first time directions are requested, Apple Maps shows a safety warning
    if driver.is_present(GETTING_THERE_SAFELY_OK):
        driver.click(GETTING_THERE_SAFELY_OK)
    driver.click(transport_type_button(transport_type.value))
    sleep(2)


def _end_navigation(driver: PumaDriver):
    """
    Ends turn-by-turn navigation, by expanding the tray at the bottom of the screen and tapping End Route. Apple Maps
    then shows the destination.
    """
    driver.click(NAVIGATION_TRAY)
    sleep(1)
    driver.click(END_ROUTE_BUTTON)
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
    # turn-by-turn navigation, which is only available on real devices. Ending the navigation shows the destination.
    navigation_state = SimpleState(xpaths=[NAVIGATION_TRAY],
                                   parent_state=place_state,
                                   parent_state_transition=_end_navigation)

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
        _open_directions(self.driver, search_string, transport_type)

    @action(home_state, end_state=navigation_state)
    def start_navigation(self, search_string: str, transport_type: TransportType = TransportType.CAR):
        """
        Searches for a place, and starts navigating from the current location of the device to that place.
        Note that turn-by-turn navigation is not available on the iOS simulator, only on real devices.

        :param search_string: The place to search for.
        :param transport_type: The type of transport to use.
        """
        _open_directions(self.driver, search_string, transport_type)
        self.driver.click(GO_BUTTON)
        sleep(2)

    @action(navigation_state, end_state=place_state)
    def end_navigation(self):
        """
        Ends turn-by-turn navigation. Apple Maps then shows the destination.
        """
        _end_navigation(self.driver)

    def start_route(self, from_query: str, to_query: str, speed: int, transport_type: TransportType = TransportType.CAR):
        """
        Travels a route from one place to another, by spoofing the location of the device along the route, while Apple
        Maps shows the route. The route is planned with OpenStreetMap, so it can differ slightly from the route Apple
        Maps shows.

        The location is moved to the start of the route first. Then Apple Maps navigates to the destination, and the
        device starts moving at the given speed. On a simulator, turn-by-turn navigation is not available, so Apple Maps
        shows the directions instead.

        This method returns once the device starts moving. Use get_route_simulator() to change the speed or to wait
        until the destination is reached (wait_until_route_finished()), and stop_route() to stop the route and reset the
        location of the device.

        :param from_query: The place to start from, e.g. 'Louvre, Paris'.
        :param to_query: The destination, e.g. 'Eiffel Tower, Paris'.
        :param speed: The speed in km/h.
        :param transport_type: The type of transport to use. Public transport (TRANSIT) is not supported.
        """
        if transport_type not in ROUTE_TRANSPORT_MODES:
            raise ValueError(f'Cannot simulate a route by {transport_type.name}, use one of '
                             f'{[t.name for t in ROUTE_TRANSPORT_MODES]}')
        logger.info(f'Starting route from {from_query} to {to_query} by {transport_type.name} at {speed} km/h')
        # stand still at the start of the route while Apple Maps plans it
        self.route_simulator.update_speed(0)
        self.route_simulator.execute_route_with_queries(from_query, to_query, ROUTE_TRANSPORT_MODES[transport_type])
        sleep(2)
        self.get_directions(to_query, transport_type)
        _wait_for(self.driver, GO_BUTTON)
        if self.driver.is_present(GO_BUTTON):
            self.driver.click(GO_BUTTON)
            sleep(2)
            self.current_state = self.navigation_state
        else:
            logger.info('Navigation is not available, only showing the directions')
        self.route_simulator.update_speed(speed)

    def stop_route(self):
        """
        Stops traveling the route started with start_route(), ends the navigation in Apple Maps if it is still active,
        and resets the location of the device to its real location.
        """
        self.route_simulator.stop_route()
        if self.driver.is_present(NAVIGATION_TRAY):
            self.end_navigation()
        self.driver.execute_script('mobile: resetSimulatedLocation')
        logger.info('Stopped route')
