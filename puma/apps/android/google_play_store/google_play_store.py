from enum import Enum, StrEnum
from time import sleep

from puma.apps.android.google_play_store import logger
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.puma_driver import supported_version, PumaDriver
from puma.state_graph.state import SimpleState, compose_clicks, ContextualState
from puma.state_graph.state_graph import StateGraph
from puma.state_graph.utils import is_valid_package_name

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
GOOGLE_PLAY_POINTS_POPUP_HANDLER = PopUpHandler(
    ['//*[@text="Introducing google play points"]'],
    ['//*[@text="Not now"]'])
COMPLETE_ACCOUNT_POPUP_HANDLER = PopUpHandler(
    ['//*[@text="Complete account setup"]'],
    ['//*[@text="Continue"]', '//*[@text="Skip"]'])

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

# Diagnostic / other XPATHs
NOT_AVAILABLE_COUNTRY = '//*[@content-desc="This item is not available in your country."]'
SOMETHING_WENT_WRONG = '//*[@text="Something went wrong"]'
DEVICE_INCOMPATIBLE = '//*[@content-desc="Your device isn\'t compatible with this version."]'
PAID_APP = "//*[contains(@content-desc,'€') or contains(@content-desc,'$')]"
TOP_FOR_0_EURO = "//*[contains(@content-desc,'€0 ')]"
APP_PAGE_EXPECTED_BUTTONS = '//*[@content-desc="Uninstall" or @content-desc="Install" or @content-desc="Cancel"]'

class AppStatus(Enum):
    UNKNOWN = 0
    NOT_INSTALLED = 1
    INSTALLED = 2
    UPDATE_AVAILABLE = 3
    INSTALLING = 4
    INSTALLING_UPDATE = 5

class AllAppsStatus(StrEnum):
    CHECKING_FOR_UPDATES = "Checking for updates..."
    UPDATES_AVAILABLE = "Updates available"
    UPDATING_APPS = "Updating apps…"
    ALL_APPS_UP_TO_DATE = "All apps up to date"
    UNKNOWN = "Unknown"

class AppPage(SimpleState, ContextualState):
    """
    A state representing the app page of a specific application.

    This class extends both SimpleState and ContextualState, but the contextual aspect is an outlier. See the
    validate_context method.
    """
    def __init__(self, parent_state):
        """
        Initializes the App page state with a given parent state.

        :param parent_state: The parent state of this app page state.
        """
        super().__init__(
            xpaths=[HOME_SCREEN_TABS, APP_PAGE_THREE_DOTS],
            parent_state=parent_state,
            parent_state_transition=compose_clicks([APP_PAGE_NAVIGATE_UP], "navigate_up"))
        # keep a dict that tracks which app pages were opened last on which device. See validate_context()
        self.last_opened = {}

    def validate_context(self, driver: PumaDriver, package_name: str = None) -> bool:
        """
        The package name cannot be found in the UI, except by opening the share menu and checking the URL that can be
        shared. We do not want to use this, because that would mean triggering UI actions every time this contextual
        state is verified.
        Therefore, we opted to store the last opened package name for each device in this State. This means that the
        contextual state is not actually verified against the UI, but against the package name that was opened with the
        open_app_page method. When switching between two app pages, this works as long as the user does not interrupt
        Puma during these UI actions.

        :param driver: Puma driver
        :param package_name: package name
        :return boolean
        """
        if not package_name:
            return True
        return self.last_opened[driver.udid] == package_name

    def open_app_page(self, driver: PumaDriver, package_name: str = None):
        """
        Opens the app page for a specific package name. This is done by opening an intent, opening the URL of the app
        page in the play store application.
        This method also stores which package name's app page was opened on which device, enabling contextual validation
        in validate_context().

        :param driver: Puma driver
        :param package_name: package name
        """
        if not is_valid_package_name(package_name):
            raise ValueError(f'Invalid package name: {package_name}')
        driver.open_url(f'https://play.google.com/store/apps/details?id={package_name}', APPLICATION_PACKAGE)
        self.last_opened[driver.udid] = package_name


@supported_version("48.3.25-31")
class GooglePlayStore(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the Google Play Store.

    This class uses a state machine approach to manage transitions between different states
    of the Play store UI. It provides methods to navigate between states, validate states,
    and handle unexpected states or errors.
    """
    apps_tab_state = SimpleState([ACCOUNT_ICON, HOME_SCREEN_TABS, APPS_TAB_SELECTED], initial_state=True)
    profile_state = SimpleState([], parent_state=apps_tab_state)
    manage_apps_state = SimpleState([MANAGE_APP_STATE, MANAGE_APP_STATE_SYNC], parent_state=apps_tab_state)
    app_page_state = AppPage(parent_state=apps_tab_state)

    apps_tab_state.to(profile_state, compose_clicks([ACCOUNT_ICON], name='click_profile'))
    profile_state.to(manage_apps_state, compose_clicks([MANAGE_APPS_AND_DEVICES], name='click_manage_apps_and_devices'))
    app_page_state.from_states([apps_tab_state, profile_state, manage_apps_state], app_page_state.open_app_page)

    def __init__(self, device_udid):
        """
        Initializes the Google Play Store with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        """
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)
        self.add_popup_handler(PAYMENT_POPUP_HANDLER)
        self.add_popup_handler(LOCAL_RECOMMENDATIONS_POPUP_HANDLER)
        self.add_popup_handler(TRY_GOOGLE_PASS_POPUP_HANDLER)
        self.add_popup_handler(GOOGLE_PLAY_POINTS_POPUP_HANDLER)
        self.add_popup_handler(COMPLETE_ACCOUNT_POPUP_HANDLER)

    def _get_app_status_internal(self) -> AppStatus:
        """
        Util method for @action methods on the app_page_state.
        :return the AppState of the application page, based on found UI elements.
        """
        if self.driver.is_present(APP_PAGE_INSTALL_BUTTON):
            return AppStatus.NOT_INSTALLED
        if self.driver.is_present(APP_PAGE_UPDATE_BUTTON):
            return AppStatus.UPDATE_AVAILABLE
        if self.driver.is_present(APP_PAGE_UNINSTALL_BUTTON):
            return AppStatus.INSTALLED
        if self.driver.is_present(APP_PAGE_CANCEL_INSTALL_BUTTON):
            if self.driver.is_present(APP_PAGE_UNINSTALL_BUTTON):
                return AppStatus.INSTALLING_UPDATE
            else:
                return AppStatus.INSTALLING

        logger.error(f'Could not determine the install state of the current app.')
        return AppStatus.UNKNOWN

    @action(app_page_state)
    def get_app_status(self, package_name: str) -> AppStatus:
        """
        Returns the AppState of the given application. Possible states are:
        INSTALLED, NOT_INSTALLED, UPDATE_AVAILABLE, INSTALLING, INSTALL_UPDATE, and UNKNOWN.
        :return the AppState of the given application
        """
        state = self._get_app_status_internal()
        if state == AppStatus.UNKNOWN:
            try:
                self._log_why_app_page_not_available(package_name)
            except Exception:
                logger.exception("Exception while logging diagnostics for why app page is not available")

        return self._get_app_status_internal()

    @action(app_page_state)
    def install_app(self, package_name: str = None):
        """
        Installs the given application. If the application is already installed (or is being installed) this method
        will log a warning and do nothing.
        :param package_name: The exact package name of the application.
        """
        #TODO add check that the install button is present
        if self._get_app_status_internal() != AppStatus.NOT_INSTALLED:
            logger.warn(f'Tried to install app {package_name}, but it was already installed')
            return
        if self.driver.is_present(APP_PAGE_INSTALL_BUTTON):
            self.driver.click(APP_PAGE_INSTALL_BUTTON)
        else:
            logger.error(f"Could not install the application {package_name} because the install button was not present. "
                         f"Skipping...")
            return

    @action(app_page_state)
    def uninstall_app(self, package_name: str = None):
        """
        Uninstalls the given application. If the application is not installed this method will log a warning and do
        nothing.
        :param package_name: The exact package name of the application.
        """
        if self._get_app_status_internal() not in [AppStatus.INSTALLED, AppStatus.UPDATE_AVAILABLE]:
            logger.warn(f'Tried to uninstall app {package_name}, but it was not installed')
            return
        self.driver.click(APP_PAGE_UNINSTALL_BUTTON)
        self.driver.click(APP_PAGE_UNINSTALL_SURE_BUTTON)

    @action(app_page_state)
    def update_app(self, package_name: str = None):
        """
        Updates the given application. If no update is available this method will log a warning and do nothing.
        :param package_name: The exact package name of the application.
        """
        if self._get_app_status_internal() != AppStatus.UPDATE_AVAILABLE:
            logger.warn(f'Tried to update app {package_name}, but there is no update available')
            return
        self.driver.click(APP_PAGE_UPDATE_BUTTON)

    @action(manage_apps_state)
    def update_all_apps(self):
        """
        Updates all applications. If no updates are available this method will log a warning and do nothing.
        """
        if self.updates_available_all_apps:
            self.driver.click(UPDATE_ALL_BUTTON)
        else:
            if self.updating_all_apps:
                logger.warn('Tried to update all apps, but the updating was already in progress.')
            if self.all_apps_up_to_date:
                logger.warn('Tried to update all apps, but update button not visible. All apps are already up-to-date.')
            return

    @action(manage_apps_state)
    def get_update_all_apps_status(self):
        """
        Get the status of the update. Can be 'Updates available', 'Updating...' or 'All apps up to date'
        """
        if self.updates_available_all_apps():
            return AllAppsStatus.UPDATES_AVAILABLE
        if self.all_apps_up_to_date():
            return AllAppsStatus.ALL_APPS_UP_TO_DATE
        if self.checking_for_updates_all_apps():
            return AllAppsStatus.CHECKING_FOR_UPDATES
        if self.updating_all_apps():
            return AllAppsStatus.UPDATING_APPS
        logger.error('The status could not be determined.')
        return AllAppsStatus.UNKNOWN

    @action(manage_apps_state)
    def updates_available_all_apps(self) -> bool:
        """
        Checks whether there are updates available for all apps.
        :return: whether there are updates available
        """
        while self.driver.is_present(self._status_xpath(AllAppsStatus.CHECKING_FOR_UPDATES)):
            logger.info('Status is checking for updates, waiting...')
            sleep(2)
        return self.driver.is_present(self._status_xpath(AllAppsStatus.UPDATES_AVAILABLE))

    @action(manage_apps_state)
    def checking_for_updates_all_apps(self)-> bool:
        """
        Checks whether the status for all apps is checking for updates.
        :return: Whether the status is checking for updates
        """
        return self.driver.is_present(self._status_xpath(AllAppsStatus.CHECKING_FOR_UPDATES))

    @action(manage_apps_state)
    def updating_all_apps(self) -> bool:
        """
        Checks whether the status for all apps is updating.
        :return: Whether the status is updating
        """
        return self.driver.is_present(self._status_xpath(AllAppsStatus.UPDATING_APPS))

    @action(manage_apps_state)
    def all_apps_up_to_date(self) -> bool:
        """
        Checks whether all apps are up to date.
        :return: Whether all apps are up to date
        """
        return self.driver.is_present(self._status_xpath(AllAppsStatus.ALL_APPS_UP_TO_DATE))

    def _log_why_app_page_not_available(self, package_name):
        # app is not available in this country
        if self.driver.is_present(NOT_AVAILABLE_COUNTRY):
            logger.error(f'Could not install package {package_name} because it is not available in this country')
        # "Something went wrong" message: app doesn't seem to exist
        elif self.driver.is_present(SOMETHING_WENT_WRONG):
            logger.error(
                f'Could not install package {package_name} because the Play Store page doesn\'t seem to exist. Is the '
                f'package name correct?')
        # Device is not compatible with app version
        elif self.driver.is_present(DEVICE_INCOMPATIBLE):
            logger.error(
                f'Could not install package {package_name} because the device is not compatible with the app version. '
                f'This is probably because the phone is rooted.')
        else:
            # App is paid
            if self.driver.is_present(PAID_APP):
                # Add exception for the case when the euro sign is present in the context of: "#1 top for €0 in education"
                if not self.driver.is_present(TOP_FOR_0_EURO):
                    logger.error(
                        f'Could not install package {package_name} because it is a paid app. Paid apps are currently '
                        f'not supported')
                    return
            # Catch all other situations where the app page is not as expected
            if not self.driver.is_present(APP_PAGE_EXPECTED_BUTTONS):
                screenshot_path = self.driver.save_screenshot()
                logger.error(f"App page is not as expected, none of the expected buttons are present (see screenshot:"
                             f" {screenshot_path})")

    @staticmethod
    def _status_xpath(xpath: str) -> str:
        return f'//*[@text="{xpath}"]'