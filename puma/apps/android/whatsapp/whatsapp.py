import re
from time import sleep
from typing import Union, List

from puma.apps.android.whatsapp import logger
from puma.apps.android.whatsapp.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, supported_version
from puma.state_graph.state import SimpleState, ContextualState, State, compose_clicks
from puma.state_graph.state_graph import StateGraph
from puma.utils.xpath_utils import build_content_desc_xpath_widget


def go_to_chat(driver: PumaDriver, conversation: str):
    """
    Navigates to a specific chat conversation in the application.

    This function constructs an XPath to locate and click on a conversation element
    based on the conversation name. It is designed to be used within a state transition
    to navigate to a specific chat state.

    :param driver: The PumaDriver instance used to interact with the application.
    :param conversation: The name of the conversation to navigate to.
    """
    driver.gtl_logger.info(f'Clicking on conversation {conversation} with driver {driver}')
    driver.get_elements(CONVERSATIONS_ROW_BY_SUBJECT.format(conversation=conversation))[-1].click()


def go_to_voice_call(driver: PumaDriver, contact: str):
    """
    Starts a voice call with a specific user.

    :param driver: The PumaDriver instance used to interact with the application.
    :param contact: The name of user to call.
    """
    driver.click(CALL_TAB_SEARCH_BUTTON)
    driver.send_keys(SEARCH_BAR, contact)
    driver.click(VOICE_CALL_START_BUTTON)


def go_to_video_call(driver: PumaDriver, contact: str):
    """
    Starts a video call with a specific user.

    :param driver: The PumaDriver instance used to interact with the application.
    :param contact: The name of user to call.
    """
    driver.click(CALL_TAB_SEARCH_BUTTON)
    driver.send_keys(SEARCH_BAR, contact)
    driver.click(VIDEO_CALL_START_BUTTON)


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
        super().__init__(xpaths=[CHAT_CONTACT_HEADER,
                                 CHAT_ROOT_LAYOUT],
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

        content_desc = (driver.get_element(CHAT_CONTACT_HEADER).get_attribute('text'))
        return conversation.lower() in content_desc.lower()

    @staticmethod
    def open_chat_settings(driver: PumaDriver, conversation: str):
        driver.click(CHAT_CONTACT_HEADER_WITH_NAME.format(conversation=conversation))


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
        super().__init__(xpaths=[CHAT_SETTINGS_CONTACT_NAME,
                                 CHAT_SETTINGS_NOTIFICATIONS,
                                 CHAT_SETTINGS_MEDIA_VISIBILITY],
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

        content_desc = (driver.get_element(CHAT_SETTINGS_CONTACT_NAME).get_attribute('text'))
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
        super().__init__(xpaths=[CALL_END_CALL_BUTTON,
                                 CALL_SCREEN_BACKGROUND,
                                 VOICE_CALL_CAMERA_BUTTON],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates the context of the call state.

        This method checks if the current call screen matches the expected contact name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the call recipient to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not conversation:
            return True

        content_desc = (driver.get_element(CALL_CONTACT_HEADER).get_attribute('text'))
        return conversation.lower() in content_desc.lower()

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
        super().__init__(xpaths=[CALL_END_CALL_BUTTON,
                                 CALL_SCREEN_BACKGROUND,
                                 VIDEO_CALL_CAMERA_BUTTON,
                                 VIDEO_CALL_SWITCH_CAMERA],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates the context of the call state.

        This method checks if the current call screen matches the expected contact name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the call recipient to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not conversation:
            return True

        content_desc = (driver.get_element(CALL_CONTACT_HEADER).get_attribute('text'))
        return conversation.lower() in content_desc.lower()


@supported_version("2.25.31.76")
class WhatsApp(StateGraph):
    """
    TODO
    """

    conversations_state = SimpleState([CONVERSATIONS_WHATSAPP_LOGO,
                                       CONVERSATIONS_HOME_ROOT_FRAME,
                                       CONVERSATIONS_NEW_CHAT_OR_SEND_MESSAGE,
                                       CONVERSATIONS_CHAT_TAB],
                                      initial_state=True)
    settings_state = SimpleState([SETTINGS_QR,
                                  SETTINGS_ACCOUNT_SWITCH],
                                 parent_state=conversations_state)
    profile_state = SimpleState([PROFILE_PROFILE_PICTURE,
                                 PROFILE_NAME,
                                 PROFILE_PHONE],
                                parent_state=settings_state)
    chat_state = WhatsAppChatState(parent_state=conversations_state)
    new_chat_state = SimpleState([NEW_CHAT_HEADER,
                                  NEW_CHAT_NEW_GROUP,
                                  NEW_CHAT_NEW_CONTACT,
                                  NEW_CHAT_NEW_COMMUNITY],
                                 parent_state=conversations_state)
    calls_state = SimpleState([CALLS_HEADER,
                               CALLS_START_CALL],
                              parent_state=conversations_state)
    updates_state = SimpleState([UPDATES_HEADER,
                                 UPDATES_STATUS_HEADER,
                                 UPDATES_NEW_STATUS],
                                parent_state=conversations_state)
    voice_call_state = WhatsAppVoiceCallState(parent_state=calls_state)
    video_call_state = WhatsAppVideoCallState(parent_state=calls_state)
    send_location_state = SimpleState([SEND_LOCATION_HEADER,
                                       SEND_LOCATION_LIVE_LOCATION,
                                       SEND_LOCATION_CURRENT_LOCATION],
                                      parent_state=chat_state)
    chat_settings_state = WhatsAppChatSettingsState(parent_state=chat_state)

    conversations_state.to(chat_state, go_to_chat)
    conversations_state.to(settings_state, compose_clicks([HAMBURGER_MENU, OPEN_SETTINGS_BY_TITLE]))
    conversations_state.to(new_chat_state, compose_clicks([CONVERSATIONS_NEW_CHAT_OR_SEND_MESSAGE]))
    conversations_state.to(calls_state, compose_clicks([CALLS_TAB]))
    conversations_state.to(updates_state, compose_clicks([UPDATES_TAB]))
    calls_state.to(voice_call_state, go_to_voice_call)
    calls_state.to(video_call_state, go_to_video_call)
    settings_state.to(profile_state, compose_clicks([PROFILE_INFO]))
    chat_state.to(send_location_state, compose_clicks([CHAT_ATTACH_BUTTON, CHAT_ATTACH_LOCATION_BUTTON]))
    chat_state.to(chat_settings_state, WhatsAppChatState.open_chat_settings)


    def __init__(self, device_udid: str, app_package: str):
        StateGraph.__init__(self, device_udid, app_package)

    def _handle_mention(self, message:str):
        """
        Make sure to convert a @name to an actual mention. Only one mention is allowed.
        :param message: The message containing the mention.
        """
        self.driver.send_keys(TEXT_ENTRY, message)
        sleep(1)
        # Find the mentioned name in the message. Note that it will search until the last word character. This means for
        # @jan-willem or @jan willem, only @jan will be found.
        mention_match = re.search(r"@\w+", message)
        mentioned_name = mention_match.group(0).strip("@")

        self.driver.press_left_arrow()
        while not (mention_suggestions := self.driver.get_elements(CHAT_MENTION_SUGGESTIONS)):
             self.driver.press_left_arrow()

        mentioned_person_el = \
            [person for person in
             mention_suggestions
             if mentioned_name.lower() in person.tag_name.lower()][0]
        mentioned_person_el.click()

        # Remove a space resulting from selecting the mention person
        self.driver.press_backspace()

    def _ensure_message_sent(self, message_text: str):
        message_status_el = self.driver.get_element(
            f"//*[@resource-id='com.whatsapp:id/conversation_text_row']"
            f"//*[@text='{message_text}']"  # Text field element containing message text
            f"/.."  # Parent of the message (i.e. conversation text row)
            f"//*[@resource-id='com.whatsapp:id/status']")  # Status element
        while message_status_el.tag_name == "Pending":
            logger.info("Message pending, waiting for the message to be sent.")
            sleep(10)
        return message_status_el

    @action(chat_state)
    def send_message(self, message_text: str, conversation: str = None, wait_until_sent: bool = False):
        """
        Send a message in the current chat. If the message contains a mention, this is handled correctly.
        :param message_text: The text that the message contains.
        :param conversation: The chat conversation in which to send this message. Optional: not needed when already in a conversation
        :param wait_until_sent: Exit this function only when the message has been sent.
        """
        self.driver.click(TEXT_ENTRY)
        self._handle_mention(message_text) \
            if "@" in message_text \
            else self.driver.send_keys(TEXT_ENTRY, message_text)

        # Allow time for the link preview to load
        if 'http' in message_text:
            sleep(2)
        self.driver.click(SEND_CONTENT)
        # TODO convert to post action validation
        if wait_until_sent:
            _ = self._ensure_message_sent(message_text)

    @action(profile_state)
    def change_profile_picture(self, photo_dir_name: str, index: int = 1):
        self.driver.click(PROFILE_INFO_EDIT_BUTTON)
        self.driver.click(PROFILE_GALLERY)
        self.driver.click(PROFILE_FOLDERS)
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
        self.driver.click(UPDATES_NEW_STATUS)
        self.driver.click(UPDATES_CAMERA_BUTTON)
        self.driver.click(UPDATES_SHUTTER)
        if caption:
             self.driver.send_keys(UPDATES_EDIT_CAPTION, caption)
        self.driver.click(SEND_RESOURCE)

    @action(profile_state)
    def set_about(self, about_text: str):
        self.driver.click(PROFILE_INFO_STATUS_CARD)
        self.driver.click(PROFILE_STATUS_EDIT_ICON)
        self.driver.send_keys(EDIT_TEXT, about_text)
        self.driver.click(PROFILE_SAVE_BUTTON)
        # This action ends in a screen that isn't a state, so move back one screen.
        self.driver.back()

    @action(new_chat_state)
    def create_new_chat(self, conversation: str, first_message: str):
        """
        Start a new 1-on-1 conversation with a contact and send a message.
        :param conversation: Contact to start the conversation with.
        :param first_message: First message to send to the contact
        """
        self.driver.click(f'//*[@resource-id="{WHATSAPP_PACKAGE}:id/contactpicker_text_container"]//*[@text="{conversation}"]')
        self.driver.click(build_content_desc_xpath_widget('Button', 'Message'))
        self.send_message(first_message)

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
        self.driver.click(CONVERSATIONS_NEW_BROADCAST_TITLE)
        for receiver in receivers:
            self.driver.click(CONVERSATIONS_CHAT_ABLE_CONTACT)

        self.driver.click(NEXT_BUTTON)
        self.driver.send_keys(TEXT_ENTRY, broadcast_text)
        self.driver.click(SEND_RESOURCE)

    @action(chat_state)
    def delete_message_for_everyone(self, conversation: str, message_text: str):
        """
        Remove a message with the message text. Should be recently sent, so it is still in view and still possible to
        delete for everyone.
        :param conversation: The chat conversation in which to send this message, if not currently in the desired chat.
        :param message_text: literal message text of the message to remove. The first match will be removed in case
        there are multiple with the same text.
        """
        self.driver.long_click_element(f"//*[@resource-id='{WHATSAPP_PACKAGE}:id/conversation_text_row']//*[@text='{message_text}']")
        self.driver.click(CHAT_DELETE_BUTTON)
        self.driver.click(CHAT_DELETE_FOR_EVERYONE)

    @action(new_chat_state)
    def create_group(self, conversation: str, members: Union[str, List[str]]):
        """
        Create a new group.
        :param conversation: The subject of the group.
        :param members: The contact(s) you want to add to the group (string or list).
        """
        self.driver.click(NEW_CHAT_NEW_GROUP)

        members = [members] if not isinstance(members, list) else members
        for member in members:
            contacts = self.driver.get_elements(TEXT_VIEWS)
            member_to_add = [contact for contact in contacts if contact.text.lower() == member.lower()][0]
            member_to_add.click()

        self.driver.click(NEXT_BUTTON)
        self.driver.send_keys(CONVERSATIONS_GROUP_NAME, conversation)
        self.driver.click(OK_BUTTON)
        # Creating a group takes a few seconds
        sleep(2)

    @action(conversations_state)
    def archive_conversation(self, conversation: str):
        """
        Archives a given conversation.
        :param conversation: The conversation to archive.
        """
        self.driver.long_click_element(f'//*[contains(@resource-id,"{WHATSAPP_PACKAGE}:id/conversations_row_contact_name") and @text="{conversation}"]')
        self.driver.click(CONVERSATIONS_MENUITEM_ARCHIVE)
        # Wait until the archive popup disappeared
        archived_popup_present = True
        tries = 0
        while archived_popup_present and tries < 5:
            logger.info("waiting for archived popup to disappear")
            sleep(5)
            tries += 1
            archived_popup_present = 'archived' in self.driver.get_elements(CONVERSATIONS_ARCHIVED)[0].text
        logger.info("Archive pop-up gone!")

    @action(chat_state)
    def open_view_once_photo(self, conversation: str):
        """
        Open view once photo in the specified chat. Should be done right after the photo is sent, to ensure the correct
        photo is opened, this will be the lowest one.
        :param conversation: The chat in which the photo has to be opened
        """
        self.driver.get_elements(CHAT_VIEW_ONCE_MEDIA)[-1].click()

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
        self.driver.click(CHAT_SETTINGS_CONTAINS_DELETE_GROUP)
        self.driver.click(CHAT_SETTINGS_CONTAINS_DELETE_GROUP)

    @action(chat_state)
    def reply_to_message(self, message_to_reply_to: str, reply_text: str, conversation: str = None):
        """
        Reply to a message.
        :param conversation: The chat conversation in which to send this message.
        :param message_to_reply_to: message you want to reply to.
        :param reply_text: message text you are sending in your reply.
        """
        message_xpath = f'//android.widget.TextView[@resource-id="{WHATSAPP_PACKAGE}:id/message_text" and contains(@text, "{message_to_reply_to}")]'
        self.driver.swipe_to_find_element(message_xpath)
        self.driver.long_click_element(message_xpath)
        self.driver.click(CHAT_REPLY)
        self.driver.send_keys(TEXT_ENTRY, reply_text)
        self.driver.click(SEND)

    @action(chat_state)
    def send_emoji(self, conversation: str):
        """
        Send the first emoji in the emoji menu.
        :param conversation: The chat conversation in which to send this sticker.
        """
        self.driver.click(CHAT_EMOJI_PICKER)
        sleep(1)
        self.driver.click(CHAT_EMOJIS)
        self.driver.click(CHAT_EMOJI)
        self.driver.click(SEND)

    @action(chat_state)
    def send_sticker(self, conversation: str = None):
        """
        Send the first sticker in the sticker menu.
        :param conversation: The chat conversation in which to send this sticker.
        """
        self.driver.click(CHAT_EMOJI_PICKER)
        sleep(1)
        self.driver.click(CHAT_STICKERS)
        self.driver.click(CHAT_STICKER)

    @action(chat_state)
    def send_voice_message(self, duration: int = 2, conversation: str = None):
        """
        Sends a voice message in the specified conversation.
        :param conversation: The chat conversation in which to send this voice recording.
        :param duration: the duration in of the voice message to send in seconds.
        """
        self.driver.long_click_element(CHAT_VOICE_NOTE_BUTTON, duration=duration)

    @action(send_location_state, end_state=chat_state)
    def send_current_location(self, conversation: str = None):
        """
        Send the current location in the specified chat.
        :param conversation: The chat conversation in which to send the location.
        """
        sleep(5)  # it takes some time to fix the location
        self.driver.click(SEND_LOCATION_CURRENT_LOCATION_BUTTON)

    @action(send_location_state, end_state=chat_state)
    def send_live_location(self, caption: str = None, conversation: str = None):
        """
        Send a live location in the specified chat.
        :param conversation: The chat conversation in which to start the live location sharing.
        :param caption: Optional caption sent along with the live location
        """
        self.driver.click(SEND_LOCATION_LIVE_LOCATION_BUTTON)
        if self.driver.is_present(SEND_LOCATION_LIVE_LOCATION_DIALOG):
            self.driver.click(SEND_LOCATION_POPUP_CONTINUE)
        if caption is not None:
            self.driver.send_keys(SEND_LOCATION_CAPTION, caption)
        self.driver.click(SEND)

    @action(chat_state)
    def stop_live_location(self, conversation: str = None):
        """
        Stops the current live location sharing.
        :param conversation: The chat conversation in which to stop the live location sharing.
        """
        self.driver.swipe_to_click_element(CHAT_STOP_SHARING)

        if self.driver.is_present(STOP_BUTTON):
            self.driver.click(STOP_BUTTON)

    @action(chat_state)
    def send_contact(self, contact_name: str, conversation: str = None):
        """
        Send a contact in the specified chat.
        :param contact_name: the name of the contact to send.
        :param conversation: The chat conversation in which to send the contact.
        """
        self.driver.click(CHAT_ATTACH_BUTTON)
        self.driver.click(CHAT_ATTACH_CONTACT_BUTTON)
        self.driver.swipe_to_click_element(CHAT_CONTACT_NAME.format(contact_name=contact_name))
        self.driver.click(NEXT_BUTTON)
        self.driver.click(CHAT_ATTACH_SEND_BUTTON)

    @action(chat_settings_state)
    def activate_disappearing_messages(self, conversation: str = None):
        """
        Activates disappearing messages (auto delete) in the current or a given chat.
        Messages will now auto-delete after 24h.
        :param conversation: The conversation for which disappearing messages should be activated.
        """
        self.driver.swipe_to_click_element(CHAT_SETTINGS_DISAPPEARING_MESSAGES)
        self.driver.click(RADIO_BUTTON_24_HOURS)
        self.driver.back()

    @action(chat_settings_state)
    def deactivate_disappearing_messages(self, conversation: str = None):
        """
        Disables disappearing messages (auto delete) in the current or a given chat.
        :param conversation: The conversation for which disappearing messages should be activated.
        """
        self.driver.swipe_to_click_element(CHAT_SETTINGS_DISAPPEARING_MESSAGES)
        self.driver.click(RADIO_BUTTON_OFF)
        self.driver.back()

    @action(calls_state, end_state=voice_call_state)
    def start_voice_call(self, conversation: str):
        """
        Make a WhatsApp voice call. The call is made to a given contact.
        :param conversation: name of the contact to call.
        """
        go_to_voice_call(self.driver, conversation)

    @action(calls_state, end_state=video_call_state)
    def start_video_call(self, conversation: str):
        """
        Make a WhatsApp voice call. The call is made to a given contact.
        :param conversation: name of the contact to call.
        """
        go_to_video_call(self.driver, conversation)

    @action(voice_call_state, end_state=calls_state)
    def end_voice_call(self, conversation: str = None):
        """
        Ends the current voice call.
        """
        self._end_call()

    @action(video_call_state, end_state=calls_state)
    def end_video_call(self, conversation: str = None):
        """
        Ends the current video call.
        """
        self._end_call()

    def _end_call(self):
        if not self.driver.is_present(CALL_END_CALL_BUTTON, implicit_wait=1):
            # tap screen to make call button visible
            self.driver.click(CALL_SCREEN_BACKGROUND)
        self.driver.click(CALL_END_CALL_BUTTON)

    # This method is not an @action, since it is not tied to a state.
    def answer_call(self):
        """
        Answer when receiving a call via Whatsapp.
        """
        self.driver.open_notifications()
        sleep(2)
        self.driver.click(RECEIVE_CALL_ANSWER_BUTTON)

    # This method is not an @action, since it is not tied to a state.
    def decline_call(self):
        """
        Declines an incoming Whatsapp call.
        """
        self.driver.open_notifications()
        sleep(2)
        self.driver.click(RECEIVE_CALL_DECLINE_BUTTON)

    @action(chat_settings_state)
    def leave_group(self, conversation: str = None):
        """
        This method will leave the given group. It will not delete that group.
        :param conversation: Name of the group we want to leave.
        """
        self.driver.swipe_to_click_element(CHAT_SETTINGS_EXIT_GROUP_LIST_ITEM)
        self.driver.click(CHAT_SETTINGS_EXIT_GROUP_BUTTON)

    @action(chat_settings_state)
    def remove_member_from_group(self, conversation: str, member: str):
        """
        Removes a given member from a given group chat.
        It is assumed the group chat exists and has the given member.
        :param conversation: The group
        :param member: The member to remove
        """
        self.driver.swipe_to_click_element(CHAT_SETTINGS_MEMBER.format(member=member))
        self.driver.click(CHAT_SETTINGS_REMOVE_MEMBER)
        self.driver.click(CHAT_SETTINGS_OK_BUTTON)

    @action(chat_state)
    def forward_message(self, conversation: str, message_contains: str, to_chat: str):
        """
        Forwards a message from one conversation to another.
        It is assumed the message and both conversations exists.
        :param conversation: The chat from which the message has to be forwarded
        :param message_contains: the text from the message that has to be forwarded. Uses String.contains(), so only part
        of the message is needed, but be sure the given text is enough to match your intended message uniquely.
        :param to_chat: The chat to which the message has to be forwarded.
        """
        self.driver.long_click_element(CHAT_MESSAGE_BY_CONTENT.format(message_contains=message_contains))
        self.driver.click(CHAT_FORWARD_MESSAGE)
        self.driver.click(CHAT_FORWARD_CONTACT_BY_NAME.format(to_chat=to_chat))
        self.driver.click(SEND)

    @action(chat_state)
    def send_media(self, directory_name: str, conversation: str = None, index: int = 1, caption: str = None,
                   view_once: bool = False):
        # Go to gallery
        self.driver.click(CHAT_ATTACH_BUTTON)
        self.driver.click(CHAT_ATTACH_GALLERY_BUTTON)
        self.driver.click(CHAT_GALLERY_FOLDERS_BUTTON)
        self._find_media_in_folder(directory_name, index)
        sleep(0.5)
        self.driver.click(CHAT_FIRST_MEDIA_IN_FOLDER)

        if caption:
            sleep(0.5)
            self.driver.send_keys(CHAT_CAPTION_TEXT_BOX, caption)
            # Clicking the text box after sending keys is required for Whatsapp to notice text has been inserted.
            self.driver.click(CHAT_CAPTION_TEXT_BOX)
            self.driver.back()

        if view_once:
            self.driver.click(CHAT_SEND_MEDIA_VIEW_ONCE)
            if self.driver.is_present(CHAT_POPUP_BUTTON_OK):
                self.driver.click(CHAT_POPUP_BUTTON_OK)
        sleep(1)
        self.driver.click(SEND)

    def _find_media_in_folder(self, directory_name: str, index: int):
        try:
            self.driver.swipe_to_click_element(CHAT_DIRECTORY_NAME.format(directory_name=directory_name))
        except PumaClickException:
            raise PumaClickException(f'The directory {directory_name} could not be found.')
        self.driver.click(CHAT_DIRECTORY_NAME.format(directory_name=directory_name))
        sleep(0.5)
        try:
            self.driver.click(CHAT_DIRECTORY_MEDIA_BY_INDEX.format(index=index))
        except PumaClickException:
            raise PumaClickException(
                f'The media at index {index} could not be found. The index is likely too large or negative.')
