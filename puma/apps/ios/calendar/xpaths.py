from puma.state_graph.locators import accessibility_id, ios_predicate

# Day view
DAY_VIEW_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "DayViewContainerView"')
DAY_VIEW_ADD_BUTTON = accessibility_id('add-plus-button')
DAY_VIEW_SEARCH_BUTTON = accessibility_id('searchbar-button')
# New event
NEW_EVENT_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "New"')
NEW_EVENT_EVENT_REMINDER_CONTROL = accessibility_id('event-reminder-control')
# The new event form remembers whether an event or a reminder was created last
NEW_EVENT_EVENT_SEGMENT = ios_predicate('type == "XCUIElementTypeButton" AND name == "Event"')
NEW_EVENT_TITLE_FIELD = accessibility_id('title-field')
NEW_EVENT_SAVE_BUTTON = accessibility_id('add-button')
# named 'cancel-button' when creating an event, 'Cancel' when creating a reminder
NEW_EVENT_CANCEL_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name IN {"cancel-button", "Cancel"}')
NEW_EVENT_DISCARD_CHANGES_LABEL = 'Discard Changes'
NEW_EVENT_LOCATION_FIELD = accessibility_id('location-video-call-field')
NEW_EVENT_LOCATION_SEARCH_FIELD = accessibility_id('location-video-call-search-field')
NEW_EVENT_ALL_DAY_SWITCH = accessibility_id('all-day-switch')
NEW_EVENT_START_CELL = '//XCUIElementTypeCell[@name="start-date-picker-cell"]'
NEW_EVENT_END_CELL = '//XCUIElementTypeCell[@name="end-date-picker-cell"]'
# the date and time buttons in a start or end cell. Time buttons contain a colon, e.g. '10:30' or '10:30 AM'
NEW_EVENT_DATE_BUTTON = '//XCUIElementTypeButton[not(contains(@name, ":")) and @name != "Date and Time Picker"]'
NEW_EVENT_TIME_BUTTON = '//XCUIElementTypeButton[contains(@name, ":")]'
# Search
SEARCH_FIELD = ios_predicate('type == "XCUIElementTypeSearchField" AND name == "Search"')
SEARCH_CLOSE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Close"')
# Event details
EVENT_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "EKEventView"')
EVENT_TITLE_CELL = accessibility_id('event-details-title-cell')
EVENT_TITLE_CELL_TEXTS = ('//XCUIElementTypeCell[@name="event-details-title-cell"]'
                          '//*[self::XCUIElementTypeStaticText or self::XCUIElementTypeTextView]')
EVENT_DELETE_BUTTON = accessibility_id('delete-event-button')
EVENT_DELETE_LABEL = 'Delete Event'


def location_text(location: str) -> str:
    """The option to use the typed location as-is, instead of a location from Apple Maps."""
    return ios_predicate(f'type == "XCUIElementTypeStaticText" AND name == "“{location}”"')


def day_view_event(title: str) -> str:
    return ios_predicate(f'type == "XCUIElementTypeButton" AND name == "event-shown:{title}"')


def search_result(title: str) -> str:
    return ios_predicate(f'type == "XCUIElementTypeCell" AND name BEGINSWITH "{title}, "')


def event_title(title: str) -> str:
    return ios_predicate(f'name == "event-details-title-text" AND label == "{title}"')
