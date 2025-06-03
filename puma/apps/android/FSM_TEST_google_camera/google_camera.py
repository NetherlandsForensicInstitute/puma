from collections import deque

from statemachine import StateMachine, State
from statemachine.transition import Transition
from statemachine.transition_list import TransitionList

from puma.apps.android.FSM_TEST_google_camera.puma_fsm import PumaState


def make_back_action(back, state): # TODO: This can probably be placed in some utility class
    return lambda self: back.add_transitions(self.to(state))


class GoogleCameraFsm(StateMachine):
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

    def before_switch_camera(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    def before_switch_mode(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"


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
    c = GoogleCameraFsm()
    d = GoogleCameraFsm()

    path = find_shortest_path(c, GoogleCameraFsm.video_front)
    print("Shortest path to video_front:", [t.event for t in path])
    path = find_shortest_path(d, "video_front")
    print("Shortest path to video_front:", [t.event for t in path])
