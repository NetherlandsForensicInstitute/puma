import unittest

from puma.apps.android.open_camera.open_camera import OpenCamera

# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Alice": ""
}


class TestOpenCamera(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Open Camera.
    The test can only be run manually, as you need a setup with at least one phone.
    Prerequisites:
    - All prerequisites mentioned in the README.
    - Phone with Open camera installed
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = OpenCamera(device_udids["Alice"])

    def test_take_picture_front(self):
        self.alice.take_picture(front_camera=True)

    def test_take_picture_back(self):
        self.alice.take_picture(front_camera=False)

    def test_take_video_front(self):
        self.alice.take_video(0, front_camera=True)
        self.alice.take_video(2, front_camera=True)

    def test_zoom(self):
        self.alice.take_picture(front_camera=True, zoom_amount=1.0)
        self.alice.take_picture(front_camera=True, zoom_amount=0.5)
        self.alice.take_picture(front_camera=True, zoom_amount=0.75)
        self.assertRaises(ValueError, lambda: self.alice.take_picture(front_camera=True, zoom_amount=2.0))

    def test_take_video_back(self):
        self.alice.take_video(2, front_camera=False)

    def test_ensure_correct_view(self):
        # test multiple times to ensure switching works properly
        self.alice.go_to_state(self.alice.take_photo_state)
        self.alice._ensure_correct_view(front_camera=True)
        self.alice._ensure_correct_view(front_camera=False)
        self.alice._ensure_correct_view(front_camera=True)
        self.alice._ensure_correct_view(front_camera=False)


if __name__ == '__main__':
    unittest.main()
