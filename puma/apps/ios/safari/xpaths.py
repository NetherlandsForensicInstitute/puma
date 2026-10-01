from puma.state_graph.locators import accessibility_id, ios_class_chain, ios_predicate

# Accessibility ids are used where possible, as XPath lookups are slow on iOS
# Toolbar (bottom of the screen, iOS 26 compact layout)
TOOLBAR_ADDRESS_BAR = accessibility_id('TabBarItemTitle')
TOOLBAR_ADDRESS_BAR_EDIT = accessibility_id('URL')
TOOLBAR_RELOAD_BUTTON = accessibility_id('ReloadButton')
TOOLBAR_VOICE_SEARCH_BUTTON = accessibility_id('VoiceSearchButton')
# Named 'More' in iOS 26.2, 'MoreMenuButton' in iOS 26.6
TOOLBAR_MORE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name IN {"More", "MoreMenuButton"}')
# More menu. The names of the menu items differ between iOS versions, so they are located by label.
MENU_ADD_TO_BOOKMARKS = ios_predicate('type == "XCUIElementTypeButton" AND label == "Add to Bookmarks"')
MENU_NEW_TAB = ios_predicate('type == "XCUIElementTypeButton" AND label == "New Tab"')
MENU_NEW_PRIVATE_TAB = ios_predicate('type == "XCUIElementTypeButton" AND label == "New Private Tab"')
MENU_BOOKMARKS = ios_predicate('type == "XCUIElementTypeButton" AND label == "Bookmarks"')
MENU_ALL_TABS = ios_predicate('type == "XCUIElementTypeButton" AND label == "All Tabs"')
# New tab
NEW_PRIVATE_TAB_START_PAGE = accessibility_id('privateBrowsingPersistentModuleContent')
# Tab overview
TAB_OVERVIEW = accessibility_id('TabOverview')
TAB_OVERVIEW_NEW_TAB_BUTTON = accessibility_id('NewTabButton')
TAB_OVERVIEW_DONE_BUTTON = accessibility_id('DoneButton')
TAB_OVERVIEW_TAB = '//XCUIElementTypeButton[starts-with(@name, "TabOverviewItemView")]'
TAB_OVERVIEW_PRIVATE_TAB_GROUP = ios_predicate('name == "CapsuleTabGroup" AND label BEGINSWITH "Private"')
TAB_OVERVIEW_PRIVATE_TAB_GROUP_SELECTED = ios_predicate('name == "CapsuleTabGroup" AND label BEGINSWITH "Private" AND value == "1"')
TAB_OVERVIEW_STANDARD_TAB_GROUP = ios_predicate('name == "CapsuleTabGroup" AND NOT (label BEGINSWITH "Private")')
TAB_OVERVIEW_STANDARD_TAB_GROUP_SELECTED = ios_predicate('name == "CapsuleTabGroup" AND NOT (label BEGINSWITH "Private") AND value == "1"')
# Bookmarks
BOOKMARKS_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "Sidebar"')
BOOKMARKS_TABLE = accessibility_id('BookmarksTable')
BOOKMARKS_DISMISS_BUTTON = accessibility_id('DismissButton')
BOOKMARKS_CONTEXT_MENU_DELETE = accessibility_id('Delete')
# Face ID prompt, shown when opening locked private tabs on a real device
POPUP_FACE_ID_PROMPT = ios_predicate('type == "XCUIElementTypeButton" AND name BEGINSWITH "com.apple.localauthentication"')
POPUP_FACE_ID_CANCEL = ios_predicate('type == "XCUIElementTypeButton" AND name ENDSWITH "authentication.button.cancel"')
# Popups
POPUP_TAB_OVERVIEW_TIP_CLOSE = '//XCUIElementTypeStaticText[@name="Quickly Access All Tabs"]/following-sibling::XCUIElementTypeButton[@name="Close"]'
POPUP_SEARCH_FIRST_TIME_EXPERIENCE = accessibility_id('UniversalSearchFirstTimeExperienceView')
POPUP_SEARCH_FIRST_TIME_CONTINUE = ios_predicate('type == "XCUIElementTypeButton" AND name == "Continue"')
POPUP_LOCKED_PRIVATE_BROWSING_NOT_NOW = accessibility_id('NotNowButton')
# The bar above the keyboard when a field on a web page has focus. It hides the toolbar of Safari. Some web pages give a
# field focus when they are loaded.
POPUP_FORM_DONE_BUTTON = ios_class_chain('**/XCUIElementTypeToolbar[$name == "Previous"$]'
                                         '/**/XCUIElementTypeButton[`name == "Done"`]')


def bookmark(title: str) -> str:
    return ios_predicate(f'type == "XCUIElementTypeCell" AND name BEGINSWITH "BookmarksSidebarTableCellView" AND label == "{title}"')
