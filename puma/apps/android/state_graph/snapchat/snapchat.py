from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.state_graph.snapchat import logger
from puma.state_graph.action import action
from puma.state_graph.app_template import APPLICATION_PACKAGE
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

APPLICATION_PACKAGE = 'com.snapchat.android'

CHAT_STATE_CONVERSATION_NAME = '//android.widget.TextView[@resource-id="com.snapchat.android:id/conversation_title_text_view"]'
CHAT_STATE_TEXT_FIELD = '//android.widget.EditText[@resource-id="com.snapchat.android:id/chat_input_text_field"]'

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
    xpath = f'//androidx.recyclerview.widget.RecyclerView[@resource-id="com.snapchat.android:id/recycler_view"]//javaClass[@text="{conversation}"]'
    driver.driver.find_elements(by=AppiumBy.XPATH, value=xpath)[-1].click()

class SnapchatChatState(SimpleState, ContextualState):
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
        super().__init__(xpaths=[CHAT_STATE_CONVERSATION_NAME, CHAT_STATE_TEXT_FIELD],
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

        logger.info('getting content_desc')
        content_desc = driver.get_element('//android.widget.TextView').get_attribute('content-desc')
        logger.info(f'getting content_desc {content_desc}')
        logger.info(f'conversation is {conversation}')

        return conversation in content_desc

class Snapchat(StateGraph):
    camera_state = SimpleState(['//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/camera_page"]'], initial_state=True)
    conversation_state = SimpleState(['//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/feed_new_chat"]'], parent_state=camera_state)
    chat_state = SnapchatChatState(parent_state=conversation_state)

    camera_state.to(conversation_state, compose_clicks(['//android.view.ViewGroup[@content-desc="Chat"]']))
    conversation_state.to(chat_state, go_to_chat)

    # TODO: continue with send snap and add the rest from the template and contributing for adding a new application

    def __init__(self, device_udid):
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)

    def _press_enter(self):
        enter_keycode = 66
        self.driver.press_keycode(enter_keycode)

    @action(chat_state)
    def send_message(self, msg: str, conversation: str = None):
        """
        Sends a message in the current chat conversation.

        :param msg: The message to send.
        :param conversation: The name of the conversation to send the message in.
        """
        self.driver.click(CHAT_STATE_TEXT_FIELD)
        self.driver.send_keys(CHAT_STATE_TEXT_FIELD, msg)
        self._press_enter()




if __name__ == "__main__":
        bob = Snapchat(device_udid="34281JEHN03866")
        contact_charlie = "Charlie"

        bob.go_to_state(bob.conversation_state)
        bob.go_to_state(bob.chat_state, conversation=contact_charlie)
        bob.send_message("hi", contact_charlie)

