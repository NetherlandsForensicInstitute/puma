from puma.state_graph.locators import accessibility_id, ios_predicate, ios_class_chain, quoted

# Most texts of WhatsApp start with an invisible left-to-right mark (U+200E), e.g. '\u200eDelete for everyone'.
# Therefore texts are matched with ENDSWITH or CONTAINS.

# A Cancel button, e.g. of the selection of messages, of the photo library and of sending a location
CANCEL_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Cancel"')

# Tab bar
TAB_CHATS = accessibility_id('TabBarButton_Chats')
TAB_UPDATES = accessibility_id('TabBarButton_Status')
TAB_YOU = accessibility_id('TabBarButton_Settings')

# Overview of all chats. Each chat is a cell named after the chat.
CONVERSATIONS_NEW_CHAT_BUTTON = accessibility_id('NavigationBar_NewChatButton')
CONVERSATIONS_SEARCH_FIELD = accessibility_id('TokenizedSearchBar_TextView')
# The list of archived chats, opened from the top of the overview
CONVERSATIONS_ARCHIVED = accessibility_id('ChatListView_archiveCell')
ARCHIVED_TABLE = accessibility_id('WAArchivedChatsViewController')
# Searching shows the results on top of the overview
SEARCH_BACK_BUTTON = accessibility_id('AISearch_PaperPlane_Back_Button')

# New chat: a list of contacts, shown on top of the overview. While searching, the close button is named Close.
NEW_CHAT_CLOSE_BUTTON = ios_predicate('name == "PickerView_CloseButton" '
                                      'OR (type == "XCUIElementTypeButton" AND name == "Close")')
NEW_CHAT_SEARCH_FIELD = accessibility_id('PickerView_SearchBar')
NEW_CHAT_NEW_GROUP = accessibility_id('PickerView_NewGroupCell')
NEW_CHAT_NEW_BROADCAST = accessibility_id('PickerView_NewBroadcastCell')

# A chat
CHAT_MESSAGES_TABLE = accessibility_id('ChatMessagesTableView')
CHAT_COMPOSER = accessibility_id('ChatBar_ComposerTextView')
CHAT_SEND_BUTTON = accessibility_id('ChatBar_SendButton')
CHAT_ATTACH_BUTTON = accessibility_id('ChatBar_AttachMediaButton')
CHAT_STICKERS_BUTTON = accessibility_id('ChatBar_GimmickButton')
CHAT_VOICE_MESSAGE_BUTTON = accessibility_id('ChatBar_VoiceMessageButton')
# The name of the chat, which opens the contact or group info
CHAT_HEADER = accessibility_id('NavigationBar_HeaderViewButton')
CHAT_VOICE_CALL_BUTTON = accessibility_id('NavigationBar_CallButton')
CHAT_VIDEO_CALL_BUTTON = accessibility_id('NavigationBar_VideoCallButton')
BACK_BUTTON = accessibility_id('BackButton')
# Each message is a cell, containing an element with a label describing the message:
# - sent: '\u200eYour <kind>, <text>, <time>, \u200eSent to <chat>, \u200e<status>', with status Sent, Delivered or Read
# - received: '\u200e<kind>, <text>, <time>, \u200eReceived from <sender>'
# The kind is 'message' for text messages, and e.g. 'contact' for a shared contact, of which the text is the name.
CHAT_MESSAGE_CELL = 'WAMessageBubbleTableViewCell'
SENT_TO = '\u200eSent to '
RECEIVED_FROM = '\u200eReceived from '
# A reply has a label of multiple lines: 'Replying to <sender>.', the label of the reply, 'Quoted message.', and the
# text of the message replied to.
REPLY_PREFIX = '\u200eReplying to '
REPLY_QUOTED = '\u200eQuoted message.'

# The menu of a message, shown when long pressing it
MESSAGE_MENU = accessibility_id('ContextMenu_ScrollView')
MESSAGE_MENU_REPLY = accessibility_id('ContextMenu_message_replyInChat')
MESSAGE_MENU_FORWARD = accessibility_id('ContextMenu_message_forward')
MESSAGE_MENU_DELETE = accessibility_id('ContextMenu_MenuItem_Delete')

# Selecting messages, e.g. to delete or forward them
# the toolbar shows the number of selected messages. The sticker tray has a toolbar with the same name, WAToolbar.
SELECTION_TOOLBAR = accessibility_id('Toolbar_SelectedMessageCount')
SELECTION_DELETE_BUTTON = accessibility_id('Toolbar_DeleteButton')
DELETE_FOR_EVERYONE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Delete for everyone"')

# Contact info and group info, opened from the name of a chat
GROUP_INFO_MENU = accessibility_id('NavigationBar_GroupInfoOverflowMenu')
CHAT_INFO = ios_predicate('label ENDSWITH "Contact info" OR name == "NavigationBar_GroupInfoOverflowMenu"')
CONTACT_INFO_PROFILE_PICTURE = accessibility_id('contact-info-header-profile-image')
# The profile picture is shown full screen, with a Close button. Contacts without a picture show a placeholder.
PROFILE_PICTURE_CLOSE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Close"')
CHAT_INFO_DISAPPEARING_MESSAGES = ios_predicate(
    'type == "XCUIElementTypeStaticText" AND label ENDSWITH "Disappearing messages"')
DISAPPEARING_MESSAGES_TIMER = ios_predicate('label ENDSWITH "Message timer"')

# Groups. A group is created from a new chat: members are chosen with the contact picker, then the group is named.
GROUP_NAME_FIELD = ios_predicate('type == "XCUIElementTypeTextField"')
GROUP_CREATE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Create"')
GROUP_MENU_EDIT_DESCRIPTION = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Edit description"')
TEXT_INPUT_FIELD = accessibility_id('WATextInputViewController_TextView')
TEXT_INPUT_SAVE_BUTTON = accessibility_id('WATextInputViewController_SaveButton')
GROUP_REMOVE_MEMBER_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Remove from group"')
GROUP_REMOVE_CONFIRM_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Remove"')
GROUP_EXIT = ios_predicate('type == "XCUIElementTypeStaticText" AND label ENDSWITH "Exit group"')
GROUP_EXIT_BUTTON = accessibility_id('GroupExitBottomSheet_ExitGroupButton')
GROUP_EXIT_AND_DELETE_BUTTON = accessibility_id('GroupExitBottomSheet_ExitAndDeleteGroupButton')
# Shown in the group info after leaving a group, and its confirmation
GROUP_DELETE = ios_predicate('type == "XCUIElementTypeStaticText" AND label ENDSWITH "Delete group"')
GROUP_DELETE_CONFIRM_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Delete group"')

# Menu of the + button in a chat
ATTACH_MENU = accessibility_id('AttachmentPicker_Menu')
ATTACH_PHOTOS = accessibility_id('WAActionSheetController_PhotoLibrary')
ATTACH_LOCATION = accessibility_id('WAActionSheetController_Location')
ATTACH_CONTACT = accessibility_id('WAActionSheetController_Contact')

# The tray with stickers and GIFs, opened with the sticker button next to the message field
STICKER_TRAY = accessibility_id('Stickers_CollectionView')
# The grabber at the top of the sticker tray: tapping it does nothing, dragging it down closes the tray
STICKER_TRAY_GRABBER = accessibility_id('StickerBrowserView_grabberView')
STICKERS = ios_class_chain('**/XCUIElementTypeCollectionView[`name == "Stickers_CollectionView"`]'
                           '/XCUIElementTypeCell[`label BEGINSWITH "\u200eSticker"`]')

# A received view once photo that has not been opened yet, and the photo opened full screen. Once opened, the label
# of the photo ends with 'Opened'.
RECEIVED_VIEW_ONCE_PHOTO = ios_predicate('label BEGINSWITH "\u200eView once photo" '
                                         'AND label CONTAINS "\u200eReceived from" AND NOT label ENDSWITH "Opened"')
MEDIA_VIEWER_IMAGE = accessibility_id('MediaBrowser_Image')

# Choosing photos and videos to send. The newest photos and videos are shown first.
MEDIA_PICKER_ASSETS = accessibility_id('MediaPicker_Asset')
MEDIA_PICKER_CAPTION = accessibility_id('MediaPickerSendBar_CaptionTextView')
MEDIA_PICKER_SEND_BUTTON = accessibility_id('MediaPickerSendBar_SendButton')
# The albums of the photo library, shown with the Albums button at the top of the photo library. An opened album has
# a back button with the same name as the back button of the chat below it, which has a longer label.
MEDIA_PICKER_ALBUMS_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Albums"')
MEDIA_PICKER_ALBUM_BACK_BUTTON = ios_predicate('name == "BackButton" AND label == "Back"')
MEDIA_PICKER_VIEW_ONCE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Turn on view once"')

# Sending a location
LOCATION_TITLE = ios_predicate('type == "XCUIElementTypeStaticText" AND label ENDSWITH "Send location"')
LOCATION_CURRENT = accessibility_id('LocationTable_CurrentLocationCell')
LOCATION_LIVE = accessibility_id('LocationTable_LiveLocationCell')
# Sharing the live location, for 1 hour by default
CAPTION_FIELD = accessibility_id('CaptionBar_TextView')
CAPTION_SEND_BUTTON = accessibility_id('CaptionBar_SendButton')
# Shown in a chat while the live location is shared, and the confirmation of stopping it
STOP_SHARING_BUTTON = accessibility_id('ChatViewController_StopSharingButton')
STOP_SHARING_CONFIRM_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Stop sharing" '
                                            'AND name != "ChatViewController_StopSharingButton"')

# Forwarding messages: the selected messages are forwarded with the toolbar, to a chat chosen from a list
SELECTION_FORWARD_BUTTON = accessibility_id('Toolbar_ForwardButton')
FORWARD_SEARCH_FIELD = accessibility_id('ForwardPicker_SearchTextField')
FORWARD_SEND_BUTTON = accessibility_id('ForwardPickerView_ForwardButton')

# Sending a contact
SHARE_CONTACT_SEND_BUTTON = accessibility_id('ShareContactNavigationBar_DoneButton')

# Choosing contacts, e.g. to share them or to add them to a group
PICKER_SEARCH_FIELD = ios_predicate('type == "XCUIElementTypeSearchField"')
PICKER_NEXT_BUTTON = accessibility_id('ParticipantPickerNavigationBar_RightBarButton')

# The You tab, with the settings, and the profile opened from it
SETTINGS_EDIT_PROFILE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Edit profile"')
SETTINGS_BROADCAST_LISTS = accessibility_id('SettingsView_BroadcastListCell')
PROFILE_ABOUT = accessibility_id('ProfileView_AboutCell')
PROFILE_EDIT_PHOTO_BUTTON = accessibility_id('MyProfileHeaderCell_EditPhotoButton')
PROFILE_CHOOSE_PHOTO = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Choose photo"')
# The photo library of iOS, newest photos first, and the screen to crop the chosen photo
SYSTEM_PHOTOS = accessibility_id('PXGGridLayout-Info')
# The Collections of the photo library of iOS, with the albums, and the Cancel button of the photo library
SYSTEM_PHOTOS_COLLECTIONS = accessibility_id('Collections')
SYSTEM_PHOTOS_CANCEL_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND name == "Cancel"')
CROP_CHOOSE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" '
                                   'AND (label ENDSWITH "Choose" OR label ENDSWITH "Done")')
# Editing the about: a text field with a Save button. The about can be limited in time, by default to 1 day.
ABOUT_FIELD = ios_predicate('type == "XCUIElementTypeTextField"')
ABOUT_CLEAR_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Clear text"')
ABOUT_SAVE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "Save"')
ABOUT_DURATION_BUTTON = accessibility_id('EvolveAboutRedesignedCreation_DurationChip')

# The Updates tab, with the status
UPDATES_TEXT_STATUS_BUTTON = accessibility_id('StatusListView_TextButton')
UPDATES_CAMERA_STATUS_BUTTON = accessibility_id('StatusListView_CameraButton')
UPDATES_MY_STATUS = accessibility_id('updatesTab_status_myStatus')
STATUS_TEXT_FIELD = accessibility_id('WAStatusTextComposerView_TextView')
STATUS_SEND_BUTTON = accessibility_id('WAMultiSendBottomBarView_SendButton')
STATUS_CANCEL_BUTTON = accessibility_id('MediaCapture_TextModeCloseButton')
# The list of your own status updates, opened from My status
MY_STATUS_UPDATES = accessibility_id('StatusDetailView_StatusCell')
MY_STATUS_EDIT_BUTTON = accessibility_id('Edit')
MY_STATUS_DELETE_BUTTON = accessibility_id('trash')
MY_STATUS_DELETE_CONFIRM_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label BEGINSWITH "\u200eDelete" '
                                                'AND label CONTAINS "status update"')

# Calls, started from the buttons at the top of a chat
CALL_END_BUTTON = accessibility_id('CallUI_EndCallButton')
# The camera button turns the camera on in a voice call, and off in a video call
CALL_VOICE = accessibility_id('CallUI_VideoOnButton')
CALL_VIDEO = accessibility_id('CallUI_VideoOffButton')
# Shown until the call is answered
CALL_NOT_CONNECTED = ios_predicate('type == "XCUIElementTypeStaticText" AND (label ENDSWITH "Ringing..." '
                                   'OR label ENDSWITH "Calling..." OR label ENDSWITH "Connecting...")')

# Incoming calls are shown by iOS, not by WhatsApp: full screen, or as a banner at the top of the screen
INCOMING_CALL_APP = 'com.apple.InCallService'
INCOMING_CALL_ACCEPT_BUTTON = ios_predicate('type == "XCUIElementTypeButton" '
                                            'AND (name == "Accept" OR name == "acceptCall")')
INCOMING_CALL_DECLINE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" '
                                             'AND (name == "Decline" OR name == "rejectCall")')

# Every lookup on the overview takes seconds, as its element tree contains all chats. Therefore the screens shown on
# top of the overview (new chat, search) and on top of a chat (menus, trays, selection, info) are each recognized with
# a single lookup.
SCREENS_ON_TOP_OF_OVERVIEW = ios_predicate('name IN {"PickerView_SearchBar", "AISearch_PaperPlane_Back_Button"}')
SCREENS_ON_TOP_OF_CHAT = ios_predicate('name IN {"ContextMenu_ScrollView", "Toolbar_SelectedMessageCount", '
                                       '"AttachmentPicker_Menu", "Stickers_CollectionView", "MediaPicker_Asset", '
                                       '"NavigationBar_GroupInfoOverflowMenu"} OR label ENDSWITH "Contact info"')

# Pop-ups
# Shown the first time disappearing messages are opened
POPUP_DISAPPEARING_MESSAGES_TEXT = ios_predicate('label ENDSWITH "Get started with disappearing messages"')
POPUP_OK_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label ENDSWITH "OK"')


# Separates the name of a chat from details, e.g. the number of unread messages
DETAILS_SEPARATOR = ', \u200e'


def _is_named(attribute: str, name: str, separator: str = ', ') -> str:
    """
    A condition matching an element of which the attribute is a name, optionally followed by details after a separator,
    e.g. the about of a contact: 'Bob, Available'. The name is quoted, so it can contain quotes.
    """
    name = quoted(name)
    return f'({attribute} == "{name}" OR {attribute} BEGINSWITH "{name}{separator}")'


def conversation_row(conversation: str) -> str:
    """
    A chat in the overview, which is a cell named after the chat. For chats with unread messages, the number of unread
    messages follows the name, e.g. 'Bob, \u200e2 unread messages'.
    """
    return ios_class_chain(f'**/XCUIElementTypeTable[`name == "ChatListView_TableView"`]'
                           f'/XCUIElementTypeCell[`{_is_named("name", conversation, DETAILS_SEPARATOR)}`]')


def search_result_chat(conversation: str) -> str:
    """
    A chat in the search results. The label is the name, followed by e.g. the number of unread messages, or 'ARCHIVED'
    for archived chats.
    """
    return ios_predicate(f'name == "ChatListSearchView_ChatResult" '
                         f'AND {_is_named("label", conversation, DETAILS_SEPARATOR)}')


def archived_row(conversation: str) -> str:
    """
    A chat in the list of archived chats.
    """
    return ios_class_chain(f'**/XCUIElementTypeTable[`name == "WAArchivedChatsViewController"`]'
                           f'/XCUIElementTypeCell[`{_is_named("name", conversation, DETAILS_SEPARATOR)}`]')


def new_chat_contact(contact: str) -> str:
    """
    A contact in the list of a new chat. The label is the name, followed by the about of the contact if it has one.
    """
    return ios_predicate(f'name == "PickerView_ContactCell" AND {_is_named("label", contact)}')


def picker_contact(contact: str) -> str:
    """
    A contact in the list for choosing contacts, e.g. to share them.
    """
    return ios_predicate(f'name == "ParticipantPicker_ContactCell" AND {_is_named("label", contact)}')


def sent_message(text: str) -> str:
    """
    The messages sent from this device containing a text, from old to new. A newline in a predicate makes it match
    nothing, so the text cannot contain newlines.
    """
    return ios_predicate(f'label CONTAINS "{SENT_TO}" AND label CONTAINS "{quoted(text)}"')


def any_message(text: str) -> str:
    """
    The sent and received messages containing a text, from old to new. The text cannot contain newlines.
    """
    return ios_predicate(f'(label CONTAINS "{SENT_TO}" OR label CONTAINS "{RECEIVED_FROM}") '
                         f'AND label CONTAINS "{quoted(text)}"')


def forward_chat(conversation: str) -> str:
    """
    A chat in the list to forward messages to. The label is the name, followed by e.g. the about of the contact.
    """
    return ios_predicate(f'name BEGINSWITH "ForwardPicker_" AND type == "XCUIElementTypeCell" '
                         f'AND {_is_named("label", conversation)}')


def group_member(member: str) -> str:
    """
    A member in the group info. The label is the name, followed by e.g. the about of the member.
    """
    return ios_predicate(f'type == "XCUIElementTypeCell" AND {_is_named("label", member)}')


def about_duration(duration: str) -> str:
    """
    A duration of the about: '1 hour', '8 hours', '1 day', '2 days' or '1 week'.
    """
    return ios_predicate(f'name BEGINSWITH "EvolveAboutBottomSheet_Duration_" AND label ENDSWITH "{quoted(duration)}"')


def media_picker_album(album: str) -> str:
    """
    An album in the list of albums of the photo library, e.g. 'Recents' or 'Favorites'.
    """
    return ios_class_chain(f'**/XCUIElementTypeTable/XCUIElementTypeCell'
                           f'/XCUIElementTypeStaticText[`name == "{quoted(album)}"`]')


def system_photos_album(album: str) -> str:
    """
    An album in the Collections of the photo library of iOS, e.g. 'Recently Saved'. The albums are shown in rows that
    scroll sideways: only the first albums of each row can be found.
    """
    return ios_predicate(f'type == "XCUIElementTypeButton" AND label == "{quoted(album)}"')


def disappearing_messages_option(option: str) -> str:
    """
    An option for disappearing messages: 'Off', '24 hours', '7 days' or '90 days'.
    """
    return ios_predicate(f'type == "XCUIElementTypeStaticText" AND label ENDSWITH "{quoted(option)}"')
