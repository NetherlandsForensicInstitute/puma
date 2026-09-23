from typing import List

from puma.state_graph.generic_xpaths import APP_STOPPED_POPUP_CLOSE_BUTTON, APP_STOPPED_POPUP_TITLE, \
    APP_UPDATE_POPUP_DISMISS_BUTTON, PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON, PERMISSIONS_POPUP_ALLOW_BUTTON, \
    IOS_PERMISSION_DENY_BUTTON, IOS_TRACKING_DENY_BUTTON, IOS_PERMISSION_ALLOW_BUTTONS, IOS_ENABLE_DICTATION_BUTTON, \
    IOS_NOT_NOW_BUTTON
from puma.state_graph.puma_driver import PumaDriver, Platform
from puma.state_graph.state import compose_clicks


class PopUpHandler:
    """
    Handler for pop-up windows, recognized and dismissed using XPaths (or Locators).
    """

    def __init__(self, recognize_xpaths: List[str], dismiss_xpaths: List[str]):
        """
        Pop-up handler.

        :param recognize_xpaths: The XPaths to use for recognizing popup windows.
        :param dismiss_xpaths: The XPaths for the element to dismiss the pop-up.
        """
        self.recognize_xpaths = recognize_xpaths
        self.dismiss_xpaths = dismiss_xpaths

    def is_popup_window(self, driver: PumaDriver) -> bool:
        """
        Check if a pop-up is present in the current window

        :param driver: The PumaDriver instance to use for searching the window.
        return: Whether the pop-up window was found or not.
        """
        return all(driver.is_present(xpath) for xpath in self.recognize_xpaths)

    def dismiss_popup(self, driver: PumaDriver):
        """
        Dismiss a pop-up window using the provided xpath.

        :param driver: The PumaDriver instance to use for searching and clicking the button.
        """
        driver.gtl_logger.info('Dismissing pop-up')
        compose_clicks(self.dismiss_xpaths)(driver)


def simple_popup_handler(xpath: str):
    """
    Utility method to create a pop-up handler that uses the same XPath for both recognizing and dismissing the pop-up.

    :param xpath: XPath of the element to click
    :return: PopUpHandler for the provided XPath
    """
    return PopUpHandler([xpath], [xpath])


class IOSAlertHandler(PopUpHandler):
    """
    Handler for iOS alerts, including system alerts such as permission requests.

    System alerts on iOS are shown by the operating system rather than the app. Instead of XPaths, these are recognized
    and dismissed using the labels of the alert buttons, through the Appium alert API. This only works on iOS.
    """

    def __init__(self, recognize_buttons: List[str], click_buttons: List[str]):
        """
        iOS alert handler.

        :param recognize_buttons: The alert is recognized if it has a button with any of these labels.
        :param click_buttons: The labels of the buttons that dismiss the alert, in order of preference. The first
        button present in the alert is clicked.
        """
        super().__init__([], [])
        self.recognize_buttons = recognize_buttons
        self.click_buttons = click_buttons

    def is_popup_window(self, driver: PumaDriver) -> bool:
        if driver.platform != Platform.IOS:
            return False
        buttons = driver.alert_buttons()
        return any(label in buttons for label in self.recognize_buttons) and \
            any(label in buttons for label in self.click_buttons)

    def dismiss_popup(self, driver: PumaDriver):
        driver.gtl_logger.info('Dismissing alert')
        buttons = driver.alert_buttons()
        label = next(label for label in self.click_buttons if label in buttons)
        driver.click_alert_button(label)


known_popups = [simple_popup_handler(APP_UPDATE_POPUP_DISMISS_BUTTON),
                simple_popup_handler(PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON),
                simple_popup_handler(PERMISSIONS_POPUP_ALLOW_BUTTON),
                PopUpHandler([APP_STOPPED_POPUP_TITLE, APP_STOPPED_POPUP_CLOSE_BUTTON], [APP_STOPPED_POPUP_CLOSE_BUTTON])]

# iOS permission requests all have a "Don't Allow" button (or "Ask App Not to Track" for the tracking request), while
# the button granting the permission differs per permission type. Permissions are granted, like on Android.
# Other system prompts, such as the prompt to enable dictation, are declined.
known_ios_popups = [IOSAlertHandler(recognize_buttons=[IOS_PERMISSION_DENY_BUTTON, IOS_TRACKING_DENY_BUTTON],
                                    click_buttons=IOS_PERMISSION_ALLOW_BUTTONS),
                    IOSAlertHandler(recognize_buttons=[IOS_ENABLE_DICTATION_BUTTON], click_buttons=[IOS_NOT_NOW_BUTTON])]


def known_popups_for(platform: Platform) -> List[PopUpHandler]:
    """
    :param platform: The platform of the device.
    :return: The generic pop-up handlers for the given platform.
    """
    if platform == Platform.IOS:
        return known_ios_popups
    return known_popups
