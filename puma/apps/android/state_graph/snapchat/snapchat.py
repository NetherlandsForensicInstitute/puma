from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.state_graph.snapchat import logger
from puma.state_graph.action import action
from puma.state_graph.app_template import APPLICATION_PACKAGE
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

APPLICATION_PACKAGE = 'com.snapchat.android'

ALERT_DIALOG_DESCRIPTION = '//android.widget.TextView[@resource-id="com.snapchat.android:id/alert_dialog_description"]'
CAMERA_CAPTURE = '//android.widget.FrameLayout[@content-desc="Camera Capture"]'
CAMERA_PAGE = '//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/camera_page"]'
CAPTION_EDIT = '//android.widget.EditText[@resource-id="com.snapchat.android:id/caption_edit_text_view"]'
CHAT_INPUT = '//android.widget.EditText[@resource-id="com.snapchat.android:id/chat_input_text_field"]'
CHAT_TAB = '//android.view.ViewGroup[@content-desc="Chat"]'
CONVERSATION_TITLE = '//android.widget.TextView[@resource-id="com.snapchat.android:id/conversation_title_text_view"]'
DISCARD = '//android.widget.ImageButton[@content-desc="Discard"]'
DISCARD_ALERT_DIALOG_DISCARD_VIEW = '//android.view.View[@resource-id="com.snapchat.android:id/discard_alert_dialog_discard_view"]'
FEED_NEW_CHAT = '//android.widget.FrameLayout[@resource-id="com.snapchat.android:id/feed_new_chat"]'
FRIEND_ACTION = '//android.view.View[@resource-id="com.snapchat.android:id/friend_action_button2"]'
FULL_SCREEN_SURFACE_VIEW = '//android.view.View[@resource-id="com.snapchat.android:id/full_screen_surface_view"]'
MY_STORY = '//javaClass[@text="My Story · Friends Only"]/..'
NEW_STORY = '//android.view.View[@content-desc="New Story Button"]'
SEND = '//android.view.View[@content-desc="Send"]'
SENT_TO = '//android.view.ViewGroup[@resource-id="com.snapchat.android:id/sent_to_button_label_mode_view"]'
TOGGLE_CAMERA = '(//android.widget.ImageView[@resource-id="com.snapchat.android:id/camera_mode_icon_image_view"])[1]'

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
    driver.click(FRIEND_ACTION)

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
        super().__init__(xpaths=[CONVERSATION_TITLE, CHAT_INPUT],
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
        content_desc = driver.get_element(CONVERSATION_TITLE).get_attribute('text')
        logger.info(f'getting content_desc {content_desc}')
        logger.info(f'conversation is {conversation}')

        return conversation in content_desc

class SnapchatChatSnapState(SimpleState, ContextualState):
    def __init__(self, parent_state):
        super().__init__(xpaths=[NEW_STORY],
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
    camera_state = SimpleState([CAMERA_PAGE], initial_state=True)
    conversation_state = SimpleState([FEED_NEW_CHAT], parent_state=camera_state)
    chat_state = SnapchatChatState(parent_state=conversation_state)
    captured_state = SimpleState([SENT_TO])
    caption_state = SimpleState([CAPTION_EDIT], parent_state=captured_state)
    snap_state = SnapchatChatSnapState(parent_state=captured_state)
    discard_state = SimpleState([ALERT_DIALOG_DESCRIPTION])

    camera_state.to(conversation_state, compose_clicks([CHAT_TAB]))
    conversation_state.to(chat_state, go_to_chat)
    camera_state.to(captured_state, compose_clicks([CAMERA_CAPTURE]))
    captured_state.to(caption_state, compose_clicks([FULL_SCREEN_SURFACE_VIEW]))
    captured_state.to(snap_state, compose_clicks([SENT_TO]))
    captured_state.to(discard_state, compose_clicks([DISCARD]))
    discard_state.to(camera_state, compose_clicks([DISCARD_ALERT_DIALOG_DISCARD_VIEW]))

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
        self.driver.click(CHAT_INPUT)
        self.driver.send_keys(CHAT_INPUT, msg)
        self._press_enter()

    @action(camera_state)
    def toggle_camera(self):
        self.driver.click(TOGGLE_CAMERA)

    @action(camera_state)
    def take_photo(self, caption:str):
        self.driver.click(CAMERA_CAPTURE)
        if caption:
            self.driver.click(FULL_SCREEN_SURFACE_VIEW)
            caption_field = self.driver.driver.find_element(AppiumBy.XPATH,
                                                            CAPTION_EDIT)
            caption_field.send_keys(caption)
            self.driver.back()

    @action(snap_state)
    def send_snap_to(self, recipients: [str] = None):
        if recipients:
            for recipient in recipients:
                recipient_xpath = (
                    f'//androidx.recyclerview.widget.RecyclerView[@resource-id="com.snapchat.android:id/send_to_recycler_view"]'
                    f'//android.view.View[count(.//javaClass)=1]//javaClass[@text="{recipient}"]'
                )
                self.driver.click(recipient_xpath)
        else:
            self.driver.click(MY_STORY)
        self.driver.click(SEND)

if __name__ == "__main__":
        bob = Snapchat(device_udid="34281JEHN03866")
        contact_charlie = "Charlie"
        group_bob = "Group Bob"

        bob.send_message("hi", contact_charlie)
        bob.toggle_camera()
        bob.take_photo(caption="whoopwhoop")
        bob.send_snap_to(recipients=[contact_charlie])

