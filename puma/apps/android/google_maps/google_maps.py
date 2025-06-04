from enum import Enum
from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version
from puma.utils.route_simulator import RouteSimulator

GOOGLE_MAPS_PACKAGE = 'com.google.android.apps.maps'


class TransportType(Enum):
    CAR = "car"
    BIKE = "bike"


@supported_version("11.119.0101")
class GoogleMapsActions(AndroidAppiumActions):
    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      GOOGLE_MAPS_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)
        self.route_simulator = RouteSimulator(self, 0)

    def _has_search_box(self):
        return self.app_open() and self.is_present('//android.widget.TextView[@text="Search here"]')

    def _ensure_at_start(self):
        while not self._has_search_box():
            self.driver.back()
            if not self.app_open():
                self.activate_app()

    def search_place(self, search_string: str):
        self._ensure_at_start()
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.TextView[@text="Search here"]').click()
        search_box_xpath = '//android.widget.EditText[@resource-id="com.google.android.apps.maps:id/search_omnibox_edit_text"]'
        self.driver.find_element(by=AppiumBy.XPATH, value=search_box_xpath).send_keys(search_string)
        first_result = '//android.support.v7.widget.RecyclerView[@resource-id="com.google.android.apps.maps:id/typed_suggest_container"]/android.widget.LinearLayout[1]'
        self.driver.find_element(by=AppiumBy.XPATH, value=first_result).click()

    def start_navigation(self, search_string: str, transport_type: TransportType = TransportType.CAR, time_to_wait=10):
        self.search_place(search_string)
        directions_xpath = '//android.widget.Button[starts-with(@content-desc, "Directions to")]'
        self.driver.find_element(by=AppiumBy.XPATH, value=directions_xpath).click()
        if transport_type == TransportType.CAR:
            mode = 'Driving mode'
        elif transport_type == TransportType.BIKE:
            mode = 'Bicycling mode'
        multiple_choices_header = '//android.widget.LinearLayout[@resource-id="com.google.android.apps.maps:id/destination_list_header"]'
        if self.is_present(multiple_choices_header):
            # select first option
            first_option = '//android.support.v7.widget.RecyclerView[@resource-id="com.google.android.apps.maps:id/recycler_view"]/android.widget.LinearLayout[1]'
            self.driver.find_element(by=AppiumBy.XPATH, value=first_option).click()
        mode_xpath = f'//android.widget.LinearLayout[starts-with(@content-desc, "{mode}")]'
        self.driver.find_element(by=AppiumBy.XPATH, value=mode_xpath).click()
        start_xpath = '//android.widget.Button[@content-desc="Start driving navigation"]'
        for i in range(time_to_wait):
            if self.is_present(start_xpath):
                self.driver.find_element(by=AppiumBy.XPATH, value=start_xpath).click()
                return
            else:
                sleep(1)
        raise Exception(f'Route was not loaded after {time_to_wait} seconds')

    def start_route(self, from_query: str, to_query: str, speed: int,
                    transport_type: TransportType = TransportType.CAR):
        self.route_simulator.update_speed(0)
        osm_mode = 'car' if transport_type == TransportType.CAR else 'bike'
        self.route_simulator.execute_route_with_queries(from_query, to_query, osm_mode)
        self.start_navigation(to_query, transport_type)
        self.route_simulator.update_speed(speed)
