from collections import deque
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
            result = func(args[0])
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

    switch_mode = (
            video_front.to(picture_front)
            | picture_front.to(video_front)
            | video_rear.to(picture_rear)
            | picture_rear.to(video_rear)
    )

    open_settings = (
        picture_rear.to(camera_setting)
        | picture_front.to(camera_setting)
        | video_rear.to(camera_setting)
        | video_front.to(camera_setting)
    )


    # State machine definitions # TODO: Before methods are no longer called when the event is triggered
    def before_switch_camera(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    def before_switch_mode(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    def before_back(self, event: str, source: PumaState, target: PumaState, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        super().__init__()

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

    # Transitions
    def switch_camera_transition(self):
        """
        Switches between the front and rear camera.
        """
        xpath = '//android.widget.ImageButton[@resource-id="com.google.android.GoogleCamera:id/camera_switch_button"]'
        button = self.driver.find_element(by=AppiumBy.XPATH, value=xpath)
        button.click()

    # def before_transition(self, event, source, target, message=""):
    #     print(f"[before_transition] Event={event}, From={source.id}, To={target.id}")




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

    path = find_shortest_path(c, GoogleCameraFsm.video_front)
    print("Shortest path to video_front:", [t.event for t in path])
    # path = find_shortest_path(d, "video_front")
    # print("Shortest path to video_front:", [t.event for t in path])
