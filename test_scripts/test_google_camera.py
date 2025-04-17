import unittest

from puma.apps.android.google_camera.google_camera import GoogleCameraActions

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
            print("No udid was configured for Alice. Pleas add at the top of the script.\nExiting....")
            exit(1)
        self.alice = GoogleCameraActions(device_udids["Alice"])

    def test_take_picture(self):
        self.alice.take_picture()

    def test_switch_camera(self):
        # test multiple times to ensure switching works properly
        self.alice.switch_camera()
        self.alice.switch_camera()
        self.alice.switch_camera()
        self.alice.switch_camera()

    def test_swtich_and_take_picture(self):
        self.alice.take_picture()
        self.alice.switch_camera()
        self.alice.take_picture()
        self.alice.switch_camera()
        self.alice.take_picture()

if __name__ == '__main__':
    unittest.main()