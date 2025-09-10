import re
from time import sleep
from typing import Dict, List, Union

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By

from puma.apps.android import log_action
from puma.apps.android.appium_actions import supported_version, AndroidAppiumActions
from puma.apps.android.whatsapp.whatsapp_common import WhatsAppCommon


@supported_version("2.24.25.78")
class WhatsappBusinessActions(WhatsAppCommon):
    def leave_group(self, group_name):
        self.select_chat(group_name)
        self.driver.find_element(by=AppiumBy.ID, value=f"{self.app_package}:id/conversation_contact").click()
        self.scroll_to_find_element(text_equals="Exit group").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//android.widget.Button[@text='Exit group']").click()
        self.return_to_homescreen()


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
                                      'com.whatsapp.w4b',
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    @log_action
    def open_settings_you(self):
        """
        Open personal settings (or profile).
        """
        self.return_to_homescreen()
        self.open_more_options()
        # Improvement possible: get all elements and filter on text=settings
        self.driver.find_element(by=AppiumBy.XPATH, value=
        "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.ListView/android.widget.LinearLayout[8]/android.widget.LinearLayout").click()
        self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="You").click()
