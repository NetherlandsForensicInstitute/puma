import re
from abc import abstractmethod
from time import sleep
from typing import Union, List

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common import NoSuchElementException

from puma.apps.android import log_action
from puma.apps.android.whatsapp import logger
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, State, compose_clicks
from puma.state_graph.state_graph import StateGraph

HAMBURGER_MENU = '//android.widget.ImageView[@content-desc="More options"]'
# Conversations overview state xpaths
CONVERSATIONS_STATE_WHATSAPP_LOGO = '//android.widget.ImageView[@resource-id="com.whatsapp:id/toolbar_logo"]'
CONVERSATIONS_STATE_NEW_CHAT_OR_SEND_MESSAGE = '//android.widget.ImageButton[@content-desc="New chat"] | //android.widget.Button[@content-desc="Send message"]'
CONVERSATIONS_STATE_CHAT_TAB = '//android.widget.FrameLayout[@content-desc="Chats"]'
CONVERSATIONS_STATE_HOME_ROOT_FRAME = '//android.widget.FrameLayout[@resource-id="com.whatsapp:id/root_view"]'

SETTINGS_STATE_QR = '//android.widget.ImageView[@resource-id="com.whatsapp:id/profile_info_qr_code"]'
SETTINGS_STATE_ACCOUNT_SWITCH = '//android.widget.ImageView[@resource-id="com.whatsapp:id/account_switcher_button"]'

PROFILE_STATE_PROFILE_PICTURE = '//android.widget.ImageView[@resource-id="com.whatsapp:id/photo_btn"]'
PROFILE_STATE_NAME = '//android.widget.Button[@resource-id="com.whatsapp:id/profile_settings_row_text" and @text="Name"]'
PROFILE_STATE_PHONE = '//android.widget.Button[@resource-id="com.whatsapp:id/profile_settings_row_text" and @text="Phone"]'

# TODO-CC: there is no 'New chat'? You pick a contect from the 'Contacts on WhatsApp' list?
# NEW_CHAT_STATE_HEADER = '//android.widget.TextView[@text="New chat"]'
NEW_CHAT_STATE_NEW_GROUP = '//android.widget.TextView[@resource-id="com.whatsapp:id/contactpicker_row_name" and @text="New group"]'
NEW_CHAT_STATE_NEW_CONTACT = '//android.widget.TextView[@resource-id="com.whatsapp:id/contactpicker_row_name" and @text="New contact"]'
NEW_CHAT_STATE_NEW_COMMUNITY = '//android.widget.TextView[@resource-id="com.whatsapp:id/contactpicker_row_name" and @text="New community"]'

CALLS_STATE_START_CALL = '//android.widget.Button[@content-desc="Start a call"]'
CALLS_STATE_HEADER = '//android.view.ViewGroup[@resource-id="com.whatsapp:id/toolbar"]/android.widget.TextView[@text="Calls"]'

UPDATES_STATE_HEADER = '//android.view.ViewGroup[@resource-id="com.whatsapp:id/toolbar"]/android.widget.TextView[@text="Updates"]'
UPDATES_STATE_STATUS_HEADER = '//android.widget.TextView[@resource-id="com.whatsapp:id/header_textview" and @text="Status"]'
# TODO-CC: invalid after updating status?
# UPDATES_STATE_NEW_STATUS = '//android.view.View[@content-desc="New status update"]'
UPDATES_STATE_NEW_STATUS = '//android.widget.ImageButton[@content-desc="New status update"]'

#Chat state xpaths
CHAT_STATE_ROOT_LAYOUT = '//android.widget.LinearLayout[@resource-id="com.whatsapp:id/conversation_root_layout"]'
CHAT_STATE_CONTACT_HEADER = '//android.widget.TextView[@resource-id="com.whatsapp:id/conversation_contact_name"]'

CALL_STATE_CONTACT_HEADER = '//android.widget.TextView[@resource-id="com.whatsapp:id/title"]'

MESSAGE_TEXT_BOX = '//android.widget.EditText[@resource-id="com.whatsapp:id/entry"]'
MENTION_SUGGESTIONS = '//android.widget.ImageView[@resource-id="com.whatsapp:id/contact_photo"]'
SEND_BUTTON = '//android.widget.ImageButton[@content-desc="Send"]'
REPLY_ACTION = '//*[@content-desc="Reply"]'
DELETE_ACTION = '//*[@content-desc="Delete"]'
VIEW_ONCE_MEDIA = '//*[contains(@resource-id, "view_once_media")]'
CONTINUE_BUTTON_TEXT = "//android.widget.Button[@text='Continue']"
STOP_SHARING_TEXT = "//*[@text='Stop sharing']"
STOP_BUTTON = '//android.widget.Button[@content-desc="Stop"]'
CAMERA_BUTTON = '//android.widget.Button[@content-desc="Camera"]'
NEW_GROUP_TEXT = "//*[@text='New group']"
DELETE_GROUP_CONTAINS = "//*[contains(@text,'Delete group')]"
REMOVE_PARTICIPANT_STARTS_WITH = "//*[starts-with(@text, 'Remove')]"
OK_BUTTON_CLASS_TEXT = "//*[@class='android.widget.Button' and @text='OK']"
# Call state xpaths
CALL_TAB_SEARCH_BUTTON = '//android.widget.ImageButton[@content-desc="Search"]'
ANSWER_OR_VIDEO_BUTTON = "//android.widget.Button[@content-desc='Answer' or @content-desc='Video']"
DECLINE_BUTTON = "//android.widget.Button[@content-desc='Decline']"

# Settings state xpaths
OPEN_SETTINGS_BY_TITLE = '//android.widget.TextView[@text="Settings"]'
NEW_STATUS_BUTTON = '//android.widget.ImageButton[@content-desc="New status update"]'
PROFILE_INFO = '//android.widget.TextView[@resource-id="com.whatsapp:id/profile_info_name"]'

#previously fstring templates
FAB_OR_FABTEXT = "//*[@resource-id='com.whatsapp:id/fab' or @resource-id='com.whatsapp:id/fabText']"
DELETE_FOR_EVERYONE = "//*[@resource-id='com.whatsapp:id/buttonPanel']//*[@text='Delete for everyone']"
NEW_BROADCAST_TITLE = "//*[@resource-id='com.whatsapp:id/title' and @text='New broadcast']"
LOCATION_DIALOG = '//android.widget.LinearLayout[@resource-id="com.whatsapp:id/location_new_user_dialog_container"]'
SEARCH_BAR = '//android.widget.EditText[@resource-id="com.whatsapp:id/search_view_edit_text"]'
END_CALL_BUTTON = ('//*[@content-desc="Leave call" or '
                   '@resource-id="com.whatsapp:id/end_call_button" or '
                   '@resource-id="com.whatsapp:id/footer_end_call_btn"]')
CALL_SCREEN_BACKGROUND = '//android.widget.RelativeLayout[@resource-id="com.whatsapp:id/call_screen"]'
ARCHIVED_OR_FAB = "//*[contains(@text,'archived') or @resource-id='com.whatsapp:id/fab']"
SETTINGS_TITLE = '//android.widget.TextView[@resource-id="com.whatsapp:id/title" and @text="Settings"]'
FORWARD_ACTION = "//*[@resource-id='com.whatsapp:id/action_mode_bar']//*[@content-desc='Forward']"
CONVERSATION_ROW_BY_SUBJECT = "//*[contains(@resource-id,'com.whatsapp:id/conversations_row_contact_name') and @text='{subject}']"
CONTACTPICKER_TEXT = "//*[@resource-id='com.whatsapp:id/contactpicker_text_container']//*[@text='{contact}']"
CONVERSATION_TEXT_ROW_WITH_TEXT = "//*[@resource-id='com.whatsapp:id/conversation_text_row']//*[@text='{message_text}']"
BROADCAST_CONTACT_ROW = "//*[@resource-id='com.whatsapp:id/chat_able_contacts_row_name' and @text='{receiver}']"
CONTACT_NAME_IN_PICKER = '//android.widget.TextView[@resource-id="com.whatsapp:id/name" and @text="{contact_name}"]'
NAVIGATION_TAB_BY_TEXT = ('//android.widget.TextView['
                          '( @resource-id="com.whatsapp:id/navigation_bar_item_small_label_view"'
                          ' or @resource-id="com.whatsapp:id/navigation_bar_item_large_label_view" )'
                          ' and @text="{tab_text}"]')
CALLS_TAB = '//android.widget.TextView[@resource-id="com.whatsapp:id/navigation_bar_item_small_label_view" and @text="Calls"]'
UPDATES_TAB = '//android.widget.TextView[@resource-id="com.whatsapp:id/navigation_bar_item_small_label_view" and @text="Updates"]'
CALL_TYPE_IMAGEVIEW_TEMPLATE = '(//android.widget.ImageView[@content-desc="{call_type}"])[1]'
CONVERSATION_TEXT_CONTAINS = ("//*[@resource-id='com.whatsapp:id/conversation_text_row']"
                              "//*[contains(@text,'{message_contains}')]")
CONTACT_LIST_ITEM = "//*[@resource-id='com.whatsapp:id/contact_list']//*[@text='{to_chat}']"
MEDIA_DIRECTORY = '//android.widget.TextView[@text="{directory_name}"]'
COMPOSE_MEDIA_BY_INDEX = ('//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View'
                          '/android.view.View[4]/android.view.View[{index}]/android.view.View[2]/android.view.View')
# f-string template callables for templated xpaths (lowercase names)
def home_root_frame() -> str:
    return '//android.widget.FrameLayout[@content-desc="com.whatsapp:id/root_view"]'

# Conversations State
def conversation_row_for_subject(subject: str) -> str:
    return f"//*[contains(@resource-id,'com.whatsapp:id/conversations_row_contact_name') and @text='{subject}']"
#----
def contactpicker_text(contact: str) -> str:
    return f"//*[@resource-id='com.whatsapp:id/contactpicker_text_container']//*[@text='{contact}']"

def conversation_text_row_with_text(message_text: str) -> str:
    return f"//*[@resource-id='com.whatsapp:id/conversation_text_row']//*[@text='{message_text}']"

def message_status(message_text: str) -> str:
    return (f"//*[@resource-id='com.whatsapp:id/conversation_text_row']"
            f"//*[@text='{message_text}']"
            f"/.."
            f"//*[@resource-id='com.whatsapp:id/status']")

def broadcast_contact_row(receiver: str) -> str:
    return f"//*[@resource-id='com.whatsapp:id/chat_able_contacts_row_name' and @text='{receiver}']"

def contact_name_in_picker(contact_name: str) -> str:
    return f'//android.widget.TextView[@resource-id="com.whatsapp:id/name" and @text="{contact_name}"]'

def navigation_tab_by_text(tab_text: str) -> str:
    return (f'//android.widget.TextView['
            f'( @resource-id="com.whatsapp:id/navigation_bar_item_small_label_view"'
            f' or @resource-id="com.whatsapp:id/navigation_bar_item_large_label_view" )'
            f' and @text="{tab_text}"]')

def call_type_imageview(call_type: str) -> str:
    return f'(//android.widget.ImageView[@content-desc="{call_type}"])[1]'

def conversation_text_contains(message_contains: str) -> str:
    return (f"//*[@resource-id='com.whatsapp:id/conversation_text_row']"
            f"//*[contains(@text,'{message_contains}')]")

def contact_list_item(app_package: str, to_chat: str) -> str:
    return f"//*[@resource-id='com.whatsapp:id/contact_list']//*[@text='{to_chat}']"


def media_directory(directory_name: str) -> str:
    return f'//android.widget.TextView[@text="{directory_name}"]'

def compose_media_by_index(index: int) -> str:
    return (f'//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View'
            f'/android.view.View[4]/android.view.View[{index}]/android.view.View[2]/android.view.View')

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

def go_to_call(driver: PumaDriver, contact: str):
    """
    Navigates to a specific chat conversation in the application.

    This function constructs an XPath to locate and click on a conversation element
    based on the conversation name. It is designed to be used within a state transition
    to navigate to a specific chat state.

    :param driver: The PumaDriver instance used to interact with the application.
    :param conversation: The name of the conversation to navigate to.
    """
    logger.info(f'Clicking on contact {contact} with driver {driver}')
    driver.get_element(CALL_TAB_SEARCH_BUTTON).click()
    driver.send_keys(SEARCH_BAR, contact)


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
        # TODO: add xpaths
        super().__init__(xpaths=[],
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

        # TODO fix xpath
        content_desc = (driver.get_element(CHAT_STATE_CONTACT_HEADER).get_attribute('text'))
        return conversation.lower() in content_desc.lower()


class WhatsAppCallState(SimpleState, ContextualState):
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
                                 CALL_SCREEN_BACKGROUND],
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
    call_state = WhatsAppCallState(parent_state=calls_state)
    # send_location_state = SimpleState([], parent_state=chat_state)
    # chat_settings = WhatsAppChatSettingsState(parent_state=chat_state)

    conversations_state.to(chat_state, go_to_chat)
    conversations_state.to(settings_state, compose_clicks([HAMBURGER_MENU, OPEN_SETTINGS_BY_TITLE]))
    conversations_state.to(new_chat_state, compose_clicks([CONVERSATIONS_STATE_NEW_CHAT_OR_SEND_MESSAGE]))
    conversations_state.to(calls_state, compose_clicks([CALLS_TAB]))
    conversations_state.to(updates_state, compose_clicks([UPDATES_TAB]))
    calls_state.to(call_state, go_to_call)
    settings_state.to(profile_state, compose_clicks([PROFILE_INFO]))


    # @abstractmethod
    def __init__(self, device_udid: str, app_package: str):
        StateGraph.__init__(self, device_udid, app_package)
        self.WHATSAPP_PACKAGE = app_package

    def _handle_mention(self, message):
        """
        Make sure to convert an @name to an actual mention. Only one mention is allowed.
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

    def send_message_in_current_conversation(self, message_text, wait_until_sent=False):
        self.driver.click(MESSAGE_TEXT_BOX)
        self._handle_mention(message_text) \
            if "@" in message_text \
            else self.driver.send_keys(MESSAGE_TEXT_BOX, message_text)

        #Allow time for the link preview to load
        if 'http' in message_text:
            sleep(2)
        self.driver.click(SEND_BUTTON)
        # if wait_until_sent:
            # TODO convert to post action validation
            # _ = self._ensure_message_sent(message_text)

    @action(chat_state)
    def send_message(self, message_text, conversation: str, wait_until_sent=False):
        """
        Send a message in the current chat. If the message contains a mention, this is handled correctly.
        :param wait_until_sent: Exit this function only when the message has been sent.
        :param conversation: The chat conversation in which to send this message.
        :param message_text: The text that the message contains.
        """
        self.send_message_in_current_conversation(message_text, wait_until_sent)

    # @action(send_location_state)
    # def send_current_location(self, to_chat: str):
    #     pass

    @action(profile_state)
    def change_profile_picture(self, photo_dir_name, index=1):
        self.driver.get_element(f'//android.widget.Button[@resource-id="com.whatsapp:id/profile_info_edit_btn"]').click()
        self.driver.get_element("//*[@text='Gallery']").click()
        self.driver.get_element('//android.widget.ImageButton[@content-desc="Folders"]').click()
        self._find_media_in_folder(photo_dir_name, index)
        self.driver.get_element(f'//android.widget.Button[@resource-id="com.whatsapp:id/ok_btn"]').click()

    ########################################
    # region CC

        # {
        #   "platformName": "Android",
        #   "appium:options": {
        #     "automationName": "UiAutomator2",
        #     "platformVersion": "16.0",
        #     "deviceName": "Android",
        #     "udid": "",
        #     "noReset": true
        #   }
        # }

    def get_ui_component(self, widget_type: str, resource_id: str):
        return self.driver.get_element(f'//android.widget.{widget_type}[@resource-id="{self.WHATSAPP_PACKAGE}:id/{resource_id}"]')

    def get_ui_component_by_xpath(self, xpath: str):
        return self.driver.get_element(xpath)

    # TODO: you 'add' a status, not set it?
    @action(updates_state)
    def set_status(self, caption: str = None):
        """
        Sets a status by taking a picture and setting the given caption.
        :param caption: the caption to publish with the status.
        """
        self.get_ui_component_by_xpath(UPDATES_STATE_NEW_STATUS).click()
        # TODO-CC: why was a check for if_present present? It it weren't there, the following steps would also break?
        self.get_ui_component_by_xpath(CAMERA_BUTTON).click()

        self.get_ui_component('ImageView', 'shutter').click()
        if caption:
             self.get_ui_component('EditText', 'caption').send_keys(caption)
    @action(profile_state)
    def set_about(self, about_text: str):
        self.driver.get_element('//*[@resource-id="com.whatsapp:id/profile_info_status_card"]').click()
        self.driver.get_element('//*[@resource-id="com.whatsapp:id/status_tv_edit_icon"]').click()
        self.driver.send_keys('//*[@resource-id="com.whatsapp:id/edit_text"]', about_text)
        self.driver.get_element('//*[@resource-id="com.whatsapp:id/save_button"]').click()
        # This action ends in a screen that isn't a state, so move back one screen.
        self.driver.back()

        self.get_ui_component('ImageButton', 'send').click()

        # self.driver.get_element(UPDATES_STATE_NEW_STATUS).click()
        #
        # if self.driver.is_present(CAMERA_BUTTON):
        #     self.driver.get_element(CAMERA_BUTTON).click()
        #
        # # TODO-CC: first time I got the 'allow WhatsApp access to your camera'
        # #       + 'Allow WhatsApp to take pictures and record video'
        #
        # self.driver.get_element(f'//android.widget.ImageView[@resource-id="{self.WHATSAPP_PACKAGE}:id/shutter"]').click()
        # if caption:
        #     self.driver.get_element(f'//android.widget.EditText[@resource-id="{self.WHATSAPP_PACKAGE}:id/caption"]').send_keys(caption)
        #
        # self.driver.get_element(f'//android.widget.ImageButton[@resource-id="{self.WHATSAPP_PACKAGE}:id/send"]').click()
        #
        # # TODO-CC: now I get 'This status update will be sent to your contacts. Change privacy settings. (Cancel, Send)'

    @action(new_chat_state)
    @log_action
    #TODO CC
    def create_new_chat(self, contact, first_message):
        """
        Start a new 1-on-1 conversation with a contact and send a message.
        :param contact: Contact to start the conversation with.
        :param first_message: First message to send to the contact
        """
        self.driver.get_element(f'//*[@resource-id="{self.WHATSAPP_PACKAGE}:id/contactpicker_text_container"]//*[@text="{contact}"]').click()
        self.send_message_in_current_conversation(first_message)

    def open_more_options(self):
        """
        Open more options (hamburger menu) in the home screen.
        """
        self.driver.get_element('//android.widget.ImageView[@content-desc="More options"]').click()

    @action(conversations_state)
    def send_broadcast(self, receivers: List[str], broadcast_text: str):
        """
        Broadcast a message.
        :param receivers: list of receiver names, minimum of 2!.
        :param broadcast_text: Text to send.
        """
        if len(receivers) < 2:
            raise Exception(f"Error: minimum of 2 receivers required for a broadcast, got: {receivers}")

        self.open_more_options()
        # self.driver.get_element(f'//*[@resource-id=:"{self.WHATSAPP_PACKAGE}:id/title" and @text="New broadcast"]').click()
        self.driver.get_element(NEW_BROADCAST_TITLE).click()
        for receiver in receivers:
            self.driver.get_element(f'//*[@resource-id="{self.WHATSAPP_PACKAGE}:id/chat_able_contacts_row_name" and @text="{receiver}"]').click()

        self.driver.get_element(f'//android.widget.ImageButton[@resource-id="{self.WHATSAPP_PACKAGE}:id/next_btn"]').click()
        self.driver.get_element(f'//android.widget.EditText[@resource-id="{self.WHATSAPP_PACKAGE}:id/entry"]').send_keys(broadcast_text)
        self.driver.get_element(f'//android.widget.ImageButton[@resource-id="{self.WHATSAPP_PACKAGE}:id/send"]').click()

    @action(chat_state)
    def delete_message_for_everyone(self, conversation: str, message_text: str):
        """
        Remove a message with the message text. Should be recently sent, so it is still in view and still possible to
        delete for everyone.
        :param conversation: The chat conversation in which to send this message, if not currently in the desired chat.
        :param message_text: literal message text of the message to remove. The first match will be removed in case
        there are multiple with the same text.
        """
        message_element = self.driver.find_element(f"//*[@resource-id='{self.WHATSAPP_PACKAGE}:id/conversation_text_row']//*[@text='{message_text}']")
        self._long_press_element(message_element)
        self.driver.get_element('//*[@content-desc="Delete"]').click()
        self.driver.get_element(f'//*[@resource-id="{self.WHATSAPP_PACKAGE}:id/buttonPanel"]//*[@text="Delete for everyone"]').click()

    @action(conversations_state)
    def create_group(self, subject: str, participants: Union[str, List[str]]):
        """
        Create a new group.
        :param subject: The subject of the group.
        :param participants: The contact(s) you want to add to the group (string or list).
        Note that only 1 participant is implemented for now.
        """
        self.open_more_options()
        self.driver.get_element('//*[@text="New group"]').click()

        participants = [participants] if not isinstance(participants, list) else participants
        for participant in participants:
            # TODO-CC: classname
            contacts = self.driver.get_element(by=AppiumBy.CLASS_NAME, value='android.widget.TextView')
            participant_to_add = [contact for contact in contacts if contact.text.lower() == participant.lower()][0]
            participant_to_add.click()

        self.driver.get_element(f'//*[@resource-id="{self.WHATSAPP_PACKAGE}:id/next_btn"]').click()
        self.driver.get_element(f'//*[@resource-id="{self.WHATSAPP_PACKAGE}:id/group_name"]').send_keys(subject)

        # TODO-CC: classname
        image_buttons = self.driver.find_elements(by=AppiumBy.CLASS_NAME, value='android.widget.ImageButton')
        # TODO-CC: is this necessary? or can we just get the Create button with xpath
        next_button = [button for button in image_buttons if button.tag_name == "Create"][0]
        next_button.click()

        # TODO-CC: print should be log?
        print("Waiting 5 sec to create group")
        sleep(5)

        # TODO-CC: use xpaths to check? Or just try to find the single_msg_tv
        # if self.currently_at_homescreen():
        print("On homescreen now")
        # Check if creating the group succeeded
        top_conv =self.driver.get_element(f'//*[@resource-id="{self.WHATSAPP_PACKAGE}:id/single_msg_tv"]')
        max_attempts = 20
        while "Creating" in top_conv.text or "Couldn't create" in top_conv.text:
            if "Couldn't create" in top_conv.text:
                print("Couldn't create. Tapping to retry")
                top_conv.click()
            else:
                print("Waiting for group to be created.")
            sleep(5)
            max_attempts -= 1
            if max_attempts == 0:
                # TODO-CC: is this a timeout?
                raise TimeoutError(f"Could not create group after 20 attempts. Try restarting your emulator and try again.")
        # self.return_to_homescreen()

    @action(conversations_state)
    def archive_conversation(self, subject):
        """
        Archives a given conversation.
        :param subject: The conversation to archive.
        """
        # TODO-CC: get elements necessary?
        conversation = self.driver.get_elements(f'//*[contains(@resource-id,"{self.WHATSAPP_PACKAGE}:id/conversations_row_contact_name") and @text="{subject}"]')[0]
        self._long_press_element(conversation)
        self.driver.get_element(f'//*[@resource-id="{self.WHATSAPP_PACKAGE}:id/menuitem_conversations_archive"]').click()
        # Wait until the archive popup disappeared
        archived_popup_present = True
        # TODO-CC: limit amount of tries
        while archived_popup_present:
            print("waiting for archived popup to disappear")
            sleep(5)
            archived_popup_present = 'archived' in self.driver.get_elements(f'//*[contains(@text,"archived") or @resource-id="{self.WHATSAPP_PACKAGE}:id/fab"]')[0].text
        print("Archive pop-up gone!")

    # endregion
    ########################################

    # def _ensure_message_sent(self, message_text):
    #     message_status_el = self.driver.get_element(message_status(message_text))
    #     while message_status_el.tag_name == "Pending":
    #         #TODO gtl logger?
    #         logger.info("Message pending, waiting for the message to be sent.")
    #         sleep(10)
    #     logger.info("Message sent.")
    #     return message_status_el
    @log_action
    #TODO CC
    def delete_message_for_everyone(self, message_text: str, chat: str = None):
        """
        Remove a message with the message text. Should be recently sent, so it is still in view and still possible to
        delete for everyone.
        :param message_text: literal message text of the message to remove. The first match will be removed in case
        there are multiple with the same text.
        :param chat: The chat conversation in which to send this message, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        message_element = self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='{self.app_package}:id/conversation_text_row']//*[@text='{message_text}']")
        self._long_press_element(message_element)
        self.driver.find_element(by=AppiumBy.XPATH, value='//*[@content-desc="Delete"]').click()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value=f"//*[@resource-id='{self.app_package}:id/buttonPanel']//*[@text='Delete for everyone']").click()

    @log_action
    #TODO
    def reply_to_message(self, message_to_reply_to: str, reply_text: str, chat: str = None):
        """
        Reply to a message. Assumes you are in the chat in which the message was sent.
        :param message_to_reply_to: message you want to reply to.
        :param reply_text: message text you are sending in your reply.
        :param chat: The chat conversation in which to send this message, if not currently in the desired chat.
        """
        # Wait and see if the message to be forwarded is no longer pending. If so, we must wait because a pending
        # message cannot be forwarded
        self._if_chat_go_to_chat(chat)
        message_element = self.scroll_to_find_element(text_contains=message_to_reply_to)
        self._long_press_element(message_element)
        self.driver.find_element(by=AppiumBy.XPATH, value='//*[@content-desc="Reply"]').click()
        text_box = self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/entry")
        text_box.send_keys(reply_text)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/send").click()

    @log_action
    #TODO: Broadcast window is not a state CC
    def send_broadcast(self, receivers: [str], broadcast_text: str):
        """
        Broadcast a message.
        :param receivers: list of receiver names, minimum of 2!.
        :param broadcast_text: Text to send.
        """
        self.return_to_homescreen()
        if len(receivers) < 2:
            print("Error: minimum of 2 receivers required for a broadcast!")
            return
        self.open_more_options()
        new_broadcast = self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='{self.app_package}:id/title' and @text='New broadcast']")
        new_broadcast.click()
        for receiver in receivers:
            self.driver.find_element(by=AppiumBy.XPATH, value=
            f"//*[@resource-id='{self.app_package}:id/chat_able_contacts_row_name' and @text='{receiver}']").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/next_btn").click()
        text_box = self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/entry")
        text_box.send_keys(broadcast_text)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/send").click()

    @log_action
    #TODO
    def send_sticker(self, chat: str = None):
        """
        Send the only sticker in the sticker menu. Assumes 1 sticker is present in WhatsApp.
        Note that the selection of the sticker is based on coordinates of the Pixel 5. For other phones with different
        screen sizes, it should be validated that this is correct.
        :param chat: The chat conversation in which to send this sticker, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/emoji_picker_btn").click()
        sleep(1)
        # Press sticker tab
        # TODO: make coordinates configurable or calculate what they should be
        # self.press_coordinates(663, 2136) # Pixel 5
        self._click_coordinates(663, 2032)  # Samsung G955F
        sleep(1)
        # Press sticker
        # self.press_coordinates(150, 1600) # Pixel 5
        self._click_coordinates(128, 1502)  # Samsung G955F

    def _click_coordinates(self, x, y):
        self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})

    @log_action
    #TODO
    def send_voice_recording(self, duration: int = 2000, chat: str = None):
        """
        Sends a voice message in the current conversation.
        Assumes we are in the conversation in which we want to send the voice message.
        :param duration: the duration in of the voice message to send in millisec.
        :param chat: The chat conversation in which to send this voice recording, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        voice_button = self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/voice_note_btn")
        self._long_press_element(voice_button, duration=duration)

    @log_action
    #TODO
    def send_current_location(self, chat: str = None):
        """
        Send the current location in the current chat.
        Assumes we're in a chat and that the given contact exists.
        :param chat: The chat conversation in which to send the location, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/input_attach_button").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/pickfiletype_location_holder").click()
        sleep(5)  # it takes some time to fix the location
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/send_current_location_btn").click()

    @log_action
    #TODO: location is a state, end state is chat state (contextual?)
    def send_live_location(self, caption=None, chat: str = None):
        """
        Send a live location in the current chat.
        Assumes we're in a chat and that the given contact exists.
        :param caption: Optional caption sent along with the live location
        :param chat: The chat conversation in which to start the live location sharing, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/input_attach_button").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/pickfiletype_location_holder").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/live_location_btn").click()
        dialog = f'//android.widget.LinearLayout[@resource-id="{self.app_package}:id/location_new_user_dialog_container"]'
        if self.is_present(dialog):
            self.driver.find_element(by=AppiumBy.XPATH, value="//android.widget.Button[@text='Continue']").click()
        if caption is not None:
            self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/comment").send_keys(caption)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/send").click()

    @log_action
    #TODO
    def stop_live_location(self, need_to_scroll=False, chat: str = None):
        """
        Stops the current live location sharing.
        :param need_to_scroll: Set to True if we need to scroll in the conversation to find the button "Stop Sharing"
        :param chat: The chat conversation in which to stop the live location sharing, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        if need_to_scroll:
            self.scroll_to_find_element(text_contains="Stop sharing").click()
        else:
            self.driver.find_element(by=AppiumBy.XPATH, value="//*[@text='Stop sharing']").click()

        popup_button_xpath = '//android.widget.Button[@content-desc="Stop"]'
        if self.is_present(popup_button_xpath):
            self.driver.find_element(by=AppiumBy.XPATH, value=popup_button_xpath).click()

    @log_action
    #TODO
    def send_contact(self, contact_name: str, chat: str = None):
        """
        Send a contact in the current chat.
        Assumes we're in a chat and that the given contact exists.
        :param contact_name: the name of the contact to send.
        :param chat: The chat conversation in which to send the contact, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/input_attach_button").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/pickfiletype_contact_holder").click()
        self.swipe_to_find_element(
            f'//android.widget.TextView[@resource-id="{self.app_package}:id/name" and @text="{contact_name}"]').click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/next_btn").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/send_btn").click()

    @log_action
    #TODO
    def activate_disappearing_messages(self, chat=None):
        """
        Activates disappearing messages (auto delete) in the current or a given chat.
        Messages will now auto-delete after 24h.
        Assumes that we are in the intended conversation if no group name is given, if a group name is given it is
        assumed that this group exists and that we are at the whatsapp home screen.
        :param chat: Optional: group for which disappearing messages should be activated.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/conversation_contact").click()
        self.scroll_to_find_element(text_contains='Disappearing messages').click()
        self.driver.find_elements(by=AppiumBy.XPATH, value="//*[@class='android.widget.RadioButton']")[0].click()
        if chat is None:
            self.driver.back()
            self.driver.back()
        else:
            self.return_to_homescreen()

    @log_action
    #TODO
    def deactivate_disappearing_messages(self, chat=None):
        """
        Disables disappearing messages (auto delete) in the current or a given chat.
        Assumes that we are in the intended conversation if no group name is given, if a group name is given it is
        assumed that this group exists and that we are at the whatsapp home screen.
        :param chat: Optional: group for which disappearing messages should be activated.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/conversation_contact").click()
        self.scroll_to_find_element(text_contains='Disappearing messages').click()
        self.driver.find_elements(by=AppiumBy.XPATH, value="//*[@class='android.widget.RadioButton']")[-1].click()
        if chat is None:
            self.driver.back()
            self.driver.back()
        else:
            self.return_to_homescreen()

    @log_action
    #TODO: call tab is a state
    def call_contact(self, contact, video_call=False):
        """
        Make a WhatsApp call. The call is made to a given contact name
        :param contact: name of the contact to call.
        :param video_call: False (default) for voice call, True for video call.
        """
        self.return_to_homescreen()
        call_type = "Video call" if video_call else "Voice call"
        self.navigate_to_call_tab()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageButton[@content-desc="Search"]').click()
        search_bar = self.driver.find_element(by=AppiumBy.XPATH,
                                              value=f'//android.widget.EditText[@resource-id="{self.app_package}:id/search_view_edit_text"]')
        search_bar.send_keys(contact)
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value=f'(//android.widget.ImageView[@content-desc="{call_type}"])[1]').click()  # Take the top one without checking the name, since we already searched for the contact

    @log_action
    #TODO
    def end_call(self):
        """
        Ends the current call. Assumes the call screen is open.
        """
        end_call_button = f'//*[@content-desc="Leave call" or @resource-id="{self.app_package}:id/end_call_button" or @resource-id="{self.app_package}:id/footer_end_call_btn"]'
        if not self.is_present(end_call_button, implicit_wait=1):
            # tap screen to make call button visible
            background = f'//android.widget.RelativeLayout[@resource-id="{self.app_package}:id/call_screen"]'
            self.driver.find_element(by=AppiumBy.XPATH, value=background).click()
        self.driver.find_element(by=AppiumBy.XPATH, value=end_call_button).click()

    @log_action
    #TODO, not an action
    def answer_call(self):
        """
        Answer when receiving a call via Whatsapp.
        """
        self.open_notifications()
        sleep(2)
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value="//android.widget.Button[@content-desc='Answer' or @content-desc='Video']").click()

    @log_action
    #TODO, not an action
    def decline_call(self):
        """
        Declines an incoming Whatsapp call.
        """
        self.open_notifications()
        sleep(2)
        self.driver.find_element(by=AppiumBy.XPATH, value="//android.widget.Button[@content-desc='Decline']").click()

    @log_action
    #TODO
    def set_group_description(self, group_name, description):
        """
        Set the group description.
        :param group_name: Name of the group to set the description for.
        :param description: Description of the group.
        """
        self.return_to_homescreen()
        self.select_chat(group_name)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/conversation_contact").click()
        self.scroll_to_find_element(text_equals="Add group description").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/edit_text").send_keys(description)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/ok_btn").click()
        self.return_to_homescreen()

    @log_action
    #TODO
    def delete_group(self, group_name):
        """
        Leaves and deletes a given group.
        Assumes the group exists, isn't left yet, and that we start from the whatsapp home screen.
        :param group_name: the group to be deleted.
        """
        self.leave_group(group_name)
        self.select_chat(group_name)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/conversation_contact").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[contains(@text,'Delete group')]").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[contains(@text,'Delete group')]").click()
        self.return_to_homescreen()

    def _long_press_element(self, element, duration=1000):
        """
        Press some element for some duration.
        :param element: Element to long press.
        :param duration: Duration of the press in millisec.
        :return:
        """
        location = element.location
        size = element.size

        # Calculate the center of the element
        x = location['x'] + size['width'] // 2
        y = location['y'] + size['height'] // 2
        self.driver.execute_script('mobile: longClickGesture', {'x': x, 'y': y, 'duration': duration})

    @log_action
    @abstractmethod
    #TODO: implement this action
    def leave_group(self, group_name):
        """
        This method will leave the given group. It will not delete that group.
        This method assumes we start at the whatsapp home screen.
        :param group_name: Name of the group we want to leave.
        """
        pass

    @log_action
    #TODO: maybe make a state for chat settings? But the state is different for one-on-one and group conversations.
    def remove_participant_from_group(self, group_name, participant):
        """
        Removes a given participant from a given group chat.
        It is assumed the group chat exists and has the given participant, and that we start at the whatsapp home screen.
        :param group_name: The group
        :param participant: The participant to remove
        """
        self.select_chat(group_name)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/conversation_contact").click()
        self.scroll_to_find_element(text_equals=participant).click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[starts-with(@text, 'Remove')]").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[@class='android.widget.Button' and @text='OK']").click()
        sleep(5)
        self.return_to_homescreen()

    @log_action
    #TODO
    def forward_message(self, from_chat, message_contains, to_chat):
        """
        Forwards a message from one conversation to another.
        It is assumed the message and both conversations exists, and that we start at the whatsapp home screen.
        :param from_chat: The chat from which the message has to be forwarded
        :param message_contains: the text from the message that has to be forwarded. Uses String.contains(), so only part
        of the message is needed, but be sure the given text is enough to match your intended message uniquely.
        :param to_chat: The chat to which the message has to be forwarded.
        """
        self.select_chat(from_chat)
        chat_message = self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='{self.app_package}:id/conversation_text_row']//*[contains(@text,'{message_contains}')]")
        self._long_press_element(chat_message)
        self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='{self.app_package}:id/action_mode_bar']//*[@content-desc='Forward']").click()
        self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='{self.app_package}:id/contact_list']//*[@text='{to_chat}']").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/send").click()


    @log_action
    #TODO
    def open_view_once_photo(self, chat=None):
        """
        Open view once photo in the current or specified chat. Should be done right after the photo is sent, to ensure the correct photo is opened, this will be the lowest one.
        :param chat: Optional: The chat in which the photo has to be opened. If not supplied, the photo will be opened in the current chat.
        """
        self._if_chat_go_to_chat(chat)
        most_recent_view_once = \
            self.driver.find_elements(by=AppiumBy.XPATH, value='//*[contains(@resource-id, "view_once_media")]')[-1]
        most_recent_view_once.click()
        self.driver.back()

    def _find_media_in_folder(self, directory_name, index):
        try:
            self.driver.swipe_to_click_element(xpath=f'//android.widget.TextView[@text="{directory_name}"]')
        except NoSuchElementException:
            raise NoSuchElementException(f'The directory {directory_name} could not be found.')
        self.driver.get_element(f'//android.widget.TextView[@text="{directory_name}"]').click()
        sleep(0.5)
        try:
            self.driver.get_element(f'//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[4]/android.view.View[{index}]/android.view.View[2]/android.view.View').click()
        except NoSuchElementException:
            raise NoSuchElementException(
                f'The media at index {index} could not be found. The index is likely too large or negative.')
