import unittest
from unittest.mock import Mock, patch

from puma.apps.ios.app_store.app_store import SCREEN_TIMEOUT, AppPage, AppState, AppStore, AppStoreError, lookup_app_store_id
from puma.apps.ios.app_store.locators import CONFIRMATION_SHEET, CONFIRMATION_SHEET_CLOSE, \
    CONFIRMATION_SHEET_INSTALL, OFFER_BUTTON, OFFER_BUTTON_STARTED
from puma.utils.wait import wait_until


def _lookup_response(results: list) -> Mock:
    response = Mock()
    response.json.return_value = {'resultCount': len(results), 'results': results}
    return response


class TestLookupAppStoreId(unittest.TestCase):
    @patch('puma.apps.ios.app_store.app_store.requests.get')
    def test_lookup(self, get):
        get.return_value = _lookup_response([{'trackId': 570060128, 'trackName': 'Duolingo'}])
        self.assertEqual(570060128, lookup_app_store_id('com.duolingo.DuolingoMobile', 'nl'))
        self.assertEqual({'bundleId': 'com.duolingo.DuolingoMobile', 'country': 'nl'}, get.call_args.kwargs['params'])

    @patch('puma.apps.ios.app_store.app_store.requests.get')
    def test_app_not_found(self, get):
        get.return_value = _lookup_response([])
        with self.assertRaises(AppStoreError):
            lookup_app_store_id('com.example.unknown', 'nl')

    @patch('puma.apps.ios.app_store.app_store.requests.get')
    def test_invalid_country(self, get):
        for country in ['', 'n', 'nld', 'n1']:
            with self.subTest(country), self.assertRaises(ValueError):
                lookup_app_store_id('com.duolingo.DuolingoMobile', country)
        get.assert_not_called()

    @patch('puma.apps.ios.app_store.app_store.requests.get')
    def test_invalid_bundle_id(self, get):
        with self.assertRaises(ValueError):
            lookup_app_store_id('not a bundle id', 'nl')
        get.assert_not_called()


class TestAppPage(unittest.TestCase):
    def setUp(self):
        self.driver = Mock(udid='mock_udid')
        self.page = AppPage(parent_state=None)
        self.page.countries['mock_udid'] = 'nl'

    @patch('puma.apps.ios.app_store.app_store.lookup_app_store_id', return_value=570060128)
    def test_open_app_page(self, lookup):
        self.page.open_app_page(self.driver, 'com.duolingo.DuolingoMobile')
        lookup.assert_called_once_with('com.duolingo.DuolingoMobile', 'nl')
        self.driver.open_url.assert_called_once_with('itms-apps://apps.apple.com/app/id570060128')

    @patch('puma.apps.ios.app_store.app_store.lookup_app_store_id', return_value=570060128)
    def test_app_store_id_is_cached(self, lookup):
        self.page.open_app_page(self.driver, 'com.duolingo.DuolingoMobile')
        self.page.open_app_page(self.driver, 'com.duolingo.DuolingoMobile')
        lookup.assert_called_once()

    @patch('puma.apps.ios.app_store.app_store.lookup_app_store_id', return_value=1)
    def test_countries_are_per_device(self, lookup):
        self.page.countries['other_udid'] = 'us'
        self.page.open_app_page(Mock(udid='other_udid'), 'com.reddit.Reddit')
        lookup.assert_called_once_with('com.reddit.Reddit', 'us')
        lookup.reset_mock()
        self.page.open_app_page(self.driver, 'com.duolingo.DuolingoMobile')
        lookup.assert_called_once_with('com.duolingo.DuolingoMobile', 'nl')

    @patch('puma.apps.ios.app_store.app_store.lookup_app_store_id', return_value=1)
    def test_validate_context(self, _):
        self.assertTrue(self.page.validate_context(self.driver))
        self.assertFalse(self.page.validate_context(self.driver, 'com.duolingo.DuolingoMobile'))
        self.page.open_app_page(self.driver, 'com.duolingo.DuolingoMobile')
        self.assertTrue(self.page.validate_context(self.driver, 'com.duolingo.DuolingoMobile'))
        self.assertFalse(self.page.validate_context(self.driver, 'com.reddit.Reddit'))


class TestUninstall(unittest.TestCase):
    def setUp(self):
        self.app_store = AppStore.__new__(AppStore)
        self.app_store.driver = Mock(udid='mock_udid')
        self.app_store.gtl_logger = Mock()
        self.app_store.app_page_state.last_opened_app_page['mock_udid'] = 'com.duolingo.DuolingoMobile'

    def test_uninstall(self):
        self.app_store.driver.execute_script.return_value = True
        self.app_store.uninstall_app('com.duolingo.DuolingoMobile')
        self.app_store.driver.execute_script.assert_called_with('mobile: removeApp', {'bundleId': 'com.duolingo.DuolingoMobile'})
        self.assertNotIn('mock_udid', self.app_store.app_page_state.last_opened_app_page)

    def test_uninstall_not_installed_app(self):
        self.app_store.driver.execute_script.return_value = False
        self.app_store.uninstall_app('com.duolingo.DuolingoMobile')
        self.app_store.driver.execute_script.assert_called_once_with('mobile: isAppInstalled', {'bundleId': 'com.duolingo.DuolingoMobile'})
        self.app_store.gtl_logger.warn.assert_called_once()
        self.assertIn('mock_udid', self.app_store.app_page_state.last_opened_app_page)

    def test_uninstall_invalid_bundle_id(self):
        with self.assertRaises(ValueError):
            self.app_store.uninstall_app('not a bundle id')
        self.app_store.driver.execute_script.assert_not_called()


class TestUnknownState(unittest.TestCase):
    def setUp(self):
        self.app_store = AppStore.__new__(AppStore)
        self.app_store.driver = Mock()
        self.app_store.gtl_logger = Mock()
        self.app_store.driver.is_present.return_value = False  # no offer button found, so the state is unknown

    def test_install_with_unknown_state(self):
        with self.assertRaises(AppStoreError):
            self._call('install_app')
        self.app_store.driver.click.assert_not_called()

    def test_update_with_unknown_state(self):
        with self.assertRaises(AppStoreError):
            self._call('update_app')
        self.app_store.driver.click.assert_not_called()

    def _call(self, method: str):
        # call the method inside the @action decorator, so no state of the App Store is needed
        func = next(cell.cell_contents for cell in getattr(AppStore, method).__closure__
                    if callable(cell.cell_contents) and getattr(cell.cell_contents, '__name__', '') == method)
        func(self.app_store, 'com.example.app')


class TestConfirmation(unittest.TestCase):
    def setUp(self):
        self.app_store = AppStore.__new__(AppStore)
        self.app_store.driver = Mock()
        self.app_store.gtl_logger = Mock()

    def _present(self, *present):
        self.app_store.driver.is_present.side_effect = lambda locator: locator in present

    @patch('puma.apps.ios.app_store.app_store.sleep')
    def test_sheet_with_install_button_is_confirmed(self, _):
        # the sheet is shown first, after confirming the download starts
        shown = [CONFIRMATION_SHEET, CONFIRMATION_SHEET_INSTALL]
        self.app_store.driver.is_present.side_effect = lambda locator: locator in shown
        self.app_store.driver.click.side_effect = lambda locator: shown.clear() or shown.append(OFFER_BUTTON_STARTED)
        self.app_store._confirm_download('com.example.app')
        self.app_store.driver.click.assert_called_once_with(CONFIRMATION_SHEET_INSTALL)

    @patch('puma.apps.ios.app_store.app_store.sleep')
    def test_sheet_with_side_button_is_closed(self, _):
        self._present(CONFIRMATION_SHEET)
        with self.assertRaises(AppStoreError):
            self.app_store._confirm_download('com.example.app')
        self.app_store.driver.click.assert_called_once_with(CONFIRMATION_SHEET_CLOSE)

    @patch('puma.apps.ios.app_store.app_store.sleep')
    def test_download_started(self, _):
        self._present(OFFER_BUTTON_STARTED)
        self.app_store._confirm_download('com.example.app')
        self.app_store.driver.click.assert_not_called()

    @patch('puma.apps.ios.app_store.app_store.sleep')
    @patch('puma.apps.ios.app_store.app_store.time', side_effect=[0, 1, 5, 9])
    def test_nothing_happens(self, *_):
        self._present()
        self.app_store._confirm_download('com.example.app')
        self.app_store.driver.click.assert_not_called()


class TestWaitForInstallation(unittest.TestCase):
    def setUp(self):
        self.app_store = AppStore.__new__(AppStore)
        self.app_store.driver = Mock()
        self.app_store.gtl_logger = Mock()
        self.app_store._confirm_download = Mock()
        # the wait is run by the driver, which is a mock here. Run it with the real implementation.
        self.app_store.driver.wait_until.side_effect = lambda condition, timeout, **kwargs: wait_until(condition, timeout, interval=0)

    def _install_action(self, method: str):
        # the method inside the @action decorator, so no state of the App Store is needed
        func = next(cell.cell_contents for cell in getattr(AppStore, method).__closure__
                    if callable(cell.cell_contents) and getattr(cell.cell_contents, '__name__', '') == method)
        return lambda *args, **kwargs: func(self.app_store, *args, **kwargs)

    def _states(self, *states: AppState):
        self.app_store._get_app_state_internal = Mock(side_effect=list(states))

    def test_install_waits_until_installed(self):
        self._states(AppState.NOT_INSTALLED, AppState.NOT_INSTALLED, AppState.INSTALLING, AppState.UNKNOWN,
                     AppState.INSTALLING, AppState.INSTALLED)
        self._install_action('install_app')('com.example.app')
        self.app_store.driver.click.assert_called_once_with(OFFER_BUTTON)
        self.assertEqual(6, self.app_store._get_app_state_internal.call_count)

    def test_install_confirms_the_download_before_waiting(self):
        self._states(AppState.NOT_INSTALLED, AppState.INSTALLED)
        self._install_action('install_app')('com.example.app')
        self.app_store._confirm_download.assert_called_once_with('com.example.app')

    def test_install_waits_for_installation_in_progress(self):
        self._states(AppState.INSTALLING, AppState.INSTALLING, AppState.INSTALLED)
        self._install_action('install_app')('com.example.app')
        self.app_store.driver.click.assert_not_called()

    def test_install_times_out(self):
        self.app_store._get_app_state_internal = Mock(return_value=AppState.INSTALLING)
        self.app_store.driver.wait_until.side_effect = lambda condition, timeout, **kwargs: wait_until(condition, 0.05, interval=0.01)
        with self.assertRaises(TimeoutError):
            self._install_action('install_app')('com.example.app', timeout=0.05)

    def test_install_installed_app_does_not_wait(self):
        self._states(AppState.INSTALLED)
        self._install_action('install_app')('com.example.app')
        self.app_store.driver.click.assert_not_called()
        self.app_store.driver.wait_until.assert_not_called()

    def test_update_waits_until_installed(self):
        self._states(AppState.UPDATE_AVAILABLE, AppState.UPDATE_AVAILABLE, AppState.INSTALLING, AppState.INSTALLED)
        self._install_action('update_app')('com.example.app')
        self.app_store.driver.click.assert_called_once_with(OFFER_BUTTON)

    def test_update_without_update_does_not_wait(self):
        self._states(AppState.INSTALLED)
        self._install_action('update_app')('com.example.app')
        self.app_store.driver.click.assert_not_called()
        self.app_store.driver.wait_until.assert_not_called()


class TestAppState(unittest.TestCase):
    def _state(self, button_name: str | None) -> AppState:
        app_store = AppStore.__new__(AppStore)
        app_store.driver = Mock()
        app_store.driver.is_present.return_value = button_name is not None
        app_store.driver.get_element.return_value.get_attribute.return_value = button_name
        state = app_store._get_app_state_internal()
        app_store.driver.is_present.assert_called_with(OFFER_BUTTON, SCREEN_TIMEOUT)
        return state

    def test_app_states(self):
        expected = {'get': AppState.NOT_INSTALLED, 'redownload': AppState.NOT_INSTALLED, 'open': AppState.INSTALLED,
                    'update': AppState.UPDATE_AVAILABLE, 'loading': AppState.INSTALLING, 'waiting': AppState.INSTALLING,
                    'downloading': AppState.INSTALLING, 'installing': AppState.INSTALLING}
        for offer_state, app_state in expected.items():
            with self.subTest(offer_state):
                self.assertEqual(app_state, self._state(f'AppStore.offerButton[state={offer_state}]'))

    def test_unknown_states(self):
        self.assertEqual(AppState.UNKNOWN, self._state(None))
        self.assertEqual(AppState.UNKNOWN, self._state('AppStore.offerButton[state=surprise]'))
        self.assertEqual(AppState.UNKNOWN, self._state('Something else'))


if __name__ == '__main__':
    unittest.main()
