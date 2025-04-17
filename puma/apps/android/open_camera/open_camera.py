from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version

OPEN_CAMERA_PACKAGE = 'net.sourceforge.opencamera'


@supported_version("1.53.1")
class OpenCameraActions(AndroidAppiumActions):
    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      OPEN_CAMERA_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def _click_shutter(self):
        """
        Presses the shutter to take a picture or start/stop recording.
        """
        xpath = '//android.widget.ImageButton[@resource-id="net.sourceforge.opencamera:id/take_photo"]'
        shutter = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        shutter.click()

    def _switch_to_photo_mode(self):
        """
        If in video mode, switches to photo mode.
        """
        photo_mode_button = '//android.widget.ImageButton[@content-desc="Switch to photo mode"]'
        if self.is_present(photo_mode_button):
            button = self.driver.find_element(by=AppiumBy.XPATH, value=photo_mode_button)
            button.click()

    def _switch_to_video_mode(self):
        """
        If in photo mode, switches to video mode.
        """
        video_mode_button = '//android.widget.ImageButton[@content-desc="Switch to video mode"]'
        if self.is_present(video_mode_button):
            button = self.driver.find_element(by=AppiumBy.XPATH, value=video_mode_button)
            button.click()

    def take_picture(self):
        """
        Takes a picture.
        """
        self._switch_to_photo_mode()
        self._click_shutter()

    def switch_camera(self):
        """
        Switches between the front and back camera.
        """
        xpath = '//android.widget.ImageButton[@resource-id="net.sourceforge.opencamera:id/switch_camera"]'
        switch_camera_button = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        switch_camera_button.click()

    def take_video(self, duration: int):
        """
        Takes a video of a given duration.
        """
        self._switch_to_video_mode()
        self._click_shutter()
        try:
            sleep(duration)
        finally:
            self._click_shutter()

    def zoom(self, zoom_amount: float):
        """
        Zooms to a given level between 0.0 (zoomed out completely) and 1.0 (zoomed in completely).
        """
        if zoom_amount < 0 or zoom_amount > 1:
            raise ValueError(f'Invalid zoom level: {zoom_amount}. Zoom level needs to be between 0.0 and 1.0')
        xpath = '//android.widget.SeekBar[@content-desc="Zoom"]'
        zoom_slider = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        x = zoom_slider.location.get('x')
        y = zoom_slider.location.get('y')
        width = zoom_slider.size.get('width')
        height = zoom_slider.size.get('height')
        # We need to click slightly inside the bounds of the slider, so we don't use the full height
        height = int(0.95 * height)
        x_to_tap = x + (width // 2)
        y_to_tap = y + (height * (1 - zoom_amount))
        self.driver.tap([(x_to_tap, y_to_tap)])
