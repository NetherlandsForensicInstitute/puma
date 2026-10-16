from puma.state_graph.locators import accessibility_id, ios_predicate, ios_class_chain

# Overview of all lists
LISTS_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "Reminders.TTRIAccountsListsView"')
LISTS_ADD_LIST_BUTTON = accessibility_id('Add List')
# New list
NEW_LIST_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "New List"')
NEW_LIST_NAME_FIELD = accessibility_id('List Name')
# A list
LIST_NEW_REMINDER_BUTTON = accessibility_id('New Reminder')
LIST_MORE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "More"')
LIST_DONE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Done"')
NEW_LIST_CANCEL_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Cancel"')
# Toolbar shown while editing a reminder in a list
LIST_EDIT_DETAILS_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Edit Details"')
LIST_SWIPE_DELETE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Delete"')
LISTS_DELETE_LABEL = 'Delete'
# Details of a reminder
DETAILS_TABLE = accessibility_id('ReminderDetail.ID.DetailsTable')
DETAILS_NOTES_FIELD = ios_class_chain('**/XCUIElementTypeTable[`name == "ReminderDetail.ID.DetailsTable"`]/**/XCUIElementTypeTextField[`name == "Notes text view"`]')
DETAILS_DATE_SWITCH = ios_predicate('type == "XCUIElementTypeSwitch" AND name == "Date"')
DETAILS_TIME_SWITCH = ios_predicate('type == "XCUIElementTypeSwitch" AND name == "Time"')
# Popups
POPUP_WELCOME_TEXT = ios_predicate('type == "XCUIElementTypeStaticText" AND name == "Welcome to Reminders"')
POPUP_ICLOUD_SYNC_TEXT = ios_predicate('type == "XCUIElementTypeStaticText" AND name == "Enable iCloud Syncing?"')
POPUP_NOTIFICATIONS_INTRO_TEXT = ios_predicate('type == "XCUIElementTypeStaticText" AND name == "Never Miss a Reminder"')
POPUP_CONTINUE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Continue"')
POPUP_NOT_NOW_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Not Now"')


def list_cell(name: str) -> str:
    """A list in the overview. Its label is the name, followed by the number of reminders."""
    return ios_predicate(f'type == "XCUIElementTypeCell" AND (label == "{name}" OR label BEGINSWITH "{name}, ")')


def list_title(name: str) -> str:
    return ios_predicate(f'type == "XCUIElementTypeNavigationBar" AND name == "{name}"')


def reminder_row(title: str) -> str:
    """A reminder in a list. Its label is the title, followed by the status and due date."""
    return ios_predicate(f'type == "XCUIElementTypeCell" AND label BEGINSWITH "{title}, "')


def reminder_circle(title: str) -> str:
    """The button to complete a reminder."""
    return f'//XCUIElementTypeCell[starts-with(@label, "{title}, ")]//XCUIElementTypeButton[@name="circle"]'


LIST_REMINDER_TITLES = '//XCUIElementTypeCell[contains(@label, ", Incomplete")]//XCUIElementTypeTextField[@name="Title"]'
