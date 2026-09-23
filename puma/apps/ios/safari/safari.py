from time import sleep, time
from typing import Callable

from puma.apps.ios.safari import logger
from puma.apps.ios.safari.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler, simple_popup_handler
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, Platform, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

SAFARI_BUNDLE_ID = 'com.apple.mobilesafari'


def _wait_for(driver: PumaDriver, xpath: str, timeout: float = 4) -> bool:
    start = time()
    while time() - start < timeout:
        if driver.is_present(xpath):
            return True
        sleep(0.3)
    return False


def open_menu_item(menu_item: str, name: str = 'open_menu_item') -> Callable[[PumaDriver], None]:
    """
    Creates a transition that opens the More menu (the '...' button in the toolbar) and clicks an item in it.
    The menu takes a while to animate in, and occasionally does not open on the first tap, so this is retried.

    :param menu_item: The locator of the menu item to click.
    :param name: The name of the transition.
    """
    def _open_menu_item(driver: PumaDriver):
        for _ in range(3):
            driver.click(MORE_BUTTON)
            if _wait_for(driver, menu_item):
                driver.click(menu_item)
                return
        raise PumaClickException(f'Could not open menu item {menu_item}')
    _open_menu_item.__name__ = name
    return _open_menu_item


class PrivateBrowsingLockedError(Exception):
    """
    Raised when private tabs are locked with Face ID or a passcode, which Puma cannot unlock.
    """
    pass


def _open_private_tabs(driver: PumaDriver):
    """
    Opens the private tabs in the tab overview. On real devices, private browsing can be locked with Face ID. Puma
    cannot unlock it, so the Face ID prompt is cancelled and an exception is raised.
    """
    driver.click(PRIVATE_TAB_GROUP)
    if _wait_for(driver, FACE_ID_PROMPT, timeout=2):
        driver.click(FACE_ID_CANCEL)
        raise PrivateBrowsingLockedError(
            'Private browsing in Safari is locked with Face ID, which Puma cannot unlock. To use private tabs, turn off '
            '"Require Face ID to Unlock Private Browsing" in Settings > Apps > Safari.')


class CurrentTab(SimpleState, ContextualState):
    """
    A state representing a tab with a loaded web page.

    Like in Google Chrome on Android, the index of the tab cannot be read from the tab itself. Therefore the index of the
    last opened tab is stored per device, and used to validate the context.
    """

    def __init__(self, parent_state):
        super().__init__(xpaths=[ADDRESS_BAR, RELOAD_BUTTON, MORE_BUTTON],
                         parent_state=parent_state,
                         parent_state_transition=open_menu_item(MENU_ALL_TABS, 'go_to_tab_overview'))
        self.last_opened = {}

    def validate_context(self, driver: PumaDriver, tab_index: int = None) -> bool:
        if not tab_index:
            return True
        return self.last_opened.get(driver.udid) == tab_index

    def switch_to_tab(self, driver: PumaDriver, tab_index: int = None):
        """
        Opens a tab from the tab overview.

        :param driver: The PumaDriver instance.
        :param tab_index: The index of the tab in the tab overview, starting at 1. Defaults to the last tab.
        """
        index = tab_index if tab_index else 'last()'
        driver.click(f'({TAB_OVERVIEW_TAB})[{index}]')
        self.last_opened[driver.udid] = tab_index


@supported_version("26.2")
class Safari(StateGraph):
    """
    A class representing the Safari web browser on iOS.

    Like Google Chrome on Android, Safari does not fit the parent-child relationship of states very well, as most
    states can be reached from most other states. The tab overview is used as the parent of most states.
    This implementation targets the compact tab bar layout introduced in iOS 26 (address bar at the bottom).

    Note that pages loaded in a private tab cannot be distinguished from pages in a normal tab in the UI hierarchy.
    """
    platform = Platform.IOS

    # States
    tab_overview_state = SimpleState(xpaths=[TAB_OVERVIEW, TAB_OVERVIEW_NEW_TAB_BUTTON, STANDARD_TAB_GROUP_SELECTED])
    private_tab_overview_state = SimpleState(xpaths=[TAB_OVERVIEW, TAB_OVERVIEW_NEW_TAB_BUTTON, PRIVATE_TAB_GROUP_SELECTED],
                                             parent_state=tab_overview_state,
                                             parent_state_transition=compose_clicks([STANDARD_TAB_GROUP], 'go_to_tab_overview'))
    new_tab_state = SimpleState(xpaths=[ADDRESS_BAR, VOICE_SEARCH_BUTTON, MORE_BUTTON],
                                invalid_xpaths=[PRIVATE_BROWSING_START_PAGE],
                                initial_state=True,
                                parent_state=tab_overview_state,
                                parent_state_transition=open_menu_item(MENU_ALL_TABS, 'go_to_tab_overview'))
    new_private_tab_state = SimpleState(xpaths=[ADDRESS_BAR, PRIVATE_BROWSING_START_PAGE],
                                        parent_state=private_tab_overview_state,
                                        parent_state_transition=open_menu_item(MENU_ALL_TABS, 'go_to_private_tab_overview'))
    current_tab_state = CurrentTab(parent_state=tab_overview_state)
    bookmarks_state = SimpleState(xpaths=[BOOKMARKS_NAVIGATION_BAR, BOOKMARKS_TABLE, BOOKMARKS_DISMISS_BUTTON],
                                  parent_state=current_tab_state,
                                  parent_state_transition=compose_clicks([BOOKMARKS_DISMISS_BUTTON], 'close_bookmarks'))

    # Transitions
    tab_overview_state.to(new_tab_state, compose_clicks([TAB_OVERVIEW_NEW_TAB_BUTTON], 'open_new_tab'))
    tab_overview_state.to(current_tab_state, current_tab_state.switch_to_tab)
    tab_overview_state.to(private_tab_overview_state, _open_private_tabs)
    private_tab_overview_state.to(new_private_tab_state, compose_clicks([TAB_OVERVIEW_NEW_TAB_BUTTON], 'open_new_private_tab'))
    current_tab_state.to(new_tab_state, open_menu_item(MENU_NEW_TAB, 'open_new_tab'))
    current_tab_state.to(bookmarks_state, open_menu_item(MENU_BOOKMARKS, 'open_bookmarks'))

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Safari with a device UDID.

        :param device_udid: The unique device identifier of the iOS device or simulator.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, SAFARI_BUNDLE_ID, **kwargs)
        self.add_popup_handlers(simple_popup_handler(TAB_OVERVIEW_TIP_CLOSE),
                                PopUpHandler([SEARCH_FIRST_TIME_EXPERIENCE], [SEARCH_FIRST_TIME_CONTINUE]),
                                simple_popup_handler(LOCKED_PRIVATE_BROWSING_NOT_NOW))

    @action(current_tab_state)
    def visit_url(self, url_string: str, tab_index: int = None):
        """
        Visits a url in an existing tab.

        :param url_string: The url (or search terms) to enter in the address bar.
        :param tab_index: The index of the tab to use, starting at 1. Defaults to the last tab.
        """
        self._enter_url(url_string)

    @action(new_tab_state, end_state=current_tab_state)
    def visit_url_new_tab(self, url_string: str):
        """
        Opens a new tab and visits the url.

        :param url_string: The url (or search terms) to enter in the address bar.
        """
        self._enter_url(url_string)

    @action(new_private_tab_state, end_state=current_tab_state)
    def visit_url_private(self, url_string: str):
        """
        Opens a new private tab and visits the url.

        :param url_string: The url (or search terms) to enter in the address bar.
        """
        self._enter_url(url_string)

    @action(current_tab_state)
    def bookmark_page(self, tab_index: int = None):
        """
        Bookmarks the current page. Note that Safari allows adding the same page as a bookmark multiple times.

        :param tab_index: The index of the tab to use, starting at 1. Defaults to the last tab.
        """
        open_menu_item(MENU_ADD_TO_BOOKMARKS)(self.driver)
        # wait for the 'Added to Bookmarks' confirmation to disappear
        sleep(2)

    @action(bookmarks_state, end_state=current_tab_state)
    def load_bookmark(self, title: str):
        """
        Loads a bookmark in the current tab.

        :param title: The title of the bookmark to load.
        """
        self.driver.click(bookmark(title))
        sleep(1)

    @action(bookmarks_state)
    def delete_bookmark(self, title: str) -> bool:
        """
        Deletes a bookmark.

        :param title: The title of the bookmark to delete.
        :return: True if the bookmark has been deleted, False if there was no bookmark with this title.
        """
        if not self.driver.is_present(bookmark(title)):
            logger.info(f'There is no bookmark with title "{title}", skipping...')
            return False
        self.driver.long_click_element(bookmark(title), duration=1.5)
        # The context menu keeps animating its preview, so XCUITest waits 10 seconds for the app to become idle before
        # every click. Temporarily lower that timeout.
        idle_timeout = self.driver.driver.get_settings().get('waitForIdleTimeout', 10)
        self.driver.set_idle_timeout(1)
        try:
            self.driver.click(BOOKMARK_CONTEXT_MENU_DELETE)
        finally:
            self.driver.set_idle_timeout(idle_timeout)
        return True

    def _enter_url(self, url_string: str):
        self.driver.click(ADDRESS_BAR)
        # The first time the address bar is used, Safari explains its search suggestions
        if _wait_for(self.driver, ADDRESS_BAR_EDIT, 2) and self.driver.is_present(SEARCH_FIRST_TIME_CONTINUE):
            self.driver.click(SEARCH_FIRST_TIME_CONTINUE)
        self.driver.send_keys(ADDRESS_BAR_EDIT, url_string)
        self.driver.press_enter()
        sleep(2)
