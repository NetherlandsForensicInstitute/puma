from transitions import Machine

class GoogleCameraActions(object):
    states = ['picture_rear','picture_front','video_rear','video_front']

    def __init__(self):
        # self.machine = Machine(model=self, states=GoogleCameraActions.states, initial='picture_rear')
        #
        # # Define transitions for switching camera views
        # self.machine.add_transition('switch_camera_video_to_front', 'video_rear', 'video_front')
        # self.machine.add_transition('switch_camera_video_to_rear', 'video_front', 'video_rear')
        # self.machine.add_transition('switch_camera_picture_to_front', 'picture_rear', 'picture_front')
        # self.machine.add_transition('switch_camera_picture_to_rear', 'picture_front', 'picture_rear')
        #
        # # Define transitions for switching modes
        # self.machine.add_transition('switch_mode_video_to_picture', 'video_front', 'picture_front')
        # self.machine.add_transition('switch_mode_picture_to_video', 'picture_front', 'video_front')
        # self.machine.add_transition('switch_mode_video_rear_to_picture_rear', 'video_rear', 'picture_rear')
        # self.machine.add_transition('switch_mode_picture_rear_to_video_rear', 'picture_rear', 'video_rear')

        # Option 2: supply as dict:
        transitions = [
            {'trigger': 'switch_camera_video_to_front', 'source': 'video_rear', 'dest': 'video_front'},
            {'trigger': 'switch_camera_video_to_rear', 'source': 'video_front', 'dest': 'video_rear'},
            {'trigger': 'switch_camera_picture_to_front', 'source': 'picture_rear', 'dest': 'picture_front'},
            {'trigger': 'switch_camera_picture_to_rear', 'source': 'picture_front', 'dest': 'picture_rear'},
            {'trigger': 'switch_mode_video_to_picture', 'source': 'video_front', 'dest': 'picture_front'},
            {'trigger': 'switch_mode_picture_to_video', 'source': 'picture_front', 'dest': 'video_front'},
            {'trigger': 'switch_mode_video_rear_to_picture_rear', 'source': 'video_rear', 'dest': 'picture_rear'},
            {'trigger': 'switch_mode_picture_rear_to_video_rear', 'source': 'picture_rear', 'dest': 'video_rear'}
        ]
        self.machine = Machine(model=self, states=GoogleCameraActions.states, transitions=transitions, initial='picture_rear')


if __name__ == '__main__':
    google_cam = GoogleCameraActions()
    google_cam.switch_camera_picture_to_front()
    print(google_cam.state)

