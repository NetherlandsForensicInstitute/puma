from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy
from typing_extensions import deprecated

from puma.apps.android import log_action
from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version
from puma.apps.android.google_chrome import logger
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, compose_clicks, ContextualState
from puma.state_graph.state_graph import StateGraph

GOOGLE_CHROME_PACKAGE = 'com.android.chrome'

SEARCH_BOX_XPATH = '//android.widget.EditText[@resource-id="com.android.chrome:id/search_box_text"]'
SEARCH_BOX_ENGINE_ICON = '//android.widget.ImageView[@resource-id="com.android.chrome:id/search_box_engine_icon"]'
TAB_SWITCH_BUTTON = '//android.widget.ImageButton[@resource-id="com.android.chrome:id/tab_switcher_button"]'
THREE_DOTS = '//android.widget.ImageButton[@content-desc="Customize and control Google Chrome"]'
BOOKMARK_BUTTON = '//android.widget.Button[lower-case(@content-desc)="bookmark"]'
EDIT_BOOKMARK_BUTTON = '//android.widget.Button[lower-case(@content-desc)="edit bookmark"]'
URL_BAR_XPATH = '//android.widget.EditText[@resource-id="com.android.chrome:id/url_bar"]'
PROFILE_XPATH = '//android.widget.ImageButton[contains(@content-desc, "Signed in as"]'
NEW_TAB_XPATH = '//android.widget.ImageButton[@content-desc="New tab"]'
TAB_LIST = '//*[@resource-id="com.android.chrome:id/tab_list_recycler_view"]'


class CurrentTab(SimpleState, ContextualState):
    """
    A state repesenting an existing tab in the application.

    This class extends both SimpleState and ContextualState to represent a tab screen. The contextual state is an outlier,
    see the validate_context method.
    """

    def __init__(self, parent_state):
        """
        Initializes the Current Tab state with a given parent state.

        :param parent_state: The parent state of this current tab state.
        """
        super().__init__(
            xpaths=[URL_BAR_XPATH, NEW_TAB_XPATH],
            parent_state=parent_state,
            parent_state_transition=compose_clicks([TAB_SWITCH_BUTTON]))
        # Keep a dict that tracks which tab indices were opened last on which device. See validate_context()
        self.last_opened = {}


    def validate_context(self, driver: PumaDriver, tab_index: str = None) -> bool:
        """
        We can not validate if we are in the nth tab from the tab overview, while in the tab contextual state, as this
        index is not available in the state.
        Therefore, we opted to store the last opened tab index for each device in this state. This means that the
        contextual state is not actually verified against the UI, but against the tab index saved in the last opened
        dict. When switching between two tabs, this works as long as the user does not interrupt Puma during these UI
        actions.
        #TODO document this situation in the CONTRIBUTING
        :param driver: Puma driver
        :param tab_index: Index of the tab last opened
        :return: boolean
        """
        return self.last_opened[driver.udid] == tab_index

    def switch_to_tab(self, driver: PumaDriver, tab_index):
        """
        Navigate to the tab at the specified index in the tab overview. This method also stores which tab index was
        opened on which device, enabling contextual validation in validate_context().

        :param driver: The PumaDriver instance used to interact with the application
        :param tab_index: Index of the tab to navigate to
        """
        logger.info(f'Clicking on tab at index {tab_index}.')
        driver.click(TAB_SWITCH_BUTTON)
        driver.click(
            f'({TAB_LIST}//*[@resource-id="com.android.chrome:id/content_view"])[{tab_index}]')  # TODO extract?
        self.last_opened[driver.udid] = tab_index

# TODO add class current tab state
@supported_version("141.0.7390.111")
class GoogleChrome(StateGraph):
    new_tab = SimpleState(xpaths=[SEARCH_BOX_XPATH, PROFILE_XPATH, SEARCH_BOX_ENGINE_ICON], initial_state=True)
    tab_overview = SimpleState(xpaths=[TAB_LIST]) #TODO add search apps field
    current_tab = CurrentTab(parent_state=tab_overview) #TODO move to tab state class
    #
    new_tab.to(tab_overview, compose_clicks([TAB_SWITCH_BUTTON], name='go_to_tab_overview'))
    tab_overview.to(current_tab, compose_clicks([TAB_SWITCH_BUTTON], name='go_to_tab_overview'))
    #Multiple states to 1: to_state.from(state1, state2)

    def _enter_url(self, url_string: str):
        url_bar_xpath = '//android.widget.EditText[@resource-id="com.android.chrome:id/url_bar"]'
        self.driver.click(url_bar_xpath) #TODO chceck if click is necessary
        self.driver.send_keys(url_bar_xpath, url_string)
        self.driver.press_enter()  # TODO build into puma driver

    @action(current_tab)
    def go_to(self, url_string: str, new_tab: bool = False):
        """
        Enters the text as stated in the url_string parameter in a current tab
        :param url_string: the argument to pass to the address bar
        :param new_tab: whether to open a new tab first
        """
        self.driver.click(SEARCH_BOX_XPATH)
        self._enter_url(url_string)

    @action(new_tab)
    def go_to_new_tab(self, url_string):
        """
        TODO
        :param url_string:
        :return:
        """
        new_tab_xpath = '//android.widget.Button[contains(@content-desc, "tab")]'
        self.driver.find_element(by=AppiumBy.XPATH, value=TAB_SWITCH_BUTTON).click()
        self.driver.find_element(by=AppiumBy.XPATH, value=new_tab_xpath).click()
        self.is_present(xpath=TAB_SWITCH_BUTTON, implicit_wait=1)
        self.driver.find_element(by=AppiumBy.XPATH, value=SEARCH_BOX_XPATH).click()
        self._enter_url(url_string)





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
