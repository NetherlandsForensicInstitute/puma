import time

from puma.apps.android.telegram import logger
from puma.apps.android.telegram.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.puma_driver import supported_version, PumaDriver, PumaClickException
from puma.state_graph.state import SimpleState, ContextualState, State, compose_clicks
from puma.state_graph.state_graph import StateGraph

TELEGRAM_PACKAGE = 'org.telegram.messenger'
TELEGRAM_WEB_PACKAGE = 'org.telegram.messenger.web'


class TeleGramChatState(SimpleState, ContextualState):
    def __init__(self, parent_state: State):
        super().__init__([CHAT_STATE_MESSAGE_TEXTBOX, CHAT_STATE_GIF_BUTTON],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True
        return driver.is_present(CHAT_STATE_CONVERSATION_NAME.format(conversation=conversation))


class TelegramChatSettingsState(SimpleState, ContextualState):
    def __init__(self, parent_state: State):
        super().__init__(
            [CHAT_SETTINGS_STATE_BACK, CHAT_SETTINGS_STATE_THREE_DOTS, CHAT_SETTINGS_STATE_CONVERSATION_NAME],
            parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if conversation is None:
            return True
        return driver.is_present(CHAT_SETTINGS_STATE_CONVERSATION_NAME_CONTEXT.format(conversation=conversation))

    def can_edit(self, driver: PumaDriver):
        return driver.is_present(CHAT_SETTINGS_EDIT_GROUP_BUTTON)

    def can_add_members(self, driver: PumaDriver):
        return driver.is_present(CHAT_SETTINGS_STATE_ADD_MEMBERS)


def open_chat_settings(driver: PumaDriver, conversation: str):
    driver.click(CHAT_STATE_CONVERSATION_NAME.format(conversation=conversation))


def go_to_chat(driver: PumaDriver, conversation: str):
    if not conversation:
        raise ValueError(f'Cannot open a conversation without a conversation name')
    driver.click(CHAT_OVERVIEW_SEARCH_BUTTON)
    driver.send_keys(SEARCH_INPUT_FIELD, conversation)
    driver.click(FIRST_SEARCH_HIT.format(conversation=conversation))


@supported_version("12.0.1")
class Telegram(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the Telegram Messenger application.

    This class uses a state machine approach to manage transitions between different states
    of the Telegram user interface. It provides methods to navigate between states, validate states,
    and handle unexpected states or errors.
    """
    conversations_state = SimpleState(
        [CHAT_OVERVIEW_NEW_MESSAGE_BUTTON, CHAT_OVERVIEW_SEARCH_BUTTON, CHAT_OVERVIEW_NAV_MENU_BUTTON],
        initial_state=True)
    chat_state = TeleGramChatState(parent_state=conversations_state)
    chat_settings_state = TelegramChatSettingsState(parent_state=chat_state)
    call_state = SimpleState([CALL_STATE_END_CALL_BUTTON, CALL_STATE_MUTE_BUTTON, CALL_STATE_SPEAKER_BUTTON],
                             parent_state=chat_state)
    send_media_state = SimpleState(
        [SEND_MEDIA_STATE_INSTANT_CAMERA_BUTTON, SEND_MEDIA_STATE_GALLERY_BUTTON, SEND_MEDIA_STATE_FILE_BUTTON,
         SEND_MEDIA_STATE_LOCATION_BUTTON],
        parent_state=chat_state)
    send_from_gallery_state = SimpleState(
        [SEND_FROM_GALLERY_STATE_BACK_BUTTON, SEND_FROM_GALLERY_FOLDER_PICKER,
         SEND_FROM_GALLERY_THREE_DOTS_BUTTON, SEND_FROM_GALLERY_MEDIA_SWITCH.format(index=1)],
        parent_state=chat_state)  # pressing back goes to the chat state
    new_message_state = SimpleState(
        [NEW_MESSAGE_STATE_NEW_GROUP_BUTTON, NEW_MESSAGE_STATE_NEW_CONTACT_BUTTON, NEW_MESSAGE_STATE_NEW_CHANNEL_BUTTON,
         NEW_MESSAGE_STATE_CREATE_NEW_CONTACT_BUTTON],
        parent_state=conversations_state)

    conversations_state.to(chat_state, go_to_chat)
    chat_state.to(call_state, compose_clicks([CHAT_STATE_CALL_BUTTON], name="press_call_button"))
    chat_state.to(chat_settings_state, open_chat_settings)
    chat_state.to(send_media_state, compose_clicks([CHAT_STATE_MEDIA_BUTTON], name="press_attachment_button"))
    send_media_state.to(send_from_gallery_state,
                        compose_clicks([SEND_MEDIA_STATE_GALLERY_BUTTON], name='press_gallery_button'))
    conversations_state.to(new_message_state,
                           compose_clicks([CHAT_OVERVIEW_NEW_MESSAGE_BUTTON], name='press_new_message_button'))

    def __init__(self, device_udid, telegram_web_version: bool = False):
        package = TELEGRAM_WEB_PACKAGE if telegram_web_version else TELEGRAM_PACKAGE
        StateGraph.__init__(self, device_udid, package)

    @action(chat_state)
    def send_message(self, message: str, conversation: str = None):
        # self.driver.click(CHAT_STATE_MESSAGE_TEXTBOX)
        self.driver.send_keys(CHAT_STATE_MESSAGE_TEXTBOX, message)
        # send_button = self.driver.get_element('//android.view.View[@content-desc="Send"]')
        # Telegram has a horrible UI; the bounds of the send button are defined incorrectly so we need to click off-center
        self.driver.click_within(CHAT_STATE_SEND_BUTTON, 0.8, 0.5)

    @action(chat_state)
    def send_voice_message(self, duration: int, conversation: str = None):
        if not self._in_voice_message_mode():
            self.driver.click(CHAT_STATE_RECORD_VIDEO_OR_AUDIO_MESSAGE)
        self.driver.press_and_hold(CHAT_STATE_RECORD_VIDEO_OR_AUDIO_MESSAGE, duration)

    @action(chat_state)
    def send_video_message(self, duration: int, conversation: str = None):
        if self._in_voice_message_mode():
            self.driver.click(CHAT_STATE_RECORD_VIDEO_OR_AUDIO_MESSAGE)
        self.driver.press_and_hold(CHAT_STATE_RECORD_VIDEO_OR_AUDIO_MESSAGE, duration)

    @action(send_from_gallery_state, end_state=chat_state)
    def send_media_from_gallery(self, media_index: int | list[int],
                                caption: str = None,
                                folder: str | int = None,
                                conversation: str = None):
        if not media_index:
            raise ValueError(f'Cannot send media from gallery without a proper set of indices')
        # open folder if needed
        if folder:
            self.driver.click(SEND_FROM_GALLERY_FOLDER_PICKER)
            if isinstance(folder, str):
                logger.warning(
                    f'Using OCR to click on media folder {folder}. OCR is unreliable, if possible use the folder index number!')
                time.sleep(1)
                self.driver.click_text_ocr(folder)
            else:
                self.driver.click(f'//android.widget.LinearLayout/android.view.View[{folder}]')
        # select picture/video
        if isinstance(media_index, int):
            media_index = [media_index]
        clicked = 0
        for i in media_index:
            try:
                if i in [2, 3]:  # these switches can be obscured by other UI elements. We do a long press for those
                    self.driver.long_click(f'{SEND_FROM_GALLERY_MEDIA_SWITCH.format(index=i)}/..')
                else:
                    self.driver.click(SEND_FROM_GALLERY_MEDIA_SWITCH.format(index=i))
                self.gtl_logger.info(f'Selected gallery item with index {i}')
                clicked += 1
            except PumaClickException as e:
                logger.warning(f'Could not select media with index {i}. Are enough media files present?')
        if clicked == 0:
            raise PumaClickException(
                f'Tried to select gallery items with indexes {media_index}, but could not select any of them.')
        if caption:
            self.driver.send_keys('//android.widget.EditText[@text]', caption)
            self.gtl_logger.info(f'Entered caption {caption}')
        # send button
        self.driver.click('//android.widget.Button')
        self.gtl_logger.info(f'Pressed send button')

    @action(chat_state, end_state=call_state)
    def start_call(self, conversation: str = None):
        self.driver.click(CHAT_STATE_CALL_BUTTON)

    @action(call_state)
    def mute_mic(self):
        self.driver.click(CALL_STATE_MUTE_BUTTON)

    def end_call(self):
        if self.current_state != Telegram.call_state:
            logger.warning(f'Tried to end a call, but no call was in progress')
        self.driver.click(CALL_STATE_END_CALL_BUTTON)

    @action(send_media_state, end_state=chat_state)
    def send_location(self, conversation: str = None):
        self.driver.click(SEND_MEDIA_STATE_LOCATION_BUTTON)
        self.driver.click(SEND_MEDIA_STATE_MY_LOCATION_BUTTON)
        self.driver.click(SEND_MEDIA_STATE_SEND_CURRENT_LOCATION_BUTTON)

    @action(send_media_state, end_state=chat_state)
    def send_live_location(self, conversation: str = None, duration_option: int | str = 1):
        self.driver.click(SEND_MEDIA_STATE_LOCATION_BUTTON)
        if not self.driver.is_present(SEND_MEDIA_STATE_LIVE_LOCATION_BUTTON, implicit_wait=1):
            logger.warning(f'Could not share live location, was live location already being shared?')
            self.driver.back()
            return
        self.driver.click(SEND_MEDIA_STATE_LIVE_LOCATION_BUTTON)
        if isinstance(duration_option, int):
            self.driver.click(SEND_MEDIA_STATE_LIVE_LOCATION_DURATION_OPTION_INDEX.format(duration=duration_option))
        else:
            xpath = SEND_MEDIA_STATE_LIVE_LOCATION_DURATION_OPTION_TEXT.format(duration=duration_option)
            if not self.driver.is_present(xpath, implicit_wait=1):
                raise PumaClickException(
                    f'Could not select option for live location sharing with name "{duration_option}". Is this option present in the UI?')
            self.driver.click(xpath)
        self.driver.click(SEND_MEDIA_STATE_LIVE_LOCATION_SHARE_BUTTON)

    @action(chat_state)
    def stop_live_location_sharing(self, conversation: str = None):
        if not self.driver.is_present(CHAT_STATE_STOP_LIVE_LOCATION_SHARING_BUTTON):
            logger.warning(f'Could not stop sharing live location as it wasn\'t shared.')
            return
        self.driver.click(CHAT_STATE_STOP_LIVE_LOCATION_SHARING_BUTTON)
        self.driver.click(CHAT_STATE_STOP_LIVE_LOCATION_CONFIRM_BUTTON)

    @action(new_message_state, end_state=chat_state)
    def create_new_group(self, group_name: str, members: list[str] = [], auto_delete: int = None):
        if auto_delete is not None and auto_delete not in [1, 2, 3]:
            raise ValueError(f'Unsupported auto-delete option: {auto_delete}')
        self.driver.click(NEW_MESSAGE_STATE_NEW_GROUP_BUTTON)
        for member in members:
            self.gtl_logger.info(f'adding group member {member}')
            self.driver.click(NEW_GROUP_MEMBER.format(member=member))
        self.driver.click(NEW_GROUP_NEXT)
        self.gtl_logger.info(f'Entering group name "{group_name}" and setting auto-delete option')
        self.driver.send_keys(NEW_GROUP_NAME_INPUT, group_name)
        if auto_delete:
            self.driver.click(NEW_GROUP_AUTO_DELETE_OPTION)
            self.driver.click(f'//android.widget.LinearLayout/android.widget.FrameLayout[{auto_delete}]')
        self.driver.click(NEW_GROUP_DONE_BUTTON)

    @action(chat_settings_state)
    def add_members(self, new_members: list[str], conversation: str = None):
        if not Telegram.chat_settings_state.can_add_members(self.driver):
            raise PumaClickException(f"Cannot add members in conversation {conversation}. "
                                     f"Check whether it is a group and whether permissions are setup correctly.")
        self.driver.click(CHAT_SETTINGS_STATE_ADD_MEMBERS)
        for name in new_members:
            self.driver.send_keys(CHAT_SETTINGS_STATE_ADD_MEMBERS_SEARCH, name)
            try:
                self.driver.click(
                    f'//androidx.recyclerview.widget.RecyclerView//android.widget.TextView[lower-case(@text)=lower-case("{name}")]')
            except PumaClickException:
                raise PumaClickException(
                    f'Could not add member {name} as it could not be found in the UI after a search')
        self.driver.click('//android.widget.ImageView[@content-desc="Next"]')
        self.driver.click('//android.widget.TextView[@text="Add"]')

    @action(chat_settings_state)
    def remove_member(self, member: str, conversation: str = None):
        if not Telegram.chat_settings_state.can_add_members(self.driver):
            raise PumaClickException(f"Cannot remove members in conversation {conversation}. "
                                     f"Check whether it is a group and whether permissions are setup correctly.")
        self.driver.long_click(CHAT_SETTINGS_STATE_MEMBER_CONTEXT.format(member=member))
        self.driver.click(CHAT_SETTINGS_STATE_REMOVE_MEMBER_BUTTON)

    @action(chat_settings_state)
    def edit_group_name(self, conversation: str, new_group_name: str):
        if not Telegram.chat_settings_state.can_add_members(self.driver):
            raise PumaClickException(f"Cannot rename conversation {conversation}. "
                                     f"Check whether it is a group and whether permissions are setup correctly.")
        self.driver.click(CHAT_SETTINGS_EDIT_GROUP_BUTTON)
        self.driver.send_keys(EDIT_GROUP_NAME, new_group_name)
        self.driver.click(EDIT_GROUP_DONE)

    @action(chat_settings_state)
    def edit_group_description(self, conversation: str, description:str):
        if not Telegram.chat_settings_state.can_add_members(self.driver):
            raise PumaClickException(f"Cannot rename conversation {conversation}. "
                                     f"Check whether it is a group and whether permissions are setup correctly.")
        self.driver.click(CHAT_SETTINGS_EDIT_GROUP_BUTTON)
        self.driver.send_keys(EDIT_GROUP_DESCRIPTION, description)
        self.driver.click(EDIT_GROUP_DONE)

    @action(chat_state)
    def delete_and_leave_group(self, conversation: str):
        self.driver.click(CHAT_STATE_THREE_DOTS)
        self.driver.click(CHAT_STATE_DELETE_AND_LEAVE_GROUP)
        if self.driver.is_present(CHAT_STATE_DELETE_AND_LEAVE_GROUP_FOR_ALL):
            self.driver.click(CHAT_STATE_DELETE_AND_LEAVE_GROUP_FOR_ALL)
        self.driver.click(CHAT_STATE_DELETE_AND_LEAVE_GROUP_CONFIRM_BUTTON)

    def _in_voice_message_mode(self):
        return self.driver.get_element(CHAT_STATE_RECORD_VIDEO_OR_AUDIO_MESSAGE).get_attribute(
            'content-desc') == 'Record voice message'