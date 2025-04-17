import unittest

from puma.apps.android.open_camera.open_camera import OpenCameraActions

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
            print("No udid was configured for Alice. Pleas add at the top of the script.\nExiting....")
            exit(1)
        self.alice = OpenCameraActions(device_udids["Alice"])

    def test_take_picture(self):
        self.alice.take_picture()

    def test_switch_camera(self):
        # test multiple times to ensure switching works properly
        self.alice.switch_camera()
        self.alice.switch_camera()
        self.alice.switch_camera()
        self.alice.switch_camera()

    def test_switch_and_take_picture(self):
        self.alice.take_picture()
        self.alice.switch_camera()
        self.alice.take_picture()
        self.alice.switch_camera()
        self.alice.take_picture()

    def test_take_video(self):
        self.alice.take_video(0)
        self.alice.take_video(2)


    def test_zoom(self):
        self.alice.zoom(1)
        self.alice.zoom(0)
        self.alice.zoom(0.5)
        self.assertRaises(ValueError, lambda: self.alice.zoom(2))
        self.assertRaises(ValueError, lambda: self.alice.zoom(-1))


if __name__ == '__main__':
    unittest.main()
