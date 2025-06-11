from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.FSMTEST_util.puma_driver import PumaDriver
from puma.apps.android.FSMTEST_util.puma_fsm import SimpleState, PumaUIGraph, action, simple_popup_handler, FState

APPLICATION_PACKAGE = 'ch.swisscows.messenger.teleguardapp'

CONVERSATION_STATE_TELEGUARD_HEADER = '//android.view.View[@content-desc="TeleGuard"]'
CONVERSATION_STATE_HAMBURGER_MENU = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.view.View[3]'
CONVERSATION_STATE_SETTINGS_BUTTON = '//android.widget.ImageView[@content-desc="Settings"]'
CONVERSATION_STATE_ABOUT_BUTTON = '//android.widget.ImageView[@content-desc="About"]'
CONVERSATION_STATE_TELEGUARD_STATUS = '//android.view.View[@content-desc="Online"]|//android.view.View[contains(@content-desc, "Connection to server")]'

CHAT_STATE_CONVERSATION_NAME = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.widget.ImageView[2][@content-desc]'
CHAT_STATE_TEXT_FIELD = '//android.widget.EditText'
CHAT_STATE_MICROPHONE_BUTTON = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[4]' # TODO: This is gone, when draft message is present. Use something else.
CHAT_STATE_SEND_BUTTON = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[3]'


def go_to_settings(driver: PumaDriver):
    print(f"click on settings button with driver {driver}")
    driver.click(CONVERSATION_STATE_HAMBURGER_MENU)
    driver.click(CONVERSATION_STATE_SETTINGS_BUTTON)


def go_to_chat(driver: PumaDriver, conversation: str):
    xpath = f'//android.widget.ImageView[contains(lower-case(@content-desc), "{conversation.lower()}")] | \
                    //android.view.View[contains(lower-case(@content-desc), "{conversation.lower()}")]'
    driver.driver.find_elements(by=AppiumBy.XPATH, value=xpath)[
        -1].click()  # TODO Fix this, there should a ticket somewhere (#104)
    print(f'Clicking on conversation {conversation} with driver {driver}')


def go_to_about(driver: PumaDriver):
    driver.click(CONVERSATION_STATE_HAMBURGER_MENU)
    driver.click(CONVERSATION_STATE_ABOUT_BUTTON)


class ChatState(SimpleState, FState):
    def __init__(self, parent_state):
        super().__init__("Chat screen",
                         xpaths=[CHAT_STATE_CONVERSATION_NAME, CHAT_STATE_MICROPHONE_BUTTON, CHAT_STATE_TEXT_FIELD],
                         parent_state=parent_state)

    def variable_validate(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True

        content_desc = (driver.get_element(CHAT_STATE_CONVERSATION_NAME).get_attribute('content-desc'))
        return conversation.lower() in content_desc.lower()


class TestFsm(PumaUIGraph):
    # TODO: infer name from attribute name (here: state1)
    conversations_state = SimpleState("Conversation screen", [CONVERSATION_STATE_TELEGUARD_HEADER, CONVERSATION_STATE_HAMBURGER_MENU, CONVERSATION_STATE_TELEGUARD_STATUS], initial_state=True)
    chat_state = ChatState(conversations_state)
    settings_state = SimpleState("Settings", ['//android.view.View[@content-desc="Change TeleGuard ID"]'], parent_state=conversations_state)
    about_screen_state = SimpleState("About", ['//android.view.View[@content-desc="About"]', '//android.view.View[@content-desc=" Terms of use"]'], parent_state=conversations_state)

    conversations_state.to(chat_state, go_to_chat)
    conversations_state.to(settings_state, go_to_settings)
    conversations_state.to(about_screen_state, go_to_about)

    def __init__(self, device_udid):
        """
        Class with an API for TeleGuard using Appium. Can be used with an emulator or real device attached to the computer.
        """
        PumaUIGraph.__init__(self, device_udid, APPLICATION_PACKAGE)
        self.add_popup_handler(simple_popup_handler('bah'))

    @action(chat_state)
    def send_message(self, msg: str, conversation: str = None):
        """
        Sends a message
        """
        print(f"Sending message {msg}")
        self.driver.click(CHAT_STATE_TEXT_FIELD)
        self.driver.send_keys(CHAT_STATE_TEXT_FIELD, msg)
        self.driver.click(CHAT_STATE_SEND_BUTTON)

    @action(conversations_state)
    def add_contact(self, id: str):
        """
        Add a contact by TeleGuard ID.
        :param id: The teleguard ID
        """
        self.driver.click(CONVERSATION_STATE_HAMBURGER_MENU)
        self.driver.click('//android.widget.ImageView[@content-desc="Add contact"]')
        self.driver.send_keys('//android.widget.EditText', id)
        self.driver.click('//android.widget.Button[@content-desc="INVITE"]')

    @action(conversations_state)
    def accept_invite(self):
        """
        Accept an invite from another user. If you have multiple invites, only one invite will be accepted (the topmost
        invite in the UI).
        """
        self.driver.swipe_to_click_element('//android.view.View[contains(@content-desc, "You have been invited")]')
        self.driver.click('//android.widget.Button[@content-desc="ACCEPT INVITE"]')


if __name__ == '__main__':
    t = TestFsm('34281JEHN03866')
    t.draw_graph()
    # t.go_to_state(TestFsm.settings_state)
    # t.send_message("Hello Bob", conversation="bob")
    # t.send_message("Hello Bob second message")
    # t.send_message("Test", conversation='TeleGuard')
    # t.go_to_state(TestFsm.about_screen_state)
