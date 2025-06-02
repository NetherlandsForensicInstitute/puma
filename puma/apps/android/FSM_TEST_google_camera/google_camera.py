from statemachine import StateMachine, State


def raise_error():
    raise ValueError('FSM says krak')

class GoogleCameraFsm(StateMachine):
    picture_rear = State(initial=True)
    picture_front = State(enter=lambda: raise_error())
    video_rear = State()
    video_front = State()

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

    def before_switch_camera(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"

    def before_switch_mode(self, event: str, source: State, target: State, message: str = ""):
        message = ". " + message if message else ""
        return f"Running {event} from {source.id} to {target.id}{message}"


if __name__ == '__main__':
    c = GoogleCameraFsm()
    print(c.current_state)
    c.switch_camera()
    print(c.current_state)
