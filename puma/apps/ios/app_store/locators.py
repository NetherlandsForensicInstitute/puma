from puma.state_graph.locators import accessibility_id, ios_class_chain, ios_predicate

# Tabs. The account sheet and the product pages are shown on top of the tabs. The tab buttons are named 'Today' or
# 'AppStore.tabBar.today', depending on the situation
TODAY_TAB = ios_predicate('type == "XCUIElementTypeButton" AND (name == "Today" OR name == "AppStore.tabBar.today")')
# The Today tab, when another tab is selected. The selected tab has the value 1
OTHER_TAB_SELECTED = ios_class_chain('**/XCUIElementTypeTabBar/**/XCUIElementTypeButton'
                                     '[`(name == "Today" OR name == "AppStore.tabBar.today") AND value != "1"`]')
TODAY_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "Today"')
ACCOUNT_BUTTON = accessibility_id('AppStore.accountButton')
# Account sheet. Its navigation bar is only found with a delay, so the buttons are used to recognize it
ACCOUNT_CLOSE_BUTTON = accessibility_id('AppStore.account.CloseButton')
ACCOUNT_UPDATES_BUTTON = accessibility_id('AppStore.account.updates')
# App Updates
UPDATES_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "App Updates"')
UPDATES_UPDATE_ALL_CELL = accessibility_id('AppStore.account.updateAllAutomatic')
# App page
APP_PAGE_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "AppStore.ProductDiffablePageView"')
BACK_BUTTON = accessibility_id('BackButton')
# The offer button at the top of the app page shows the install state of the app in its name, e.g.
# AppStore.offerButton[state=open]. Other apps shown further down the page have their own offer buttons, so only the
# button in the top lockup is used.
OFFER_BUTTON = ios_class_chain('**/XCUIElementTypeCell[`name BEGINSWITH "AppStore.shelfItem.productTopLockup"`]'
                               '/**/XCUIElementTypeButton[`name BEGINSWITH "AppStore.offerButton[state="`]')
# The first time an app is downloaded, iOS shows a sheet to confirm the download. This sheet is shown by iOS, not by the
# App Store.
CONFIRMATION_SHEET = accessibility_id('payment-sheet')
# With Face ID and Touch ID turned off for downloads, the sheet only has an Install button. Otherwise, the footer is a
# text asking to confirm with the side button (or Face ID), which is no button.
CONFIRMATION_SHEET_INSTALL = ios_predicate('type == "XCUIElementTypeButton" AND name == "footer"')
CONFIRMATION_SHEET_CLOSE = accessibility_id('dismiss')
# The offer button, once the download has started or the app is installed
OFFER_BUTTON_STARTED = ios_class_chain(
    '**/XCUIElementTypeCell[`name BEGINSWITH "AppStore.shelfItem.productTopLockup"`]'
    '/**/XCUIElementTypeButton[`name BEGINSWITH "AppStore.offerButton[state=" AND (name CONTAINS "downloading" OR '
    'name CONTAINS "installing" OR name CONTAINS "open")`]')
