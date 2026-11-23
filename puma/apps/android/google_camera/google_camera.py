from time import sleep

from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.puma_driver import PumaDriver, supported_version
from puma.state_graph.state_graph import StateGraph
from puma.state_graph.state import SimpleState, compose_clicks


PHOTO_STATE_TAKE_PHOTO = '//android.widget.ImageButton[@content-desc="Take photo"]'
PHOTO_STATE_PHOTO = '//android.widget.TextView[@content-desc="Photo"]'
PHOTO_STATE_SWITCH_TO_VIDEO = '//android.view.View[@resource-id="video_supermode"]'
PHOTO_STATE_SHUTTER_BUTTON = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]'

VIDEO_STATE_VIDEO = '//android.widget.TextView[@content-desc="Video"]'
VIDEO_STATE_TAKE_VIDEO = '//android.widget.ImageButton[@content-desc="Start video"]'
VIDEO_STATE_SWITCH_TO_PHOTO = '//android.view.View[@resource-id="camera_supermode"]'
VIDEO_STATE_STOP_VIDEO = '//android.widget.ImageButton[@content-desc="Stop video"]'

SWITCH_CAMERA_BUTTON = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/camera_switch_button"]'

SETTINGS_STATE_CAMERA_SETTINGS = '//android.widget.FrameLayout[@content-desc="Camera settings"]'
SETTINGS_STATE_TITLE = '//android.widget.TextView[@resource-id="android:id/title" and @text="General"]'

OPEN_OPTIONS_MENU = '//android.widget.Button[@resource-id="com.google.android.GoogleCamera:id/options_entry_button"]'
OPEN_SETTINGS = '//android.widget.Button[@content-desc="Open settings"]'
OPTIONS_PANEL = '//android.widget.LinearLayout[@resource-id="com.google.android.GoogleCamera:id/pinned_panel"]'

POPUP_TURN_ON_BY_DEFAULT = '//android.widget.TextView[@text="Turned on by default"]'
POPUP_BOTTOMSHEET = '//android.widget.LinearLayout[@resource-id="com.google.android.GoogleCamera:id/bottomsheet_container"]'
DONE = '//android.widget.Button[@text="Done"]'

APPLICATION_PACKAGE = 'com.google.android.GoogleCamera'


class _BackPopUpHandler(PopUpHandler):
    def dismiss_popup(self, driver: PumaDriver):
        driver.gtl_logger.info('Dismissing pop-up with back')
        driver.back()


def _go_to_settings(driver: PumaDriver):
    driver.click(OPEN_OPTIONS_MENU)
    # the options panel slides up: a click during the animation lands on an option below the settings button
    sleep(1)
    driver.click(OPEN_SETTINGS)
    # the settings open in a new activity, which takes a moment
    sleep(1)


def _close_settings(driver: PumaDriver):
    driver.back()
    # the options panel is still open and covers the shutter and the switch between photo and video
    if driver.is_present(OPTIONS_PANEL, 2):
        driver.back()


@supported_version("10.3.183.888945295.14")
class GoogleCamera(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the Google Camera application.

    This class uses a state machine approach to manage transitions between different states
    of the Google Camera user interface. It provides methods to navigate between states,
    take pictures, and record videos.
    """

    # Define states
    photo = SimpleState(xpaths=[PHOTO_STATE_TAKE_PHOTO,
                                PHOTO_STATE_PHOTO],
                        initial_state=True)
    video = SimpleState(xpaths=[VIDEO_STATE_VIDEO,
                                VIDEO_STATE_TAKE_VIDEO])
    settings = SimpleState(xpaths=[SETTINGS_STATE_CAMERA_SETTINGS,
                                   SETTINGS_STATE_TITLE],
                           parent_state=photo,
                           parent_state_transition=_close_settings)  # note that settings does not have a real parent state. the back restores the last state before navigating to settings.

    # Define transitions. Only forward transitions are needed, back transitions are added automatically
    photo.to(video, compose_clicks([PHOTO_STATE_SWITCH_TO_VIDEO], name='go_to_video'))
    video.to(photo, compose_clicks([VIDEO_STATE_SWITCH_TO_PHOTO], name='go_to_camera'))
    photo.to(settings, _go_to_settings)
    video.to(settings, _go_to_settings)

    def __init__(self, device_udid, **kwargs):
        """
        Initializes the GoogleCamera with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE, **kwargs)
        self.add_popup_handler(PopUpHandler([POPUP_TURN_ON_BY_DEFAULT], [DONE]))
        # info sheets, such as the one about the palm timer, do not all have a button to close them
        self.add_popup_handler(_BackPopUpHandler([POPUP_BOTTOMSHEET], []))

    @action(photo)
    def take_picture(self, front_camera: bool = None):
        """
        Takes a single picture.

        This method ensures the correct camera view (front or back) and then takes a picture.

        :param front_camera: If True, uses the front camera; if False, uses the back camera; if None, no change is made.
        """
        self._ensure_correct_camera_view(front_camera)
        self.driver.click(PHOTO_STATE_SHUTTER_BUTTON)

    @action(video)
    def record_video(self, duration, front_camera: bool = None):
        """
        Records a video for the given duration.

        This method ensures the correct camera view (front or back) and then starts and stops video recording.

        :param duration: The duration in seconds to record the video.
        :param front_camera: If True, uses the front camera; if False, uses the back camera; if None, no change is made.
        """
        self._ensure_correct_camera_view(front_camera)
        self.driver.click(VIDEO_STATE_TAKE_VIDEO)
        sleep(duration)
        self.driver.click(VIDEO_STATE_STOP_VIDEO)

    def _ensure_correct_camera_view(self, front_camera):
        """
        Ensures the correct camera view (front or back) is selected.

        :param front_camera: If True, ensures the front camera is selected; if False, ensures the back camera is selected.
        """
        if front_camera is None:
            return
        switch_button = self.driver.get_element(SWITCH_CAMERA_BUTTON)
        currently_in_front = 'front' not in switch_button.get_attribute("content-desc")
        if currently_in_front != front_camera:
            switch_button.click()
