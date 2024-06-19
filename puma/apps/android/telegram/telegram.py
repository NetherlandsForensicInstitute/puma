from time import sleep
from typing import Dict

from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.appium_actions import supported_version, AndroidAppiumActions

TELEGRAM_PACKAGE = 'org.telegram.messenger'
TELEGRAM_DEFAULT_ACTIVITY = '.DefaultIcon'


@supported_version("10.13.4")
class TelegramActions(AndroidAppiumActions):

    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for Telegram Android using Appium. Can be used with an emulator or real device attached to the computer.
        """
        AndroidAppiumActions.__init__(self,
                                      device_udid,
                                      TELEGRAM_PACKAGE,
                                      TELEGRAM_DEFAULT_ACTIVITY,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def _currently_at_homescreen(self) -> bool:
        return self.is_present('//android.widget.FrameLayout[@content-desc="New Message"]')

    def _currently_in_conversation(self) -> bool:
        return self.is_present('//android.widget.ImageView[@content-desc="Emoji, stickers, and GIFs"]')

    def _currently_in_camera(self) -> bool:
        return self.is_present('//android.widget.Button[lower-case(@content-desc)="shutter"]')

    def _currently_in_call(self) -> bool:
        return self.is_present('//android.widget.Button[@text="End Call"]')

    def _load_conversation_titles(self):
        while True:
            xpath = "//androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[not(@content-desc)]"
            convos = self.driver.find_elements(by=AppiumBy.XPATH, value=xpath)
            if len(convos) == 0:
                break
            print('some conversations still do not have a title loaded, clicking...')
            convos[0].click()
            self.driver.back()
        print('all conversations loaded!')

    def return_to_homescreen(self):
        """
        Returns to the start screen of Telegram
        """
        if self.driver.current_package != TELEGRAM_PACKAGE:
            self.driver.activate_app(TELEGRAM_PACKAGE)
        while not self._currently_at_homescreen():
            self.driver.back()
        self._load_conversation_titles()
        sleep(1)

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

    def select_chat(self, chat: str):
        """
        Opens a given conversation based on the (partial) name of a chat.
        For groups or channels, it is advised to use :meth:`TelegramActions.select_group` or
        :meth:`TelegramActions.select_channel`, as the matching is more explicit
        :param chat: (part of) the conversation name to open
        """
        self.return_to_homescreen()
        xpath = f'//android.view.ViewGroup[starts-with(lower-case(@content-desc), "{chat.lower()}")]'
        self.driver.find_element(by=AppiumBy.XPATH, value=xpath).click()

    def select_group(self, group_name: str):
        """
        Opens a given conversation based on the exact name of a group.
        :param group_name: Exact group name to open
        """
        self.select_chat(f'Group. {group_name}')

    def select_channel(self, channel_name: str):
        """
        Opens a given conversation based on the exact name of a channel.
        :param channel_name: Exact channel name to open
        """
        self.select_chat(f'Channel. {channel_name}')

    def send_message(self, message: str, chat: str = None):
        """
        Send a message in the current or given chat
        :param message: The text message to send
        :param chat: Optional: The chat conversation in which to send this message, if not currently in the desired chat
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.EditText[@text="Message"]').send_keys(
            message)
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.view.View[@content-desc="Send"]').click()

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

    def take_and_send_picture(self,
                              chat: str = None,
                              caption: str = None,
                              wait_time: int = 1,
                              front_camera: bool = False):
        """
        Opens the embedded camera in the Telegram app, takes a picture, and sends it.
        :param chat: Optional: the conversation in which to send the picture. If not used, we assume a conversation is opened
        :param caption: Optional: a cpation to include with the picture
        :param wait_time: Optional: time to wait (in seconds) after opening the camera before taking a picture. Default 1s
        :param front_camera: Optional: whether or not to use the front camera. Default False
        """
        self._if_chat_go_to_chat(chat)
        # click the attachment icon
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageView[lower-case(@content-desc)="attach media"]').click()
        # click the camera: this might be unstable due to bad xpath expression
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout[2]').click()
        # switch camera if need be
        if front_camera:
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.ImageView[lower-case(@content-desc)="switch camera"]').click()
        sleep(wait_time)
        # take picture
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.Button[lower-case(@content-desc)="shutter"]').click()
        sleep(1)
        # add caption
        if caption is not None:
            self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.EditText').click()
            self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.EditText').send_keys(caption)
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.EditText/../../android.widget.ImageView').click()
        # press send
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageView[lower-case(@content-desc)="send"]').click()
        sleep(0.3)  # the animation after sending a picture might throw off the script

    def start_call(self, chat: str = None, video: bool = False):
        """
        Makes a call and ends the call after a given number of seconds.
        The call is made to either
            * the current conversation we're in
            * a given contact name
        :param chat: Optional: name of the conversation to start a call in
        :param video: False (default) for voice call, True for video call.
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

    def end_call(self):
        """
        Ends the current call. Assumes the call screen is open.
        """
        if not self._currently_in_call():
            raise Exception('Expected to be in a call, but could not detect call screen!')
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.Button[lower-case(@text)="end call"]').click()

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
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.TextView[@resource-id="android:id/title" and @text="Ongoing Telegram call"]').click()

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

    def flip_video_in_call(self):
        """
        Switches between the front camera and rear camera while in a video call.
        """
        if not self._currently_in_call():
            raise Exception('Expected to be in a call, but could not detect call screen!')
        self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.FrameLayout[@content-desc="Flip"]').click()

    def _if_chat_go_to_chat(self, chat: str):
        if chat is not None:
            self.return_to_homescreen()
            self.select_chat(chat)
        if not self._currently_in_conversation():
            raise Exception('Expected to be in conversation screen now, but screen contents are unknown')
