import unittest
from unittest.mock import Mock

from puma.state_graph.generic_xpaths import PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON
from puma.state_graph.state import SimpleState
from puma.state_graph.state_graph import StateGraph


class PopupDriver:
    def __init__(self):
        self.permission_visible = True
        self.clicks = []
        self.gtl_logger = Mock()

    def app_open(self):
        return True

    def activate_app(self):
        raise AssertionError('The app should already be active')

    def is_present(self, xpath):
        if xpath == '//state':
            return True
        if xpath == PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON:
            return self.permission_visible
        return False

    def click(self, xpath):
        self.clicks.append(xpath)
        if xpath == PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON:
            self.permission_visible = False


class PersistentPopupDriver(PopupDriver):
    def click(self, xpath):
        self.clicks.append(xpath)


class PopupRecoveryApplication(StateGraph):
    main_state = SimpleState(['//state'], initial_state=True)

    def __init__(self, driver):
        self.current_state = self.initial_state
        self.driver = driver
        self.app_popups = []
        self.gtl_logger = Mock()


class TestPopupRecovery(unittest.TestCase):
    def test_recovery_dismisses_popup_when_underlying_state_still_validates(self):
        driver = PopupDriver()
        application = PopupRecoveryApplication(driver)

        application.recover_state(application.main_state)

        self.assertEqual(driver.clicks, [PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON])
        self.assertFalse(driver.permission_visible)

    def test_recovery_stops_when_popup_does_not_disappear(self):
        driver = PersistentPopupDriver()
        application = PopupRecoveryApplication(driver)

        application.recover_state(application.main_state)

        self.assertEqual(driver.clicks, [PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON])
        application.gtl_logger.warning.assert_called_once_with(
            'Popup handlers made no progress; stopping popup recovery'
        )


if __name__ == '__main__':
    unittest.main()
