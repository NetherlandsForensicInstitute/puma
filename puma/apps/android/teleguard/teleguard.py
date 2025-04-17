import inspect
from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.appium_actions import supported_version, AndroidAppiumActions
from puma.apps.android.teleguard import logger

APPLICATION_PACKAGE = 'ch.swisscows.messenger.teleguardapp'

@supported_version("4.0.7")
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
        """
        Go to chat if supplied.
        :param chat: Name of the chat to go to, this is either the contact name or the group name.
        """
        if chat is None:
            logger.warning("No chat was supplied. Assuming you are in the correct conversation screen now.")
        else:
            self.select_chat(chat)
            sleep(1)
            if not self._currently_in_conversation(chat):
                raise Exception('Expected to be in conversation screen now, but screen contents are unknown')


    def _currently_at_homescreen(self) -> bool:
        """
        Check whether currently at homescreen of the application.
        :return: boolean if at homescreen
        """
        return (self.is_present('//android.view.View[@content-desc="TeleGuard"]') and
                self.is_present('//android.view.View[@content-desc="Online"]'))

    def _currently_in_conversation(self, chat: str) -> bool:
        """
        Check if currently in a given conversation.
        :return: boolean if in conversation screen or not
        """
        # TeleGuard doesn't contain very descriptive elements, so looking explicitly at the subject of the chat is the
        # only way to identify if you are in the conversation screen.
        return self.is_present(f'//android.view.View[contains(lower-case(@content-desc), "{chat.lower()}")]')

    def return_to_homescreen(self, attempts: int = 10):
        """
        Returns to the start screen of Telegram.
        :param attempts: Number of attempts to return to home screen. Avoids an infinite loop when a popup occurs.
        """
        while not self._currently_at_homescreen() and attempts > 0:
            if self.driver.current_package != self.app_package:
                self.activate_app()
            self.driver.back()
            attempts -= 1
        if not self._currently_at_homescreen():
            raise Exception('Tried to return to homescreen but ran out of attempts...')
        sleep(0.5)

    def select_chat(self, chat: str):
        """
        Opens a given conversation based on the (partial) name of a chat.
        Matching is case-insensitive.
        :param chat: (part of) the conversation name to open
        """
        self.return_to_homescreen()
        xpath = f'//android.widget.ImageView[contains(lower-case(@content-desc), "{chat.lower()}")] | \
        //android.view.View[contains(lower-case(@content-desc), "{chat.lower()}")]'

        self.driver.find_element(by=AppiumBy.XPATH, value=xpath).click()

    def send_message(self, message: str, chat: str = None):
        """
        Send a message in the current or given chat.
        It is recommended to not use the chat param when already in the conversation, as using it will always cause
        puma to navigate out and back into the conversation.
        :param message: The text message to send
        :param chat: Optional: The chat conversation in which to send this message, if not currently in the desired chat
        """
        self._if_chat_go_to_chat(chat)
        text_box_el = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.EditText[contains(lower-case(@hint), "send a message")]')
        text_box_el.click()
        text_box_el.send_keys(message)
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[3]').click()

    def add_contact(self, id: str):
        """
        Add a contact by TeleGuard ID.
        :param id: The teleguard ID
        """
        self.return_to_homescreen()
        hamburger = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.view.View[3]')
        hamburger.click()
        add_contact_btn = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.ImageView[@content-desc="Add contact"]')
        add_contact_btn.click()
        text_box_el = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.EditText')
        text_box_el.send_keys(id)
        invite_btn = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.Button[@content-desc="INVITE"]')
        invite_btn.click()

    def accept_invite(self):
        """
        Accept an invite from another user. If you have multiple invites, only one invite will be accepted (the topmost
        invite in the UI).
        """
        self.return_to_homescreen()
        self.swipe_to_find_element('//android.view.View[contains(@content-desc, "You have been invited")]').click()
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.Button[@content-desc="ACCEPT INVITE"]').click()
