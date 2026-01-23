from typing import List

from puma.state_graph.generic_xpaths import APP_STOPPED_POPUP_CLOSE_BUTTON, APP_STOPPED_POPUP_TITLE, \
    APP_UPDATE_POPUP_DISMISS_BUTTON, PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON, PERMISSIONS_POPUP_ALLOW_BUTTON
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import compose_clicks


class PopUpHandler:
    """
    Handler for pop-up windows in Android applications.
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


known_popups = [simple_popup_handler(APP_UPDATE_POPUP_DISMISS_BUTTON),
                simple_popup_handler(PERMISSIONS_POPUP_ALLOW_FOREGROUND_BUTTON),
                simple_popup_handler(PERMISSIONS_POPUP_ALLOW_BUTTON),
                PopUpHandler([APP_STOPPED_POPUP_TITLE, APP_STOPPED_POPUP_CLOSE_BUTTON],[APP_STOPPED_POPUP_CLOSE_BUTTON])]
