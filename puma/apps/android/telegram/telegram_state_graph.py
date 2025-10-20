from puma.state_graph.action import action
from puma.state_graph.puma_driver import supported_version, PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, State
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

CALL_STATE_END_CALL_BUTTON = '//android.widget.Button[@text="End Call"]'
CALL_STATE_SPEAKER_BUTTON = '//android.widget.FrameLayout[@content-desc="Speaker"]'
CALL_STATE_MUTE_BUTTON = '//android.widget.FrameLayout[@content-desc="Mute"]'


class TeleGramChatState(SimpleState, ContextualState):

    def __init__(self, parent_state: State):
        super().__init__([CHAT_STATE_MESSAGE_TEXTBOX, CHAT_STATE_GIF_BUTTON],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True
        return driver.is_present(CHAT_STATE_CONVERSATION_NAME.format(conversation_name=conversation))


def go_to_chat(driver: PumaDriver, conversation: str):
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

    conversations_state.to(chat_state, go_to_chat)
    chat_state.to(call_state, lambda driver: driver.click(CHAT_STATE_CALL_BUTTON))

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

    def _in_voice_message_mode(self):
        return self.driver.get_element(CHAT_STATE_RECORD_VIDEO_OR_AUDIO_MESSAGE).get_attribute(
            'content-desc') == 'Record voice message'

    @action(chat_state)
    def start_call(self, conversation: str = None):
        self.driver.click(CHAT_STATE_CALL_BUTTON)

    def _find_button_location(self, width_ratio: float, height_ratio: float, xpath: str):
        send_button = self.driver.get_element(xpath)
        top_left = send_button.location['x'], send_button.location['y']
        size = send_button.size['height'], send_button.size['width']
        location = int(top_left[0] + width_ratio * size[1]), int(top_left[1] + height_ratio * size[0])
        return location