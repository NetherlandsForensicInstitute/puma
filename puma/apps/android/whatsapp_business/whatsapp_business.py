from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common import NoSuchElementException
from typing_extensions import deprecated

from puma.apps.android.appium_actions import supported_version, AndroidAppiumActions
from puma.apps.android.whatsapp.whatsapp_common import WhatsAppCommon


@deprecated('This class does not use the Puma state machine, and will therefore not be maintained. ' +
            'If you want to add functionality, please rewrite this class using StateGraph as the abstract base class.')
@supported_version("2.25.24.78")
class WhatsappBusinessActions(WhatsAppCommon):

    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for WhatsApp for Business Android using Appium. Can be used with an emulator or real device attached to the computer.
        """
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      'com.whatsapp.w4b',
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def change_profile_picture(self, photo_dir_name, index=1):
        self.return_to_homescreen()
        self.open_settings_you()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageView[@content-desc="Edit photo"]').click()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.TextView[@resource-id="android:id/text1" and @text="Add or edit profile photo"]').click()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.TextView[@resource-id="com.whatsapp.w4b:id/row_text" and @text="Gallery"]').click()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageButton[@content-desc="Folders"]').click()
        WhatsAppCommon._find_media_in_folder(self, photo_dir_name, index)
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.Button[@resource-id="com.whatsapp.w4b:id/ok_btn"]').click()

    def set_about(self, about_text: str):
        self.return_to_homescreen()
        self.open_settings_you()
        self.swipe_to_find_element(f'//android.widget.TextView[@text="About"]').click()
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.ImageView[@content-desc="edit"]').click()
        text_box = self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/edit_text")
        text_box.click()
        text_box.clear()
        text_box.send_keys(about_text)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/save_button").click()

    def leave_group(self, group_name):
        self.select_chat(group_name)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/conversation_contact").click()
        self.scroll_to_find_element(text_equals="Exit group").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//android.widget.Button[@text='Exit group']").click()
        self.return_to_homescreen()

    def send_media(self, directory_name, index=1, caption=None, chat: str = None):
        self._if_chat_go_to_chat(chat)
        # Go to gallery
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/input_attach_button").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/pickfiletype_gallery_holder").click()

        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageButton[@content-desc="Folders"]').click()
        WhatsAppCommon._find_media_in_folder(self, directory_name, index)
        sleep(0.5)
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value=f'//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[5]/android.view.View[3]/android.widget.Button').click()

        if caption:
            sleep(0.5)
            # text_box = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.TextView[contains(@content-desc, "photos or videos selected")]')
            text_box = self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/caption")
            text_box.send_keys(caption)
            # Clicking the text box after sending keys is required for Whatsapp to notice text has been inserted.
            text_box.click()
            self.driver.back()

        sleep(1)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/send").click()
