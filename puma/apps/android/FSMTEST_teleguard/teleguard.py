from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.FSMTEST_util.puma_driver import PumaDriver
from puma.apps.android.FSMTEST_util.puma_fsm import SimpleState, State, PumaUIGraph, action, simple_popup_handler, \
    FState

APPLICATION_PACKAGE = 'ch.swisscows.messenger.teleguardapp'
HAMBURGER_MENU = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.view.View[3]'

class ConversationsState(SimpleState):

    def __init__(self):
        super().__init__("Conversation screen", ['//android.view.View[@content-desc="TeleGuard"]', HAMBURGER_MENU, '//android.view.View[@content-desc="Online"]|//android.view.View[contains(@content-desc, "Connection to server")]'], initial_state=True)

    def go_to_settings(self, driver: PumaDriver):
        print(f"click on settings button with driver {driver}")
        driver.click(HAMBURGER_MENU)
        driver.click('//android.widget.ImageView[@content-desc="Settings"]')

    def go_to_chat(self, driver: PumaDriver, conversation:str):
        """
        Switches from chats to a chat screen
        """
        xpath = f'//android.widget.ImageView[contains(lower-case(@content-desc), "{conversation.lower()}")] | \
                        //android.view.View[contains(lower-case(@content-desc), "{conversation.lower()}")]'

        driver.driver.find_elements(by=AppiumBy.XPATH, value=xpath)[-1].click() #TODO Fix this, there should a ticket somewhere (#104)
        print(f'Clicking on conversation {conversation} with driver {driver}')

class ChatState(SimpleState, FState):
    def __init__(self, parent_state):
        super().__init__("Chat screen", xpaths=['//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[4]'],
                         parent_state=parent_state)

    def variable_validate(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True
        content_desc = (driver.get_element(
            '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.widget.ImageView[2]')
                        .get_attribute('content-desc'))
        return conversation.lower() in content_desc.lower()


class TestFsm(PumaUIGraph):
    # TODO: infer name from attribute name (here: state1)
    conversations = ConversationsState()
    chat_screen = ChatState(conversations)
    chat_management = SimpleState("Chat management", ['//android.widget.ImageView[@content-desc="All chat settings"]'], parent_state=chat_screen)
    setting_screen = SimpleState("Settings", ['//android.view.View[@content-desc="Change TeleGuard ID"]'], parent_state=conversations)

    conversations.to(chat_screen, conversations.go_to_chat)
    chat_screen.to(chat_management, lambda x: None)
    conversations.to(setting_screen, conversations.go_to_settings)

    def __init__(self, device_udid):
        """
        Class with an API for TeleGuard using Appium. Can be used with an emulator or real device attached to the computer.
        """
        self.driver = PumaDriver(device_udid, APPLICATION_PACKAGE)
        PumaUIGraph.__init__(self, self.driver)
        self.add_popup_handler(simple_popup_handler('bah'))

    @action(chat_screen)
    def send_message(self, msg: str, conversation: str = None):
        """
        Sends a message
        """
        print(f"Sending message {msg}")
        text_field = '//android.widget.EditText'
        self.driver.click(text_field)
        self.driver.send_keys(text_field, msg)
        # text_box_el.click()
        # text_box_el.send_keys(msg)
        self.driver.click('//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[3]')


if __name__ == '__main__':
    t = TestFsm('34281JEHN03866')
    t.go_to_state(TestFsm.setting_screen)
    t.send_message("Hello Bob", conversation="bob")
    t.send_message("Hello Bob second message")
    t.send_message("Test", conversation='TeleGuard')
