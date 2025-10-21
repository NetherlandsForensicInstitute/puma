from puma.apps.android.appium_actions import supported_version
from puma.apps.android.google_chrome import logger
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, compose_clicks, ContextualState
from puma.state_graph.state_graph import StateGraph

GOOGLE_CHROME_PACKAGE = 'com.android.chrome'

# General
TAB_SWITCH_BUTTON = '//android.widget.ImageButton[@resource-id="com.android.chrome:id/tab_switcher_button"]'
THREE_DOTS = '//android.widget.ImageButton[@resource-id="com.android.chrome:id/menu_button"]'
# Tab overview
SEARCH_TABS_XPATH = '//android.widget.EditText[@resource-id="com.android.chrome:id/search_box_text" and @text="Search your tabs"]'
SEARCH_INCOGNITO_TABS_XPATH = '//android.widget.EditText[@resource-id="com.android.chrome:id/search_box_text" and @text="Search your Incognito tabs"]'
STANDARD_TAB_OVERVIEW_BUTTON = '//android.widget.LinearLayout[contains(@content-desc,"standard tabs")]'
NEW_TAB_XPATH_TAB_OVERVIEW = '//android.widget.Button[@content-desc="New tab"]'
TAB_LIST = '//*[@resource-id="com.android.chrome:id/tab_list_recycler_view"]'
# Tab
SEARCH_BOX_XPATH = '//android.widget.EditText[@resource-id="com.android.chrome:id/search_box_text"]'
SEARCH_BOX_ENGINE_ICON = '//android.widget.ImageView[@resource-id="com.android.chrome:id/search_box_engine_icon"]'
URL_BAR_XPATH = '//android.widget.EditText[@resource-id="com.android.chrome:id/url_bar"]'
PROFILE_XPATH = '//android.widget.ImageButton[contains(@content-desc, "Signed in as")]'
NEW_TAB_XPATH_CURRENT_TAB = '//android.widget.ImageButton[@content-desc="New tab"]'
NEW_TAB_INCOGNITO_TITLE = '//android.widget.TextView[@resource-id="com.android.chrome:id/new_tab_incognito_title"]'
# Menu
BOOKMARK_THIS_PAGE_BUTTON = '//android.widget.Button[lower-case(@content-desc)="bookmark"]'
EDIT_BOOKMARK_BUTTON = '//android.widget.Button[lower-case(@content-desc)="edit bookmark"]'
NEW_INCOGNITO_TAB_BUTTON = '//android.widget.TextView[@resource-id="com.android.chrome:id/title" and @text="New Incognito tab"]'
OPEN_BOOKMARKS_XPATH = '//android.widget.TextView[@resource-id="com.android.chrome:id/menu_item_text" and @text="Bookmarks"]'
# Bookmarks
MOBILE_BOOKMARKS_XPATH = '//android.widget.TextView[@resource-id="com.android.chrome:id/title" and @text="Mobile bookmarks"]'
DELETE_BOOKMARK_XPATH = '//android.widget.Button[lower-case(@content-desc)="delete bookmarks"]'
CLOSE_BOOKMARKS = '//android.widget.Button[@resource_id="com.android.chrome:id/close_menu_id"]'
FIRST_BOOKMARK_XPATH = '//android.widget.LinearLayout[@resource-id="com.android.chrome:id/container"]'
BOOKMARKS_PAGE_TITLE = '//android.widget.TextView[@text="Bookmarks"]'
BOOKMARKS_SORT_VIEW = '//android.widget.Button[@content-desc="Sort and view options"]'
BOOKMARKS_CREATE_FOLDER = '//android.widget.Button[@content-desc="Create new folder"]'
BOOKMARKS_GO_BACK = '//android.widget.ImageButton[@content-desc="Go back"]'

class BookmarksFolder(SimpleState, ContextualState):
    def __init__(self, parent_state):
        """
        Initializes the BookmarksFolder state with a given parent state.

        :param parent_state: The parent state of this state
        """
        super().__init__(xpaths=[BOOKMARKS_SORT_VIEW, BOOKMARKS_GO_BACK, BOOKMARKS_CREATE_FOLDER],
                         parent_state=parent_state,
                         parent_state_transition=compose_clicks([BOOKMARKS_GO_BACK]))

    def validate_context(self, driver: PumaDriver, folder_name: str = None) -> bool:
        """
        Validates if we are in the correct bookmarks folder.
        :param driver: Puma driver
        :param folder_name: Name of the bookmarks folder
        :return: boolean
        """
        #TODO check
        return driver.is_present(f'//android.view.ViewGroup[@resource-id="com.android.chrome:id/action_bar"]//android.widget.TextView[@text="{folder_name}"]')

    def go_to_bookmarks_folder(self, driver: PumaDriver, folder_name: str):
        driver.click(f'//android.widget.TextView[@resource-id="com.android.chrome:id/title" and @text="{folder_name}"]')

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
            xpaths=[URL_BAR_XPATH, NEW_TAB_XPATH_CURRENT_TAB],
            parent_state=parent_state,
            parent_state_transition=compose_clicks([TAB_SWITCH_BUTTON]))
        # Keep a dict that tracks which tab indices were opened last on which device. See validate_context()
        self.last_opened = {}


    def validate_context(self, driver: PumaDriver, tab_index: int = None) -> bool:
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
        if not tab_index:
            return True
        try:
            return self.last_opened[driver.udid] == tab_index
        except:
            return False

    def switch_to_tab(self, driver: PumaDriver, tab_index: int):
        """
        Navigate to the tab at the specified index in the tab overview. This method also stores which tab index was
        opened on which device, enabling contextual validation in validate_context().

        :param driver: The PumaDriver instance used to interact with the application
        :param tab_index: Index of the tab to navigate to
        """
        logger.info(f'Clicking on tab at index {tab_index}.')
        driver.click(
            f'({TAB_LIST}//*[@resource-id="com.android.chrome:id/content_view"])[{tab_index}]') #TODO extract constant
        self.last_opened[driver.udid] = tab_index

# TODO add class current tab state
@supported_version("141.0.7390.111")
class GoogleChrome(StateGraph):
    # States
    tab_overview_state = SimpleState(xpaths=[TAB_LIST, SEARCH_TABS_XPATH]) #TODO add search apps field
    incognito_tab_overview_state = SimpleState(xpaths=[TAB_LIST, SEARCH_INCOGNITO_TABS_XPATH],
                                               parent_state=tab_overview_state,
                                               parent_state_transition=compose_clicks([STANDARD_TAB_OVERVIEW_BUTTON])) #TODO add search apps field
    new_tab_state = SimpleState(xpaths=[SEARCH_BOX_XPATH, SEARCH_BOX_ENGINE_ICON],
                                initial_state=True,
                                parent_state=tab_overview_state,
                                parent_state_transition=compose_clicks([TAB_SWITCH_BUTTON]))
    current_tab_state = CurrentTab(parent_state=tab_overview_state)
    new_incognito_tab_state = SimpleState(xpaths=[URL_BAR_XPATH, NEW_TAB_INCOGNITO_TITLE],
                                          parent_state=incognito_tab_overview_state,
                                          parent_state_transition=compose_clicks([TAB_SWITCH_BUTTON]))
    bookmarks_state = SimpleState(xpaths=[BOOKMARKS_SORT_VIEW, BOOKMARKS_CREATE_FOLDER, BOOKMARKS_PAGE_TITLE],
                                  parent_state=current_tab_state,
                                  parent_state_transition=compose_clicks([CLOSE_BOOKMARKS]))
    bookmarks_folder_state = BookmarksFolder(parent_state=bookmarks_state)

    # Transitions
    tab_overview_state.to(new_tab_state, compose_clicks([NEW_TAB_XPATH_TAB_OVERVIEW], name='go_to_tab_overview'))
    tab_overview_state.to(current_tab_state, current_tab_state.switch_to_tab)
    tab_overview_state.to(new_incognito_tab_state, compose_clicks([THREE_DOTS, NEW_INCOGNITO_TAB_BUTTON], name='go_to_incognito_state'))
    current_tab_state.to(new_tab_state, compose_clicks([NEW_TAB_XPATH_CURRENT_TAB]))
    current_tab_state.to(bookmarks_state, compose_clicks([THREE_DOTS, OPEN_BOOKMARKS_XPATH]))
    bookmarks_state.to(bookmarks_folder_state, bookmarks_folder_state.go_to_bookmarks_folder)

    def __init__(self, device_udid):
        """
        Initializes Google Chrome with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        """
        StateGraph.__init__(self, device_udid, GOOGLE_CHROME_PACKAGE)
        self.add_popup_handler(PopUpHandler(['//android.widget.TextView[@text="New ads privacy feature now available"]'],
                                            ['//android.widget.Button[@resource-id="com.android.chrome:id/ack_button"]']))

        self.add_popup_handler(PopUpHandler(['//android.widget.TextView[@text="Turn on an ad privacy feature"]'],
                                            ['//android.widget.Button[@resource-id="com.android.chrome:id/ack_button"]']))


    @action(current_tab_state)
    def go_to(self, url_string: str, tab_index: int):
        """
        Enters the text as stated in the url_string parameter in a current tab
        :param url_string: the argument to pass to the address bar
        :param tab_index: which tab to open
        """
        self._enter_url(url_string, URL_BAR_XPATH)
        #TODO handle situation where tab n is a new tab, make sure the state recovers

    @action(new_tab_state)
    def go_to_new_tab(self, url_string): #TODO rename to more sensible name
        """
        Creates a new tab and enters the url string text.
        :param url_string: Url to navigate to
        :return:
        """
        self.driver.send_keys(SEARCH_BOX_XPATH, url_string)
        self.driver.press_enter()

    @action(current_tab_state)
    def bookmark_page(self, tab_index: int):
        """
        Bookmarks the current page.
        :param tab_index: Index of the tab to bookmark.
        :return: True if bookmark has been added, False if it already existed.
        """
        self.driver.click(THREE_DOTS)
        if self.driver.is_present(EDIT_BOOKMARK_BUTTON):
            logger.info("This page was already bookmarked, skipping...")
            return False
        else:
            self.driver.click(BOOKMARK_THIS_PAGE_BUTTON)
            return True

    @action(bookmarks_folder_state)
    def load_first_bookmark(self, folder_name: str): #TODO make nb configurable?
        """
        Load the first saved bookmark in the specified folder.
        :param folder_name: The name of the folder to load the first bookmark from.
        """
        self.driver.click(THREE_DOTS)

        self.driver.click(OPEN_BOOKMARKS_XPATH)
        self.driver.click(MOBILE_BOOKMARKS_XPATH)
        self.driver.click(FIRST_BOOKMARK_XPATH)

    @action(current_tab_state)
    def delete_bookmark(self, tab_index: int):
        """
        Delete the current bookmark.
        :return: True if bookmark has been deleted, False if it wasn't bookmarked.
        """
        self.driver.click(THREE_DOTS)

        if self.driver.is_present(BOOKMARK_THIS_PAGE_BUTTON):
            logger.info("This page was not bookmarked, skipping...")
            return False
        else:
            self.driver.click(EDIT_BOOKMARK_BUTTON)
            self.driver.click(DELETE_BOOKMARK_XPATH)
            return True

    @action(new_incognito_tab_state)
    def go_to_incognito(self, url_string: str):
        """
        Opens an incognito window and enters the url_string to the address bar.
        :param url_string: the input to pass to the address bar
        """
        self.driver.click(THREE_DOTS)
        self.driver.click(NEW_INCOGNITO_TAB_BUTTON)
        self._enter_url(url_string, URL_BAR_XPATH)

    def _enter_url(self, url_string: str, url_bar_xpath):
        self.driver.send_keys(url_bar_xpath, url_string)
        self.driver.press_enter()









