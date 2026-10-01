from puma.state_graph.locators import accessibility_id, ios_predicate, ios_class_chain

# Overview of all conversations
CONVERSATIONS_LIST = accessibility_id('ConversationList')
CONVERSATIONS_COMPOSE_BUTTON = accessibility_id('composeButton')
CONVERSATIONS_SEARCH_FIELD = ios_predicate('type == "XCUIElementTypeSearchField"')
# Buttons shown when swiping a conversation to the left
CONVERSATIONS_SWIPE_DELETE_BUTTON = accessibility_id('trash')
# Confirmation of deleting a conversation. For unknown senders, the confirmation also offers to report spam.
CONVERSATIONS_CONFIRM_DELETE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Delete"')

# A conversation
CONVERSATION_TITLE = accessibility_id('ConversationTitle')
CONVERSATION_MESSAGE_BODY_FIELD = accessibility_id('messageBodyField')
CONVERSATION_SEND_BUTTON = accessibility_id('sendButton')
# Each message is a cell containing a message balloon. The label of the cell is '<sender>, <text>, <time>'.
CONVERSATION_MESSAGE_CELLS = ios_class_chain('**/XCUIElementTypeCell[$name == "CKBalloonTextView"$]')
# The sender of messages sent from this device, as shown in the label of a message. This depends on the language of the
# device.
CONVERSATION_SENT_BY_ME = 'Your iMessage'

# New message. This screen is shown on top of the overview, and also contains a conversation title and message field.
NEW_MESSAGE_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "CKComposeChat"')
NEW_MESSAGE_RECIPIENT_FIELD = ios_predicate('type == "XCUIElementTypeTextField" AND name != "messageBodyField"')
NEW_MESSAGE_CANCEL_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Cancel"')

# Popups
POPUP_APPLE_INTELLIGENCE_WELCOME_TEXT = ios_predicate(
    'type == "XCUIElementTypeStaticText" AND name == "Apple Intelligence in Messages"')
POPUP_CONTINUE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Continue"')
# Shown the first time a conversation is deleted. The text contains a non-breaking space before 'Deleted'.
POPUP_RECENTLY_DELETED_TEXT = ios_predicate('type == "XCUIElementTypeAlert" AND name BEGINSWITH "Deleted messages are moved to"')
POPUP_OK_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "OK"')
POPUP_OK_LABEL = 'OK'


def conversation_row(name: str) -> str:
    """
    The name of a conversation in the overview. Each row is present twice in the element tree, so the name inside the
    list is used instead of the row itself.
    """
    return ios_class_chain(f'**/XCUIElementTypeCollectionView[`name == "ConversationList"`]'
                           f'/**/XCUIElementTypeStaticText[`name == "{name}"`]')


def conversation_cell(name: str) -> str:
    """
    The row of a conversation in the overview, which can be swiped. The name of the row starts with the name of the
    conversation, followed by the last message or 'Pinned'.
    """
    return ios_class_chain(f'**/XCUIElementTypeCollectionView[`name == "ConversationList"`]'
                           f'/XCUIElementTypeCell[`name BEGINSWITH "{name}, "`]')


def recipient_suggestion(recipient: str) -> str:
    """
    A suggestion shown while typing a recipient, e.g. 'Bob Jansen, +31 6 12345678, iMessage'.
    """
    return ios_class_chain(f'**/XCUIElementTypeTable[`name == "Results"`]'
                           f'/XCUIElementTypeCell[`label BEGINSWITH "{recipient}, "`]')
