import random
import threading
import time
from time import sleep
from typing import Optional, List

import geopy.distance
import gpxpy
import requests
from geopy import Point
from gpxpy.gpx import GPXTrackPoint

# The OSRM servers of OpenStreetMap Germany (FOSSGIS), which have a routing profile per transport mode
OSRM_URL = "https://routing.openstreetmap.de/routed-{transport_mode}/route/v1/driving/{start};{end}"
TRANSPORT_MODES = ('car', 'bike', 'foot')


def read_gpx(gpx_file: str) -> List[Point]:
    """
    Reads the points of all tracks in a gpx file.

    :param gpx_file: path to a gpx file defining the route to travel.
    :return: the points of the route.
    """
    points: [GPXTrackPoint] = []
    with open(gpx_file, 'r') as opened_file:
        gpx = gpxpy.parse(opened_file)
        for track in gpx.tracks:
            for segment in track.segments:
                points.extend(segment.points)
    # Do not include p.elevation because calculating distances between points with an elevation is not supported by
    # geopy
    return [Point(p.latitude, p.longitude, 0) for p in points]


def plan_route(start_loc: str, destination: str, transport_mode: str) -> List[Point]:
    """
    Plans a route between two places. The places are looked up with Nominatim, the route is planned with OSRM, both
    from OpenStreetMap.

    :param start_loc: the place to start from, e.g. 'Louvre, Paris'.
    :param destination: the destination, e.g. 'Eiffel Tower, Paris'.
    :param transport_mode: the mode of transportation: 'car', 'foot' or 'bike'.
    :return: the points of the route.
    """
    if transport_mode not in TRANSPORT_MODES:
        raise ValueError(f"Unsupported transport mode '{transport_mode}', use one of {TRANSPORT_MODES}")
    geocoder = geopy.get_geocoder_for_service("nominatim")(user_agent="Maps")
    start_location = geocoder.geocode(start_loc)
    destination_location = geocoder.geocode(destination)
    if start_location is None or destination_location is None:
        raise ValueError(f"Could not find '{start_loc if start_location is None else destination}' in OpenStreetMap")
    return _get_osm_route(start_location.latitude, start_location.longitude,
                          destination_location.latitude, destination_location.longitude, transport_mode)


def _get_osm_route(start_lat, start_lon, end_lat, end_lon, transport_mode: str = 'car') -> List[Point]:
    # OSRM wants lon,lat (instead of lat,lon)
    url = OSRM_URL.format(transport_mode=transport_mode, start=f"{start_lon},{start_lat}",
                          end=f"{end_lon},{end_lat}")
    params = {
        "overview": "full",  # full geometry of the route, otherwise we don't get all points
        "geometries": "geojson"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    if not data.get("routes"):
        raise ValueError("No route found between the given points.")

    route = data["routes"][0]["geometry"]["coordinates"]
    # Convert from (lon, lat) to Points containing (lat, lon)
    return [Point(lat, lon) for lon, lat in route]


class RouteSimulator:
    """
    Spoofs the location of a device along a route. Used by the PumaDriver: start routes with the start_route_...
    methods of the PumaDriver, not with this class.

    The location is set with the set_location method of the given driver, so it works on Android and iOS.
    """

    def __init__(self, driver, location_update_interval: float = 1):
        """
        :param driver: the PumaDriver of the device, used to set the location.
        :param location_update_interval: (optional) how often the location needs to be updated. default once per second
        """
        self.driver = driver
        self.location_update_interval = location_update_interval
        self.update_speed(0)
        # fields relating to current and future locations
        self._current_location: Optional[Point] = None
        self._next_locations: [Point] = []
        self._last_location_update: Optional[float] = None
        self._threads: List[threading.Thread] = []

    def update_speed(self, speed: float, variance_absolute: float = 0, variance_relative: float = 0.0):
        """
        Updates the speed at which the route is being traveled. Optionally, the speed can be variable by giving
        either an absolute or relative variance.
        This method can be called to update the speed as a route is being traveled.

        :param speed: The (average) speed in km/h.
        :param variance_absolute: The absolute variance in speed. A value of 5 means the speed will vary between -5kmph
        and +5kmph of the given speed.
        :param variance_relative: The relative variance in speed. A value of 0.05 means the speed will vary between 95%
        and 105% of the given speed.
        """
        self._current_speed = speed
        if variance_absolute:
            self._target_speed_lower_bound = max(0.0, speed - variance_absolute)
            self._target_speed_upper_bound = max(0.0, speed + variance_absolute)
            return
        if variance_relative:
            self._target_speed_lower_bound = speed * max(0.0, 1 - variance_relative)
            self._target_speed_upper_bound = speed * max(0.0, 1 + variance_relative)
            return
        # no variance: constant speed
        self._target_speed_lower_bound = speed
        self._target_speed_upper_bound = speed

    def execute_route_with_points(self, point_list: [Point]):
        """
        Moves the device to the first point, and starts traveling along the other points.

        :param point_list: the list with points of the route
        """
        if not point_list:
            raise ValueError("A route needs at least one point")
        self._next_locations = list(point_list)
        # set the first location before the threads start, so the location thread does not exit right away
        self._current_location = self._next_locations.pop(0)
        self._last_location_update = time.time()
        self._start_route()

    def _start_route(self):
        """
        Starts two new threads to update the location according to the given route.
        """
        self._threads = [threading.Thread(target=target, daemon=True) for target in (self._route_loop, self._appium_loop)]
        for thread in self._threads:
            thread.start()

    def is_route_finished(self) -> bool:
        """
        :return: True if no route is being traveled: the end of the route has been reached, the route was stopped, or
        no route was started. After reaching the end, the device stays at the last location until stop_route() is called.
        """
        return not self._next_locations

    def wait_until_route_finished(self, timeout: float = None) -> bool:
        """
        Waits until the end of the route has been reached.

        :param timeout: (optional) the maximum number of seconds to wait. By default, waits until the route is finished.
        :return: True if the route is finished, False if the timeout expired first.
        """
        start = time.time()
        while not self.is_route_finished():
            if timeout is not None and time.time() - start > timeout:
                return False
            sleep(1)
        return True

    def stop_route(self):
        """
        Stops traversing the current route. This will clear all stored locations, so the route cannot be resumed.
        If you wish to pause while on the route, simply update the speed to 0.
        """
        self._next_locations = None
        self._current_location = None
        # wait for a location update that is in progress, so it cannot undo a reset of the location after this
        for thread in self._threads:
            thread.join(timeout=10)

    # The following methods are for internal use only, and are for traveling along the loaded route.
    def _travel_distance(self, distance_to_travel):
        """
        This method ONLY updates self._current_location along the loaded route, given a distance that should be
        traveled. This methods does nothing if there are no next locations, or if the given distance is not strictly
        positive.
        """
        # only travel if there's a waypoint as next location, and if distance is > 0
        if not self._next_locations or distance_to_travel <= 0:
            return
        distance_to_next_point = geopy.distance.geodesic(self._current_location, self._next_locations[0]).m
        # distance to next point < distance to travel: recursive function call.
        if distance_to_next_point < distance_to_travel:
            self._current_location = self._next_locations.pop(0)
            self._travel_distance(distance_to_travel - distance_to_next_point)
        else:
            # travel the required distance along the line between the current position and the next position
            percent_to_go = distance_to_travel / distance_to_next_point
            pos1 = self._current_location
            pos2 = self._next_locations[0]
            next_pos = Point(
                pos1.latitude + (pos2.latitude - pos1.latitude) * percent_to_go,
                pos1.longitude + (pos2.longitude - pos1.longitude) * percent_to_go,
                pos1.altitude + (pos2.altitude - pos1.altitude) * percent_to_go
            )
            self._current_location = next_pos

    def _update_location(self):
        """
        This method ONLY updates the _current_location and _last_location_update fields. it does not spoof the location.
        This method will look at the current speed and how long ago the location was last updated, and travel a distance
        according to said speed and duration.
        This method does nothing if there is no next location.
        """
        if not self._next_locations or not self._current_location:
            return
        now = time.time()
        time_elapsed = now - self._last_location_update
        # calculate current speed with variance
        self._current_speed = random.uniform(self._target_speed_lower_bound, self._target_speed_upper_bound)
        distance_to_travel = time_elapsed * ((self._current_speed * 1000) / 3600)  # km/h to m/s
        self._travel_distance(distance_to_travel)
        self._last_location_update = now

    def _route_loop(self):
        """
        This method will travel the loaded route, and stop looping when the last point is reached.
        The loop will attempt to execute every location_update_interval seconds (with a minimum of once every 0.1s)
        """
        while self._next_locations:
            start = time.time()
            self._update_location()
            delay = time.time() - start
            sleep(max(self.location_update_interval - delay, 0.1))

    def _appium_loop(self):
        """
        This method will loop and spoof the location through the driver.
        It will exit if there is no set _current_location.
        The loop will attempt to execute every location_update_interval seconds (with a minimum of once every 0.1s)
        """
        while True:
            # read once: stop_route() can clear it from another thread
            location = self._current_location
            if not location:
                return
            start = time.time()
            self.driver.set_location(location.latitude, location.longitude, location.altitude, self._current_speed)
            delay = time.time() - start
            sleep(max(self.location_update_interval - delay, 0.1))
