from puma.apps.android.snapchat.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

APPLICATION_PACKAGE = 'com.snapchat.android'


def go_to_chat(driver: PumaDriver, conversation: str):
    """
    Navigates to a specific chat conversation in the application.

    This function constructs an XPath to locate and click on a conversation element
    based on the conversation name. It is designed to be used within a state transition
    to navigate to a specific chat state.

    :param driver: The PumaDriver instance used to interact with the application.
    :param conversation: The name of the conversation to navigate to.
    """

    driver.get_elements(CHAT_CONVERSATION.format(conversation=conversation))[-1].click()
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

        return driver.is_present(CONVERSATION_TITLE_TEXT.format(conversation=conversation.lower()))

class SnapchatChatSnapState(SimpleState, ContextualState):
    """
    A state representing a snap screen, a list of all conversations to send a snap to, in the application.

    This class extends both SimpleState and ContextualState to represent a snap screen
    and validate its context based on the conversation name.
    """

    def __init__(self, parent_state):
        """
        Initializes the SnapState with a parent state.

        :param parent_state: The parent state of this snap state.
        """
        super().__init__(xpaths=[NEW_STORY],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates the context of the snap state.

        This method checks if the current snap screen matches the expected conversation name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the conversation to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not conversation:
            return True

        return driver.is_present(CHAT_CONVERSATION_SEND_TO.format(conversation=conversation.lower()))


@supported_version('12.89.0.40')
class Snapchat(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the Snapchat application.

    This class uses a state machine approach to manage transitions between different states
    of the Snapchat user interface. It provides methods to navigate between states, validate states,
    and handle unexpected states or errors.
    """
    camera_state = SimpleState([CAMERA_PAGE], initial_state=True)
    conversation_state = SimpleState([FEED_NEW_CHAT], parent_state=camera_state)
    chat_state = SnapchatChatState(parent_state=conversation_state)
    captured_state = SimpleState([SENT_TO])
    caption_state = SimpleState([CAPTION_EDIT], parent_state=captured_state)
    snap_state = SnapchatChatSnapState(parent_state=captured_state)
    discard_state = SimpleState([ALERT_DIALOG_DESCRIPTION])

    camera_state.to(conversation_state, compose_clicks([CHAT_TAB], name='press_chat_tab'))
    conversation_state.to(chat_state, go_to_chat)
    camera_state.to(captured_state, compose_clicks([CAMERA_CAPTURE], name='press_camera_capture'))
    captured_state.to(caption_state, compose_clicks([FULL_SCREEN_SURFACE_VIEW], name='press_screen_surface'))
    captured_state.to(snap_state, compose_clicks([SENT_TO], name='press_sent_to'))
    captured_state.to(discard_state, compose_clicks([DISCARD_BUTTON], name='press_discard_button'))
    discard_state.to(camera_state, compose_clicks([DISCARD_ALERT_DIALOG_DISCARD_VIEW], name='press_discard_alert'))

    def __init__(self, device_udid):
        """
        Initializes Snapchat with a device UDID.

        This class provides an API for interacting with the Snapchat application.
        It can be used with an emulator or a real device attached to the computer.

        :param device_udid: The unique device identifier for the Android device.
        """
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)

    @action(chat_state)
    def send_message(self, message: str, conversation: str = None):
        """
        Sends a message in the specified chat conversation.

        :param message: The message to send.
        :param conversation: The name of the conversation to send the message in. If nothing is specified, the current chat will be used.
        """
        self.driver.click(CHAT_INPUT)
        self.driver.send_keys(CHAT_INPUT, message)
        self.driver.press_enter()

    @action(camera_state)
    def toggle_camera(self):
        """
        Toggles camera.
        Default state is front facing camera. After closing the app the camera is faced the same direction as it was when previously closed.
        """
        self.driver.click(TOGGLE_CAMERA)

    @action(camera_state)
    def take_photo(self, caption: str = None):
        """
        Takes a photo.

        :param caption: The caption to add on the photo.
        """
        self.driver.click(CAMERA_CAPTURE)
        if caption:
            self.driver.click(FULL_SCREEN_SURFACE_VIEW)
            caption_field = self.driver.get_element(CAPTION_EDIT)
            caption_field.send_keys(caption)
            self.driver.back()

    @action(snap_state)
    def send_snap_to(self, recipients: list[str]):
        """
        Sends a snap to recipients.

        :param recipients: The recipients to send the snap to.
        """
        for recipient in recipients:
            self.driver.click(RECIPIENTS_TO_ADD.format(recipient=recipient))
        self.driver.click(SEND_BUTTON)

    @action(snap_state)
    def send_snap_to_my_story(self):
        """
        Sends a snap to my story.
        """
        self.driver.click(MY_STORY)
        self.driver.click(SEND_BUTTON)
