from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy
from puma.apps.android.appium_actions import AndroidAppiumActions, supported_version

SNAPCHAT_PACKAGE = 'com.snapchat.android'
SNAPCHAT_DEFAULT_ACTIVITY = '.LandingPageActivity'


@supported_version("12.90.0.46")
class SnapchatActions(AndroidAppiumActions):
    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for Snapchat Android using Appium. Can be used with an emulator or real device attached to the computer.
        """
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      SNAPCHAT_PACKAGE,
                                      SNAPCHAT_DEFAULT_ACTIVITY,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def _currently_at_homescreen(self) -> bool:
        return self.is_present(
            '//android.widget.LinearLayout[@resource-id="com.snapchat.android:id/ngs_navigation_bar"]') \
            and not self.is_present('//*[@text="View Profile"]')

    def _currently_in_conversation_overview(self) -> bool:
        return self.is_present(
            '//android.widget.TextView[@resource-id="com.snapchat.android:id/hova_page_title" and @text="Chat"]')

    def _currently_on_top_of_conversation_overview(self) -> bool:
        """
        Check if the current position is at the top of the conversation view.
        """
        on_top = False
        header_patterns = ["Unread", "Groups", "Unreplied"]
        for pattern in header_patterns:
            if self.is_present(f'//android.widget.TextView[lower-case(@content-desc)="{pattern.lower()}"]'):
                on_top = True
                break
        return on_top

    def _currently_in_conversation(self) -> bool:
        return self.is_present(
            '//android.widget.EditText[@resource-id="com.snapchat.android:id/chat_input_text_field"]')

    def _currently_in_camera_tab(self) -> bool:
        """
        Check if the current position is the camera tab.
        The camera button is checked, but this element also occurs in the camera view when sending a photo to a contact.
        Thus, an additional check is needed if "Send To" is not present is required.
        :return:
        """
        return (
                self.is_present('//android.widget.FrameLayout[@content-desc="Camera Capture"]') and not
                self.is_present('//android.widget.TextView[@text="Send To"]')
        )

    def _go_to_main_tab(self, tab_name: str):
        """
        Navigate to one of the main tabs.
        :param tab_name: One of the main tabs of snapchat: Map, Chat, Camera, Stories, or Spotlight
        """
        if self.driver.current_package != SNAPCHAT_PACKAGE:
            self.driver.activate_app(SNAPCHAT_PACKAGE)
        while not self._currently_at_homescreen():
            self.driver.back()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value=f'//android.widget.LinearLayout[@resource-id="com.snapchat.android:id/ngs_navigation_bar"]/android.view.ViewGroup[@content-desc="{tab_name}"]').click()

    #TODO create a separate function for each tab, so the user cannot make any typos
    def go_to_conversation_tab(self):
        """
        Navigate to the top of the conversation tab.
        When tapping "navigate to chat" when already in the conversation
        tab, the focus shifts down to the Quick Add section. This poses a problem when selecting a specific
        conversation that is out of view. This method makes sure to be at the top
        """
        if not self._currently_in_conversation_overview():
            self._go_to_main_tab("Chat")
        if not self._currently_on_top_of_conversation_overview():
            self._go_to_main_tab("Chat")

    def go_to_camera_tab(self):
        """
        Navigate to camera tab.
        """
        if not self._currently_in_camera_tab():
            self._go_to_main_tab("Camera")

    def select_chat(self, chat_subject: str):
        """
        Opens a given conversation.
        :param chat_subject: the name of the conversation to open
        """
        self.go_to_conversation_tab()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value=f'//javaClass[contains(lower-case(@text), "{chat_subject.lower()}")]/..').click()

    def _if_chat_go_to_chat(self, chat: str):
        if chat is not None:
            self.select_chat(chat)
        sleep(1)
        if not self._currently_in_conversation():
            raise Exception('Expected to be in conversation screen now, but screen contents are unknown')

    def send_message(self, message: str, chat: str = None):
        """
        Sends a text message, either in the current conversation, or in a given conversation.
        :param message: the message to send
        :param chat: optional: the conversation in which to send the message. If not used, it is assumed the
                     conversation is already opened.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.EditText[@resource-id="com.snapchat.android:id/chat_input_text_field"]') \
            .send_keys(message)
        self._press_enter()

    def _press_enter(self):
        enter_keycode = 66
        self.driver.press_keycode(enter_keycode)

    def send_snap(self, recipients: [str] = None, caption: str = None, front_camera: bool = True):
        """
        Sends a snap (picture), either to one or more contacts, or posts it to `My story`
        :param recipients: Optional: a list of recipients to send the snap to
        :param caption: Optional: a caption to set on the snap
        :param front_camera: Optional: whether or not to use the front camera (True by default)
        """
        # go to camera and snap picture
        self.go_to_camera_tab()
        if not front_camera:
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.view.ViewGroup[@content-desc="Flip Camera"]').click()
            sleep(0.5)
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.FrameLayout[@content-desc="Camera Capture"]').click()
        # write caption if needed
        if caption:
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.view.View[@resource-id="com.snapchat.android:id/full_screen_surface_view"]').click()
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.EditText[@resource-id="com.snapchat.android:id/caption_edit_text_view"]').send_keys(
                caption)
            self.driver.back()
        # press send
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.ImageButton[lower-case(@content-desc)="send"]').click()

        # select recipients, or post as story, and send
        if recipients:
            for recipient in recipients:
                self.driver.find_element(by=AppiumBy.XPATH,
                                         value=f'//javaClass[lower-case(@text) ="{recipient.lower()}"]').click()
        else:
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//javaClass[lower-case(@text)="my story · friends only"]/..').click()
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.view.View[lower-case(@content-desc)="send"]').click()
