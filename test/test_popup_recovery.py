import unittest
from unittest.mock import Mock

from puma.state_graph.generic_xpaths import PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON
from puma.state_graph.popup_handler import simple_popup_handler
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


class SequentialPermissionDriver(PopupDriver):
    def __init__(self):
        super().__init__()
        self.permission_clicks = 0

    def click(self, xpath):
        self.clicks.append(xpath)
        if xpath == PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON:
            self.permission_clicks += 1
            self.permission_visible = self.permission_clicks < 2


class CascadingPopupDriver(PopupDriver):
    def __init__(self):
        super().__init__()
        self.permission_visible = False
        self.visible_popups = {'//first-popup', '//second-popup'}

    def is_present(self, xpath):
        return xpath in self.visible_popups or super().is_present(xpath)

    def click(self, xpath):
        if xpath not in self.visible_popups:
            raise AssertionError(f'Cannot click a popup that has disappeared: {xpath}')
        self.clicks.append(xpath)
        self.visible_popups.clear()


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

        self.assertEqual(driver.clicks, [PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON] * 5)
        application.gtl_logger.warning.assert_called_once_with(
            'Popup recovery reached its retry limit'
        )

    def test_recovery_handles_sequential_permissions_with_one_handler(self):
        driver = SequentialPermissionDriver()
        application = PopupRecoveryApplication(driver)

        application.recover_state(application.main_state)

        self.assertEqual(driver.clicks, [PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON] * 2)
        self.assertFalse(driver.permission_visible)

    def test_recovery_rechecks_popups_after_each_dismissal(self):
        driver = CascadingPopupDriver()
        application = PopupRecoveryApplication(driver)
        application.add_popup_handlers(
            simple_popup_handler('//first-popup'),
            simple_popup_handler('//second-popup'),
        )

        application.recover_state(application.main_state)

        self.assertEqual(driver.clicks, ['//first-popup'])
        self.assertFalse(driver.visible_popups)


if __name__ == '__main__':
    unittest.main()
