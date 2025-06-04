from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy
from statemachine import StateMachine
from statemachine.transition_list import TransitionList

from puma.apps.android.fsm_test.fsm.puma_fsm import PumaState
from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version
from puma.apps.android.fsm_test.util.fsm_util import make_back_action, action, find_shortest_path

GOOGLE_CAMERA_PACKAGE = 'com.google.android.GoogleCamera'

@supported_version("9.8.102")
class GoogleCameraFsm(StateMachine, AndroidAppiumActions):
    back = TransitionList()
    picture_rear = PumaState(initial=True)
    picture_front = PumaState()
    video_rear = PumaState()
    video_front = PumaState()
    camera_setting = PumaState(parent=make_back_action(back, picture_rear))

    switch_camera = (
            video_rear.to(video_front)
            | video_front.to(video_rear)
            | picture_front.to(picture_rear)
            | picture_rear.to(picture_front)
    )

    switch_to_video = (
        picture_rear.to(video_rear)
        | picture_front.to(picture_front)
    )

    switch_to_picture = (
        video_rear.to(picture_rear)
        | video_front.to(picture_front)
    )

    open_settings = (
        picture_rear.to(camera_setting)
        | picture_front.to(camera_setting)
        | video_rear.to(camera_setting)
        | video_front.to(camera_setting)
    )

    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for Google Camera using Appium and a finite state machine.
        Can be used with an emulator or real device attached to the computer.
        """
        StateMachine.__init__(self)
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      GOOGLE_CAMERA_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    # Actions
    @action(picture_rear)
    def take_picture_rear(self):
        """
        Takes a single picture.
        """
        self.shutter_button()

    @action(picture_front)
    def take_picture_front(self):
        """
        Takes a single picture.
        """
        self.shutter_button()

    @action(video_rear)
    def take_video_rear(self, duration: int):
        """
        Takes a video with the rear camera.
        :param duration: the duration of the video
        """
        self.shutter_button()
        sleep(duration)
        self.shutter_button()

    @action(video_front)
    def take_video_front(self, duration: int):
        """
        Takes a video with the front camera.
        :param duration: the duration of the video
        """
        self.shutter_button()
        sleep(duration)
        self.shutter_button()

    # Transitions
    def before_switch_camera(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        """
        Switches between the front and rear camera.
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/camera_switch_button"]'
        button = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        button.click()

    def before_switch_to_video(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        """
        Switches from camera to video.
        """
        xpath = '//android.widget.TextView[@content-desc="Switch to Video Camera"]'
        button = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        button.click()

    def before_switch_to_picture(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        """
        Switches from camera to video.
        """
        xpath = '//android.widget.TextView[@content-desc="Switch to Camera Mode"]'
        button = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        button.click()

    def before_back(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        """
        Uses the back functionality of Android.
        """
        self.driver.back()

    # Utility methods
    def shutter_button(self):
        """
        Utility method for pressing the shutter button.
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]'
        shutter = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        shutter.click()


if __name__ == '__main__':
    c = GoogleCameraFsm('34281JEHN03866')
    # d = GoogleCameraFsm()
    # for t in c.current_state.transitions:
    #     print("Registered event:", t.event, "from:", t.source.id, "to:", t.target.id)

    c.take_picture_front()
    c.take_video_rear(3)
    c.take_picture_rear()
    c.take_video_front(3)

    path = find_shortest_path(c, GoogleCameraFsm.video_front)
    print("Shortest path to video_front:", [t.event for t in path])
    # path = find_shortest_path(d, "video_front")
    # print("Shortest path to video_front:", [t.event for t in path])
