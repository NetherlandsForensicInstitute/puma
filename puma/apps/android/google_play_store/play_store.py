import re
from time import sleep

from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.puma_driver import supported_version, PumaDriver
from puma.state_graph.state import SimpleState, compose_clicks, ContextualState
from puma.state_graph.state_graph import StateGraph

APPLICATION_PACKAGE = 'com.android.vending'

PAYMENT_POPUP_HANDLER = PopUpHandler(['//android.widget.TextView[@text="Pay your way with Google Play"]',
                                      '//android.widget.ImageView[@content-desc="close"]'],
                                     ['//android.widget.ImageView[@content-desc="close"]'])
LOCAL_RECOMMENDATIONS_POPUP_HANDLER = PopUpHandler(
    ['//android.widget.TextView[@text="Want to see local recommendations in Google Play?"]',
     '//android.widget.Button[@text="No thanks"]'], ['//android.widget.Button[@text="No thanks"]'])
TRY_GOOGLE_PASS_POPUP_HANDLER = PopUpHandler(
    ['//android.widget.TextView[@resource-id="com.android.vending:id/0_resource_name_obfuscated" and @text="Try Google Play Pass"]'],
    ['//android.widget.Button[@resource-id="com.android.vending:id/0_resource_name_obfuscated" and @text="Not now"]'])

ACCOUNT_ICON = '//android.widget.FrameLayout[starts-with(@content-desc, "Signed in as")]'

HOME_SCREEN_TABS = '(//android.view.View[count(.//android.widget.TextView[@text="Games" or @text="Apps" or @text="Search" or @text="Books"]) = 4])[last()]'
APPS_TAB_SELECTED = '//android.view.View[.//android.widget.ImageView[@selected="true"] and ./android.widget.TextView[@text="Apps"]]'
GAMES_TAB_SELECTED = '//android.view.View[.//android.widget.ImageView[@selected="true"] and ./android.widget.TextView[@text="Games"]]'
SEARCH_TAB_SELECTED = '//android.view.View[.//android.widget.ImageView[@selected="true"] and ./android.widget.TextView[@text="Search"]]'
BOOKS_TAB_SELECTED = '//android.view.View[.//android.widget.ImageView[@selected="true"] and ./android.widget.TextView[@text="Books"]]'

APPS_TAB_BUTTON = '//android.view.View[./android.widget.TextView[@text="Apps"]]'
SEARCH_TAB_BUTTON = '//android.view.View[./android.widget.TextView[@text="Search"]]'
GAMES_TAB_BUTTON = '//android.view.View[./android.widget.TextView[@text="Games"]]'
BOOKS_TAB_BUTTON = '//android.view.View[./android.widget.TextView[@text="Books"]]'

SEARCH_RESULT_STATE_BOX = '//android.widget.TextView'
SEARCH_RESULT_STATE_FIRST_RESULT_OPEN_OR_INSTALL = '//android.widget.TextView[@text="Open" or @text="Install"]'
# TODO: Check if this works if the first result is sponsored
SEARCH_RESULT_STATE_FIRST_RESULT = '//androidx.compose.ui.platform.ComposeView[@resource-id="com.android.vending:id/0_resource_name_obfuscated"]/android.view.View/android.view.View[1]/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.view.View[1]'

SEARCH_STATE_SEARCH_ICON = '//android.view.View[@content-desc="Search Google Play"]'
SEARCH_STATE_SEARCH_BOX = '//android.widget.EditText'
VOICE_SEARCH_BUTTON = '//android.view.View[@content-desc="Voice Search"]'

APP_PAGE_REVIEWS_BADGE = '//android.view.View[starts-with(@content-desc, "Average rating") and ends-with(@content-desc, "reviews")]'
APP_PAGE_DOWNLOADS_BADGE = '//android.view.View[starts-with(@content-desc, "Downloaded")]'
APP_PAGE_CONTENT_RATING_BADGE = '//android.view.View[starts-with(@content-desc, "Content rating")]'
APP_PAGE_INSTALL_BUTTON = '//android.view.View[@content-desc="Install"]'
APP_PAGE_UNINSTALL_BUTTON = '//android.view.View[@content-desc="Uninstall"]'
APP_PAGE_UNINSTALL_SURE_BUTTON = '//android.view.View[@content-desc="Uninstall"]'
APP_PAGE_OPEN_BUTTON = '//android.view.View[@content-desc="Open"]'
APP_PAGE_UPDATE_BUTTON = '//android.view.View[@content-desc="Update"]'
APP_PAGE_ABOUT_THIS_APP = '//android.widget.TextView[@text="About this app"]'
APP_PAGE_THREE_DOTS = '//android.view.View[@content-desc="More options"]'

UPDATE_ALL_BUTTON = '//android.view.View[@content-desc="Update all"]'
MANAGE_APP_STATE = '//android.widget.TextView[@text="Manage apps and device"]'
MANAGE_APP_STATE_SYNC = '//android.widget.TextView[@text="Sync apps to devices"]'
MANAGE_APPS_AND_DEVICES = '//android.widget.TextView[@resource-id="com.android.vending:id/0_resource_name_obfuscated" and @text="Manage apps and device"]'


def search_app(driver: PumaDriver, app_name: str = None):
    driver.send_keys(SEARCH_STATE_SEARCH_BOX, app_name)
    driver.press_enter()

class AppPage(SimpleState, ContextualState):
    def __init__(self, parent_state):
        """
        Initializes the App page state with a given parent state.

        :param parent_state: The parent state of this app page state.
        """
        super().__init__(
            xpaths=[HOME_SCREEN_TABS, APP_PAGE_THREE_DOTS],
            parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, app_name: str = None) -> bool:
        if not app_name:
            return True
        actual_app_name = driver.get_element('(//android.widget.TextView[@text])[1]').get_attribute('text') # When app is not installed
        actual_app_name2 = driver.get_element('(//android.view.View[@text])[9]').get_attribute('content-desc') # When app is installed
        return app_name.lower() in actual_app_name.lower() or app_name.lower() in actual_app_name2.lower()

class SearchResult(SimpleState, ContextualState):
    def __init__(self, parent_state):
        """
        Initializes the App page state with a given parent state.

        :param parent_state: The parent state of this app page state.
        """
        super().__init__(
            xpaths=[SEARCH_RESULT_STATE_BOX, SEARCH_STATE_SEARCH_ICON, VOICE_SEARCH_BUTTON],
            parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, app_name: str = None) -> bool:
        if not app_name:
            return True
        actual_search_app_name = driver.get_element('//androidx.compose.ui.platform.ComposeView[@resource-id="com.android.vending:id/0_resource_name_obfuscated"]/android.view.View/android.view.View[1]/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[2]/android.view.View/android.view.View[2]/android.view.View[1]/android.widget.TextView').get_attribute('text')
        driver.gtl_logger.warning(f'actual_search_app_name: {actual_search_app_name}')
        return app_name.lower() in actual_search_app_name.lower()



@supported_version("")
class PlayStore(StateGraph):
    apps_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, APPS_TAB_SELECTED], initial_state=True)
    search_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, SEARCH_TAB_SELECTED])
    games_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, GAMES_TAB_SELECTED])
    books_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, BOOKS_TAB_SELECTED])

    search_page_state = SimpleState([SEARCH_STATE_SEARCH_BOX, VOICE_SEARCH_BUTTON], parent_state=search_tab_state)
    search_result_state = SearchResult(parent_state=search_tab_state)

    profile_state = SimpleState([], parent_state=apps_tab_state)
    manage_apps_state = SimpleState([MANAGE_APP_STATE, MANAGE_APP_STATE_SYNC], parent_state=apps_tab_state)

    # TODO: Contextual state without parent state is not allowed. However, the app page state does not have a defined parent state.
    app_page_state = AppPage(parent_state=search_result_state)

    apps_tab_state.from_states([search_tab_state, games_tab_state, books_tab_state, search_result_state, app_page_state], compose_clicks([APPS_TAB_BUTTON], name='click_apps_tab'))
    search_tab_state.from_states([apps_tab_state, games_tab_state, books_tab_state, app_page_state], compose_clicks([SEARCH_TAB_BUTTON], name='click_search_tab'))
    games_tab_state.from_states([apps_tab_state, search_tab_state, books_tab_state, search_result_state, app_page_state], compose_clicks([GAMES_TAB_BUTTON], name='click_games_tab'))
    books_tab_state.from_states([apps_tab_state, search_tab_state, games_tab_state, search_result_state, app_page_state], compose_clicks([BOOKS_TAB_BUTTON], name='click_books_tab'))

    search_tab_state.to(search_page_state, compose_clicks([SEARCH_TAB_BUTTON], name='click_search_tab'))
    search_page_state.to(search_result_state, search_app)
    search_result_state.to(app_page_state, compose_clicks([SEARCH_RESULT_STATE_FIRST_RESULT], name='click_first_result'))

    profile_state.from_states([search_tab_state, games_tab_state, books_tab_state, app_page_state], compose_clicks([ACCOUNT_ICON], name='click_profile'))
    profile_state.to(manage_apps_state, compose_clicks([MANAGE_APPS_AND_DEVICES], name='click_manage_apps_and_devices'))

    # search_tab_state.to(app_page_state, None)  # TODO: transition: as action or somehow else? State accessible from anywhere by opening the URL?

    def __init__(self, device_udid):
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)
        self.add_popup_handler(PAYMENT_POPUP_HANDLER)
        self.add_popup_handler(LOCAL_RECOMMENDATIONS_POPUP_HANDLER)
        self.add_popup_handler(TRY_GOOGLE_PASS_POPUP_HANDLER)

    # TODO: do we want this kind of action that is not based on UI actions?
    def _is_valid_package_name(self, package_name: str) -> bool:
        pattern = r'^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$'
        return bool(re.fullmatch(pattern, package_name)) and len(package_name) <= 100

    def open_app_page(self, package_name: str):
        if not self._is_valid_package_name(package_name):
            raise ValueError(f'Invalid package name for app: {package_name}')
        self.driver.open_url(f'https://play.google.com/store/apps/details?id={package_name}')
        self.current_state = PlayStore.app_page_state

    @action(app_page_state)
    def open_app(self, app_name: str = None):
        self.driver.click(APP_PAGE_OPEN_BUTTON)

    @action(app_page_state)
    def install_app(self, app_name: str = None):
        self.driver.click(APP_PAGE_INSTALL_BUTTON)

    @action(app_page_state)
    def uninstall_app(self, app_name: str = None):
        self.driver.click(APP_PAGE_UNINSTALL_BUTTON)
        self.driver.click(APP_PAGE_UNINSTALL_SURE_BUTTON)

    @action(app_page_state)
    def update_app(self, app_name: str = None):
        self.driver.click(APP_PAGE_UPDATE_BUTTON)

    @action(manage_apps_state)
    def update_all_apps(self):
        self.driver.click(UPDATE_ALL_BUTTON)
