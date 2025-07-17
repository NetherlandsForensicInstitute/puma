from time import sleep
from typing import Dict, Optional

from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android import log_action
from puma.apps.android.appium_actions import supported_version, AndroidAppiumActions

TELEGRAM_PACKAGE = 'org.telegram.messenger'
TELEGRAM_WEB_PACKAGE = 'org.telegram.messenger.web'


@supported_version("11.9.0")
class TelegramActions(AndroidAppiumActions):

    def __init__(self,
                 device_udid,
                 telegram_web_version: bool = False,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for Telegram Android using Appium. Can be used with an emulator or real device attached to the
        computer.
        This class can be used for both the Play Store version and the version found at telegram.org. When using the
        latter however, you need to use the `telegram_web_version` parameter, and set it to True.
        """
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      TELEGRAM_WEB_PACKAGE if telegram_web_version else TELEGRAM_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def _currently_at_homescreen(self, **kwargs) -> bool:
        return self.is_present('//android.widget.FrameLayout[@content-desc="New Message"]', **kwargs)

    def _currently_in_conversation(self, **kwargs) -> bool:
        return self.is_present('//android.widget.ImageView[@content-desc="Emoji, stickers, and GIFs"]', **kwargs)

    def _currently_in_camera(self, **kwargs) -> bool:
        return self.is_present('//android.widget.Button[lower-case(@content-desc)="shutter"]', **kwargs)

    def _currently_in_call(self, **kwargs) -> bool:
        return self.is_present('//android.widget.Button[lower-case(@text)="end call"]', **kwargs)

    def _currently_in_active_call(self, **kwargs) -> bool:
        """
        Returns true if currently in a call that is in actual progress (meaning: the other party answered the call).
        """
        return self.is_present('//android.widget.LinearLayout[@content-desc="Encryption key of this call"]', **kwargs)

    def _load_conversation_titles(self):
        while True:
            xpath = "//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[not(@content-desc)]"
            convos = self.driver.find_elements(by=AppiumBy.XPATH, value=xpath)
            if len(convos) == 0:
                break
            print('some conversations still do not have a title loaded, clicking...')
            convos[0].click()
            self.driver.back()
            if not self._currently_at_homescreen():
                self.driver.back()
        print('all conversations loaded!')

    def return_to_homescreen(self, attempts: int = 10, try_restart: bool = True):
        """
        Returns to the start screen of Telegram
        :param attempts: Number of attempts to return to home screen. Avoids an infinite loop when a popup occurs.
        """
        attempt = 0
        while not self._currently_at_homescreen() and attempt < attempts:
            if self.driver.current_package != self.app_package:
                self.activate_app()
            self.driver.back()
            attempt += 1
        if not self._currently_at_homescreen():
            if try_restart:
                self.restart_app()
                self.return_to_homescreen(attempts, False)
            else:
                raise Exception('Tried to return to homescreen but ran out of attempts...')
        self._load_conversation_titles()
        sleep(1)

    @log_action
    def start_new_chat(self, chat: str):
        self.return_to_homescreen()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.FrameLayout[@content-desc="New Message"]').click()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageButton[@content-desc="Search"]').click()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.EditText[@text="Search"]').send_keys(chat)
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value=f'//android.view.ViewGroup[starts-with(lower-case(@text), "{chat.lower()}")]').click()

    @log_action
    def select_chat(self, chat: str | int):
        """
        Opens a given conversation based on the (partial) name of a chat, or opens the chat at the passed index
        Note that the index is 1 based, so the first chat is index 1.
        For groups or channels, it is advised to use :meth:`TelegramActions.select_group` or
        :meth:`TelegramActions.select_channel`, as the matching is more explicit
        :param chat: (part of) the conversation name to open or the 1-based index of the chat to open
        """
        self.return_to_homescreen()
        if type(chat) is str:
            xpath = f'//android.view.ViewGroup[starts-with(lower-case(@content-desc), "{chat.lower()}")]'
        elif type(chat) is int:
            xpath = f'//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[{chat}]'
        else:
            raise ValueError(f'Argument was of type {type(chat)}, but needs to be str or int')

        self.driver.find_element(by=AppiumBy.XPATH, value=xpath).click()
        if not self._currently_in_conversation(implicit_wait=1):
            raise RuntimeError("Conversation was not opened after clicking the conversation")

    @log_action
    def select_group(self, group_name: str):
        """
        Opens a given conversation based on the exact name of a group.
        :param group_name: Exact group name to open
        """
        self.select_chat(f'Group. {group_name}')

    @log_action
    def select_channel(self, channel_name: str):
        """
        Opens a given conversation based on the exact name of a channel.
        :param channel_name: Exact channel name to open
        """
        self.select_chat(f'Channel. {channel_name}')

    @log_action
    def send_message(self, message: str, chat: str | int):
        """
        Send a message in the current or given chat
        :param message: The text message to send
        :param chat: Optional: The chat conversation in which to send this message, if not currently in the desired chat. This is either the (partial) chat name or the index of the chat on the home screen.
        """
        self._if_chat_go_to_chat(chat)
        message_editText_xpath = '//android.widget.EditText[@text="Message" or @hint="Message"]'
        message_editText = self.driver.find_element(by=AppiumBy.XPATH, value=message_editText_xpath)
        message_editText.clear()
        message_editText.send_keys(message)

        # The actual send button is not in the same place as the element. The button is at about 75% of the box.
        # We adjust the location of the click from the middle to the right of the box.
        # TODO: clicking the correct spot in the bounding box is no longer necessary because the click box is now the same size as the button (issue 97)
        location = self._find_button_location(0.75, 0.5, '//android.view.View[@content-desc="Send"]')
        self.driver.tap([(location)])

    @log_action
    def reply_to_message(self, message_to_reply_to: str, reply: str, chat: str = None):
        """
        Send a text message as a reply to a previous message.
        This method will scroll up until the given message text is found, select that message, and reply to it
        :param message_to_reply_to: the message to reply to
        :param reply: The text message that will be sent as a reply
        :param chat: Optional: The chat conversation in which to send this message, if not currently in the desired chat
        """
        try:
            self._tap_message(message_to_reply_to, chat)
        except:
            raise Exception(f'Failed to scroll to message "{message_to_reply_to}", does it exist?')
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.TextView[@text="Reply"]').click()
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.EditText').send_keys(reply)
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.view.View[@content-desc="Send"]').click()

    @log_action
    def emoji_reply_to_message(self, message_to_respond_to: str, emoji_to_respond_with: str = '👍', chat: str = None):
        """
        Send emoji response to a previous message.
        This method will scroll up until the given message text is found, select that message, and reply to it
        :param message_to_reply_to: the message to reply to
        :param emoji_to_respond_with: the emoji with which to respond. Optional, by default '👍'
        :param chat: Optional: The chat conversation in which to send this message, if not currently in the desired chat
        """
        self._tap_message(message_to_respond_to, chat)
        if self.is_present(f'//android.widget.FrameLayout[@text="{emoji_to_respond_with}"]', implicit_wait=2):
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value=f'//android.widget.FrameLayout[@text="{emoji_to_respond_with}"]').click()
        else:
            print(f'ERROR: emoji {emoji_to_respond_with} does not exist on screen!')
            self.driver.back()

    def _tap_message(self, message_to_tap, chat):
        self._if_chat_go_to_chat(chat)
        message = self.scroll_to_find_element(text_contains=message_to_tap)
        # we want to click the middle right part of the message to open the menu
        x = message.location['x'] + message.size['width'] - 50
        y = message.location['y'] + message.size['height'] / 2
        print(f'Tapping screen at ({x},{y})')
        self.driver.tap([(x, y)])

    @log_action
    def take_and_send_picture(self,
                              chat: str = None,
                              caption: str = None,
                              wait_time: int = 1,
                              front_camera: bool = False):
        """
        Opens the embedded camera in the Telegram app, takes a picture, and sends it.
        :param chat: Optional: the conversation in which to send the picture. If not used, we assume a conversation is opened
        :param caption: Optional: a caption to include with the picture
        :param wait_time: Optional: time to wait (in seconds) after opening the camera before taking a picture. Default 1s
        :param front_camera: Optional: whether to use the front camera. Default False
        """
        self._if_chat_go_to_chat(chat)
        # click the attachment icon
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageView[lower-case(@content-desc)="attach media"]').click()

        camera_preview_xpath = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout[2]'
        shutter_xpath = '//android.widget.Button[lower-case(@content-desc)="shutter"]'
        for i in range(10):
            if self.is_present(camera_preview_xpath):
                self.driver.find_element(by=AppiumBy.XPATH, value=camera_preview_xpath).click()
                if self.is_present(shutter_xpath):
                    break
            sleep(1)
        if not self.is_present(shutter_xpath):
            raise Exception("Clicking the camera preview to take a picture failed.")

        # switch camera if need be
        if front_camera:
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.ImageView[lower-case(@content-desc)="switch camera"]').click()
        sleep(wait_time)
        # take picture
        self.driver.find_element(by=AppiumBy.XPATH, value=shutter_xpath).click()
        # add caption
        if caption is not None:
            text_field = '//android.widget.EditText'
            for i in range(10):
                if self.is_present(text_field):
                    break
                sleep(1)
            self.driver.find_element(by=AppiumBy.XPATH, value=text_field).click()
            self.driver.find_element(by=AppiumBy.XPATH, value=text_field).send_keys(caption)

            if self.driver.is_keyboard_shown():
                self.driver.find_element(by=AppiumBy.XPATH,
                                         value='//android.widget.EditText/../../android.widget.ImageView').click()
        # press send
        # The actual send button is not in the same place as the element. The button is at about 75% of the box.
        # We adjust the location of the click from the middle to the right bottom corner of the box.
        # TODO: clicking the correct spot in the bounding box is no longer necessary because the click box is now the same size as the button (issue 97)
        location = self._find_button_location(0.75, 0.75, '//*[lower-case(@content-desc)="send"]')
        self.driver.tap([(location)])

        sleep(0.3)  # the animation after sending a picture might throw off the script

    @log_action
    def start_call(self, chat: str = None, video: bool = False) -> bool:
        """
        Makes a call and ends the call after a given number of seconds.
        The call is made to either
            * the current conversation we're in
            * a given contact name
        :param chat: Optional: name of the conversation to start a call in
        :param video: False (default) for voice call, True for video call.
        :return: True if call was successfully started
        """
        self._if_chat_go_to_chat(chat)
        if not video:
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.ImageButton[lower-case(@content-desc)="call"]').click()
        else:
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.ImageButton[lower-case(@content-desc)="more options"]').click()
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.TextView[lower-case(@text)="video call"]').click()
        # wait a short while (max 2s) for the call to have started
        return self._currently_in_call(implicit_wait=2)

    @log_action
    def get_call_status(self) -> Optional[str]:
        """
        Returns a string describing the status of the current call, which is a text visible on the call screen.
        If the call is in progress, no text indicates this, but this method will return "In progress".
        If not currently in a call, this method returns None.
        Known statuses include 'Requesting', 'Waiting' and 'Ringing'.
        """
        if not self._currently_in_call():
            return None
        if self._currently_in_active_call():
            return "In progress"
        status_element = '//android.widget.LinearLayout[ends-with(@text, "Telegram Call")]/android.widget.FrameLayout/android.widget.TextView'
        status_element = self.driver.find_element(by=AppiumBy.XPATH, value=status_element)
        return status_element.get_attribute("text")

    @log_action
    def end_call(self):
        """
        Ends the current call. Assumes the call screen is open.
        """
        if not self._currently_in_call():
            raise Exception('Cannot end call while not in call screen.')
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.Button[lower-case(@text)="end call"]').click()

    @log_action
    def answer_call(self):
        """
        Answer when receiving a call via Telegram.
        """
        self.driver.open_notifications()
        if not self.is_present('//android.widget.Button[lower-case(@content-desc)="answer"]', implicit_wait=3):
            self.driver.back()
            raise Exception('Tried to answer call, but couldn\'t find notification to answer any calls')
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.Button[lower-case(@content-desc)="answer"]').click()
        open_call_button = '//android.widget.TextView[@resource-id="android:id/title" and @text="Ongoing Telegram call"]'
        if self.is_present(open_call_button):
            self.driver.find_element(by=AppiumBy.XPATH, value=open_call_button).click()

    @log_action
    def decline_call(self):
        """
        Declines an incoming Telegram call.
        """
        self.driver.open_notifications()
        if not self.is_present('//android.widget.Button[lower-case(@content-desc)="decline"]', implicit_wait=3):
            self.driver.back()
            raise Exception('Tried to answer call, but couldn\'t find notification to answer any calls')
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.Button[lower-case(@content-desc)="decline"]').click()
        self.driver.back()

    @log_action
    def toggle_video_in_call(self):
        """
        Toggles video in an ongoing call.
        """
        if not self._currently_in_call():
            raise Exception('Expected to be in a call, but could not detect call screen!')
        if self.is_present('//android.widget.TextView[lower-case(@text)="start video"]'):
            # turn on video:
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.FrameLayout[@content-desc="Start Video"]').click()
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.TextView[@content-desc="Share Video"]').click()
        else:
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.FrameLayout[@content-desc="Stop Video"]').click()

    @log_action
    def flip_video_in_call(self):
        """
        Switches between the front camera and rear camera while in a video call.
        """
        if not self._currently_in_call():
            raise Exception('Expected to be in a call, but could not detect call screen!')
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.FrameLayout[@content-desc="Flip"]').click()

    def _if_chat_go_to_chat(self, chat: str | int):
        if chat is not None:
            self.select_chat(chat)
            sleep(1)
        if not self._currently_in_conversation():
            raise Exception('Expected to be in conversation screen now, but screen contents are unknown')

    def _find_button_location(self, width_ratio: float, height_ratio: float, xpath: str):
        send_button = self.driver.find_element(by=AppiumBy.XPATH,
                                               value=xpath)
        top_left = send_button.location['x'], send_button.location['y']
        size = send_button.size['height'], send_button.size['width']
        location = int(top_left[0] + width_ratio * size[1]), int(top_left[1] + height_ratio * size[0])
        return location