import re

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

SEARCH_STATE_SEARCH_BOX = '//android.widget.EditText'
VOICE_SEARCH_BUTTON = '//android.view.View[@content-desc="Voice Search"]'

APP_PAGE_REVIEWS_BADGE = '//android.view.View[starts-with(@content-desc, "Average rating") and ends-with(@content-desc, "reviews")]'
APP_PAGE_DOWNLOADS_BADGE = '//android.view.View[starts-with(@content-desc, "Downloaded")]'
APP_PAGE_CONTENT_RATING_BADGE = '//android.view.View[starts-with(@content-desc, "Content rating")]'
APP_PAGE_INSTALL_BUTTON = '//android.view.View[@content-desc="Install"]'


class AppPage(SimpleState, ContextualState):
    def __init__(self, parent_state):
        """
        Initializes the App page state with a given parent state.

        :param parent_state: The parent state of this app page state.
        """
        super().__init__(
            xpaths=[HOME_SCREEN_TABS, APP_PAGE_INSTALL_BUTTON, APP_PAGE_REVIEWS_BADGE, APP_PAGE_DOWNLOADS_BADGE,
                    APP_PAGE_CONTENT_RATING_BADGE],
            parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, app_name: str = None) -> bool:
        if not app_name:
            return True
        actual_app_name = driver.get_element('(//android.widget.TextView[@text])[1]').get_attribute('text')
        return app_name.lower() in actual_app_name.lower()


@supported_version("")
class PlayStore(StateGraph):
    apps_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, APPS_TAB_SELECTED], initial_state=True)
    search_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, SEARCH_TAB_SELECTED])
    games_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, GAMES_TAB_SELECTED])
    books_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, BOOKS_TAB_SELECTED])

    search_page_state = SimpleState([SEARCH_STATE_SEARCH_BOX, VOICE_SEARCH_BUTTON], parent_state=search_tab_state)

    apps_tab_state.from_states([search_tab_state, games_tab_state, books_tab_state], compose_clicks([APPS_TAB_BUTTON], name='click_apps_tab'))
    search_tab_state.from_states([apps_tab_state, games_tab_state, books_tab_state], compose_clicks([SEARCH_TAB_BUTTON], name='click_search_tab'))
    games_tab_state.from_states([apps_tab_state, search_tab_state, books_tab_state], compose_clicks([GAMES_TAB_BUTTON], name='click_games_tab'))
    books_tab_state.from_states([apps_tab_state, search_tab_state, games_tab_state], compose_clicks([BOOKS_TAB_BUTTON], name='click_books_tab'))

    search_tab_state.to(search_page_state, compose_clicks([SEARCH_TAB_BUTTON], name='click_search_tab'))

    # search_tab_state.to(app_page_state, None)  # TODO: transition: as action or somehow else? State accessible from anywhere by opening the URL?

    def __init__(self, device_udid):
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)
        self.add_popup_handler(PAYMENT_POPUP_HANDLER)

    # TODO: do we want this kind of action that is not based on UI actions?
    def _is_valid_package_name(package_name: str) -> bool:
        pattern = r'^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$'
        return bool(re.fullmatch(pattern, package_name)) and len(package_name) <= 100

    def open_app_page(self, package_name: str):
        if not self._is_valid_package_name(package_name):
            raise ValueError(f'Invalid package name for app: {package_name}')
        self.driver.open_url(f'https://play.google.com/store/apps/details?id={package_name}')
        self.current_state = PlayStore.app_page_state
