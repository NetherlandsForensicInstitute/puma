from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy
from typing_extensions import deprecated

from puma.apps.android import log_action
from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version

GOOGLE_CHROME_PACKAGE = 'com.android.chrome'

TAB_SWITCH_BUTTON = '//android.widget.ImageButton[@resource-id="com.android.chrome:id/tab_switcher_button"]'
THREE_DOTS = '//android.widget.ImageButton[@content-desc="Customize and control Google Chrome"]'
BOOKMARK_BUTTON = '//android.widget.Button[lower-case(@content-desc)="bookmark"]'
EDIT_BOOKMARK_BUTTON = '//android.widget.Button[lower-case(@content-desc)="edit bookmark"]'


@deprecated('This class does not use the Puma state machine, and will therefore not be maintained.')
@supported_version("139.0.7258.62")
class GoogleChromeActions(AndroidAppiumActions):
    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 impicit_wait=1,
                 appium_server='http://localhost:4723'):
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      GOOGLE_CHROME_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=impicit_wait,
                                      appium_server=appium_server)

    @log_action
    def go_to(self, url_string: str, new_tab: bool = False):
        """
        Enters the text as stated in the url_string parameter.
        The user has the option to open a new tab first.
        :param url_string: the argument to pass to the address bar
        :param new_tab: whether to open a new tab first
        """
        search_box_xpath = '//android.widget.EditText[@resource-id="com.android.chrome:id/search_box_text"]'
        if self.is_present(search_box_xpath):
            self.driver.find_element(by=AppiumBy.XPATH, value=search_box_xpath).click()

        if new_tab:
            new_tab_xpath = '//android.widget.Button[contains(@content-desc, "tab")]'
            self.driver.find_element(by=AppiumBy.XPATH, value=TAB_SWITCH_BUTTON).click()
            self.driver.find_element(by=AppiumBy.XPATH, value=new_tab_xpath).click()
            self.is_present(xpath=TAB_SWITCH_BUTTON, implicit_wait=1)
            self.driver.find_element(by=AppiumBy.XPATH, value=search_box_xpath).click()

        url_bar_xpath = '//android.widget.EditText[@resource-id="com.android.chrome:id/url_bar"]'
        url_bar = self.driver.find_element(by=AppiumBy.XPATH, value=url_bar_xpath)
        url_bar.click()
        url_bar.send_keys(url_string)
        self.driver.press_keycode(66)

    @log_action
    def bookmark_page(self):
        """
        Bookmarks the current page.
        :return: True if bookmark has been added, False if it already existed.
        """
        self.driver.find_element(by=AppiumBy.XPATH, value=THREE_DOTS).click()
        if self.is_present(EDIT_BOOKMARK_BUTTON):
            self.back()
            return False
        else:
            self.driver.find_element(by=AppiumBy.XPATH, value=BOOKMARK_BUTTON).click()
            return True

    @log_action
    def delete_bookmark(self):
        """
        Delete the current bookmark.
        :return: True if bookmark has been deleted, False if it wasn't bookmarked.
        """
        delete_bookmark_xpath = '//android.widget.Button[lower-case(@content-desc)="delete bookmarks"]'
        self.driver.find_element(by=AppiumBy.XPATH, value=THREE_DOTS).click()
        if self.is_present(BOOKMARK_BUTTON):
            self.back()
            return False
        else:
            self.driver.find_element(by=AppiumBy.XPATH, value=EDIT_BOOKMARK_BUTTON).click()
            self.driver.find_element(by=AppiumBy.XPATH, value=delete_bookmark_xpath).click()
            return True

    @log_action
    def load_bookmark(self):
        """
        Load the first saved bookmark in the folder 'Mobile Bookmarks'.
        """
        bookmarks_xpath = '//android.widget.TextView[@resource-id="com.android.chrome:id/menu_item_text" and @text="Bookmarks"]'
        mobile_bookmarks_xpath = '//android.widget.TextView[@resource-id="com.android.chrome:id/title" and @text="Mobile bookmarks"]'
        first_bookmark_xpath = '//android.widget.LinearLayout[@resource-id="com.android.chrome:id/container"]'
        self.driver.find_element(by=AppiumBy.XPATH, value=THREE_DOTS).click()
        self.driver.find_element(by=AppiumBy.XPATH, value=bookmarks_xpath).click()
        if self.is_present(mobile_bookmarks_xpath):
            self.driver.find_element(by=AppiumBy.XPATH, value=mobile_bookmarks_xpath).click()
        self.driver.find_element(by=AppiumBy.XPATH, value=first_bookmark_xpath).click()

    @log_action
    def switch_to_tab(self, num_tab: int = 1):
        """
        Switches to another tab, by default the first open tab.
        :param num_tab: the number of the tab to open
        """
        self.driver.find_element(by=AppiumBy.XPATH, value=TAB_SWITCH_BUTTON).click()
        tab_list = '//*[@resource-id="com.android.chrome:id/tab_list_recycler_view"]'
        self.driver.find_element(by=AppiumBy.XPATH, value=f'({tab_list}//*[@resource-id="com.android.chrome:id/content_view"])[{num_tab}]').click()

    @log_action
    def go_to_incognito(self, url_string: str):
        """
        Opens an incognito window and enters the url_string to the address bar.
        :param url_string: the input to pass to the address bar
        """
        three_dots_xpath = '//android.widget.ImageButton[contains(@content-desc, "Customize")]'
        incognito_tab_xpath = '//android.widget.TextView[@resource-id="com.android.chrome:id/title" and @text="New Incognito tab"]'
        self.driver.find_element(by=AppiumBy.XPATH, value=three_dots_xpath).click()
        self.driver.find_element(by=AppiumBy.XPATH, value=incognito_tab_xpath).click()
        self.go_to(url_string)
