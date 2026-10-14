from puma.state_graph.locators import accessibility_id, ios_predicate, ios_class_chain


def quoted(text: str) -> str:
    """
    A text as a string literal in an iOS predicate or class chain.
    """
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


# Telegram draws most of its own interface, so many controls (the buttons in the navigation bar, the tab bar and the
# back button) are not in the element tree at all. What is exposed has an accessibility name, which is matched here.

# Overview of all chats. Each chat is a cell named after the chat, with the last message as its value. The search field
# is always in the element tree, but when the list is scrolled down a bit it is hidden behind the navigation bar.
CONVERSATIONS_SEARCH_FIELD = ios_predicate('type == "XCUIElementTypeSearchField" AND name == "Search"')
# The Contacts tab has the same search field at the same place. Only the Chats list has an unnamed button for the
# title at the top of the screen (the Calls and Settings tabs have no search field at all). It is not in an open chat.
# Measured on an iPhone 15 Pro (393 by 852 points, with a Dynamic Island): where the title is on other devices, such as an
# iPad or an iPhone SE, was not checked, so check rect.y and rect.width when adding such a device.
CONVERSATIONS_TITLE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == nil AND rect.y < 100 '
                                           'AND rect.width > 150')

# Searching replaces the overview. The filters below the search field only exist while searching, and the search results
# are cells named after the chat, below the header 'CHATS AND CONTACTS'. Before something is typed, public channels are
# suggested, which are never opened.
SEARCH_FILTER_CHANNELS = ios_predicate('type == "XCUIElementTypeButton" AND name == "Channels"')
# The close button at the end of the search field is not in the element tree. The row of the search field spans the
# width of the screen, with the close button at its right end, so it is tapped relative to the search field.
SEARCH_CLOSE_WIDTH_RATIO = 0.96

# The reminder of iOS to select more photos, shown regularly when Telegram has limited access to the photos
KEEP_CURRENT_SELECTION_BUTTON = 'Keep Current Selection'

# A chat
CHAT_SEND_MEDIA_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Send media"')
CHAT_VOICE_MESSAGE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Voice message"')
CHAT_INPUT = ios_class_chain('**/XCUIElementTypeTextView')
# While typing, the voice message button turns into the send button, which has a tiny frame (2x2 points)
CHAT_SEND_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Send"')
# Sent messages are named 'Your <kind>', e.g. 'Your message' or 'Your photo'. The value holds the lines of the message:
# its text (a photo has 'Caption: <caption>', a shared location has 'Location'), the date and the status.
SENT_PREFIX = 'Your '
CAPTION_PREFIX = 'Caption: '


def chat_header(conversation: str) -> str:
    """
    The name of the chat at the top of a chat, with the online status as its value (e.g. 'online'). The overview and the
    search results have a cell with the same name, which has the last message as its value, and is never in the element
    tree at the same time as an open chat.
    """
    return ios_predicate(f'type == "XCUIElementTypeOther" AND label == {quoted(conversation)} '
                         f'AND NOT value CONTAINS "Message"')


def conversation_row(conversation: str) -> str:
    """
    All elements with the name of a chat: a result of the search, or the header of an open chat (which is above the
    search results and never on the search screen). Callers pick the one below the search field.
    """
    return ios_predicate(f'type == "XCUIElementTypeOther" AND label == {quoted(conversation)}')


# The sheet that opens from the send media button. Its tabs are named, its close button is not: it is the unnamed button
# of 44 by 44 points in the top left corner of the sheet.
ATTACH_GALLERY_TAB = ios_predicate('type == "XCUIElementTypeButton" AND name == "Gallery"')
ATTACH_LOCATION_TAB = ios_predicate('type == "XCUIElementTypeButton" AND name == "Location"')
ATTACH_CLOSE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == nil AND rect.width == 44 AND rect.height == 44 '
                                    'AND rect.x < 30')

# The gallery shows the camera first, and then the photos, named 'Photo <date>'. A photo is selected by tapping the
# circle in its top right corner, which is not in the element tree, so it is tapped relative to the photo.
GALLERY_CAMERA = ios_predicate('type == "XCUIElementTypeButton" AND name == "Camera"')
GALLERY_MEDIA_CLASS_CHAIN = '**/XCUIElementTypeImage[`name BEGINSWITH "Photo " OR name BEGINSWITH "Video "`]'
GALLERY_SELECT_WIDTH_RATIO = 0.86
GALLERY_SELECT_HEIGHT_RATIO = 0.13
# Once media is selected, a caption can be added and sent. The caption field is a button without a name or label.
# The send button of the chat has a tiny frame (2 by 2 points), the one of the gallery is a normal button.
GALLERY_SEND_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Send" AND rect.width > 30')
GALLERY_CAPTION_FIELD = ios_predicate('type == "XCUIElementTypeButton" AND name == nil AND rect.width > 250 '
                                      'AND rect.width < 350 AND rect.height < 50')


def gallery_media(index: int) -> str:
    """
    The photo (or video) with a 1-based index, in the order of the gallery.
    """
    return ios_class_chain(f'{GALLERY_MEDIA_CLASS_CHAIN}[{index}]')


# The location tab shows the map, the options to send the location, and below those the places nearby. The options have
# no name, but the header above the places does, so the option to send the current location is found relative to it.
LOCATION_PLACES_HEADER = ios_predicate('type == "XCUIElementTypeOther" AND name == "OR CHOOSE A PLACE"')
# The two options are unnamed rows of the full width, above the header: 'Send My Current Location' and below it 'Share
# My Live Location for...', which starts sharing the location continuously. The rows are only used when there are
# exactly these two.
LOCATION_OPTION_ROWS = ios_predicate('type == "XCUIElementTypeOther" AND name == nil AND rect.width > 350 '
                                     'AND rect.height > 40 AND rect.height < 80 AND rect.y > 400')
