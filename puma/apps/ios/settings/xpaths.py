from puma.state_graph.locators import accessibility_id, ios_predicate

# Main screen
SETTINGS_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "Settings"')
GENERAL_CELL = accessibility_id('com.apple.settings.general')
DISPLAY_CELL = accessibility_id('com.apple.settings.displayAndBrightness')
# Display & Brightness
DISPLAY_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "Display & Brightness"')
AUTO_LOCK_CELL = ios_predicate('type == "XCUIElementTypeCell" AND name == "AUTOLOCK"')
# Auto-Lock
AUTO_LOCK_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "Auto-Lock"')
# The options are named after the number of seconds, 'Never' is named '-1'
SELECTED_AUTO_LOCK_OPTION = '//XCUIElementTypeCell[contains(@traits, "Selected")]'


def auto_lock_option(seconds: int) -> str:
    return ios_predicate(f'type == "XCUIElementTypeCell" AND name == "{seconds}"')
