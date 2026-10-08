import unittest
from time import sleep, time

from puma.apps.ios.app_store.app_store import AppStore, AppState

# Fill in the udid below. Run `xcrun xctrace list devices` to see the udids of real devices.
device_udids = {
    "Alice": ""
}
# Real devices need the signing settings of WebDriverAgent, see docs/setup-ios.md
desired_capabilities = {
    # "appium:xcodeOrgId": "<your team id>",
    # "appium:xcodeSigningId": "Apple Development",
}
COUNTRY = "nl"  # The country of the App Store of the device
BUNDLE_ID = ""  # This app will be installed and uninstalled, so choose an app for which uninstalling does not matter
UPDATABLE_BUNDLE_ID = ""  # This app should be installed already and updatable. You can check which apps can be updated in your account, under "App Updates"


def _wait_until_installed(phone: AppStore, bundle_id: str, timeout: int = 300):
    start = time()
    while phone.get_app_state(bundle_id) != AppState.INSTALLED:
        if time() - start > timeout:
            raise TimeoutError(f"{bundle_id} was not installed within {timeout} seconds")
        sleep(5)


class TestAppStore(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of the App Store on
    iOS. The test can only be run manually, as you need a real iOS device.

    Prerequisites:
    - All prerequisites mentioned in the README, including no password for free downloads.
    - 1 iOS device with the App Store
    - Appium running
    - Preferably an app that is already installed and can be updated (Fill in above)
    - Preferably another app that can be updated, so update all can be tested
    """

    @classmethod
    def setUpClass(cls):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        cls.alice = AppStore(device_udids["Alice"], country=COUNTRY, desired_capabilities=desired_capabilities)
        if not BUNDLE_ID:
            print("Global variable BUNDLE_ID was not configured, please add it at the top of the script.\nExiting...")
            exit(1)
        if not UPDATABLE_BUNDLE_ID:
            print("Global variable UPDATABLE_BUNDLE_ID was not configured, please add it at the top of the script.\nExiting...")
            exit(1)

    def test_get_app_state(self):
        app_state = self.alice.get_app_state(BUNDLE_ID)
        print(f"App state is {app_state}")

    def test_install_app(self):
        self.alice.uninstall_app(BUNDLE_ID)
        self.alice.install_app(BUNDLE_ID)
        _wait_until_installed(self.alice, BUNDLE_ID)

    def test_uninstall_app(self):
        self.alice.install_app(BUNDLE_ID)
        _wait_until_installed(self.alice, BUNDLE_ID)
        self.alice.uninstall_app(BUNDLE_ID)
        self.assertEqual(AppState.NOT_INSTALLED, self.alice.get_app_state(BUNDLE_ID))

    def test_update_app(self):
        if self.alice.get_app_state(UPDATABLE_BUNDLE_ID) != AppState.UPDATE_AVAILABLE:
            self.skipTest(f"No update is available for {UPDATABLE_BUNDLE_ID}, so updating could not be tested")
        self.alice.update_app(UPDATABLE_BUNDLE_ID)
        _wait_until_installed(self.alice, UPDATABLE_BUNDLE_ID)

    def test_update_all_apps(self):
        if self.alice.get_app_state(UPDATABLE_BUNDLE_ID) != AppState.UPDATE_AVAILABLE:
            self.skipTest("No updates are available, so updating all apps could not be tested")
        self.alice.update_all_apps()
        # update_all_apps does not wait for the updates, so the app is being updated or has been updated already
        self.assertIn(self.alice.get_app_state(UPDATABLE_BUNDLE_ID), [AppState.INSTALLING, AppState.INSTALLED])


if __name__ == '__main__':
    unittest.main()
