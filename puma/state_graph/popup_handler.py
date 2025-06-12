from puma.state_graph.puma_driver import PumaDriver


class PopUpHandler:
    """
    Handler for popup windows in Android applications.
    """

    def __init__(self, recognize_xpath: str, dismiss_xpath: str):
        """
        Popup handler.

        :param recognize_xpath: The XPath to use for recognizing popup windows.
        :param click: The XPath for the element to dismiss the popup.
        """
        self.recognize_xpath = recognize_xpath
        self.dismiss_xpath = dismiss_xpath

    def is_popup_window(self, driver: PumaDriver) -> bool:
        """
        Check if a popup is present in the current window

        :param driver: The PumaDriver instance to use for searching the window.
        return: Whether the popup window was found or not.
        """
        return driver.is_present(self.recognize_xpath)

    def dismiss_popup(self, driver: PumaDriver):
        """
        Dismiss a popup window using the provided xpath.

        :param driver: The PumaDriver instance to use for searching and clicking the button.
        """
        driver.click(self.dismiss_xpath)


def simple_popup_handler(xpath: str):
    """
    Utility method to create a popup handler that uses the same XPath for both recognizing and dismissing the popup.
    :param xpath: xpath of the element to click
    :return: PopUpHandler for the provided xpath
    """
    return PopUpHandler(xpath, xpath)


known_popups = [simple_popup_handler('//android.widget.ImageView[@content-desc="Dismiss update dialog"]'),
                simple_popup_handler(
                    '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"]'),
                simple_popup_handler(
                    '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]')]
