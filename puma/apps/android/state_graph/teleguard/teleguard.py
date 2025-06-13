from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.state_graph.google_camera.google_camera import GoogleCamera
from puma.apps.android.state_graph.teleguard import logger
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.action import action
from puma.state_graph.state_graph import StateGraph
from puma.state_graph.state import ContextualState, SimpleState, compose_clicks
from puma.state_graph.popup_handler import simple_popup_handler
from puma.apps.android.appium_actions import supported_version

APPLICATION_PACKAGE = 'ch.swisscows.messenger.teleguardapp'

# TODO: Move to separate xpaths file?
CONVERSATION_STATE_TELEGUARD_HEADER = '//android.view.View[@content-desc="TeleGuard"]'
CONVERSATION_STATE_HAMBURGER_MENU = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.view.View[3]'
CONVERSATION_STATE_SETTINGS_BUTTON = '//android.widget.ImageView[@content-desc="Settings"]'
CONVERSATION_STATE_ABOUT_BUTTON = '//android.widget.ImageView[@content-desc="About"]'
CONVERSATION_STATE_TELEGUARD_STATUS = '//android.view.View[@content-desc="Online"]|//android.view.View[contains(@content-desc, "Connection to server")]'

CHAT_STATE_CONVERSATION_NAME = ('//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.widget.ImageView[2][@content-desc]|'
                                '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.view.View[1][@content-desc]')
CHAT_STATE_TEXT_FIELD = '//android.widget.EditText'
CHAT_STATE_MICROPHONE_BUTTON = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[4]'
CHAT_STATE_SEND_BUTTON = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[3]'

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

@supported_version('4.0.7')
class TeleGuard(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the TeleGuard application.

    This class uses a state machine approach to manage transitions between different states
    of the TeleGuard user interface. It provides methods to navigate between states, validate states,
    and handle unexpected states or errors.
    """

    conversations_state = SimpleState( [CONVERSATION_STATE_TELEGUARD_HEADER, CONVERSATION_STATE_HAMBURGER_MENU, CONVERSATION_STATE_TELEGUARD_STATUS], initial_state=True)
    chat_state = TeleGuardChatState(parent_state=conversations_state)
    settings_state = SimpleState(['//android.view.View[@content-desc="Change TeleGuard ID"]'], parent_state=conversations_state)
    about_screen_state = SimpleState( ['//android.view.View[@content-desc="About"]', '//android.view.View[@content-desc=" Terms of use"]'], parent_state=conversations_state)

    conversations_state.to(chat_state, go_to_chat)
    conversations_state.to(settings_state, compose_clicks([CONVERSATION_STATE_HAMBURGER_MENU, CONVERSATION_STATE_SETTINGS_BUTTON], name='go_to_settings'))
    conversations_state.to(about_screen_state, compose_clicks([CONVERSATION_STATE_HAMBURGER_MENU, CONVERSATION_STATE_ABOUT_BUTTON], name='go_to_about'))

    def __init__(self, device_udid):
        """
        Initializes the TestFsm with a device UDID.

        This class provides an API for interacting with the TeleGuard application using Appium.
        It can be used with an emulator or a real device attached to the computer.

        :param device_udid: The unique device identifier for the Android device.
        """
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE)

    @action(chat_state)
    def send_message(self, msg: str, conversation: str = None):
        """
        Sends a message in the current chat conversation.

        :param msg: The message to send.
        :param conversation: The name of the conversation to send the message in.
        """
        self.driver.click(CHAT_STATE_TEXT_FIELD)
        self.driver.send_keys(CHAT_STATE_TEXT_FIELD, msg)
        self.driver.click(CHAT_STATE_SEND_BUTTON)

    @action(conversations_state)
    def add_contact(self, id: str):
        """
        Adds a contact by TeleGuard ID.

        :param id: The TeleGuard ID of the contact to add.
        """
        self.driver.click(CONVERSATION_STATE_HAMBURGER_MENU)
        self.driver.click('//android.widget.ImageView[@content-desc="Add contact"]')
        self.driver.send_keys('//android.widget.EditText', id)
        self.driver.click('//android.widget.Button[@content-desc="INVITE"]')

    @action(conversations_state)
    def accept_invite(self):
        """
        Accepts an invite from another user.

        If there are multiple invites, only the topmost invite in the UI will be accepted.
        """
        self.driver.swipe_to_click_element('//android.view.View[contains(@content-desc, "You have been invited")]')
        self.driver.click('//android.widget.Button[@content-desc="ACCEPT INVITE"]')

#TODO remove main
if __name__ == '__main__':
    t = TeleGuard('34281JEHN03866')
    c = GoogleCamera('34281JEHN03866')
    t.go_to_state(TeleGuard.settings_state)
    t.send_message("Hello Bob", conversation="bob")
    c.take_picture(front_camera=True)
    t.send_message("Hello Bob second message")
    c.take_picture()
    t.send_message("Test", conversation='TeleGuard')
    c.record_video(2, True)
    t.go_to_state(TeleGuard.about_screen_state)
    c.go_to_state(GoogleCamera.photo)
