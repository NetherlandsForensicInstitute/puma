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
    driver.click('//android.view.View[@resource-id="com.snapchat.android:id/friend_action_button2"]')

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
        content_desc = driver.get_element('//android.widget.TextView[@resource-id="com.snapchat.android:id/conversation_title_text_view"]').get_attribute('text')
        logger.info(f'getting content_desc {content_desc}')
        logger.info(f'conversation is {conversation}')

        return conversation in content_desc


class SnapchatChatSnapState(SimpleState, ContextualState):
    def __init__(self, parent_state):
        super().__init__(xpaths=['//android.view.View[@content-desc="New Story Button"]'],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True

        logger.info('getting content_desc')
        conversation_xpath = f'//androidx.recyclerview.widget.RecyclerView[@resource-id="com.snapchat.android:id/send_to_recycler_view"]//javaClass[@text="{conversation}"]'
        elements = driver.driver.find_elements(AppiumBy.XPATH, conversation_xpath)
        content_desc = elements[0].get_attribute("text")
        logger.info(f'getting content_desc {content_desc}')
        logger.info(f'conversation is {conversation}')
        logger.info(conversation in content_desc)

        return conversation in content_desc

class Snapchat(StateGraph):
    camera_state = SimpleState(['//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/camera_page"]'], initial_state=True)

    conversation_state = SimpleState(['//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/feed_new_chat"]'], parent_state=camera_state)
    chat_state = SnapchatChatState(parent_state=conversation_state)

    discard_state = SimpleState(['//android.widget.TextView[@resource-id="com.snapchat.android:id/alert_dialog_description"]'])
    photo_state = SimpleState(['//android.view.ViewGroup[@resource-id="com.snapchat.android:id/sent_to_button_label_mode_view"]'])
    snap_state = SnapchatChatSnapState(parent_state=photo_state)

    camera_state.to(conversation_state, compose_clicks(['//android.view.ViewGroup[@content-desc="Chat"]']))
    conversation_state.to(chat_state, go_to_chat)

    camera_state.to(photo_state, compose_clicks(['//android.widget.FrameLayout[@content-desc="Camera Capture"]']))
    photo_state.to(snap_state, compose_clicks(['//android.view.ViewGroup[@resource-id="com.snapchat.android:id/sent_to_button_label_mode_view"]'])) #//android.widget.ImageButton[@content-desc="Send"]

    # snap_state.to(photo_state, compose_clicks(['//android.view.View[@content-desc="Back arrow"]']))
    photo_state.to(discard_state, compose_clicks(['//android.widget.ImageButton[@content-desc="Discard"]']))
    discard_state.to(camera_state, compose_clicks(['//android.view.View[@resource-id="com.snapchat.android:id/discard_alert_dialog_discard_view"]']))


    def __init__(self, device_udid):
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)

    def _press_enter(self):
        enter_keycode = 66
        self.driver.driver.press_keycode(enter_keycode)

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

    @action(snap_state)
    def send_snap_to(self, recipients: [str] = None):
        if recipients:
            for recipient in recipients:
                self.driver.click(f'(//androidx.recyclerview.widget.RecyclerView[@resource-id="com.snapchat.android:id/send_to_recycler_view"]//javaClass[@text="{recipient}"])[1]')
        else:
            self.driver.click(f'//javaClass[@text="My Story · Friends Only"]/..')
        self.driver.click(f'//android.view.View[@content-desc="Send"]')



# TODO: continue with send snap and add the rest from the template and contributing for adding a new application
if __name__ == "__main__":
        bob = Snapchat(device_udid="34281JEHN03866")
        contact_charlie = "Charlie"
        group_bob = "Group Bob"

        bob.send_message("hi", contact_charlie)

        bob.send_snap_to([contact_charlie])

