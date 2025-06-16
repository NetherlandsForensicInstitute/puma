from typing import List

from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import compose_clicks


class PopUpHandler:
    """
    Handler for popup windows in Android applications.
    """

    def __init__(self, recognize_xpaths: List[str], dismiss_xpaths: List[str]):
        """
        Popup handler.

        :param recognize_xpath: The XPath to use for recognizing popup windows.
        :param click: The XPath for the element to dismiss the popup.
        """
        self.recognize_xpaths = recognize_xpaths
        self.dismiss_xpaths = dismiss_xpaths

    def is_popup_window(self, driver: PumaDriver) -> bool:
        """
        Check if a popup is present in the current window

        :param driver: The PumaDriver instance to use for searching the window.
        return: Whether the popup window was found or not.
        """
        return all(driver.is_present(xpath) for xpath in self.recognize_xpaths)

    def dismiss_popup(self, driver: PumaDriver):
        """
        Dismiss a popup window using the provided xpath.

        :param driver: The PumaDriver instance to use for searching and clicking the button.
        """
        compose_clicks(self.dismiss_xpaths)(driver)


def simple_popup_handler(xpath: str):
    """
    Utility method to create a popup handler that uses the same XPath for both recognizing and dismissing the popup.
    :param xpath: xpath of the element to click
    :return: PopUpHandler for the provided xpath
    """
    return PopUpHandler([xpath], [xpath])


known_popups = [simple_popup_handler('//android.widget.ImageView[@content-desc="Dismiss update dialog"]'),
                simple_popup_handler(
                    '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"]'),
                simple_popup_handler(
                    '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]')]
