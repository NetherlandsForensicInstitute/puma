from puma.state_graph.action import action
from puma.state_graph.puma_driver import supported_version, PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, State
from puma.state_graph.state_graph import StateGraph

TELEGRAM_PACKAGE = 'org.telegram.messenger'
TELEGRAM_WEB_PACKAGE = 'org.telegram.messenger.web'

CHAT_OVERVIEW_TITLE_HEADER = '//android.widget.TextView[@text="Telegram"]'
CHAT_OVERVIEW_NEW_CONVERSATION_BUTTON = '//android.widget.FrameLayout[@content-desc="New Message"]'
CHAT_OVERVIEW_NEW_STORY_BUTTON = '//android.widget.FrameLayout[@content-desc="Capture story"]'

CHAT_STATE_CALL_BUTTON = '//android.widget.ImageButton[@content-desc="Call"]'
CHAT_STATE_BACK_BUTTON = '//android.widget.ImageView[@content-desc="Go back"]'
CHAT_STATE_MESSAGE_TEXTBOX = '//android.widget.EditText[@text]'
CHAT_STATE_MEDIA_BUTTON = '//android.widget.ImageView[@content-desc="Attach media"]'
CHAT_STATE_GIF_BUTTON = '//android.widget.ImageView[@content-desc="Emoji, stickers, and GIFs"]'
CHAT_STATE_CONVERSATION_NAME = '//android.widget.ImageView[@content-desc="Go back"]/../android.widget.FrameLayout/*[1]'


class TeleGramChatState(SimpleState, ContextualState):

    def __init__(self, parent_state: State):
        super().__init__([CHAT_STATE_CALL_BUTTON, CHAT_STATE_MESSAGE_TEXTBOX, CHAT_STATE_GIF_BUTTON], parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True
        chat_title = (driver.get_element(CHAT_STATE_CONVERSATION_NAME).get_attribute('text'))
        return conversation.lower() in chat_title.lower()

def go_to_chat(driver: PumaDriver, conversation: str):
    driver.click('//android.widget.ImageButton[@content-desc="Search"]')
    driver.send_keys('//android.widget.EditText[@text="Search"]', conversation)
    # TODO: check if no results, and validate if first result is good!
    driver.click('//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[1]')

@supported_version("12.0.1")
class Telegram(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the Telegram Messenger application.

    This class uses a state machine approach to manage transitions between different states
    of the Telegram user interface. It provides methods to navigate between states, validate states,
    and handle unexpected states or errors.
    """
    conversations_state = SimpleState(
        [CHAT_OVERVIEW_TITLE_HEADER, CHAT_OVERVIEW_NEW_CONVERSATION_BUTTON, CHAT_OVERVIEW_NEW_STORY_BUTTON],
        initial_state=True)
    chat_state = TeleGramChatState(parent_state=conversations_state)

    conversations_state.to(chat_state, go_to_chat)

    def __init__(self, device_udid, telegram_web_version: bool = False):
        package = TELEGRAM_WEB_PACKAGE if telegram_web_version else TELEGRAM_PACKAGE
        StateGraph.__init__(self, device_udid, package)


    @action(chat_state)
    def send_message(self, message: str, conversation: str = None):
        # self.driver.click(CHAT_STATE_MESSAGE_TEXTBOX)
        self.driver.send_keys(CHAT_STATE_MESSAGE_TEXTBOX, message)
        print('sent keys')
        # send_button = self.driver.get_element('//android.view.View[@content-desc="Send"]')
        # Telegrma has a horrible UI; the bounds of the send button are defined incorrectly so we need to click off-center
        location = self._find_button_location(0.8, 0.5, '//android.view.View[@content-desc="Send"]')
        self.driver.driver.tap([(location)])
        print('clicked send')

    def _find_button_location(self, width_ratio: float, height_ratio: float, xpath: str):
        send_button = self.driver.get_element(xpath)
        top_left = send_button.location['x'], send_button.location['y']
        size = send_button.size['height'], send_button.size['width']
        location = int(top_left[0] + width_ratio * size[1]), int(top_left[1] + height_ratio * size[0])
        print(f'clicking on {location}')
        return location