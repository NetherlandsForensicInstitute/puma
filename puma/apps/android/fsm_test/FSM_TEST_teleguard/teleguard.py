from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy
from statemachine import StateMachine
from statemachine.transition_list import TransitionList

from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version
from puma.apps.android.fsm_test.fsm.puma_fsm import PumaState
from puma.apps.android.fsm_test.util.fsm_util import make_back_action, action, transition, validation

APPLICATION_PACKAGE = 'ch.swisscows.messenger.teleguardapp'

@supported_version("4.0.7")
class TeleguardFSM(StateMachine):
    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for TeleGuard using Appium. Can be used with an emulator or real device attached to the computer.
        """
        StateMachine.__init__(self)
        self.appium_actions = AndroidAppiumActions(
                                      device_udid,
                                      APPLICATION_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)
        self.driver = self.appium_actions.driver
        self.package_name = APPLICATION_PACKAGE
        self.initial_switch()

    back = TransitionList()
    enter_state = PumaState(initial=True)
    chats = PumaState()
    chat = PumaState(parent=make_back_action(back, chats))

    initial_switch = (enter_state.to(chats))

    open_chat = (
        chats.to(chat)
    )

    @action(chat, lambda *args: TeleguardFSM.check_current_chat(args[0], args[1]))
    def send_message(self, to: str, msg: str):
        """
        Sends a message
        """
        text_box_el = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.EditText[contains(lower-case(@hint), "send a message")]')
        text_box_el.click()
        text_box_el.send_keys(msg)
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[3]').click()

    @transition
    def before_open_chat(self, *args, **kwargs):
        """
        Switches from chats to a chat screen
        """
        xpath = f'//android.widget.ImageView[contains(lower-case(@content-desc), "{args[1].lower()}")] | \
                //android.view.View[contains(lower-case(@content-desc), "{args[1].lower()}")]'

        self.driver.find_elements(by=AppiumBy.XPATH, value=xpath)[-1].click()

    @transition
    def before_back(self, *args, **kwargs):
        """
        Uses the back functionality of Android
        """
        self.driver.back()

    @validation
    def on_enter_chats(self, *args):
        print('Entered chats validation')
        return self.appium_actions.is_present('//android.view.View[@content-desc="Online"]') and self.appium_actions.is_present('//android.view.View[@content-desc="TeleGuard"]')
        

    @validation
    def on_enter_chat(self, *args):
        return self.appium_actions.is_present(f'//android.view.View[contains(lower-case(@content-desc), "{args[1].lower()}")]')

    @staticmethod
    def check_current_chat(self, to: str):
        return self.appium_actions.is_present(f'//android.view.View[contains(lower-case(@content-desc), "{to.lower()}")]')


if __name__ == '__main__':
    t = TeleguardFSM('34281JEHN03866')

    t.send_message('bob', 'testing')
    t.send_message('TeleGuard', 'test')
