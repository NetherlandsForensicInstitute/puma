import unittest

from puma.apps.android.google_play_store.google_play_store import GooglePlayStore

# Fill in the udid below. Run ADB devices to see the udids.
device_udids = {
    "Alice": ""
}
PACKAGE_NAME = ""  # This app will be installed and uninstalled, so choose an app for which uninstalling does not matter
UPDATABLE_PACKAGE_NAME = ""  # This app should be installed already and updatable. You can check which apps can be updated under "Manage apps and device"


class TestPlayStore(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of the Google
    PlayStore. The test can only be run manually, as you need a setup with one phone.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - 1 phone with the Google Play Store
    - Appium running
    - Preferably an app that is already installed and can be updated (Fill in above)
    - Preferably another app that can be updated, so update all can be tested
    """

    @classmethod
    def setUpClass(cls):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        cls.alice = GooglePlayStore(device_udids["Alice"])
        if not PACKAGE_NAME:
            print("Global variable PACKAGE_NAME was not configured, please add it at the top of the script.\n Exiting...")
        if not UPDATABLE_PACKAGE_NAME:
            print("Global variable UPDATABLE_PACKAGE_NAME was not configured, please add it at the top of the script.\n Exiting...")

    def test_get_app_state(self):
        app_state = self.alice.get_app_state(PACKAGE_NAME)
        print(f"App state is {app_state}")

    def test_install_app(self):
        self.alice.uninstall_app(PACKAGE_NAME)
        self.alice.install_app(PACKAGE_NAME)

    def test_uninstall_app(self):
        self.alice.install_app(PACKAGE_NAME)
        self.alice.uninstall_app(PACKAGE_NAME)

    def test_update_app(self):
        self.alice.update_app(UPDATABLE_PACKAGE_NAME)

    def test_update_all_apps(self):
        self.alice.update_all_apps()
