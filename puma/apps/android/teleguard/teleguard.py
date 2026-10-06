from typing import List

from appium.webdriver import WebElement
from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.teleguard.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, supported_version, PumaClickException
from puma.state_graph.state import ContextualState, SimpleState, compose_clicks
from puma.state_graph.state_graph import StateGraph

APPLICATION_PACKAGE = 'ch.swisscows.messenger.teleguardapp'


def go_to_chat(driver: PumaDriver, conversation: str):
    """
    Navigates to a specific chat conversation in the application.

    This function constructs an XPath to locate and click on a conversation element
    based on the conversation name. It is designed to be used within a state transition
    to navigate to a specific chat state.

    :param driver: The PumaDriver instance used to interact with the application.
    :param conversation: The name of the conversation to navigate to.
    """
    xpath = f'//android.widget.ImageView[contains(lower-case(@content-desc), "{conversation.lower()}")] | ' \
            f'//android.view.View[contains(lower-case(@content-desc), "{conversation.lower()}")]'
    driver.driver.find_elements(by=AppiumBy.XPATH, value=xpath)[-1].click()


class TeleGuardChatState(SimpleState, ContextualState):
    """
    A state representing a chat screen in the application.

    This class extends both SimpleState and ContextualState to represent a chat screen
    and validate its context based on the conversation name.
    """

    def __init__(self, parent_state):
        """
        Initializes the ChatState with a parent state.

        :param parent_state: The parent state of this chat state.
        """
        super().__init__(xpaths=[CHAT_STATE_CONVERSATION_NAME, CHAT_STATE_MICROPHONE_BUTTON, CHAT_STATE_TEXT_FIELD],
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

        content_desc = (driver.get_element(CHAT_STATE_CONVERSATION_NAME).get_attribute('content-desc'))
        return conversation.lower() in content_desc.lower()


@supported_version('4.0.9')
class TeleGuard(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the TeleGuard application.

    This class uses a state machine approach to manage transitions between different states
    of the TeleGuard user interface. It provides methods to navigate between states, validate states,
    and handle unexpected states or errors.
    """

    conversations_state = SimpleState( [CONVERSATION_STATE_TELEGUARD_HEADER, CONVERSATION_STATE_HAMBURGER_MENU, CONVERSATION_STATE_TELEGUARD_STATUS], initial_state=True)
    chat_state = TeleGuardChatState(parent_state=conversations_state)
    chat_options_state = SimpleState(
        [CHAT_OPTIONS_STATE_TURN_OFF_NOTIFICATIONS, CHAT_OPTIONS_STATE_CLEAR_HISTORY, CHAT_OPTIONS_STATE_BLOCK_USER],
        parent_state=chat_state)
    send_media_state = SimpleState(
        [SEND_MEDIA_STATE_TITLE, SEND_MEDIA_STATE_UPLOAD_PHOTO_BUTTON, SEND_MEDIA_STATE_UPLOAD_CANCEL_BUTTON],
        parent_state=chat_state)
    settings_state = SimpleState([SETTINGS_STATE_CHANGE_TELEGUARD_ID], parent_state=conversations_state)
    about_screen_state = SimpleState([ABOUT_STATE_ABOUT, ABOUT_STATE_TERMS_OF_USE], parent_state=conversations_state)

    conversations_state.to(chat_state, go_to_chat)
    conversations_state.to(settings_state, compose_clicks([CONVERSATION_STATE_HAMBURGER_MENU, CONVERSATION_STATE_SETTINGS_BUTTON], name='go_to_settings'))
    conversations_state.to(about_screen_state, compose_clicks([CONVERSATION_STATE_HAMBURGER_MENU, CONVERSATION_STATE_ABOUT_BUTTON], name='go_to_about'))

    chat_state.to(chat_options_state, compose_clicks([CHAT_STATE_THREE_DOTS], name='go_to_chat_options'))
    chat_state.to(send_media_state, compose_clicks([CHAT_STATE_SEND_MEDIA_BUTTON], name='go_to_send_media'))

    def __init__(self, device_udid):
        """
        Initializes the TestFsm with a device UDID.

        This class provides an API for interacting with the TeleGuard application.
        It can be used with an emulator or a real device attached to the computer.

        :param device_udid: The unique device identifier for the Android device.
        """
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)

    @action(conversations_state)
    def add_contact(self, teleguard_id: str):
        """
        Adds a contact by TeleGuard ID.

        :param teleguard_id: The TeleGuard ID of the contact to add.
        """
        self.driver.click(CONVERSATION_STATE_HAMBURGER_MENU)
        self.driver.click(CONVERSATION_STATE_ADD_CONTACT)
        self.driver.send_keys(CONVERSATION_STATE_EDIT_TEXT, teleguard_id)
        self.driver.click(CONVERSATION_STATE_INVITE)

    @action(conversations_state)
    def invite_received(self, scroll: bool = False, max_swipes: int = 10) -> bool:
        """
        Checks whether an invite has been received. By default this method does not scroll to look for an invite.
        """
        if scroll:
            try:
                self.driver.swipe_to_find_element(CONVERSATION_STATE_YOU_HAVE_BEEN_INVITED, max_swipes=max_swipes)
                return True
            except PumaClickException:
                return False
        return self.driver.is_present(CONVERSATION_STATE_YOU_HAVE_BEEN_INVITED)

    @action(conversations_state)
    def accept_invite(self) -> str:
        """
        Accepts an invite from another user and returns the name of the accepted invite.

        If there are multiple invites, only the topmost invite in the UI will be accepted.

        If no invite was sent, an exception is raised.
        """
        self.driver.swipe_to_click_element(CONVERSATION_STATE_YOU_HAVE_BEEN_INVITED)
        name = self.driver.get_element(CONVERSATION_STATE_INVITATION_NAME).get_attribute('content-desc')
        self.driver.click(CONVERSATION_STATE_INVITATION_ACCEPT)
        return name

    def _extract_name(self, conversation_row: WebElement) -> str:
        """
        Given a conversation row, extracts the name of the conversation.
        For users with an avatar, the first line of the content description is the conversation name.
        For users without an avatar, there is an extra first line with just the first letter of the name.
        We try to detect this pattern and return the first or second line based on this.

        :param conversation_row: The conversation row to extract a name from.
        """
        content_description = conversation_row.get_attribute('content-desc')
        lines = content_description.split('\n')[:2]
        if len(lines[0])>1:
            return lines[0]
        elif lines[1][0] == lines[0]:
            return lines[1]
        else:
            return lines[0]

    @action(conversations_state)
    def conversations_with_unread_messages(self) -> List[str]:
        """
        Returns a list of names of conversations that have unread messages.
        """
        try:
            elements = self.driver.get_elements(CONVERSATION_STATE_UNREAD_MESSAGES)
            names = [self._extract_name(e) for e in elements]
            return names
        except PumaClickException:
            return []

    @action(chat_state)
    def send_message(self, message: str, conversation: str = None):
        """
        Sends a message in the current chat conversation.

        :param message: The message to send.
        :param conversation: The name of the conversation to send the message in.
        """
        self.driver.click(CHAT_STATE_TEXT_FIELD)
        self.driver.send_keys(CHAT_STATE_TEXT_FIELD, message)
        self.driver.click(CHAT_STATE_SEND_BUTTON)

    @action(chat_options_state, end_state=chat_state)
    def clear_history(self, conversation: str = None):
        """
        Clears the history of the current or selected conversation.

        :param conversation: The name of the conversation to clear the history of.
        """
        self.driver.click(CHAT_OPTIONS_STATE_CLEAR_HISTORY)
        self.driver.click(CHAT_OPTIONS_STATE_CLEAR_HISTORY_CONFIRM_BUTTON)

    @action(send_media_state, end_state=chat_state)
    def send_picture(self, picture_id: int = None, caption: str = None, conversation: str = None):
        """
        Sends a picture in the current or selected conversation.

        :param picture_id: The index in the media picker of the picture to send.
        :param caption: The caption to add to the picture.
        :param conversation: The name of the conversation to send the picture in.
        """
        if picture_id:
            self.driver.click(SEND_MEDIA_STATE_PICTURE_INDEX.format(index=picture_id + 1))
            self.driver.click(SEND_MEDIA_STATE_SELECT_BUTTON)
        else:
            # take picture
            self.driver.click(SEND_MEDIA_STATE_PICTURE_INDEX.format(index=1))
            self.driver.click(SEND_MEDIA_STATE_CAMERA_SHUTTER_BUTTON)
            self.driver.click(SEND_MEDIA_STATE_CAMERA_CONFIRM_BUTTON)
            self.driver.click(SEND_MEDIA_STATE_CAMERA_CONFIRM_EDIT_BUTTON)
        if caption:
            self.driver.send_keys(CHAT_STATE_TEXT_FIELD, caption)
        self.driver.click(CHAT_STATE_SEND_BUTTON)
