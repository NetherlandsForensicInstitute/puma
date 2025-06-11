from time import sleep

import puma.apps.android.FSMTEST_util.puma_fsm
from puma.apps.android.FSMTEST_util.puma_driver import PumaDriver
from puma.apps.android.FSMTEST_util.puma_fsm import PumaUIGraph, SimpleState, action, click

APPLICATION_PACKAGE = 'com.google.android.GoogleCamera'

class GoogleCamera(PumaUIGraph):

    # Define states
    photo = SimpleState("Camera",
                         xpaths=['//android.widget.ImageButton[@content-desc="Take photo"]',
                                 '//android.widget.TextView[@content-desc="Camera"]'],
                         initial_state=True)
    video = SimpleState("Video",
                         xpaths=['//android.widget.TextView[@content-desc="Video"]',
                                 '//android.widget.ImageButton[@content-desc="Start video"]'])
    settings = SimpleState("Settings",
                         xpaths=['//android.widget.TextView[@text="Camera settings"]',
                                 '//android.widget.TextView[@resource-id="android:id/title" and @text="General"]'],
                         parent_state=photo) # note that settings does not have a real parent state. the back restores the last state before navigating to settings.

    # Define transitions. Only forward transitions are needed, back transitions are added automatically
    photo.to(video, click(['//android.widget.TextView[@content-desc="Switch to Video Camera"]']))
    video.to(photo, click(['//android.widget.TextView[@content-desc="Switch to Camera Mode"]']))
    settings_xpaths = ['//android.widget.ImageView[@content-desc="Camera settings"]',
                       '//android.widget.Button[@content-desc="Open settings"]']
    photo.to(settings, click(settings_xpaths))
    video.to(settings, click(settings_xpaths))

    def __init__(self, device_udid):
        self.driver = PumaDriver(device_udid, APPLICATION_PACKAGE)
        PumaUIGraph.__init__(self, self.driver)

        # Optional: create your own app-specific popup handler
        # self.add_popup_handler(simple_popup_handler('test'))

    # Define your actions
    @action(photo)
    def take_picture(self, front_camera = None):
        """
        Takes a single picture.
        """
        self._ensure_correct_camera_view(front_camera)
        self.driver.click('//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]')

    @action(video)
    def record_video(self, duration, front_camera = None):
        """

        Takes a video for the given duration.
        :return:
        """
        self._ensure_correct_camera_view(front_camera)
        self.driver.click('//android.widget.ImageButton[@content-desc="Start video"]')
        sleep(duration)
        self.driver.click('//android.widget.ImageButton[@content-desc="Stop video"]')

    def _ensure_correct_camera_view(self, front_camera):
        if front_camera is None:
            return
        switch_button = self.driver.get_element('//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/camera_switch_button"]')
        currently_in_front =  FRONT in switch_button.get_attribute("content-desc")
        if currently_in_front != front_camera:
            switch_button.click()

if __name__ == "__main__":
    alice = GoogleCamera('32131JEHN38079')
    alice.take_picture(alice.front)
    alice.record_video(2, True)
    alice.take_picture(alice.back)
    alice.record_video(2, False)
    alice.go_to_state(GoogleCamera.settings)







