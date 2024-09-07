import re
from time import sleep
from typing import Dict

import geopy.distance
import gpxpy
import gpxpy.gpx
from gpxpy.gpx import GPXTrackPoint
from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.appium_actions import AndroidAppiumActions

UPDATE_TIME = 1
SPEED = 80  # km/h
SECONDS_PER_HOUR = 3600


def extrapolate_over_points(file):
    distance_to_travel = UPDATE_TIME * ((SPEED * 1000) / SECONDS_PER_HOUR)
    print("distance to travel " + str(distance_to_travel))
    travelled = 0
    gpx = gpxpy.parse(open(file, 'r'))
    for track in gpx.tracks:
        for segment in track.segments:
            point_index = 0
            points = segment.points
            current_position = points[point_index]
            yield current_position.latitude, current_position.longitude, current_position.elevation
            while point_index + 1 < len(points):
                next_travel_point = points[point_index + 1]
                distance_to_next_travel_point = geopy.distance.geodesic((current_position.latitude, current_position.longitude), (next_travel_point.latitude, next_travel_point.longitude)).m
                print(distance_to_next_travel_point)
                if distance_to_next_travel_point < distance_to_travel - travelled:
                    travelled += distance_to_next_travel_point
                    current_position = next_travel_point
                    point_index += 1
                else:
                    percent_to_go = (distance_to_travel - travelled) / distance_to_next_travel_point
                    x_dist = abs(float(current_position.latitude) - float(next_travel_point.latitude))
                    y_dist = abs(float(current_position.longitude) - float(next_travel_point.longitude))
                    if current_position.latitude > next_travel_point.latitude:
                        next_x = current_position.latitude - x_dist * percent_to_go
                    else:
                        next_x = current_position.latitude + x_dist * percent_to_go
                    if current_position.longitude > next_travel_point.longitude:
                        next_y = current_position.longitude - y_dist * percent_to_go
                    else:
                        next_y = current_position.longitude + y_dist * percent_to_go
                    travelled = 0
                    current_position = GPXTrackPoint(next_x, next_y, current_position.elevation)
                    yield current_position.latitude, current_position.longitude, current_position.elevation


class GoogleMapsActions(AndroidAppiumActions):
    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for WhatsApp Android using Appium. Can be used with an emulator or real device attached to the computer.
        """
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      'com.google.android.apps.maps',
                                      'com.google.android.maps.MapsActivity',
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def select_search(self):
        element = self.driver.find_element(by=AppiumBy.ID, value="com.google.android.apps.maps:id/search_omnibox_text_box")
        element.click()

    def search(self, search_text: str):
        self.select_search()
        sleep(1)
        element = self.driver.find_element(by=AppiumBy.ID, value="com.google.android.apps.maps:id/search_omnibox_edit_text")
        sleep(1)
        element.send_keys(search_text)
        self.driver.press_keycode(66)  # Enter

    def locate_self(self):
        element = self.driver.find_element(by=AppiumBy.ID, value="com.google.android.apps.maps:id/mylocation_button")
        element.click()

    def select_directions(self):
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.view.View[@content-desc="Directions to Murrenhof, Herenweg 20"]').click()

    def start_directions(self):
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.Button[@content-desc="Start driving navigation"]').click()

    def set_location(self, lat, lon, alt):
        self.driver.set_location(lat, lon, alt)

    def get_current_speed_limit(self):
        try:
            if self.is_present('//android.widget.RelativeLayout[contains(@content-desc,"Speed limit")]'):
                speed_limit_element = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.RelativeLayout[contains(@content-desc,"Speed limit")]')
                regex_result = re.search("Speed\\slimit\\s(\\d+)\\skilometres", speed_limit_element.get_attribute('content-desc'))
                speed = int(regex_result.group(1))
                return speed
        except:
            return 60
        return 60

    def execute_directions_extrapolate_over_points(self, file):
        for point in extrapolate_over_points(file):
            print(point)
            sleep(UPDATE_TIME)
            self.set_location(point[0], point[1], point[2])


if __name__ == '__main__':
    google_maps = GoogleMapsActions("emulator-5554")
    google_maps.set_location(4, 52, 0)
    sleep(3)
    google_maps.set_location(52.2671224, 4.9628846, 0)
    sleep(1)
    google_maps.locate_self()
    google_maps.search('Murrenhof, Herenweg 20, 3625 AE Breukeleveen')
    sleep(2)
    google_maps.select_directions()
    sleep(2)
    google_maps.start_directions()
    sleep(3)
    google_maps.execute_directions_extrapolate_over_points('puma/apps/android/google_maps/low_points.gpx')
