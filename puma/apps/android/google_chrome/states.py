from puma.apps.android.google_chrome import logger
from puma.apps.android.google_chrome.xpaths import TAB_SWITCH_BUTTON, TAB_LIST, URL_BAR, \
    NEW_TAB_FROM_CURRENT_TAB, BOOKMARKS_SORT_VIEW, BOOKMARKS_CREATE_FOLDER, BOOKMARKS_GO_BACK
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks


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
            xpaths=[URL_BAR, NEW_TAB_FROM_CURRENT_TAB],
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
