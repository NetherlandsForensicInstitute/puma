from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.appium_actions import supported_version, AndroidAppiumActions

APPLICATION_PACKAGE = 'ch.swisscows.messenger.teleguardapp'

@supported_version("YOUR VERSION") #TODO
class TeleguardActions(AndroidAppiumActions):
    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for TeleGuard using Appium. Can be used with an emulator or real device attached to the computer.
        """
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      APPLICATION_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)
        self.package_name = APPLICATION_PACKAGE

    def _if_chat_go_to_chat(self, chat: str):
        if chat is not None:
            self.select_chat(chat)
            sleep(1)
        if not self._currently_in_conversation(chat):
            raise Exception('Expected to be in conversation screen now, but screen contents are unknown')

    def _currently_at_homescreen(self) -> bool:
        return (self.is_present('//android.view.View[@content-desc="TeleGuard"]') and
                self.is_present('//android.view.View[@content-desc="Online"]'))

    def _currently_in_conversation(self, chat) -> bool:
        # Teleguard doesn't contain very descriptive elements, so looking explicitly at the subject of the chat is the
        # only way to identify if you are in the conversation screen. TODO pydoc
        return self.is_present(f'//android.view.View[contains(lower-case(@content-desc), "{chat.lower()}")]')

    def return_to_homescreen(self, attempts=10):
        """
        Returns to the start screen of Telegram
        :param attempts: Number of attempts to return to home screen. Avoids an infinite loop when a popup occurs.
        """
        if self.driver.current_package != self.package_name:
            self.driver.activate_app(self.package_name)
        while not self._currently_at_homescreen() and attempts > 0:
            self.driver.back()
            attempts -= 1
        if attempts == 0 and not self._currently_at_homescreen():
            raise Exception('Tried to return to homescreen but ran out of attempts...')
        sleep(1)

    def select_chat(self, chat: str):
        """
        Opens a given conversation based on the (partial) name of a chat.
        For groups or channels, it is advised to use :meth:`TelegramActions.select_group` or
        :meth:`TelegramActions.select_channel`, as the matching is more explicit
        :param chat: (part of) the conversation name to open
        """
        self.return_to_homescreen()
        xpath = f'//android.widget.ImageView[contains(lower-case(@content-desc), "{chat.lower()}")]'

        self.driver.find_element(by=AppiumBy.XPATH, value=xpath).click()

    def send_message(self, message: str, chat: str = None):
        """
        Send a message in the current or given chat
        :param message: The text message to send
        :param chat: Optional: The chat conversation in which to send this message, if not currently in the desired chat
        """
        self._if_chat_go_to_chat(chat)
        text_box_el = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.EditText[contains(lower-case(@hint), "send a message")]')
        text_box_el.click()
        text_box_el.send_keys(message)
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[3]').click()
