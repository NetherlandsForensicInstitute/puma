import time

from puma.apps.android.telegram import logger
from puma.state_graph.action import action
from puma.state_graph.puma_driver import supported_version, PumaDriver, PumaClickException
from puma.state_graph.state import SimpleState, ContextualState, State, compose_clicks
from puma.state_graph.state_graph import StateGraph

TELEGRAM_PACKAGE = 'org.telegram.messenger'
TELEGRAM_WEB_PACKAGE = 'org.telegram.messenger.web'

CHAT_OVERVIEW_NEW_CONVERSATION_BUTTON = '//android.widget.FrameLayout[@content-desc="New Message"]'
CHAT_OVERVIEW_NAV_MENU_BUTTON = '//android.widget.ImageView[@content-desc="Open navigation menu"]'
CHAT_OVERVIEW_SEARCH_BUTTON = '//android.widget.ImageButton[@content-desc="Search"]'

SEARCH_INPUT_FIELD = '//android.widget.EditText[@text="Search"]'
FIRST_SEARCH_HIT = '//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[starts-with(lower-case(@text), lower-case("{conversation_name},"))]'

CHAT_STATE_CONVERSATION_NAME = '//android.widget.ImageView[@content-desc="Go back"]/../android.widget.FrameLayout[starts-with(lower-case(@content-desc),lower-case("{conversation_name}\n"))]/android.widget.TextView[starts-with(lower-case(@text), lower-case("{conversation_name}"))]'
CHAT_STATE_CALL_BUTTON = '//android.widget.ImageButton[@content-desc="Call"]'
CHAT_STATE_BACK_BUTTON = '//android.widget.ImageView[@content-desc="Go back"]'
CHAT_STATE_GIF_BUTTON = '//android.widget.ImageView[@content-desc="Emoji, stickers, and GIFs"]'
CHAT_STATE_MESSAGE_TEXTBOX = '//android.widget.EditText[@text]'
CHAT_STATE_MEDIA_BUTTON = '//android.widget.ImageView[@content-desc="Attach media"]'
CHAT_STATE_RECORD_VIDEO_OR_AUDIO_MESSAGE = '//android.widget.FrameLayout[@content-desc="Record voice message" or @content-desc="Record video message"]'
CHAT_STATE_SEND_BUTTON = '//android.view.View[@content-desc="Send"]'

SEND_MEDIA_STATE_INSTANT_CAMERA_BUTTON = '//android.widget.FrameLayout[@content-desc="Instant camera"]/preceding-sibling::android.widget.FrameLayout[last()]'
SEND_MEDIA_STATE_GALLERY_BUTTON = '//android.widget.FrameLayout[@text="Gallery"]'
SEND_MEDIA_STATE_FILE_BUTTON = '//android.widget.FrameLayout[@text="File"]'
SEND_MEDIA_STATE_LOCATION_BUTTON = '//android.widget.FrameLayout[@text="Location"]'
SEND_MEDIA_STATE_MY_LOCATION_BUTTON = '//android.widget.ImageView[@content-desc="My location"]'

SEND_FROM_GALLERY_STATE_BACK_BUTTON = '//android.widget.ImageView[@content-desc="Go back"]'
SEND_FROM_GALLERY_THREE_DOTS_BUTTON = '//android.widget.ImageButton[@content-desc="More options"]'
SEND_FROM_GALLERY_FOLDER_PICKER = '//android.widget.ImageView[@content-desc="Go back"]/following-sibling::*[1][@text]'
SEND_FROM_GALLERY_MEDIA_SWITCH = '(//android.widget.Switch)[{index}]'

CALL_STATE_END_CALL_BUTTON = '//android.widget.Button[@text="End Call"]'
CALL_STATE_SPEAKER_BUTTON = '//android.widget.FrameLayout[@content-desc="Speaker"]'
CALL_STATE_MUTE_BUTTON = '//android.widget.FrameLayout[@content-desc="Mute"]'
CALL_STATE_STATUS = '//android.widget.LinearLayout[ends-with(@text, "Telegram Call")]/android.widget.FrameLayout/android.widget.TextView'


class TeleGramChatState(SimpleState, ContextualState):

    def __init__(self, parent_state: State):
        super().__init__([CHAT_STATE_MESSAGE_TEXTBOX, CHAT_STATE_GIF_BUTTON],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True
        return driver.is_present(CHAT_STATE_CONVERSATION_NAME.format(conversation_name=conversation))


def go_to_chat(driver: PumaDriver, conversation: str):
    if not conversation:
        raise ValueError(f'Cannot open a conversation without a conversation name')
    driver.click(CHAT_OVERVIEW_SEARCH_BUTTON)
    driver.send_keys(SEARCH_INPUT_FIELD, conversation)
    driver.click(FIRST_SEARCH_HIT.format(conversation_name=conversation))


@supported_version("12.0.1")
class Telegram(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the Telegram Messenger application.

    This class uses a state machine approach to manage transitions between different states
    of the Telegram user interface. It provides methods to navigate between states, validate states,
    and handle unexpected states or errors.
    """
    conversations_state = SimpleState(
        [CHAT_OVERVIEW_NEW_CONVERSATION_BUTTON, CHAT_OVERVIEW_SEARCH_BUTTON, CHAT_OVERVIEW_NAV_MENU_BUTTON],
        initial_state=True)
    chat_state = TeleGramChatState(parent_state=conversations_state)
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

    conversations_state.to(chat_state, go_to_chat)
    chat_state.to(call_state, compose_clicks([CHAT_STATE_CALL_BUTTON], name="press_call_button"))
    chat_state.to(send_media_state, compose_clicks([CHAT_STATE_MEDIA_BUTTON], name="press_attachment_button"))
    send_media_state.to(send_from_gallery_state,
                        compose_clicks([SEND_MEDIA_STATE_GALLERY_BUTTON], name='press_gallery_button'))

    def __init__(self, device_udid, telegram_web_version: bool = False):
        package = TELEGRAM_WEB_PACKAGE if telegram_web_version else TELEGRAM_PACKAGE
        StateGraph.__init__(self, device_udid, package)

    @action(chat_state)
    def send_message(self, message: str, conversation: str = None):
        # self.driver.click(CHAT_STATE_MESSAGE_TEXTBOX)
        self.driver.send_keys(CHAT_STATE_MESSAGE_TEXTBOX, message)
        # send_button = self.driver.get_element('//android.view.View[@content-desc="Send"]')
        # Telegram has a horrible UI; the bounds of the send button are defined incorrectly so we need to click off-center
        location = self._find_button_location(0.8, 0.5, CHAT_STATE_SEND_BUTTON)
        self.driver.driver.tap([(location)])

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
                logger.warn(f'Using OCR to click on media folder {folder}. OCR is unreliable, if possible use the folder index number!')
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
                logger.warn(f'Could not select media with index {i}. Are enough media files present?')
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
            logger.warn(f'Tried to end a call, but no call was in progress')
        self.driver.click(CALL_STATE_END_CALL_BUTTON)

    @action(send_media_state)
    def send_location(self, conversation: str = None):
        self.driver.click(SEND_MEDIA_STATE_LOCATION_BUTTON)
        self.driver.click(SEND_MEDIA_STATE_MY_LOCATION_BUTTON)
        self.driver.click('//android.widget.TextView[@text="Send selected location"]')

    def _in_voice_message_mode(self):
        return self.driver.get_element(CHAT_STATE_RECORD_VIDEO_OR_AUDIO_MESSAGE).get_attribute(
            'content-desc') == 'Record voice message'

    def _find_button_location(self, width_ratio: float, height_ratio: float, xpath: str):
        send_button = self.driver.get_element(xpath)
        top_left = send_button.location['x'], send_button.location['y']
        size = send_button.size['height'], send_button.size['width']
        location = int(top_left[0] + width_ratio * size[1]), int(top_left[1] + height_ratio * size[0])
        return location