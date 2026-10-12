import re
from enum import Enum
from time import sleep, time

import requests

from puma.apps.ios.app_store import logger
from puma.apps.ios.app_store.locators import *
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph
from puma.state_graph.utils import is_valid_bundle_id

APP_STORE_BUNDLE_ID = 'com.apple.AppStore'
LOOKUP_URL = 'https://itunes.apple.com/lookup'
# The number of seconds to wait for a screen to load
SCREEN_TIMEOUT = 10
# The number of seconds to wait for a download to start, or for a confirmation to be asked
DOWNLOAD_START_TIMEOUT = 8
# The default number of seconds to wait for an installation or update. An action is tried twice when it fails, so a
# timeout makes the action take twice as long.
INSTALL_TIMEOUT = 120
_OFFER_STATE = re.compile(r'^AppStore\.offerButton\[state=(?P<state>[^\]]+)\]$')


class AppStoreError(Exception):
    """
    Raised when an app cannot be found in the App Store, or when its install state cannot be determined.
    """
    pass


def _open(button: str, screen: str, name: str):
    """
    Creates a transition that clicks a button, and waits until the screen it opens is shown. The account sheet and the
    update overview are loaded from the internet, so this can take a while.
    """
    def _open_screen(driver: PumaDriver):
        driver.click(button)
        driver.is_present(screen, SCREEN_TIMEOUT)
    _open_screen.__name__ = name
    return _open_screen


class AppState(Enum):
    # INSTALLING_UPDATE is never returned, the App Store does not show whether an update is being installed. It is only
    # present for parity with the Android Play Store.
    UNKNOWN = 0
    NOT_INSTALLED = 1
    INSTALLED = 2
    UPDATE_AVAILABLE = 3
    INSTALLING = 4
    INSTALLING_UPDATE = 5


# The state of the offer button on the page of an app. Apps that were installed before, and are not on the device
# anymore, have the state 'redownload'. The App Store does not show whether an update is being installed or not.
_APP_STATES = {
    'get': AppState.NOT_INSTALLED,
    'redownload': AppState.NOT_INSTALLED,
    'open': AppState.INSTALLED,
    'update': AppState.UPDATE_AVAILABLE,
    'loading': AppState.INSTALLING,
    'waiting': AppState.INSTALLING,
    'downloading': AppState.INSTALLING,
    'installing': AppState.INSTALLING,
}


def lookup_app_store_id(bundle_id: str, country: str) -> int:
    """
    Looks up the id of an app in the App Store, using the public iTunes lookup API. This needs an internet connection
    on the machine Puma runs on.

    :param bundle_id: The bundle id of the app, e.g. com.duolingo.DuolingoMobile.
    :param country: The two-letter country code of the App Store storefront. Apps are not available in all storefronts.
    :return: The App Store id of the app.
    :raises ValueError: If the bundle id or the country code is invalid.
    :raises AppStoreError: If the app was not found in the storefront.
    """
    if not is_valid_bundle_id(bundle_id):
        raise ValueError(f'Invalid bundle id: {bundle_id}')
    if not re.fullmatch(r'[A-Za-z]{2}', country):
        raise ValueError(f'Invalid country code, expected two letters: {country}')
    response = requests.get(LOOKUP_URL, params={'bundleId': bundle_id, 'country': country}, timeout=30)
    response.raise_for_status()
    results = response.json().get('results', [])
    if not results:
        raise AppStoreError(f'App {bundle_id} was not found in the {country} App Store')
    return results[0]['trackId']


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
            xpaths=[APP_PAGE_NAVIGATION_BAR],
            parent_state=parent_state,
            parent_state_transition=compose_clicks([BACK_BUTTON], 'back'))
        # keep a dict that tracks which app pages were opened last on which device. See validate_context()
        self.last_opened_app_page = {}
        # the country of the App Store of each device. This state is shared by all devices, so this cannot be a single value
        self.countries = {}
        self._app_store_ids = {}

    def validate_context(self, driver: PumaDriver, bundle_id: str = None) -> bool:
        """
        The bundle id of the app cannot be found in the UI. Therefore, we store the last opened bundle id for each device
        in this State. This means that the contextual state is not actually verified against the UI, but against the
        bundle id that was opened with the open_app_page method. When switching between two app pages, this works as
        long as the user does not interrupt Puma during these UI actions.

        :param driver: Puma driver
        :param bundle_id: bundle id
        :return boolean
        """
        if not bundle_id:
            return True
        return self.last_opened_app_page.get(driver.udid) == bundle_id

    def open_app_page(self, driver: PumaDriver, bundle_id: str):
        """
        Opens the app page for a specific bundle id, by opening the URL of the app in the App Store. The App Store id
        of the app is looked up first, as the URL needs it.
        This method also stores which bundle id's app page was opened on which device, enabling contextual validation
        in validate_context().

        :param driver: Puma driver
        :param bundle_id: bundle id
        """
        if bundle_id not in self._app_store_ids:
            self._app_store_ids[bundle_id] = lookup_app_store_id(bundle_id, self.countries[driver.udid])
        driver.open_url(f'itms-apps://apps.apple.com/app/id{self._app_store_ids[bundle_id]}')
        self.last_opened_app_page[driver.udid] = bundle_id
        driver.is_present(APP_PAGE_NAVIGATION_BAR, SCREEN_TIMEOUT)


@supported_version("26.6")
class AppStore(StateGraph):
    """
    A class representing the App Store application on iOS.

    Apps are identified by their bundle id, as with the other iOS applications. The App Store needs the id of an app to
    open its page. Puma looks this up with the iTunes lookup API, which needs an internet connection on the machine Puma
    runs on.
    """

    today_state = SimpleState(xpaths=[TODAY_NAVIGATION_BAR, ACCOUNT_BUTTON],
                              invalid_xpaths=[ACCOUNT_CLOSE_BUTTON, UPDATES_NAVIGATION_BAR], initial_state=True)
    # Any other tab than Today, which has no account button. Product pages show the tab bar as well.
    other_tab_state = SimpleState(xpaths=[OTHER_TAB_SELECTED],
                                  invalid_xpaths=[APP_PAGE_NAVIGATION_BAR, ACCOUNT_CLOSE_BUTTON, UPDATES_NAVIGATION_BAR],
                                  parent_state=today_state, parent_state_transition=compose_clicks([TODAY_TAB], 'open_today'))
    account_state = SimpleState(xpaths=[ACCOUNT_CLOSE_BUTTON, ACCOUNT_UPDATES_BUTTON], parent_state=today_state,
                                parent_state_transition=compose_clicks([ACCOUNT_CLOSE_BUTTON], 'close_account'))
    updates_state = SimpleState(xpaths=[UPDATES_NAVIGATION_BAR], parent_state=account_state,
                                parent_state_transition=compose_clicks([BACK_BUTTON], 'back'))
    app_page_state = AppPage(parent_state=today_state)

    today_state.to(account_state, _open(ACCOUNT_BUTTON, ACCOUNT_CLOSE_BUTTON, 'open_account'))
    account_state.to(updates_state, _open(ACCOUNT_UPDATES_BUTTON, UPDATES_NAVIGATION_BAR, 'open_updates'))
    app_page_state.from_states([today_state, other_tab_state, account_state, updates_state], app_page_state.open_app_page)

    def __init__(self, device_udid: str, country: str, **kwargs):
        """
        Initializes the App Store with a device UDID.

        :param device_udid: The unique device identifier of the iOS device.
        :param country: The two-letter country code of the App Store storefront of the device, e.g. 'nl'. Used to look up
        apps. An app that is not in this storefront cannot be installed.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, APP_STORE_BUNDLE_ID, **kwargs)
        self.app_page_state.countries[device_udid] = country

    def _get_app_state_internal(self, log_unknown: bool = True) -> AppState:
        """
        Util method for @action methods on the app_page_state.
        :param log_unknown: Whether to log an error when the state cannot be determined.
        :return the AppState of the application page, based on the offer button.
        """
        if not self.driver.is_present(OFFER_BUTTON, SCREEN_TIMEOUT):
            if log_unknown:
                logger.error('Could not find the offer button of the current app.')
            return AppState.UNKNOWN
        name = self.driver.get_element(OFFER_BUTTON).get_attribute('name')
        match = _OFFER_STATE.match(name)
        app_state = _APP_STATES.get(match.group('state') if match else None)
        if not app_state:
            if log_unknown:
                logger.error(f'Could not determine the install state of the current app, the offer button is {name}.')
            return AppState.UNKNOWN
        return app_state

    def _wait_for_installation(self, bundle_id: str, timeout: int):
        """
        Waits until an installation or update has finished, which is when the offer button of the app page shows Open.
        An unknown state is regarded as not finished, as the offer button is briefly replaced while it changes.
        :param bundle_id: The bundle id of the application.
        :param timeout: The maximum time to wait, in seconds.
        :raises TimeoutError: If the installation or update did not finish within the timeout.
        """
        self.driver.wait_until(lambda: self._get_app_state_internal(log_unknown=False) == AppState.INSTALLED,
                               timeout, description=f'app {bundle_id} to be installed')

    @action(app_page_state)
    def get_app_state(self, bundle_id: str) -> AppState:
        """
        Returns the AppState of the given application. Possible states are:
        INSTALLED, NOT_INSTALLED, UPDATE_AVAILABLE, INSTALLING, and UNKNOWN. Apps that are being updated are
        INSTALLING, as the App Store does not distinguish this.
        :param bundle_id: The bundle id of the application.
        :return the AppState of the given application
        """
        return self._get_app_state_internal()

    def _confirm_download(self, bundle_id: str):
        """
        Waits until the download has started after clicking Get. The first time an app is downloaded, iOS shows a sheet
        to confirm the download. If it has an Install button, this method clicks it. If it asks to confirm with the side
        button, Face ID or a password, Puma cannot do that, so the sheet is closed.
        :param bundle_id: The bundle id of the application.
        :raises AppStoreError: If the download needs a confirmation Puma cannot give.
        """
        end = time() + DOWNLOAD_START_TIMEOUT
        while time() < end:
            if self.driver.is_present(CONFIRMATION_SHEET):
                if self.driver.is_present(CONFIRMATION_SHEET_INSTALL):
                    self.gtl_logger.info(f'Confirming the download of {bundle_id}')
                    self.driver.click(CONFIRMATION_SHEET_INSTALL)
                else:
                    self.driver.click(CONFIRMATION_SHEET_CLOSE)
                    raise AppStoreError(f'Could not install app {bundle_id}, iOS asked to confirm the download with the '
                                        f'side button, Face ID or a password. Turn this off for downloads, see the '
                                        f'README of the App Store.')
            elif self.driver.is_present(OFFER_BUTTON_STARTED):
                return
            sleep(0.5)

    @action(app_page_state)
    def install_app(self, bundle_id: str, timeout: int = INSTALL_TIMEOUT):
        """
        Installs the given application, and waits until it has been installed. If the application is already installed
        this method will log a warning and do nothing. If it is being installed, this method waits until it has been
        installed.

        Puma cannot confirm the installation with Face ID, Touch ID or a password. Turn these off for free downloads,
        see the README.
        :param bundle_id: The bundle id of the application.
        :param timeout: The maximum time to wait for the installation to finish, in seconds.
        :raises AppStoreError: If the install state of the app cannot be determined, or if iOS asks for a
        confirmation Puma cannot give.
        :raises TimeoutError: If the installation did not finish within the timeout.
        """
        app_state = self._get_app_state_internal()
        if app_state == AppState.UNKNOWN:
            raise AppStoreError(f'Could not install app {bundle_id}, its install state is unknown')
        if app_state == AppState.INSTALLING:
            self._wait_for_installation(bundle_id, timeout)
            return
        # Not only INSTALLED: with UPDATE_AVAILABLE the offer button is the Update button, which must not be clicked here
        if app_state != AppState.NOT_INSTALLED:
            self.gtl_logger.warn(f'Tried to install app {bundle_id}, but it was already installed')
            return
        self.driver.click(OFFER_BUTTON)
        self._confirm_download(bundle_id)
        self._wait_for_installation(bundle_id, timeout)

    @action(app_page_state)
    def update_app(self, bundle_id: str, timeout: int = INSTALL_TIMEOUT):
        """
        Updates the given application, and waits until it has been updated. If no update is available this method will
        log a warning and do nothing. If it is being updated, this method waits until it has been updated.
        :param bundle_id: The bundle id of the application.
        :param timeout: The maximum time to wait for the update to finish, in seconds.
        :raises AppStoreError: If the install state of the app cannot be determined.
        :raises TimeoutError: If the update did not finish within the timeout.
        """
        app_state = self._get_app_state_internal()
        if app_state == AppState.UNKNOWN:
            raise AppStoreError(f'Could not update app {bundle_id}, its install state is unknown')
        if app_state == AppState.INSTALLING:
            self._wait_for_installation(bundle_id, timeout)
            return
        if app_state != AppState.UPDATE_AVAILABLE:
            self.gtl_logger.warn(f'Tried to update app {bundle_id}, but there is no update available')
            return
        self.driver.click(OFFER_BUTTON)
        self._wait_for_installation(bundle_id, timeout)

    def uninstall_app(self, bundle_id: str):
        """
        Uninstalls the given application. If the application is not installed this method will log a warning and do
        nothing. The App Store itself cannot remove apps, so the app is removed by Appium. This does not need the page
        of the app, so it also works without internet and for apps that are not in the App Store.

        This method is not an @action, as it needs no state in the App Store. It does log the same ground truth log
        lines as an action.
        :param bundle_id: The bundle id of the application.
        """
        if not is_valid_bundle_id(bundle_id):
            raise ValueError(f'Invalid bundle id: {bundle_id}')
        action_description = f"'uninstall_app' with arguments: ('{bundle_id}',) and keyword arguments: {{}} for application: AppStore"
        self.gtl_logger.info(f'Executing action {action_description}')
        if not self.driver.execute_script('mobile: isAppInstalled', {'bundleId': bundle_id}):
            self.gtl_logger.warn(f'Tried to uninstall app {bundle_id}, but it was not installed')
        else:
            self.driver.execute_script('mobile: removeApp', {'bundleId': bundle_id})
            # The page of the app, if open, still shows the old state. Make sure it is opened again
            self.app_page_state.last_opened_app_page.pop(self.driver.udid, None)
        self.gtl_logger.info(f'Executed action {action_description}')

    @action(updates_state)
    def update_all_apps(self):
        """
        Updates all applications. If no updates are available this method will log a warning and do nothing.
        """
        if not self.driver.is_present(UPDATES_UPDATE_ALL_CELL, SCREEN_TIMEOUT):
            self.gtl_logger.warn('Tried to update all apps, but update button not visible. All apps are probably up-to-date.')
            return
        self.driver.click(UPDATES_UPDATE_ALL_CELL)
