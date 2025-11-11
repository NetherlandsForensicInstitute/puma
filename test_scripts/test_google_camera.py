import unittest

from puma.apps.android.google_camera.google_camera import GoogleCamera

# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Alice": ""
}


class TestGoogleCamera(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Google Camera.
    The test can only be run manually, as you need a setup with at least one phone.
    Prerequisites:
    - All prerequisites mentioned in the README.
    - Phone with Google camera installed
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Pleas add at the top of the script.")
            print("Exiting....")
            exit(1)
        self.alice = GoogleCamera(device_udids["Alice"])

    def test_take_picture_using_back_camera(self):
        self.alice.take_picture()

    def test_take_picture_using_front_camera(self):
        self.alice.take_picture(front_camera=True)

    def test_take_pictures_using_by_switching_cameras(self):
        self.alice.take_picture()
        self.alice.take_picture(front_camera=True)
        self.alice.take_picture()
        self.alice.take_picture(front_camera=True)

    def test_record_video_using_back_camera(self):
        self.alice.record_video(duration=2)

    def test_record_video_using_front_camera(self):
        self.alice.record_video(duration=2, front_camera=True)

if __name__ == '__main__':
    unittest.main()