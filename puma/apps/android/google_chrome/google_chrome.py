from puma.apps.android.appium_actions import supported_version
from puma.apps.android.google_chrome import logger
from puma.apps.android.google_chrome.states import BookmarksFolder, CurrentTab
from puma.apps.android.google_chrome.xpaths import TAB_SWITCH_BUTTON, THREE_DOTS, SEARCH_TABS, \
    SEARCH_INCOGNITO_TABS, STANDARD_TAB_OVERVIEW_BUTTON, NEW_TAB_XPATH_TAB_OVERVIEW, TAB_LIST, SEARCH_BOX, \
    SEARCH_BOX_ENGINE_ICON, URL_BAR, NEW_TAB_FROM_CURRENT_TAB, NEW_TAB_INCOGNITO_TITLE, \
    BOOKMARK_THIS_PAGE_BUTTON, EDIT_BOOKMARK_BUTTON, NEW_INCOGNITO_TAB_BUTTON, OPEN_BOOKMARKS, \
    DELETE_BOOKMARK, CLOSE_BOOKMARKS, FIRST_BOOKMARK, BOOKMARKS_PAGE_TITLE, \
    BOOKMARKS_SORT_VIEW, BOOKMARKS_CREATE_FOLDER, NEW_ADS_PRIVACY_TEXT_XPATH, ACK_BUTTON_XPATH, \
    OTHER_ADS_PRIVACY_TEXT_XPATH, MORE_BUTTON_XPATH, TURN_ON_AD_PRIVACY_TEXT_XPATH, CHROME_NOTIFICATIONS_TEXT_XPATH, \
    NEGATIVE_BUTTON_XPATH
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.state import SimpleState, compose_clicks
from puma.state_graph.state_graph import StateGraph

GOOGLE_CHROME_PACKAGE = 'com.android.chrome'


@supported_version("141.0.7390.111")
class GoogleChrome(StateGraph):
    """
    A class representing the Google Chrome application on Android devices.

    The Google Chrome browser application does not really fit the parent-child relationship of states well, as most
    states can be reached from most other states. However, to keep to the structure of the StateGraph, we have chosen
    the tab overview as the parent state of most states, as it is the most neutral state from which other states can be
    reached. Moreover, for simplicity, we have not implemented all possible transitions between states.
    """
    # States
    tab_overview_state = SimpleState(xpaths=[TAB_LIST, SEARCH_TABS])
    incognito_tab_overview_state = SimpleState(xpaths=[TAB_LIST, SEARCH_INCOGNITO_TABS],
                                               parent_state=tab_overview_state,
                                               parent_state_transition=compose_clicks([STANDARD_TAB_OVERVIEW_BUTTON], 'go_to_tab_overview'))
    new_tab_state = SimpleState(xpaths=[SEARCH_BOX, SEARCH_BOX_ENGINE_ICON],
                                initial_state=True,
                                parent_state=tab_overview_state,
                                parent_state_transition=compose_clicks([TAB_SWITCH_BUTTON],'go_to_tab_overview'))
    current_tab_state = CurrentTab(parent_state=tab_overview_state)
    new_incognito_tab_state = SimpleState(xpaths=[URL_BAR, NEW_TAB_INCOGNITO_TITLE],
                                          parent_state=incognito_tab_overview_state,
                                          parent_state_transition=compose_clicks([TAB_SWITCH_BUTTON], 'go_to_incognito_tab_overview'))
    bookmarks_state = SimpleState(xpaths=[BOOKMARKS_SORT_VIEW, BOOKMARKS_CREATE_FOLDER, BOOKMARKS_PAGE_TITLE],
                                  parent_state=current_tab_state,
                                  parent_state_transition=compose_clicks([CLOSE_BOOKMARKS], 'go_to_current_tab'))
    bookmarks_folder_state = BookmarksFolder(parent_state=bookmarks_state)
    # Transitions
    tab_overview_state.to(new_tab_state, compose_clicks([NEW_TAB_XPATH_TAB_OVERVIEW], 'go_to_tab_overview'))
    tab_overview_state.to(current_tab_state, current_tab_state.switch_to_tab)
    tab_overview_state.to(new_incognito_tab_state,
                          compose_clicks([THREE_DOTS, NEW_INCOGNITO_TAB_BUTTON], 'go_to_incognito_state'))
    current_tab_state.to(new_tab_state, compose_clicks([NEW_TAB_FROM_CURRENT_TAB], 'go_to_current_tab'))
    current_tab_state.to(bookmarks_state, compose_clicks([THREE_DOTS, OPEN_BOOKMARKS], 'go_to_current_tab'))
    bookmarks_state.to(bookmarks_folder_state, bookmarks_folder_state.go_to_bookmarks_folder)

    def __init__(self, device_udid):
        """
        Initializes Google Chrome with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        """
        StateGraph.__init__(self, device_udid, GOOGLE_CHROME_PACKAGE)
        self.add_popup_handlers(PopUpHandler([NEW_ADS_PRIVACY_TEXT_XPATH], [ACK_BUTTON_XPATH]),
                                PopUpHandler([OTHER_ADS_PRIVACY_TEXT_XPATH], [MORE_BUTTON_XPATH, ACK_BUTTON_XPATH]),
                                PopUpHandler([TURN_ON_AD_PRIVACY_TEXT_XPATH], [ACK_BUTTON_XPATH]),
                                PopUpHandler([CHROME_NOTIFICATIONS_TEXT_XPATH], [NEGATIVE_BUTTON_XPATH]),
                                )

    @action(current_tab_state)
    def visit_url(self, url_string: str, tab_index: int):
        """
        Visits a url in an existing tab.
        Note that if you supply a tab index that is a new tab, the action will fail. Use go_to_new_tab instead.
        :param url_string: The argument to pass to the address bar
        :param tab_index: which tab to open
        """
        logger.warning(
            "In Chrome version 141.0.7390.111, we have noticed clicking on a tab with index might not open the tab on "
            "some devices. Hopefully this will be fixed in future Chrome versions.")
        self._enter_url(url_string, URL_BAR)

    @action(new_tab_state)
    def visit_url_new_tab(self, url_string):
        """
        Creates a new tab and visits the url.
        :param url_string: Url to visit
        """
        self.driver.send_keys(SEARCH_BOX, url_string)
        self.driver.press_enter()

    @action(new_incognito_tab_state)
    def visit_url_incognito(self, url_string: str):
        """
        Opens an incognito tab and enters the url_string to the address bar.
        :param url_string: the input to pass to the address bar
        """
        self.driver.click(THREE_DOTS)
        self.driver.click(NEW_INCOGNITO_TAB_BUTTON)
        self._enter_url(url_string, URL_BAR)

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
    def load_first_bookmark(self, folder_name: str):
        """
        Load the first saved bookmark in the specified folder.
        :param folder_name: The name of the folder to load the first bookmark from.
        """
        self.driver.click(FIRST_BOOKMARK)

    @action(current_tab_state)
    def delete_bookmark(self, tab_index: int):
        """
        Delete the current bookmark.
        :param tab_index: Index of the tab to delete the bookmark from.
        :return: True if bookmark has been deleted, False if it wasn't bookmarked.
        """
        self.driver.click(THREE_DOTS)

        if self.driver.is_present(BOOKMARK_THIS_PAGE_BUTTON):
            logger.info("This page was not bookmarked, skipping...")
            return False
        else:
            self.driver.click(EDIT_BOOKMARK_BUTTON)
            self.driver.click(DELETE_BOOKMARK)
            return True

    def _enter_url(self, url_string: str, url_bar_xpath):
        self.driver.send_keys(url_bar_xpath, url_string)
        self.driver.press_enter()
