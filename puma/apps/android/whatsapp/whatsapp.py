from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common import NoSuchElementException

from puma.apps.android.appium_actions import supported_version, AndroidAppiumActions
from puma.apps.android.whatsapp.whatsapp_common import WhatsAppCommon


@supported_version("2.24.25.78")
class WhatsappActions(WhatsAppCommon):

    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for WhatsApp Android using Appium. Can be used with an emulator or real device attached to the computer.
        """
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      'com.whatsapp',
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def change_profile_picture(self, photo_dir_name, index=1):
        self.return_to_homescreen()
        self.open_settings_you()
        self.driver.find_element(by=AppiumBy.ID, value=f'{self.app_package}:id/profile_info_edit_btn').click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[@text='Gallery']").click()
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.ImageButton[@content-desc="Folders"]').click()
        self.scroll_to_find_element(text_contains=photo_dir_name).click()
        sleep(1)
        self.driver.find_element(by=AppiumBy.XPATH, value=f'//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[5]/android.view.View[{index}]/android.view.View[2]/android.view.View').click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/ok_btn").click()

    def set_about(self, about_text: str):
        self.return_to_homescreen()
        self.open_settings_you()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/profile_info_status_card").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/status_tv_edit_icon").click()
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

    def send_media(self, directory_name, index=1, caption=None, view_once=False, chat: str = None):
        self._if_chat_go_to_chat(chat)
        # Go to gallery
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/input_attach_button").click()
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/pickfiletype_gallery_holder").click()

        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.ImageButton[@content-desc="Folders"]').click()
        try:
            self.swipe_to_find_element(xpath=f'//android.widget.TextView[@text="{directory_name}"]')
        except NoSuchElementException:
            print(f'The directory {directory_name} could not be found.')
            exit(-1)
        self.driver.find_element(by=AppiumBy.XPATH, value=f'//android.widget.TextView[@text="{directory_name}"]').click()
        sleep(0.5)
        try:
            self.driver.find_element(by=AppiumBy.XPATH, value=f'//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[4]/android.view.View[{index}]/android.view.View[2]/android.view.View').click()
        except NoSuchElementException:
            print(f'The media at index {index} could not be found. The index is likely too large or negative.')
            return -1
        sleep(0.5)
        self.driver.find_element(by=AppiumBy.XPATH, value=f'//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[5]/android.view.View[3]/android.widget.Button').click()

        if caption:
            sleep(0.5)
            # text_box = self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.TextView[contains(@content-desc, "photos or videos selected")]')
            text_box = self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/caption")
            text_box.send_keys(caption)
            # Clicking the text box after sending keys is required for Whatsapp to notice text has been inserted.
            text_box.click()
            self.driver.back()

        if view_once:
            self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/view_once_toggle").click()
            popup_button = f'//android.widget.Button[@resource-id="{self.app_package}:id/vo_sp_bottom_sheet_ok_button"]'
            if self.is_present(popup_button):
                self.driver.find_element(by=AppiumBy.XPATH, value=popup_button).click()
        sleep(1)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/send").click()
