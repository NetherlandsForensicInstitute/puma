import re
from enum import Enum

from puma.apps.android.google_play_store import logger
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

APP_PAGE_INSTALL_BUTTON = '//android.view.View[@content-desc="Install"]'
APP_PAGE_UNINSTALL_BUTTON = '//android.view.View[@content-desc="Uninstall"]'
APP_PAGE_UNINSTALL_SURE_BUTTON = '//android.view.View[@content-desc="Uninstall"]'
APP_PAGE_UPDATE_BUTTON = '//android.view.View[@content-desc="Update"]'
APP_PAGE_CANCEL_INSTALL_BUTTON = '//android.view.View[@content-desc="Cancel"]'
APP_PAGE_THREE_DOTS = '//android.view.View[@content-desc="More options"]'
APP_PAGE_NAVIGATE_UP = '//android.view.View[@content-desc="Navigate up"]'

UPDATE_ALL_BUTTON = '//android.view.View[@content-desc="Update all"]'
MANAGE_APP_STATE = '//android.widget.TextView[@text="Manage apps and device"]'
MANAGE_APP_STATE_SYNC = '//android.widget.TextView[@text="Sync apps to devices"]'
MANAGE_APPS_AND_DEVICES = '//android.widget.TextView[@resource-id="com.android.vending:id/0_resource_name_obfuscated" and @text="Manage apps and device"]'


class AppState(Enum):
    UNKNOWN = 0
    NOT_INSTALLED = 1
    INSTALLED = 2
    UPDATE_AVAILABLE = 3
    INSTALLING = 4
    INSTALLING_UPDATE = 5


class AppPage(SimpleState, ContextualState):
    def __init__(self, parent_state):
        """
        Initializes the App page state with a given parent state.

        :param parent_state: The parent state of this app page state.
        """
        super().__init__(
            xpaths=[HOME_SCREEN_TABS, APP_PAGE_THREE_DOTS],
            parent_state=parent_state,
            parent_state_transition=compose_clicks([APP_PAGE_NAVIGATE_UP], "navigate_up"))
        # keep a dict that tracks which app pages were opened last on which device. This is to make the contextual
        # validation work in most cases.
        self.last_opened = {}

    @staticmethod
    def _is_valid_package_name(package_name: str) -> bool:
        pattern = r'^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$'
        return bool(re.fullmatch(pattern, package_name)) and len(package_name) <= 100

    def open_app_page(self, driver: PumaDriver, package_name: str = None):
        if not self._is_valid_package_name(package_name):
            raise ValueError(f'Invalid package name: {package_name}')
        driver.open_url(f'https://play.google.com/store/apps/details?id={package_name}', APPLICATION_PACKAGE)
        self.last_opened[driver.udid] = package_name

    def validate_context(self, driver: PumaDriver, package_name: str = None) -> bool:
        if not package_name:
            return True
        return self.last_opened[driver.udid] == package_name


@supported_version("48.3.25-31")
class GooglePlayStore(StateGraph):
    apps_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, APPS_TAB_SELECTED], initial_state=True)
    profile_state = SimpleState([], parent_state=apps_tab_state)
    manage_apps_state = SimpleState([MANAGE_APP_STATE, MANAGE_APP_STATE_SYNC], parent_state=apps_tab_state)
    app_page_state = AppPage(parent_state=apps_tab_state)

    apps_tab_state.to(profile_state, compose_clicks([ACCOUNT_ICON], name='click_profile'))
    profile_state.to(manage_apps_state, compose_clicks([MANAGE_APPS_AND_DEVICES], name='click_manage_apps_and_devices'))
    app_page_state.from_states([apps_tab_state, profile_state, manage_apps_state], app_page_state.open_app_page)

    def __init__(self, device_udid):
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)
        self.add_popup_handler(PAYMENT_POPUP_HANDLER)
        self.add_popup_handler(LOCAL_RECOMMENDATIONS_POPUP_HANDLER)
        self.add_popup_handler(TRY_GOOGLE_PASS_POPUP_HANDLER)

    def _get_app_state_internal(self):
        if self.driver.is_present(APP_PAGE_INSTALL_BUTTON):
            return AppState.NOT_INSTALLED
        if self.driver.is_present(APP_PAGE_UPDATE_BUTTON):
            return AppState.UPDATE_AVAILABLE
        if self.driver.is_present(APP_PAGE_UNINSTALL_BUTTON):
            return AppState.INSTALLED
        if self.driver.is_present(APP_PAGE_CANCEL_INSTALL_BUTTON):
            if self.driver.is_present(APP_PAGE_UNINSTALL_BUTTON):
                return AppState.INSTALLING_UPDATE
            else:
                return AppState.INSTALLING
        logger.error(f'Could not determine the install state of the current app.')
        return AppState.UNKNOWN

    @action(app_page_state)
    def get_app_state(self, package_name: str) -> AppState:
        return self._get_app_state_internal()

    @action(app_page_state)
    def install_app(self, package_name: str = None):
        if self._get_app_state_internal() != AppState.NOT_INSTALLED:
            logger.warn(f'Tried to install app {package_name}, but it was already installed')
            return
        self.driver.click(APP_PAGE_INSTALL_BUTTON)

    @action(app_page_state)
    def uninstall_app(self, package_name: str = None):
        if self._get_app_state_internal() not in [AppState.INSTALLED, AppState.UPDATE_AVAILABLE]:
            logger.warn(f'Tried to uninstall app {package_name}, but it was not installed')
            return
        self.driver.click(APP_PAGE_UNINSTALL_BUTTON)
        self.driver.click(APP_PAGE_UNINSTALL_SURE_BUTTON)

    @action(app_page_state)
    def update_app(self, package_name: str = None):
        if self._get_app_state_internal() != AppState.UPDATE_AVAILABLE:
            logger.warn(f'Tried to update app {package_name}, but there is no update available')
            return
        self.driver.click(APP_PAGE_UPDATE_BUTTON)

    @action(manage_apps_state)
    def update_all_apps(self):
        self.driver.click(UPDATE_ALL_BUTTON)
