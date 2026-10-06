from puma.state_graph.locators import accessibility_id, ios_predicate

# Contact list
CONTACT_LIST_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "Contacts"')
CONTACT_LIST_ADD_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Add"')
# New contact
NEW_CONTACT_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "New Contact"')
NEW_CONTACT_FIRST_NAME = accessibility_id('First name')
NEW_CONTACT_LAST_NAME = accessibility_id('Last name')
NEW_CONTACT_COMPANY = accessibility_id('Company')
NEW_CONTACT_ADD_PHONE = accessibility_id('add phone')
NEW_CONTACT_ADD_EMAIL = accessibility_id('add email')
NEW_CONTACT_PHONE_FIELD = ios_predicate('type == "XCUIElementTypeTextField" AND placeholderValue == "Phone"')
NEW_CONTACT_EMAIL_FIELD = ios_predicate('type == "XCUIElementTypeTextField" AND placeholderValue == "Email"')
NEW_CONTACT_DONE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Done"')
NEW_CONTACT_CLOSE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "close"')
NEW_CONTACT_DISCARD_CHANGES_BUTTON = '//XCUIElementTypeSheet//XCUIElementTypeButton[@name="Discard Changes"]'
# Contact
CONTACT_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "CNContactView"')
CONTACT_NAME_HEADER = accessibility_id('ContactCardHeaderView')
CONTACT_EDIT_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Edit"')
CONTACT_DELETE_BUTTON = accessibility_id('Delete Contact')
# the label of the button in the confirmation alert
CONTACT_CONFIRM_DELETE_LABEL = 'Delete Contact'


def contact_cell(name: str) -> str:
    return ios_predicate(f'type == "XCUIElementTypeCell" AND name == "{name}"')


def contact_header(name: str) -> str:
    return ios_predicate(f'name == "ContactCardHeaderView" AND label == "{name}"')
CONTACT_DETAILS = ios_predicate('type == "XCUIElementTypeButton" AND name == "ContactCardDetailsView"')
