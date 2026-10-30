from enum import Enum
from time import sleep

from puma.apps.android.google_maps.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, supported_version
from puma.state_graph.state import SimpleState, compose_clicks
from puma.state_graph.state_graph import StateGraph


class TransportType(Enum):
    """
    The types of transport Google Maps can navigate with. The value is the start of the content description of the
    button that selects it.
    """
    CAR = 'Driving mode'
    BIKE = 'Bicycling mode'


# The routing profiles used by the route simulator for each transport type
ROUTE_TRANSPORT_MODES = {
    TransportType.CAR: 'car',
    TransportType.BIKE: 'bike',
}


def _search(driver: PumaDriver, search_string: str):
    """
    Searches for a place and opens the first suggestion.
    """
    driver.click(HOME_SEARCH_BOX)
    driver.send_keys(SEARCH_EDIT_TEXT, search_string)
    driver.wait_until_present(SEARCH_FIRST_SUGGESTION, timeout=10)
    # The suggestions are updated for a moment after they appear, and nothing in the UI shows when they are final
    sleep(1)
    driver.gtl_logger.info('Opening the first suggestion')
    driver.click(SEARCH_FIRST_SUGGESTION)
    driver.wait_until_present(PLACE_DIRECTIONS_BUTTON, timeout=10)


def _open_directions(driver: PumaDriver, search_string: str, transport_type: TransportType):
    """
    Searches for a place, and shows the directions from the current location of the device to that place.
    """
    _search(driver, search_string)
    driver.gtl_logger.info('Pressing directions button')
    driver.click(PLACE_DIRECTIONS_BUTTON)
    driver.wait_until_present(DIRECTIONS_DRIVING_MODE, timeout=10)
    driver.gtl_logger.info(f'Selecting transport type {transport_type.name}')
    driver.click(transport_mode_button(transport_type.value))
    driver.wait_until_present(selected_transport_mode_button(transport_type.value), timeout=5)


@supported_version("26.41.00")
class GoogleMaps(StateGraph):
    """
    A class representing the Google Maps application on Android.

    Google Maps plans routes from the location of the device. To travel a route, use start_route(), which spoofs the
    location of the device along the route. The route can then be controlled through the driver, e.g.
    `maps.driver.update_route_speed(50)`.
    """

    # States
    home_state = SimpleState(xpaths=[HOME_SEARCH_BOX, HOME_EXPLORE_TAB], initial_state=True)
    place_state = SimpleState(xpaths=[PLACE_DIRECTIONS_BUTTON, CARD_CLOSE_BUTTON],
                              parent_state=home_state,
                              parent_state_transition=compose_clicks([CARD_CLOSE_BUTTON], 'close_place', wait=1))
    directions_state = SimpleState(xpaths=[DIRECTIONS_START_LOCATION, DIRECTIONS_DRIVING_MODE, CARD_CLOSE_BUTTON],
                                   parent_state=place_state,
                                   parent_state_transition=compose_clicks([CARD_CLOSE_BUTTON], 'close_directions', wait=1))
    navigation_state = SimpleState(xpaths=[NAVIGATION_TIME_REMAINING, NAVIGATION_CLOSE_BUTTON],
                                   parent_state=directions_state,
                                   parent_state_transition=compose_clicks([NAVIGATION_CLOSE_BUTTON],
                                                                          'close_navigation', wait=1))

    # Transitions
    home_state.to(place_state, _search)
    place_state.to(directions_state, compose_clicks([PLACE_DIRECTIONS_BUTTON], 'open_directions'))
    directions_state.to(navigation_state, compose_clicks([DIRECTIONS_START_BUTTON], 'start_navigation'))

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Google Maps with a device UDID.

        :param device_udid: The unique device identifier of the Android device.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, GOOGLE_MAPS_PACKAGE, **kwargs)

    @action(home_state, end_state=place_state)
    def search_place(self, search_string: str):
        """
        Searches for a place, and opens the first suggestion.

        :param search_string: The place to search for, e.g. 'Eiffel Tower' or an address.
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
    def start_navigation(self, search_string: str, transport_type: TransportType = TransportType.CAR,
                         time_to_wait: int = 10):
        """
        Searches for a place, and starts navigating from the current location of the device to that place.

        :param search_string: The place to search for.
        :param transport_type: The type of transport to use.
        :param time_to_wait: The number of seconds to wait for Google Maps to plan the route.
        """
        _open_directions(self.driver, search_string, transport_type)
        if not self.driver.wait_until_present(DIRECTIONS_START_BUTTON, timeout=time_to_wait):
            raise TimeoutError(f'Route was not loaded after {time_to_wait} seconds')
        self.gtl_logger.info('Pressing start button to start navigation')
        self.driver.click(DIRECTIONS_START_BUTTON)
        self.driver.wait_until_present(NAVIGATION_TIME_REMAINING, timeout=10)

    def end_navigation(self):
        """
        Ends turn-by-turn navigation, if it is active. Google Maps then shows the directions.
        """
        if not self.navigation_state.validate(self.driver):
            self.gtl_logger.info('Navigation is not active, not ending it')
            return
        self.current_state = self.navigation_state
        self.go_to_state(self.directions_state)

    def start_route(self, from_query: str, to_query: str, speed: float,
                    transport_type: TransportType = TransportType.CAR):
        """
        Travels a route from one place to another, by spoofing the location of the device along the route, while Google
        Maps navigates to the destination. The route is planned with OpenStreetMap, so it can differ slightly from the
        route Google Maps shows.

        The location is moved to the start of the route first. Then Google Maps navigates to the destination, and the
        device starts moving at the given speed. This method returns once the device starts moving. Use the driver to
        change the speed (driver.update_route_speed()) or to wait until the destination is reached
        (driver.wait_until_route_finished()), and stop_route() to stop.

        :param from_query: The place to start from, e.g. 'Louvre, Paris'.
        :param to_query: The destination, e.g. 'Eiffel Tower, Paris'.
        :param speed: The speed in km/h.
        :param transport_type: The type of transport to use.
        """
        # stand still at the start of the route while Google Maps plans it
        self.driver.start_route_with_queries(from_query, to_query, ROUTE_TRANSPORT_MODES[transport_type], 0)
        try:
            # Google Maps takes a moment to pick up the new location, which is not shown in the UI
            sleep(2)
            self.start_navigation(to_query, transport_type)
        except Exception:
            self.driver.stop_route()
            raise
        self.driver.update_route_speed(speed)

    def stop_route(self):
        """
        Stops traveling the route started with start_route(), ends the navigation in Google Maps if it is still active,
        and resets the location of the device to its real location.
        """
        self.driver.stop_route()
        self.end_navigation()
