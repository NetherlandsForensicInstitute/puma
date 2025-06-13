from time import sleep

from puma.state_graph.action import action
from puma.state_graph.state_graph import StateGraph
from puma.state_graph.state import SimpleState, compose_clicks
from puma.apps.android.appium_actions import supported_version

APPLICATION_PACKAGE = 'com.google.android.GoogleCamera'
@supported_version("8.8.225.510547499.09")
class GoogleCamera(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the Google Camera application.

    This class uses a state machine approach to manage transitions between different states
    of the Google Camera user interface. It provides methods to navigate between states,
    take pictures, and record videos.
    """

    # Define states
    photo = SimpleState(xpaths=['//android.widget.ImageButton[@content-desc="Take photo"]',
                                '//android.widget.TextView[@content-desc="Camera"]'],
                        initial_state=True)
    video = SimpleState(xpaths=['//android.widget.TextView[@content-desc="Video"]',
                                '//android.widget.ImageButton[@content-desc="Start video"]'])
    settings = SimpleState(xpaths=['//android.widget.TextView[@text="Camera settings"]',
                                   '//android.widget.TextView[@resource-id="android:id/title" and @text="General"]'],
                           parent_state=photo)  # note that settings does not have a real parent state. the back restores the last state before navigating to settings.

    # Define transitions. Only forward transitions are needed, back transitions are added automatically
    photo.to(video, compose_clicks(['//android.widget.TextView[@content-desc="Switch to Video Camera"]'], name='go_to_video'))
    video.to(photo, compose_clicks(['//android.widget.TextView[@content-desc="Switch to Camera Mode"]'], name='go_to_camera'))
    go_to_settings = compose_clicks(['//android.widget.ImageView[@content-desc="Open options menu"]',
                                     '//android.widget.Button[@content-desc="Open settings"]'],
                                    name= 'go_to_settings')
    photo.to(settings, go_to_settings)
    video.to(settings, go_to_settings)

    def __init__(self, device_udid):
        """
        Initializes the GoogleCamera with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        """
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)

    @action(photo)
    def take_picture(self, front_camera=None):
        """
        Takes a single picture.

        This method ensures the correct camera view (front or back) and then takes a picture.

        :param front_camera: If True, uses the front camera; if False, uses the back camera; if None, no change is made.
        """
        self._ensure_correct_camera_view(front_camera)
        self.driver.click('//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]')

    @action(video)
    def record_video(self, duration, front_camera=None):
        """
        Records a video for the given duration.

        This method ensures the correct camera view (front or back) and then starts and stops video recording.

        :param duration: The duration in seconds to record the video.
        :param front_camera: If True, uses the front camera; if False, uses the back camera; if None, no change is made.
        """
        self._ensure_correct_camera_view(front_camera)
        self.driver.click('//android.widget.ImageButton[@content-desc="Start video"]')
        sleep(duration)
        self.driver.click('//android.widget.ImageButton[@content-desc="Stop video"]')

    def _ensure_correct_camera_view(self, front_camera):
        """
        Ensures the correct camera view (front or back) is selected.

        :param front_camera: If True, ensures the front camera is selected; if False, ensures the back camera is selected.
        """
        if front_camera is None:
            return
        switch_button = self.driver.get_element('//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/camera_switch_button"]')
        currently_in_front = 'front' not in switch_button.get_attribute("content-desc")
        if currently_in_front != front_camera:
            switch_button.click()
#TODO remove main
if __name__ == "__main__":
    alice = GoogleCamera('34281JEHN03866')
    alice.take_picture(front_camera=True)
    alice.record_video(2, True)
    alice.take_picture(front_camera=False)
    alice.record_video(2, False)
    alice.go_to_state(GoogleCamera.settings)
