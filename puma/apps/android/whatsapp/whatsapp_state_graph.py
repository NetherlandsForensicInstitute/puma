import re
from time import sleep
from typing import Union, List

from puma.apps.android.whatsapp import logger
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, PumaClickException
from puma.state_graph.state import SimpleState, ContextualState, State, compose_clicks
from puma.state_graph.state_graph import StateGraph
from puma.utils.xpath_utils import build_resource_id_xpath_widget, build_resource_id_xpath, \
    build_content_desc_xpath_widget, build_text_xpath_widget, build_resource_id_text_xpath_widget, \
    build_resource_id_text_xpath, build_text_xpath, build_content_desc_xpath


def build_wa_resource_id_xpath_widget(widget_type: str, resource_id: str) -> str:
    return build_resource_id_xpath_widget(widget_type, WHATSAPP_PACKAGE, resource_id)


def build_wa_resource_id_xpath(resource_id: str) -> str:
    return build_resource_id_xpath(WHATSAPP_PACKAGE, resource_id)


def build_wa_resource_id_text_xpath_widget(widget_type: str, resource_id: str, text: str) -> str:
    return build_resource_id_text_xpath_widget(widget_type, WHATSAPP_PACKAGE, resource_id, text)


def build_wa_resource_id_text_xpath(resource_id: str, text: str) -> str:
    return build_resource_id_text_xpath(WHATSAPP_PACKAGE, resource_id, text)

WHATSAPP_PACKAGE = 'com.whatsapp'
HAMBURGER_MENU = build_content_desc_xpath_widget('ImageView', 'More options')
# Conversations overview state xpaths
CONVERSATIONS_STATE_WHATSAPP_LOGO = build_wa_resource_id_xpath_widget('ImageView', 'toolbar_logo')
CONVERSATIONS_STATE_NEW_CHAT_OR_SEND_MESSAGE = f'{build_content_desc_xpath_widget('ImageButton', 'New chat')} | {build_content_desc_xpath_widget('Button', 'Send message')}'
CONVERSATIONS_STATE_CHAT_TAB = build_content_desc_xpath_widget('FrameLayout', 'Chats')
CONVERSATIONS_STATE_HOME_ROOT_FRAME = build_wa_resource_id_xpath_widget('FrameLayout', 'root_view')
CONVERSATIONS_STATE_MENUITEM_ARCHIVE = build_wa_resource_id_xpath('menuitem_conversations_archive')
CONVERSATIONS_STATE_ARCHIVED = f'//*[contains(@text,"archived") or @resource-id="{WHATSAPP_PACKAGE}:id/fab"]'
CONVERSATIONS_STATE_GROUP_NAME = build_wa_resource_id_xpath('group_name')
CONVERSATIONS_STATE_NEW_GROUP = build_text_xpath('New group')
CONVERSATIONS_STATE_CHAT_ABLE_CONTACT = build_wa_resource_id_text_xpath('chat_able_contacts_row_name', '{receiver}')
CONVERSATIONS_STATE_SEND = build_wa_resource_id_xpath_widget('ImageButton', 'send')
CONVERSATIONS_STATE_NEXT_BUTTON = build_wa_resource_id_xpath('next_btn')

SETTINGS_STATE_QR = build_wa_resource_id_xpath_widget('ImageView', 'profile_info_qr_code')
SETTINGS_STATE_ACCOUNT_SWITCH = build_wa_resource_id_xpath_widget('ImageView', 'account_switcher_button')

PROFILE_STATE_PROFILE_PICTURE = build_wa_resource_id_xpath_widget('ImageView', 'photo_btn')
PROFILE_STATE_NAME = build_wa_resource_id_text_xpath_widget('Button', 'profile_settings_row_text', 'Name')
PROFILE_STATE_PHONE = build_wa_resource_id_text_xpath_widget('Button', 'profile_settings_row_text', 'Phone')

PROFILE_STATE_INFO_EDIT_BUTTON = build_wa_resource_id_xpath_widget('Button', 'profile_info_edit_btn')
PROFILE_STATE_GALLERY = build_text_xpath('Gallery')
PROFILE_STATE_FOLDERS = build_content_desc_xpath_widget('ImageButton', 'Folders')
PROFILE_STATE_SAVE_BUTTON = build_wa_resource_id_xpath('save_button')
EDIT_TEXT = build_wa_resource_id_xpath('edit_text')
PROFILE_STATE_STATUS_EDIT_ICON = build_wa_resource_id_xpath('status_tv_edit_icon')
PROFILE_STATE_INFO_STATUS_CARD = build_wa_resource_id_xpath('profile_info_status_card')

# TODO-CC: there is no 'New chat'? You pick a contect from the 'Contacts on WhatsApp' list?
# NEW_CHAT_STATE_HEADER = build_text_xpath_widget('TextView', 'New chat')
NEW_CHAT_STATE_NEW_GROUP = build_wa_resource_id_text_xpath_widget('TextView', 'contactpicker_row_name', 'New group')
NEW_CHAT_STATE_NEW_CONTACT = build_wa_resource_id_text_xpath_widget('TextView', 'contactpicker_row_name', 'New contact')
NEW_CHAT_STATE_NEW_COMMUNITY = build_wa_resource_id_text_xpath_widget('TextView', 'contactpicker_row_name', 'New community')

CALLS_STATE_START_CALL = build_content_desc_xpath_widget('ImageButton', 'New call')
CALLS_STATE_HEADER = '//android.view.ViewGroup[@resource-id="com.whatsapp:id/toolbar"]/android.widget.TextView[@text="Calls"]'

UPDATES_STATE_HEADER = '//android.view.ViewGroup[@resource-id="com.whatsapp:id/toolbar"]/android.widget.TextView[@text="Updates"]'
UPDATES_STATE_STATUS_HEADER = build_wa_resource_id_text_xpath_widget('TextView', 'header_textview', 'Status')
UPDATES_STATE_NEW_STATUS = build_content_desc_xpath_widget('ImageButton', 'New status update')
UPDATES_STATE_SEND_BUTTON = build_wa_resource_id_xpath_widget('ImageButton', 'send')
UPDATES_STATE_EDIT_CAPTION = build_wa_resource_id_xpath_widget('EditText', 'caption')
UPDATES_STATE_SHUTTER = build_wa_resource_id_xpath_widget('ImageView', 'shutter')

#Chat state xpaths
CHAT_STATE_ROOT_LAYOUT = build_wa_resource_id_xpath_widget('LinearLayout', 'conversation_root_layout')
CHAT_STATE_CONTACT_HEADER = build_wa_resource_id_xpath_widget('TextView', 'conversation_contact_name')
CHAT_STATE_CONTACT_HEADER_WITH_NAME = build_wa_resource_id_text_xpath_widget('TextView', 'conversation_contact_name', '{conversation}')
CHAT_STATE_DELETE_BUTTON = build_content_desc_xpath('Delete')
CHAT_STATE_DELETE_FOR_EVERYONE = f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/buttonPanel"]//*[@text="Delete for everyone"]'
CHAT_STATE_SEND = build_wa_resource_id_xpath('send')
CHAT_STATE_ENTRY = build_wa_resource_id_xpath('entry')
CHAT_STATE_REPLY = build_content_desc_xpath('Reply')
CHAT_STATE_VIEW_ONCE_MEDIA = '//*[contains(@resource-id, "view_once_media")]'
CHAT_STATE_VOICE_NOTE_BUTTON = build_wa_resource_id_xpath('voice_note_btn')
CHAT_STATE_STICKER = build_wa_resource_id_xpath('sticker')
CHAT_STATE_STICKERS = build_wa_resource_id_xpath('stickers')
CHAT_STATE_EMOJI = build_wa_resource_id_xpath('emoji')
CHAT_STATE_EMOJIS = build_wa_resource_id_xpath('emojis')
CHAT_STATE_EMOJI_PICKER = build_wa_resource_id_xpath('emoji_picker_btn')

VOICE_CALL_STATE_CAMERA_BUTTON = '//android.widget.Button[@content-desc="Turn camera on" and @resource-id="com.whatsapp:id/camera_button"]'

CALL_STATE_CONTACT_HEADER = build_wa_resource_id_xpath_widget('TextView', 'title')
START_VOICE_CALL_BUTTON = build_wa_resource_id_xpath('voice_call')
START_VIDEO_CALL_BUTTON = build_wa_resource_id_xpath('video_call')

VIDEO_CALL_STATE_CAMERA_BUTTON = '//android.widget.Button[@content-desc="Turn camera off" and @resource-id="com.whatsapp:id/camera_button"]'
VIDEO_CALL_STATE_SWITCH_CAMERA = build_wa_resource_id_xpath_widget('Button', 'calling_camera_switch_wds_button')

SEND_LOCATION_STATE_HEADER = '//android.view.ViewGroup[@resource-id="com.whatsapp:id/toolbar"]/android.widget.TextView[@text="Send location"]'
SEND_LOCATION_STATE_LIVE_LOCATION = build_wa_resource_id_xpath_widget('FrameLayout', 'live_location_btn')
SEND_LOCATION_STATE_CURRENT_LOCATION = build_wa_resource_id_xpath_widget('FrameLayout', 'send_current_location_btn')

CHAT_SETTINGS_STATE_CONTACT_NAME = (f'{build_wa_resource_id_xpath_widget('TextView', 'contact_title')} | '
                                    f'{build_wa_resource_id_xpath_widget('TextView', 'business_title')} | '
                                    f'{build_wa_resource_id_xpath_widget('TextView', 'group_title')}')
CHAT_SETTINGS_STATE_NOTIFICATIONS = build_wa_resource_id_xpath_widget('LinearLayout', 'notifications_and_sounds_layout')
CHAT_SETTINGS_STATE_MEDIA_VISIBILITY = build_wa_resource_id_xpath_widget('Button', 'media_visibility_layout')

# Same!
MESSAGE_TEXT_BOX = build_wa_resource_id_xpath_widget('EditText', 'entry')
CONVERSATIONS_STATE_ENTRY = build_wa_resource_id_xpath_widget('EditText', 'entry')

CONTAINS_DELETE_GROUP = '//*[contains(@text,"Delete group")]'
TEXT_VIEWS = '//android.widget.TextView'

MENTION_SUGGESTIONS = build_wa_resource_id_xpath_widget('ImageView', 'contact_photo')
SEND_BUTTON = build_content_desc_xpath_widget('ImageButton', 'Send')
OK_BUTTON = build_wa_resource_id_xpath('ok_btn')
CAMERA_BUTTON = build_content_desc_xpath_widget('Button', 'Camera')
# Call state xpaths
CALL_TAB_SEARCH_BUTTON = build_content_desc_xpath_widget('ImageButton', 'Search')
ATTACH_BUTTON = build_wa_resource_id_xpath_widget('ImageButton', 'input_attach_button')
ATTACH_LOCATION_BUTTON = build_wa_resource_id_xpath_widget('Button', 'pickfiletype_location_holder')

# Settings state xpaths
OPEN_SETTINGS_BY_TITLE = build_text_xpath_widget('TextView', 'Settings')
PROFILE_INFO = build_wa_resource_id_xpath_widget('TextView', 'profile_info_name')

NEW_BROADCAST_TITLE = build_wa_resource_id_text_xpath('title', 'New broadcast')
SEARCH_BAR = build_wa_resource_id_xpath_widget('EditText', 'search_view_edit_text')
END_CALL_BUTTON = ('//*[@content-desc="Leave call" or '
                   '@resource-id="com.whatsapp:id/end_call_button" or '
                   '@resource-id="com.whatsapp:id/footer_end_call_btn"]')
CALL_SCREEN_BACKGROUND = build_wa_resource_id_xpath_widget('RelativeLayout', 'call_screen')
CALLS_TAB = build_wa_resource_id_text_xpath_widget('TextView', 'navigation_bar_item_small_label_view', 'Calls')
UPDATES_TAB = build_wa_resource_id_text_xpath_widget('TextView', 'navigation_bar_item_small_label_view', 'Updates')

# Conversations State
def conversation_row_for_subject(subject: str) -> str:
    return f"//*[contains(@resource-id,'com.whatsapp:id/conversations_row_contact_name') and @text='{subject}']"


def go_to_chat(driver: PumaDriver, conversation: str):
    """
    Navigates to a specific chat conversation in the application.

    This function constructs an XPath to locate and click on a conversation element
    based on the conversation name. It is designed to be used within a state transition
    to navigate to a specific chat state.

    :param driver: The PumaDriver instance used to interact with the application.
    :param conversation: The name of the conversation to navigate to.
    """
    logger.info(f'Clicking on conversation {conversation} with driver {driver}')
    driver.get_elements(conversation_row_for_subject(conversation))[-1].click()


def go_to_voice_call(driver: PumaDriver, contact: str):
    """
    Starts a voice call with a specific user.

    :param driver: The PumaDriver instance used to interact with the application.
    :param contact: The name of user to call.
    """
    driver.click(CALL_TAB_SEARCH_BUTTON)
    driver.send_keys(SEARCH_BAR, contact)
    driver.click(START_VOICE_CALL_BUTTON)


def go_to_video_call(driver: PumaDriver, contact: str):
    """
    Starts a video call with a specific user.

    :param driver: The PumaDriver instance used to interact with the application.
    :param contact: The name of user to call.
    """
    driver.click(CALL_TAB_SEARCH_BUTTON)
    driver.send_keys(SEARCH_BAR, contact)
    driver.click(START_VIDEO_CALL_BUTTON)


class WhatsAppChatState(SimpleState, ContextualState):
    """
    A state representing a chat screen in the application.

    This class extends both SimpleState and ContextualState to represent a chat screen
    and validate its context based on the conversation name.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the ChatState with a parent state.

        :param parent_state: The parent state of this chat state.
        """
        super().__init__(xpaths=[CHAT_STATE_CONTACT_HEADER,
                                 CHAT_STATE_ROOT_LAYOUT],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates the context of the chat state.

        This method checks if the current chat screen matches the expected conversation name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the conversation to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not conversation:
            return True

        content_desc = (driver.get_element(CHAT_STATE_CONTACT_HEADER).get_attribute('text'))
        return conversation.lower() in content_desc.lower()

    @staticmethod
    def open_chat_settings(driver: PumaDriver, conversation: str):
        driver.click(CHAT_STATE_CONTACT_HEADER_WITH_NAME.format(conversation=conversation))


class WhatsAppChatSettingsState(SimpleState, ContextualState):
    """
    A state representing a chat settings screen in the application.

    This class extends both SimpleState and ContextualState to represent a chat settings screen
    and validate its context based on the contact or group name.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the ChatSettingsState with a parent state.

        :param parent_state: The parent state of this chat state.
        """
        super().__init__(xpaths=[CHAT_SETTINGS_STATE_CONTACT_NAME,
                                 CHAT_SETTINGS_STATE_NOTIFICATIONS,
                                 CHAT_SETTINGS_STATE_MEDIA_VISIBILITY],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates the context of the chat settings state.

        This method checks if the current chat settings screen matches the expected contact or group name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the conversation to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not conversation:
            return True

        content_desc = (driver.get_element(CHAT_SETTINGS_STATE_CONTACT_NAME).get_attribute('text'))
        return conversation.lower() in content_desc.lower()


class WhatsAppVoiceCallState(SimpleState, ContextualState):
    """
    A state representing a call screen in the application.

    This class extends both SimpleState and ContextualState to represent a call screen
    and validate its context based on the contact.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the CallState with a parent state.

        :param parent_state: The parent state of this call state.
        """
        super().__init__(xpaths=[END_CALL_BUTTON,
                                 CALL_SCREEN_BACKGROUND,
                                 VOICE_CALL_STATE_CAMERA_BUTTON],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, contact: str = None) -> bool:
        """
        Validates the context of the call state.

        This method checks if the current call screen matches the expected contact name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param contact: The name of the call recipient to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not contact:
            return True

        content_desc = (driver.get_element(CALL_STATE_CONTACT_HEADER).get_attribute('text'))
        return contact.lower() in content_desc.lower()

class WhatsAppVideoCallState(SimpleState, ContextualState):
    """
    A state representing a call screen in the application.

    This class extends both SimpleState and ContextualState to represent a call screen
    and validate its context based on the contact.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the CallState with a parent state.

        :param parent_state: The parent state of this call state.
        """
        super().__init__(xpaths=[END_CALL_BUTTON,
                                 CALL_SCREEN_BACKGROUND,
                                 VIDEO_CALL_STATE_CAMERA_BUTTON,
                                 VIDEO_CALL_STATE_SWITCH_CAMERA],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, contact: str = None) -> bool:
        """
        Validates the context of the call state.

        This method checks if the current call screen matches the expected contact name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param contact: The name of the call recipient to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not contact:
            return True

        content_desc = (driver.get_element(CALL_STATE_CONTACT_HEADER).get_attribute('text'))
        return contact.lower() in content_desc.lower()


class WhatsApp(StateGraph):
    """
    TODO
    """

    conversations_state = SimpleState([CONVERSATIONS_STATE_WHATSAPP_LOGO,
                                      CONVERSATIONS_STATE_HOME_ROOT_FRAME,
                                      CONVERSATIONS_STATE_NEW_CHAT_OR_SEND_MESSAGE,
                                      CONVERSATIONS_STATE_CHAT_TAB],
                                      initial_state=True)
    settings_state = SimpleState([SETTINGS_STATE_QR,
                                  SETTINGS_STATE_ACCOUNT_SWITCH],
                                 parent_state=conversations_state)
    profile_state = SimpleState([PROFILE_STATE_PROFILE_PICTURE,
                                 PROFILE_STATE_NAME,
                                 PROFILE_STATE_PHONE],
                                parent_state=settings_state)
    chat_state = WhatsAppChatState(parent_state=conversations_state)
    new_chat_state = SimpleState([NEW_CHAT_STATE_NEW_GROUP,
                                  NEW_CHAT_STATE_NEW_CONTACT,
                                  NEW_CHAT_STATE_NEW_COMMUNITY],
                                 parent_state=conversations_state)
    calls_state = SimpleState([CALLS_STATE_HEADER,
                               CALLS_STATE_START_CALL],
                              parent_state=conversations_state)
    updates_state = SimpleState([UPDATES_STATE_HEADER,
                                 UPDATES_STATE_STATUS_HEADER,
                                 UPDATES_STATE_NEW_STATUS],
                                parent_state=conversations_state)
    voice_call_state = WhatsAppVoiceCallState(parent_state=calls_state)
    video_call_state = WhatsAppVideoCallState(parent_state=calls_state)
    send_location_state = SimpleState([SEND_LOCATION_STATE_HEADER,
                                       SEND_LOCATION_STATE_LIVE_LOCATION,
                                       SEND_LOCATION_STATE_CURRENT_LOCATION],
                                      parent_state=chat_state)
    chat_settings_state = WhatsAppChatSettingsState(parent_state=chat_state)

    conversations_state.to(chat_state, go_to_chat)
    conversations_state.to(settings_state, compose_clicks([HAMBURGER_MENU, OPEN_SETTINGS_BY_TITLE]))
    conversations_state.to(new_chat_state, compose_clicks([CONVERSATIONS_STATE_NEW_CHAT_OR_SEND_MESSAGE]))
    conversations_state.to(calls_state, compose_clicks([CALLS_TAB]))
    conversations_state.to(updates_state, compose_clicks([UPDATES_TAB]))
    calls_state.to(voice_call_state, go_to_voice_call)
    calls_state.to(video_call_state, go_to_video_call)
    settings_state.to(profile_state, compose_clicks([PROFILE_INFO]))
    chat_state.to(send_location_state, compose_clicks([ATTACH_BUTTON, ATTACH_LOCATION_BUTTON]))
    chat_state.to(chat_settings_state, WhatsAppChatState.open_chat_settings)


    def __init__(self, device_udid: str, app_package: str):
        StateGraph.__init__(self, device_udid, app_package)

    def _handle_mention(self, message):
        """
        Make sure to convert a @name to an actual mention. Only one mention is allowed.
        :param message: The message containing the mention.
        """
        self.driver.send_keys(MESSAGE_TEXT_BOX, message)
        sleep(1)
        # Find the mentioned name in the message. Note that it will search until the last word character. This means for
        # @jan-willem or @jan willem, only @jan will be found.
        mention_match = re.search(r"@\w+", message)
        mentioned_name = mention_match.group(0).strip("@")

        self.driver.press_left_arrow()
        while not (mention_suggestions := self.driver.get_elements(MENTION_SUGGESTIONS)):
             self.driver.press_left_arrow()

        mentioned_person_el = \
            [person for person in
             mention_suggestions
             if mentioned_name.lower() in person.tag_name.lower()][0]
        mentioned_person_el.click()

        # Remove a space resulting from selecting the mention person
        self.driver.press_backspace()

    def _ensure_message_sent(self, message_text):
        message_status_el = self.driver.get_element(
            f"//*[@resource-id='com.whatsapp:id/conversation_text_row']"
            f"//*[@text='{message_text}']"  # Text field element containing message text
            f"/.."  # Parent of the message (i.e. conversation text row)
            f"//*[@resource-id='com.whatsapp:id/status']")  # Status element
        while message_status_el.tag_name == "Pending":
            logger.info("Message pending, waiting for the message to be sent.")
            sleep(10)
        return message_status_el

    def send_message_in_current_conversation(self, message_text, wait_until_sent=False):
        self.driver.click(MESSAGE_TEXT_BOX)
        self._handle_mention(message_text) \
            if "@" in message_text \
            else self.driver.send_keys(MESSAGE_TEXT_BOX, message_text)

        #Allow time for the link preview to load
        if 'http' in message_text:
            sleep(2)
        self.driver.click(SEND_BUTTON)
        # TODO convert to post action validation
        if wait_until_sent:
            _ = self._ensure_message_sent(message_text)

    @action(chat_state)
    def send_message(self, conversation: str, message_text, wait_until_sent=False):
        """
        Send a message in the current chat. If the message contains a mention, this is handled correctly.
        :param wait_until_sent: Exit this function only when the message has been sent.
        :param conversation: The chat conversation in which to send this message.
        :param message_text: The text that the message contains.
        """
        self.send_message_in_current_conversation(message_text, wait_until_sent)

    @action(profile_state)
    def change_profile_picture(self, photo_dir_name, index=1):
        self.driver.click(PROFILE_STATE_INFO_EDIT_BUTTON)
        self.driver.click(PROFILE_STATE_GALLERY)
        self.driver.click(PROFILE_STATE_FOLDERS)
        self._find_media_in_folder(photo_dir_name, index)
        self.driver.click(OK_BUTTON)

    @action(updates_state)
    def add_status(self, caption: str = None):
        """
        Sets a status by taking a picture and setting the given caption.
        Note: The first time an update is created, a pop-up will appear to change your privacy settings. This has to be
        handled once manually.
        :param caption: the caption to publish with the status.
        """
        self.driver.click(UPDATES_STATE_NEW_STATUS)
        self.driver.click(CAMERA_BUTTON)
        self.driver.click(UPDATES_STATE_SHUTTER)
        if caption:
             self.driver.send_keys(UPDATES_STATE_EDIT_CAPTION, caption)
        self.driver.click(UPDATES_STATE_SEND_BUTTON)

    @action(profile_state)
    def set_about(self, about_text: str):
        self.driver.click(PROFILE_STATE_INFO_STATUS_CARD)
        self.driver.click(PROFILE_STATE_STATUS_EDIT_ICON)
        self.driver.send_keys(EDIT_TEXT, about_text)
        self.driver.click(PROFILE_STATE_SAVE_BUTTON)
        # This action ends in a screen that isn't a state, so move back one screen.
        self.driver.back()

    @action(new_chat_state)
    def create_new_chat(self, conversation, first_message):
        """
        Start a new 1-on-1 conversation with a contact and send a message.
        :param conversation: Contact to start the conversation with.
        :param first_message: First message to send to the contact
        """
        self.driver.click(f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/contactpicker_text_container"]//*[@text="{conversation}"]')
        self.driver.click(build_content_desc_xpath_widget('Button', 'Message'))
        self.send_message_in_current_conversation(first_message)

    def open_more_options(self):
        """
        Open more options (hamburger menu) in the home screen.
        """
        self.driver.click(HAMBURGER_MENU)

    @action(conversations_state)
    def send_broadcast(self, receivers: List[str], broadcast_text: str):
        """
        Broadcast a message.
        :param receivers: list of receiver names, minimum of 2!
        :param broadcast_text: Text to send.
        """
        if len(receivers) < 2:
            raise Exception(f"Error: minimum of 2 receivers required for a broadcast, got: {receivers}")

        self.open_more_options()
        self.driver.click(NEW_BROADCAST_TITLE)
        for receiver in receivers:
            self.driver.click(CONVERSATIONS_STATE_CHAT_ABLE_CONTACT)

        self.driver.click(CONVERSATIONS_STATE_NEXT_BUTTON)
        self.driver.send_keys(CONVERSATIONS_STATE_ENTRY, broadcast_text)
        self.driver.click(CONVERSATIONS_STATE_SEND)

    @action(chat_state)
    def delete_message_for_everyone(self, conversation: str, message_text: str):
        """
        Remove a message with the message text. Should be recently sent, so it is still in view and still possible to
        delete for everyone.
        :param conversation: The chat conversation in which to send this message, if not currently in the desired chat.
        :param message_text: literal message text of the message to remove. The first match will be removed in case
        there are multiple with the same text.
        """
        self.driver.long_press_element(f"//*[@resource-id='{WHATSAPP_PACKAGE}:id/conversation_text_row']//*[@text='{message_text}']")
        self.driver.click(CHAT_STATE_DELETE_BUTTON)
        self.driver.click(CHAT_STATE_DELETE_FOR_EVERYONE)

    @action(conversations_state)
    def create_group(self, conversation: str, participants: Union[str, List[str]]):
        """
        Create a new group.
        :param conversation: The subject of the group.
        :param participants: The contact(s) you want to add to the group (string or list).
        """
        self.open_more_options()
        self.driver.click(CONVERSATIONS_STATE_NEW_GROUP)

        participants = [participants] if not isinstance(participants, list) else participants
        for participant in participants:
            contacts = self.driver.get_elements(TEXT_VIEWS)
            participant_to_add = [contact for contact in contacts if contact.text.lower() == participant.lower()][0]
            participant_to_add.click()

        self.driver.click(CONVERSATIONS_STATE_NEXT_BUTTON)
        self.driver.send_keys(CONVERSATIONS_STATE_GROUP_NAME, conversation)
        self.driver.click(OK_BUTTON)
        # Creating a group takes a few seconds
        sleep(2)

    @action(conversations_state)
    def archive_conversation(self, conversation: str):
        """
        Archives a given conversation.
        :param conversation: The conversation to archive.
        """
        self.driver.long_press_element(f'//*[contains(@resource-id,"{WHATSAPP_PACKAGE}:id/conversations_row_contact_name") and @text="{conversation}"]')
        self.driver.click(CONVERSATIONS_STATE_MENUITEM_ARCHIVE)
        # Wait until the archive popup disappeared
        archived_popup_present = True
        tries = 0
        while archived_popup_present and tries < 5:
            logger.info("waiting for archived popup to disappear")
            sleep(5)
            tries += 1
            archived_popup_present = 'archived' in self.driver.get_elements(CONVERSATIONS_STATE_ARCHIVED)[0].text
        logger.info("Archive pop-up gone!")

    @action(chat_state)
    def open_view_once_photo(self, conversation: str):
        """
        Open view once photo in the specified chat. Should be done right after the photo is sent, to ensure the correct
        photo is opened, this will be the lowest one.
        :param conversation: The chat in which the photo has to be opened
        """
        self.driver.get_elements(CHAT_STATE_VIEW_ONCE_MEDIA)[-1].click()

    @action(chat_settings_state)
    def set_group_description(self, conversation: str, description: str):
        """
        Set the group description.
        :param conversation: Name of the group to set the description for.
        :param description: Description of the group.
        """
        self.driver.swipe_to_click_element(f'{build_wa_resource_id_xpath('no_description_view')} | {build_wa_resource_id_xpath('has_description_view')}')
        self.driver.send_keys(EDIT_TEXT, description)
        self.driver.click(OK_BUTTON)

    @action(chat_settings_state)
    def delete_group(self, conversation: str):
        """
        Leaves and deletes a given group.
        Assumes the group exists and hasn't been left yet.
        :param conversation: the group to be deleted.
        """
        self.leave_group(conversation)
        self.driver.click(CONTAINS_DELETE_GROUP)
        self.driver.click(CONTAINS_DELETE_GROUP)

    @action(chat_state)
    def reply_to_message(self, conversation: str, message_to_reply_to: str, reply_text: str):
        """
        Reply to a message.
        :param conversation: The chat conversation in which to send this message.
        :param message_to_reply_to: message you want to reply to.
        :param reply_text: message text you are sending in your reply.
        """
        message_xpath = f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/message_text" and contains(@text, "{message_to_reply_to}")]'
        self.driver.swipe_to_find_element(message_xpath)
        self.driver.long_press_element(message_xpath)
        self.driver.click(CHAT_STATE_REPLY)
        self.driver.send_keys(CHAT_STATE_ENTRY, reply_text)
        self.driver.click(CHAT_STATE_SEND)

    @action(chat_state)
    def send_emoji(self, conversation: str):
        """
        Send the first emoji in the emoji menu.
        :param conversation: The chat conversation in which to send this sticker.
        """
        self.driver.click(CHAT_STATE_EMOJI_PICKER)
        sleep(1)
        self.driver.click(CHAT_STATE_EMOJIS)
        self.driver.click(CHAT_STATE_EMOJI)
        self.driver.click(CHAT_STATE_SEND)

    @action(chat_state)
    def send_sticker(self, conversation: str):
        """
        Send the first sticker in the sticker menu.
        :param conversation: The chat conversation in which to send this sticker.
        """
        self.driver.click(CHAT_STATE_EMOJI_PICKER)
        sleep(1)
        self.driver.click(CHAT_STATE_STICKERS)
        self.driver.click(CHAT_STATE_STICKER)

    @action(chat_state)
    def send_voice_recording(self, conversation: str, duration: int = 2000):
        """
        Sends a voice message in the specified conversation.
        :param conversation: The chat conversation in which to send this voice recording.
        :param duration: the duration in of the voice message to send in milliseconds.
        """
        self.driver.long_press_element(CHAT_STATE_VOICE_NOTE_BUTTON, duration=duration)

    @action(send_location_state, end_state=chat_state)
    def send_current_location(self, conversation: str):
        """
        Send the current location in the specified chat.
        :param conversation: The chat conversation in which to send the location.
        """
        sleep(5)  # it takes some time to fix the location
        self.driver.click('//*[@resource-id="com.whatsapp:id/send_current_location_btn"]')

    @action(send_location_state, end_state=chat_state)
    def send_live_location(self, conversation: str, caption=None):
        """
        Send a live location in the specified chat.
        :param conversation: The chat conversation in which to start the live location sharing.
        :param caption: Optional caption sent along with the live location
        """
        self.driver.click('//*[@resource-id="com.whatsapp:id/live_location_btn"]')
        dialog = f'//android.widget.LinearLayout[@resource-id="com.whatsapp:id/location_new_user_dialog_container"]'
        if self.driver.is_present(dialog):
            self.driver.click('//android.widget.Button[@text="Continue"]')
        if caption is not None:
            self.driver.send_keys('//*[@resource-id="com.whatsapp:id/comment"]', caption)
        self.driver.click('//*[@resource-id="com.whatsapp:id/send"]')

    @action(chat_state)
    def stop_live_location(self, conversation: str):
        """
        Stops the current live location sharing.
        :param conversation: The chat conversation in which to stop the live location sharing.
        """
        self.driver.swipe_to_click_element('//*[@text="Stop sharing"]')

        popup_button_xpath = '//android.widget.Button[@content-desc="Stop"]'
        if self.driver.is_present(popup_button_xpath):
            self.driver.click(popup_button_xpath)

    @action(chat_state)
    def send_contact(self, conversation: str, contact_name: str):
        """
        Send a contact in the specified chat.
        :param contact_name: the name of the contact to send.
        :param conversation: The chat conversation in which to send the contact.
        """
        self.driver.click('//*[@resource-id="com.whatsapp:id/input_attach_button"]')
        self.driver.click('//*[@resource-id="com.whatsapp:id/pickfiletype_contact_holder"]')
        self.driver.swipe_to_click_element(f'//android.widget.TextView[@resource-id="com.whatsapp:id/name" and @text="{contact_name}"]')
        self.driver.click('//*[@resource-id="com.whatsapp:id/next_btn"]')
        self.driver.click('//*[@resource-id="com.whatsapp:id/send_btn"]')

    @action(chat_settings_state)
    def activate_disappearing_messages(self, conversation: str):
        """
        Activates disappearing messages (auto delete) in the current or a given chat.
        Messages will now auto-delete after 24h.
        :param conversation: The conversation for which disappearing messages should be activated.
        """
        self.driver.swipe_to_click_element('//*[@resource-id="com.whatsapp:id/list_item_title" and @text="Disappearing messages"]')
        self.driver.click('//android.widget.RadioButton[@text="24 hours"]')
        self.driver.back()

    @action(chat_settings_state)
    def deactivate_disappearing_messages(self, conversation: str):
        """
        Disables disappearing messages (auto delete) in the current or a given chat.
        :param conversation: The conversation for which disappearing messages should be activated.
        """
        self.driver.swipe_to_click_element('//*[@resource-id="com.whatsapp:id/list_item_title" and @text="Disappearing messages"]')
        self.driver.click('//android.widget.RadioButton[@text="Off"]')
        self.driver.back()

    @action(calls_state, end_state=voice_call_state)
    def voice_call_contact(self, conversation: str):
        """
        Make a WhatsApp voice call. The call is made to a given contact.
        :param conversation: name of the contact to call.
        """
        go_to_voice_call(self.driver, conversation)

    @action(calls_state, end_state=video_call_state)
    def video_call_contact(self, conversation: str):
        """
        Make a WhatsApp voice call. The call is made to a given contact.
        :param conversation: name of the contact to call.
        """
        go_to_video_call(self.driver, conversation)

    @action(voice_call_state, end_state=calls_state)
    def end_voice_call(self):
        """
        Ends the current voice call.
        """
        self._end_call()

    @action(video_call_state, end_state=calls_state)
    def end_video_call(self):
        """
        Ends the current video call.
        """
        self._end_call()

    def _end_call(self):
        end_call_button = f'//*[@content-desc="Leave call" or @resource-id="com.whatsapp:id/end_call_button" or @resource-id="com.whatsapp:id/footer_end_call_btn"]'
        if not self.driver.is_present(end_call_button, implicit_wait=1):
            # tap screen to make call button visible
            self.driver.click(CALL_SCREEN_BACKGROUND)
        self.driver.click(end_call_button)

    # This method is not an @action, since it is not tied to a state.
    def answer_call(self):
        """
        Answer when receiving a call via Whatsapp.
        """
        self.driver.open_notifications()
        sleep(2)
        self.driver.click("//android.widget.Button[@content-desc='Answer' or @content-desc='Video']")

    # This method is not an @action, since it is not tied to a state.
    def decline_call(self):
        """
        Declines an incoming Whatsapp call.
        """
        self.driver.open_notifications()
        sleep(2)
        self.driver.click("//android.widget.Button[@content-desc='Decline']")

    @action(chat_settings_state)
    def leave_group(self, conversation: str):
        """
        This method will leave the given group. It will not delete that group.
        :param conversation: Name of the group we want to leave.
        """
        self.driver.swipe_to_click_element('//*[@resource-id="com.whatsapp:id/list_item_title" and @text="Exit group"]')
        self.driver.click('//android.widget.Button[@text="Exit group"]')

    @action(chat_settings_state)
    def remove_participant_from_group(self, conversation: str, participant):
        """
        Removes a given participant from a given group chat.
        It is assumed the group chat exists and has the given participant.
        :param conversation: The group
        :param participant: The participant to remove
        """
        self.driver.swipe_to_click_element(f'//*[@resource-id="com.whatsapp:id/name" and @text="{participant}"]')
        self.driver.click("//*[starts-with(@text, 'Remove')]")
        self.driver.click("//*[@class='android.widget.Button' and @text='OK']")

    @action(chat_state)
    def forward_message(self, conversation: str, message_contains, to_chat):
        """
        Forwards a message from one conversation to another.
        It is assumed the message and both conversations exists.
        :param conversation: The chat from which the message has to be forwarded
        :param message_contains: the text from the message that has to be forwarded. Uses String.contains(), so only part
        of the message is needed, but be sure the given text is enough to match your intended message uniquely.
        :param to_chat: The chat to which the message has to be forwarded.
        """
        self.driver.long_press_element(f"//*[@resource-id='com.whatsapp:id/conversation_text_row']//*[contains(@text,'{message_contains}')]")
        self.driver.click(f"//*[@resource-id='com.whatsapp:id/action_mode_bar']//*[@content-desc='Forward']")
        self.driver.click(f"//*[@resource-id='com.whatsapp:id/contact_list']//*[@text='{to_chat}']")
        self.driver.click('//*[@resource-id="com.whatsapp:id/send"]')

    @action(chat_state)
    def send_media(self, conversation: str, directory_name, index=1, caption=None, view_once=False):
        # Go to gallery
        self.driver.click(f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/input_attach_button"]')
        self.driver.click(f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/pickfiletype_gallery_holder"]')

        self.driver.click('//android.widget.ImageButton[@content-desc="Folders"]')
        self._find_media_in_folder(directory_name, index)
        sleep(0.5)
        self.driver.click('//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[5]/android.view.View[3]/android.widget.Button')

        if caption:
            sleep(0.5)
            caption_xpath = f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/caption"]'
            self.driver.send_keys(caption_xpath, caption)
            # Clicking the text box after sending keys is required for Whatsapp to notice text has been inserted.
            self.driver.click(caption_xpath)
            self.driver.back()

        if view_once:
            self.driver.click(f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/view_once_toggle"]')
            popup_button = f'//android.widget.Button[@resource-id="{WHATSAPP_PACKAGE}:id/vo_sp_bottom_sheet_ok_button"]'
            if self.driver.is_present(popup_button):
                self.driver.click(popup_button)
        sleep(1)
        self.driver.click(f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/send"]')

    def _find_media_in_folder(self, directory_name, index):
        try:
            self.driver.swipe_to_click_element(xpath=f'//android.widget.TextView[@text="{directory_name}"]')
        except PumaClickException:
            raise PumaClickException(f'The directory {directory_name} could not be found.')
        self.driver.click(f'//android.widget.TextView[@text="{directory_name}"]')
        sleep(0.5)
        try:
            self.driver.click(f'//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[4]/android.view.View[{index}]/android.view.View[2]/android.view.View')
        except PumaClickException:
            raise PumaClickException(
                f'The media at index {index} could not be found. The index is likely too large or negative.')
