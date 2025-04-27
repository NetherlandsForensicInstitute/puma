from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version

GOOGLE_CAMERA_PACKAGE = 'com.google.android.GoogleCamera'


@supported_version("9.8.102")
class GoogleCameraActions(AndroidAppiumActions):
    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      GOOGLE_CAMERA_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def take_picture(self):
        """
        Takes a single picture.
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]'
        shutter = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        shutter.click()

    def switch_camera(self):
        """
        Switches between the front and rear camera.
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/camera_switch_button"]'
        button = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        button.click()
