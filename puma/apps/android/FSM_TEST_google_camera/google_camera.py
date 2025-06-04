from collections import deque
from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy
from statemachine import StateMachine, State
from statemachine.transition import Transition
from statemachine.transition_list import TransitionList

from puma.apps.android.FSM_TEST_google_camera.puma_fsm import PumaState
from puma.apps.android.appium_actions import AndroidAppiumActions


GOOGLE_CAMERA_PACKAGE = 'com.google.android.GoogleCamera'


def action(first_state: PumaState): # TODO: Should probably be placed in some utility class
    def decorator(func):
        def wrapper(*args):
            while args[0].current_state != first_state:
                shortest_path = find_shortest_path(args[0], first_state)
                print(f'Taking the next step with event {shortest_path[0].event}')
                args[0].send(f"{shortest_path[0].event}", message="hello message")
            result = func(*args)
            print('should have executed the action by now')
            return result
        return wrapper
    return decorator

def make_back_action(back, state): # TODO: This can probably be placed in some utility class
    return lambda self: back.add_transitions(self.to(state))


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
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]'
        shutter = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        shutter.click()

    @action(picture_front)
    def take_picture_front(self):
        """
        Takes a single picture.
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]'
        shutter = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        shutter.click()

    @action(video_rear)
    def take_video_rear(self, duration: int):
        """
        Takes a video with the rear camera.
        :param duration: the duration of the video
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]'
        shutter = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        shutter.click()
        sleep(duration)
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]'
        shutter = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        shutter.click()

    @action(video_front)
    def take_video_front(self, duration: int):
        """
        Takes a video with the front camera.
        :param duration: the duration of the video
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]'
        shutter = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        shutter.click()
        sleep(duration)
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/shutter_button"]'
        shutter = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        shutter.click()

    # Transitions
    def before_switch_camera(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        """
        Switches between the front and rear camera.
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/camera_switch_button"]'
        button = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        button.click()

        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

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

    def before_switch_mode(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        """
        Switches between the front and rear camera.
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/camera_switch_button"]'
        button = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        button.click()

        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    def before_back(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        """
        Uses the back functionality of Android.
        """
        self.driver.back()

        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"


# TODO: Move this method to a utility class
def find_shortest_path(machine: StateMachine, destination: State | str) -> list[Transition] | None:
    """
    Gets the shortest path (in number of transitions) to the desired state
    """
    start = machine.current_state
    visited = set()
    queue = deque([(start, [])])

    while queue:
        state, path = queue.popleft()
        # if this is a path to the desirted state, return the path
        if state == destination or state.id == destination:
            return path
        # we do not want cycles: skip paths to already visited states
        if state in visited:
            continue
        visited.add(state)
        # take a step in all possible directions
        for transition in state.transitions:
            queue.append((transition.target, path + [transition]))
    return None


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
