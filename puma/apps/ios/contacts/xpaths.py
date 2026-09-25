from puma.state_graph.locators import accessibility_id, ios_predicate

# Contact list
CONTACTS_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "Contacts"')
ADD_CONTACT_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Add"')
# New contact
NEW_CONTACT_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "New Contact"')
FIRST_NAME = accessibility_id('First name')
LAST_NAME = accessibility_id('Last name')
COMPANY = accessibility_id('Company')
ADD_PHONE = accessibility_id('add phone')
ADD_EMAIL = accessibility_id('add email')
PHONE_FIELD = ios_predicate('type == "XCUIElementTypeTextField" AND placeholderValue == "Phone"')
EMAIL_FIELD = ios_predicate('type == "XCUIElementTypeTextField" AND placeholderValue == "Email"')
DONE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Done"')
CLOSE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "close"')
DISCARD_CHANGES_BUTTON = '//XCUIElementTypeSheet//XCUIElementTypeButton[@name="Discard Changes"]'
# Contact
CONTACT_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "CNContactView"')
CONTACT_NAME_HEADER = accessibility_id('ContactCardHeaderView')
EDIT_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Edit"')
DELETE_CONTACT = accessibility_id('Delete Contact')
# the label of the button in the confirmation alert
CONFIRM_DELETE_CONTACT_LABEL = 'Delete Contact'


def contact_cell(name: str) -> str:
    return ios_predicate(f'type == "XCUIElementTypeCell" AND name == "{name}"')


def contact_header(name: str) -> str:
    return ios_predicate(f'name == "ContactCardHeaderView" AND label == "{name}"')
CONTACT_DETAILS = ios_predicate('type == "XCUIElementTypeButton" AND name == "ContactCardDetailsView"')
