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
