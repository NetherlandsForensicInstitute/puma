from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy
from typing_extensions import deprecated

from puma.apps.android import log_action
from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version
from puma.apps.android.open_camera import logger
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.state import State, SimpleState, compose_clicks
from puma.state_graph.state_graph import StateGraph

# Take photo/video screen
OPEN_CAMERA_PACKAGE = 'net.sourceforge.opencamera'
TAKE_PHOTO = '//android.widget.ImageButton[@resource-id="net.sourceforge.opencamera:id/take_photo" and @content-desc="Take Photo"]'
TAKE_VIDEO = '//android.widget.ImageButton[@resource-id="net.sourceforge.opencamera:id/take_photo" and @content-desc="Start recording video"]'
# Shutter button resource id is the same for photo and video
SHUTTER_BUTTON = '//android.widget.ImageButton[@resource-id="net.sourceforge.opencamera:id/take_photo"]'
PHOTO_MODE_XPATH = '//android.widget.ImageButton[@content-desc="Switch to photo mode"]'
VIDEO_MODE_XPATH = '//android.widget.ImageButton[@content-desc="Switch to video mode"]'
SWITCH_CAMERA_XPATH = '//android.widget.ImageButton[@resource-id="net.sourceforge.opencamera:id/switch_camera"]'
ZOOM_SEEKBAR_XPATH = '//android.widget.SeekBar[@content-desc="Zoom"]'

# Popups
CAMERA_PERMISSION_POPUP = (
    '//android.widget.TextView[@resource-id="com.android.permissioncontroller:id/permission_message" '
    'and @text="Allow Open Camera to take pictures and record video?"]')


@supported_version("1.55")
class OpenCamera(StateGraph):
    # States
    take_photo_state = SimpleState(xpaths=[TAKE_PHOTO, VIDEO_MODE_XPATH], initial_state=True)
    take_video_state = SimpleState(xpaths=[TAKE_VIDEO, PHOTO_MODE_XPATH])

    # Transitions
    take_photo_state.to(take_video_state, compose_clicks([VIDEO_MODE_XPATH], name='go_to_video_mode'))
    take_video_state.to(take_photo_state, compose_clicks([PHOTO_MODE_XPATH], name='go_to_photo_mode'))

    def __init__(self, device_udid):
        StateGraph.__init__(self, device_udid, OPEN_CAMERA_PACKAGE)

    @action(take_photo_state)
    def take_picture(self, front_camera: bool):
        self._ensure_correct_view(front_camera)
        self._click_shutter()

    @action(take_video_state)
    def take_video(self, duration: int, front_camera: bool):
        """
        Takes a video of a given duration.
        """
        self._ensure_correct_view(front_camera)
        self._click_shutter()
        try:
            sleep(duration)
        finally:
            self._click_shutter()

    @action(take_photo_state)
    def zoom_picture_mode(self, zoom_amount: float):
        """
        Zooms to a given level between 0.0 (zoomed out completely) and 1.0 (zoomed in completely) in picture mode.
        :param zoom_amount: The zoom level between 0.0 and 1.0
        """
        self._zoom(zoom_amount)

    @action(take_video_state)
    def zoom_video_mode(self, zoom_amount: float):
        """
        Zooms to a given level between 0.0 (zoomed out completely) and 1.0 (zoomed in completely) in video mode.
        :param zoom_amount: The zoom level between 0.0 and 1.0
        """
        self._zoom(zoom_amount)

    def _zoom(self, zoom_amount: float):
        """
        Zooms to a given level between 0.0 (zoomed out completely) and 1.0 (zoomed in completely).
        :param zoom_amount: The zoom level between 0.0 and 1.0
        """
        if zoom_amount < 0 or zoom_amount > 1:
            raise ValueError(f'Invalid zoom level: {zoom_amount}. Zoom level needs to be between 0.0 and 1.0')
        zoom_slider = self.driver.get_element(ZOOM_SEEKBAR_XPATH)
        x = zoom_slider.location.get('x')
        y = zoom_slider.location.get('y')
        width = zoom_slider.size.get('width')
        height = zoom_slider.size.get('height')
        # We need to click slightly inside the bounds of the slider, so we don't use the full height
        height = int(0.95 * height)
        x_to_tap = x + (width // 2)
        y_to_tap = y + (height * (1 - zoom_amount))
        self.driver.tap((x_to_tap, y_to_tap))

    def _click_shutter(self):
        """
        Presses the shutter to take a picture or start/stop recording.
        """
        self.driver.click(SHUTTER_BUTTON)

    def _ensure_correct_view(self, front_camera: bool):
        """
        Switches between the front and back camera.
        """
        switch_camera_button = self.driver.get_element(SWITCH_CAMERA_XPATH)
        currently_in_front = 'front' in switch_camera_button.get_attribute("content-desc")
        logger.info(f"Currently in front camera view: {currently_in_front}")
        if currently_in_front != front_camera:
            switch_camera_button.click()
            logger.info("Switched camera view")
