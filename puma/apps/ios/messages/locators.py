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
CONVERSATION_MESSAGE_BALLOON = 'CKBalloonTextView'
# Every message, also a photo or other attachment, contains an element with this name. For attachments, the label
# describes the attachment instead of the text, e.g. '<sender>, Includes picture, <time>'.
CONVERSATION_MESSAGE_CONTENT = 'Sticker'
# The attachment of a message with a shared location, which shows a map, or this icon when sharing has stopped
CONVERSATION_LOCATION_ATTACHMENT = 'Location'
CONVERSATION_LOCATION_ICON = 'location-bubble-icon'
# The sender of messages sent from this device, as shown in the label of a message, for iMessage and SMS. This depends
# on the language of the device.
CONVERSATION_SENT_BY_ME_IMESSAGE = 'Your iMessage'
CONVERSATION_SENT_BY_ME_SMS = 'Your Text Message'
# The service of the messages below it is shown above them, e.g. 'iMessage' or 'Text Message • SMS'. The placeholder
# of the message field shows the service of the next message in the same way.
CONVERSATION_SERVICE_IMESSAGE = 'iMessage'
CONVERSATION_SERVICE_SMS = 'Text Message'
# A reply is shown below a preview of the message it replies to. Their labels are '<sender>, Reply, <text>, <time>'
# and '<sender>, Reply Preview, <text>, <time>'.
CONVERSATION_REPLY = 'Reply'
CONVERSATION_REPLY_PREVIEW = 'Reply Preview'
# The status of the last message sent from this device, shown below it. On real devices, the status can start with an
# invisible left-to-right mark (U+200E), e.g. '\u200eRead Monday'.
# The status of an edited message ends with 'Edited', e.g. 'Delivered • Edited'.
CONVERSATION_STATUS_DELIVERED = ios_predicate(
    'type == "XCUIElementTypeStaticText" AND (name BEGINSWITH "Delivered" OR name BEGINSWITH "\u200eDelivered")')
CONVERSATION_STATUS_READ = ios_predicate(
    'type == "XCUIElementTypeStaticText" AND (name BEGINSWITH "Read" OR name BEGINSWITH "\u200eRead")')
CONVERSATION_STATUS_NOT_DELIVERED = ios_predicate(
    'type == "XCUIElementTypeStaticText" AND (name == "Not Delivered" OR name == "\u200eNot Delivered")')
# Edited messages are marked below them, with 'Edited' or a status ending with 'Edited'
CONVERSATION_EDITED = 'Edited'
# The menu shown when long pressing a message, with the tapbacks (reactions) above it
CONVERSATION_MESSAGE_MENU = accessibility_id('TapbackPickerCollectionView')
CONVERSATION_MENU_REPLY = ios_predicate('type == "XCUIElementTypeButton" AND name == "Reply"')
CONVERSATION_MENU_EDIT = ios_predicate('type == "XCUIElementTypeButton" AND name == "Edit"')
CONVERSATION_MENU_UNDO_SEND = ios_predicate('type == "XCUIElementTypeButton" AND name == "Undo Send"')
CONVERSATION_MENU_MORE = ios_predicate('type == "XCUIElementTypeButton" AND name == "More…"')

# The menu of the + button next to the message field, with the apps that can send content, e.g. Photos and Audio. The
# items are named after the bundle id of the app, e.g. 'com.apple...:com.apple.mobileslideshow.PhotosMessagesApp'.
CONVERSATION_ADD_BUTTON = accessibility_id('add')
CONVERSATION_ADD_MENU_ITEMS = ios_predicate(
    'type == "XCUIElementTypeCell" AND name BEGINSWITH "com.apple.messages.MSMessageExtensionBalloonPlugin"')
CONVERSATION_ADD_MENU_CLOSE = accessibility_id('PopoverDismissRegion')
ADD_MENU_PHOTOS = 'com.apple.mobileslideshow.PhotosMessagesApp'
ADD_MENU_AUDIO = 'com.apple.siri.AudioMessagesApp.AudioMessagesExtension'
ADD_MENU_LOCATION = 'com.apple.findmy.FindMyMessagesApp'
# Recording an audio message, which starts as soon as Audio is chosen in the + menu
AUDIO_STOP_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Stop"')
AUDIO_CANCEL_BUTTON = accessibility_id('Cancel audio recording')

# Sharing the location of the device, in the app Location of the + menu
LOCATION_SHARE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Share"')
# the durations are named after their icon: 'clock' (For One Hour), 'calendar' (Until End of Day), 'infinity'
# (Indefinitely)

# The photos and videos in the picker of Photos, newest first. Their label is e.g. 'Photo, October 01, 21:07'.
PHOTOS_PICKER_ITEMS = ios_predicate('type == "XCUIElementTypeImage" AND name == "PXGGridLayout-Info"')

# Editing a message. The message itself becomes editable.
EDIT_SEND_BUTTON = accessibility_id('Send edit')
EDIT_CANCEL_BUTTON = accessibility_id('Cancel edit')

# Selecting messages, after choosing More… in the menu of a message
SELECTION_DELETE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Delete"')
SELECTION_FORWARD_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Forward"')
SELECTION_CANCEL_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Cancel"')
# The confirmation of deleting messages starts with a left-to-right mark (U+200E)
SELECTION_CONFIRM_DELETE_BUTTON = ios_predicate(
    'type == "XCUIElementTypeButton" AND (name ENDSWITH "Delete Message" OR name ENDSWITH "Delete Messages")')

# Replying to a message. The message is shown on top of the conversation, with a message field for the reply.
REPLY_CLOSE_BUTTON = accessibility_id('close')

# New message. This screen is shown on top of the overview, and also contains a conversation title and message field.
# When forwarding a message, a variant without this navigation bar is shown, so the screen is recognized by the
# recipient field.
NEW_MESSAGE_NAVIGATION_BAR = ios_predicate('type == "XCUIElementTypeNavigationBar" AND name == "CKComposeChat"')
NEW_MESSAGE_RECIPIENT_FIELD = ios_predicate('type == "XCUIElementTypeTextField" AND name != "messageBodyField"')
NEW_MESSAGE_CANCEL_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Cancel"')

# Search results, shown on top of the overview while searching
SEARCH_RESULTS_LIST = ios_predicate('type == "XCUIElementTypeCollectionView" AND name BEGINSWITH "Search results for:"')
# the button that closes searching, next to the search field
SEARCH_RESULTS_CLOSE_BUTTON = accessibility_id('close')
SEARCH_RESULTS_NO_RESULTS = ios_predicate('type == "XCUIElementTypeStaticText" AND name == "No Results"')
# The conversations found, in the section 'Conversations'. Messages found are shown in the section 'Messages', which do
# not have a contact photo button of their own.
SEARCH_RESULTS_CONVERSATIONS = ios_class_chain(
    '**/XCUIElementTypeCollectionView[`name BEGINSWITH "Search results for:"`]'
    '/XCUIElementTypeCell[$type == "XCUIElementTypeButton" AND name == "Contact photo"$]')

# Details of a conversation, opened by tapping the title. The conversation stays in the element tree.
DETAILS_NAVIGATION_BAR = ios_predicate(
    'type == "XCUIElementTypeNavigationBar" AND name == "CommunicationDetails.DetailsView"')
DETAILS_TITLE = accessibility_id('DetailsHeaderTitle')
DETAILS_STOP_SHARING_LOCATION = ios_predicate(
    'type == "XCUIElementTypeButton" AND name == "Stop Sharing My Location"')
# Details of a group conversation. TODO: these have not been verified on a device yet, see the README.
DETAILS_CHANGE_GROUP_NAME = ios_predicate('type == "XCUIElementTypeButton" AND name == "Change Name and Photo"')
DETAILS_GROUP_NAME_FIELD = ios_predicate('type == "XCUIElementTypeTextField"')
DETAILS_DONE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Done"')
DETAILS_ADD_MEMBER = ios_predicate('type == "XCUIElementTypeButton" AND name BEGINSWITH "Add Contact"')
DETAILS_REMOVE_MEMBER = ios_predicate('type == "XCUIElementTypeButton" AND name == "Remove"')
DETAILS_LEAVE_GROUP = ios_predicate('type == "XCUIElementTypeButton" AND name == "Leave this Conversation"')
DETAILS_LEAVE_GROUP_LABEL = 'Leave this Conversation'

# Popups
POPUP_APPLE_INTELLIGENCE_WELCOME_TEXT = ios_predicate(
    'type == "XCUIElementTypeStaticText" AND name == "Apple Intelligence in Messages"')
POPUP_CONTINUE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Continue"')
# Shown the first time a conversation is deleted. The text contains a non-breaking space before 'Deleted'.
POPUP_RECENTLY_DELETED_TEXT = ios_predicate(
    'type == "XCUIElementTypeAlert" AND name BEGINSWITH "Deleted messages are moved to"')
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


def search_result_conversation(name: str) -> str:
    """
    A conversation in the search results. Conversations can have names that only differ in upper and lower case, so the
    name has to match exactly.
    """
    return ios_class_chain(f'**/XCUIElementTypeCollectionView[`name BEGINSWITH "Search results for:"`]'
                           f'/XCUIElementTypeCell[`name == "{name}"`]')


def message_cell(text: str) -> str:
    """
    The last message in a conversation containing a text.
    """
    return ios_class_chain(f'**/XCUIElementTypeCell[$name == "CKBalloonTextView"$]'
                           f'[`label CONTAINS "{text}" AND NOT label CONTAINS ", Reply Preview, "`][-1]')


def tapback(reaction: str) -> str:
    """
    A tapback (reaction) in the menu of a message, e.g. 'heart' or 'thumbsUp'.
    """
    return ios_class_chain(f'**/XCUIElementTypeCollectionView[`name == "TapbackPickerCollectionView"`]'
                           f'/XCUIElementTypeCell[`name == "{reaction}"`]')


def editable_message(text: str) -> str:
    """
    The message being edited, containing a text.
    """
    return ios_class_chain(f'**/XCUIElementTypeTextView[`name == "CKBalloonTextView" AND value CONTAINS "{text}"`][-1]')


def add_menu_item(app: str) -> str:
    """
    An item in the menu of the + button, identified by the end of its name, e.g. ADD_MENU_PHOTOS.
    """
    return ios_predicate(f'type == "XCUIElementTypeCell" AND name ENDSWITH "{app}"')


def location_duration(icon: str) -> str:
    """
    A duration for sharing the location, e.g. 'clock' for one hour.
    """
    return ios_predicate(f'type == "XCUIElementTypeButton" AND name == "{icon}"')


def details_member(name: str) -> str:
    """
    A participant in the details of a group conversation. TODO: not verified on a device yet, see the README.
    """
    return ios_predicate(f'type == "XCUIElementTypeCell" AND label BEGINSWITH "{name}"')
