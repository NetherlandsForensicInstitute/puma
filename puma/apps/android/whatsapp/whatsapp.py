import re
from time import sleep
from typing import Dict, List, Union

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By

from puma.apps.android.appium_actions import supported_version, AndroidAppiumActions

WHATSAPP_PACKAGE = 'com.whatsapp'


@supported_version("2.24.25.78")
class WhatsappActions(AndroidAppiumActions):
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
                                      WHATSAPP_PACKAGE,
                                      desired_capabilities=desired_capabilities,
                                      implicit_wait=implicit_wait,
                                      appium_server=appium_server)

    def currently_at_homescreen(self) -> bool:
        return self.is_present('//android.widget.FrameLayout[@content-desc="com.whatsapp:id/root_view"]')

    def currently_in_conversation_overview(self) -> bool:
        # Send message occurs when no conversations are present yet. New chat when there are conversations.
        return self.is_present('//android.widget.ImageButton[@content-desc="New chat"] | '
                               '//android.widget.Button[@content-desc="Send message"]')

    def currently_in_conversation(self) -> bool:
        return self.is_present('//android.widget.LinearLayout[@resource-id="com.whatsapp:id/conversation_root_layout"]',
                               implicit_wait=1)

    def return_to_homescreen(self):
        if self.driver.current_package != WHATSAPP_PACKAGE:
            self.driver.activate_app(WHATSAPP_PACKAGE)
        while not self.currently_in_conversation_overview():
            self.driver.back()
        sleep(0.5)

    def get_conversation_row_elements(self, subject):
        self.return_to_homescreen()
        return self.driver.find_elements(by=AppiumBy.XPATH,
                                         value=f"//*[contains(@resource-id,'com.whatsapp:id/conversations_row_contact_name') and @text='{subject}']")

    def select_chat(self, subject):
        """
        Select the chat with subject x. For 1-on-1 chats, the subject is the name of the conversation partner. For group
        chats, this is the subject. The top found chat will be selected, so there should not be more than 1 chat with the same subject.
        """
        self.return_to_homescreen()
        chats_of_interest = self.get_conversation_row_elements(subject)
        if len(chats_of_interest) > 1:
            chats_of_interest_text = ", ".join([chat.text for chat in chats_of_interest])
            print(
                f"[WARNING]: Multiple chats found that contain the subject {subject}: {chats_of_interest_text}. Selecting the first one.")
        if len(chats_of_interest) == 0:
            raise Exception(f'Cannot find conversation with name {subject}')
        chats_of_interest[0].click()

    def create_new_chat(self, contact, first_message):
        """
        Start a new 1-on-1 conversation with a contact and send a message.
        :param contact: Contact to start the conversation with.
        :param first_message: First message to send to the contact
        """
        self.return_to_homescreen()
        self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='com.whatsapp:id/fab' or @resource-id='com.whatsapp:id/fabText']").click()
        self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='com.whatsapp:id/contactpicker_text_container']//*[@text='{contact}']").click()
        self.send_message(first_message)

    def _if_chat_go_to_chat(self, chat: str):
        if chat is not None:
            self.return_to_homescreen()
            self.select_chat(chat)
        if not self.currently_in_conversation():
            raise Exception('Expected to be in conversation screen now, but screen contents are unknown')

    def send_message(self, message_text, chat: str = None, wait_until_sent=False):
        """
        Send a message in the current chat. If the message contains a mention, this is handled correctly.
        :param wait_until_sent: Exit this function only when the message has been sent.
        :param chat: The chat conversation in which to send this message, if not currently in the desired chat.
        :param message_text: The text that the message contains.
        """
        self._if_chat_go_to_chat(chat)
        text_box = self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/entry")
        self._handle_mention(message_text, text_box) if "@" in message_text else text_box.send_keys(message_text)
        if 'http' in message_text:
            sleep(2)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/send").click()
        if wait_until_sent:
            _ = self._ensure_message_sent(message_text)

    def _handle_mention(self, message, text_box):
        """
        Make sure to convert an @name to an actual mention. Only one mention is allowed.
        :param message: The message containing the mention.
        """
        text_box.send_keys(message)
        sleep(1)
        # Find the mentioned name in the message. Note that it will search until the last word character. This means for
        # @jan-willem, only @jan will be found.
        mention_match = re.search(r"@\w+", message)
        mention_end_pos = mention_match.span()[1]
        mentioned_name = mention_match.group(0).strip("@")

        for _ in range(mention_end_pos, len(message)):
            # Move cursor to the end position of the mentioned name.
            # Keycodes were found at https://developer.android.com/reference/android/view/KeyEvent.html
            back_arrow_keycode = 21
            self.driver.press_keycode(back_arrow_keycode)
        # Removing the last character is necessary to trigger the pop-up to select the person
        # so we press backspace (Keycode 67)
        backspace_keycode = 67
        self.driver.press_keycode(backspace_keycode)
        mentioned_person_el = \
            [person for person in self.driver.find_elements(by=AppiumBy.ID, value="com.whatsapp:id/contact_photo")
             if person.tag_name.lower() == mentioned_name.lower()][0]
        mentioned_person_el.click()
        # Remove a space resulting from selecting the mention person
        self.driver.press_keycode(backspace_keycode)

    def _ensure_message_sent(self, message_text):
        message_status_el = self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='com.whatsapp:id/conversation_text_row']"
        f"//*[@text='{message_text}']"  # Text field element containing message text
        f"/.."  # Parent of the message (i.e. conversation text row)
        f"//*[@resource-id='com.whatsapp:id/status']")  # Status element
        while message_status_el.tag_name == "Pending":
            print("Message pending, waiting for the message to be sent.")
            sleep(10)
        return message_status_el

    def delete_message_for_everyone(self, message_text: str, chat: str = None):
        """
        Remove a message with the message text. Should be recently sent, so it is still in view and still possible to
        delete for everyone.
        :param message_text: literal message text of the message to remove. The first match will be removed in case
        there are multiple with the same text.
        :param chat: The chat conversation in which to send this message, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        message_element = self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='com.whatsapp:id/conversation_text_row']//*[@text='{message_text}']")
        self._long_press_element(message_element)
        self.driver.find_element(by=AppiumBy.XPATH, value='//*[@content-desc="Delete"]').click()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value="//*[@resource-id='com.whatsapp:id/buttonPanel']//*[@text='Delete for everyone']").click()

    def reply_to_message(self, message_to_reply_to: str, reply_text: str, chat: str = None):
        """
        Reply to a message. Assumes you are in the chat in which the message was sent.
        :param message_to_reply_to: message you want to reply to.
        :param reply_text: message text you are sending in your reply.
        :param chat: The chat conversation in which to send this message, if not currently in the desired chat.
        """
        # Wait and see if the message to be forwarded is no longer pending. If so, we must wait because a pending
        # message cannot be forwarded
        self._if_chat_go_to_chat(chat)
        message_element = self.scroll_to_find_element(text_contains=message_to_reply_to)
        self._long_press_element(message_element)
        self.driver.find_element(by=AppiumBy.XPATH, value='//*[@content-desc="Reply"]').click()
        text_box = self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/entry")
        text_box.send_keys(reply_text)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/send").click()

    def send_broadcast(self, receivers: [str], broadcast_text: str):
        """
        Broadcast a message.
        :param receivers: list of receiver names, minimum of 2!.
        :param broadcast_text: Text to send.
        """
        self.return_to_homescreen()
        if len(receivers) < 2:
            print("Error: minimum of 2 receivers required for a broadcast!")
            return
        self.open_more_options()
        new_broadcast = self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='com.whatsapp:id/title' and @text='New broadcast']")
        new_broadcast.click()
        for receiver in receivers:
            self.driver.find_element(by=AppiumBy.XPATH, value=
            f"//*[@resource-id='com.whatsapp:id/chat_able_contacts_row_name' and @text='{receiver}']").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/next_btn").click()
        text_box = self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/entry")
        text_box.send_keys(broadcast_text)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/send").click()

    def send_media(self, directory_name, caption=None, view_once=False, chat: str = None):
        """
        Send a photo or video with or without a caption in the current chat.
        :param directory_name: The name of the directory the media is located. Only one file should be present in the
        directory with the same name.
        For example, directory name tiger assumes a directory tiger with a picture tiger.<Extension>
         ├── tiger
         │    └── tiger.jpg
        :param caption: Default False. Pass text if you want to set a caption.
        :param view_once: Default False. True if you want to send a view_once photo.
        :param chat: The chat conversation in which to send this media, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        # Go to gallery
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/input_attach_button").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/pickfiletype_gallery_holder").click()
        if self.is_present('//android.widget.LinearLayout[@content-desc="Gallery"]'):
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.LinearLayout[@content-desc="Gallery"]').click()
            directory_tile = f'//android.widget.TextView[@resource-id="com.whatsapp:id/title" and @text="{directory_name}"]'
            self.swipe_to_find_element(xpath=directory_tile).click()
            sleep(0.5)
            self.driver.find_element(by=By.CLASS_NAME, value="android.widget.ImageView").click()
        elif self.is_present('//android.widget.TextView[@resource-id="com.whatsapp:id/title"]'):
            self.driver.find_element(by=AppiumBy.XPATH,
                                     value='//android.widget.TextView[@resource-id="com.whatsapp:id/title"]').click()
            sleep(0.5)
            self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.ListView/android.view.ViewGroup[last()]').click()
            directory_tile = f'//android.widget.TextView[@text="{directory_name}"]'
            self.swipe_to_find_element(xpath=directory_tile).click()
            sleep(0.5)
            self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.ImageView[@resource-id="com.google.android.providers.media.module:id/icon_thumbnail"]').click()
            self.driver.find_element(by=AppiumBy.XPATH, value='//android.widget.Button[@resource-id="com.google.android.providers.media.module:id/button_add"]').click()

        if caption:
            text_box = self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/caption")
            text_box.send_keys(caption)
            # Clicking the text box after sending keys is required for Whatsapp to notice text has been inserted.
            text_box.click()
            self.driver.back()

        if view_once:
            self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/view_once_toggle").click()
            popup_button = '//android.widget.Button[@resource-id="com.whatsapp:id/vo_sp_bottom_sheet_ok_button"]'
            if self.is_present(popup_button):
                self.driver.find_element(by=AppiumBy.XPATH, value=popup_button).click()
        sleep(1)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/send").click()

    def send_sticker(self, chat: str = None):
        """
        Send the only sticker in the sticker menu. Assumes 1 sticker is present in WhatsApp.
        Note that the selection of the sticker is based on coordinates of the Pixel 5. For other phones with different
        screen sizes, it should be validated that this is correct.
        :param chat: The chat conversation in which to send this sticker, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/emoji_picker_btn").click()
        sleep(1)
        # Press sticker tab
        # TODO: make coordinates configurable or calculate what they should be
        # self.press_coordinates(663, 2136) # Pixel 5
        self._click_coordinates(663, 2032)  # Samsung G955F
        sleep(1)
        # Press sticker
        # self.press_coordinates(150, 1600) # Pixel 5
        self._click_coordinates(128, 1502)  # Samsung G955F

    def _click_coordinates(self, x, y):
        self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})

    def send_voice_recording(self, duration: int = 2000, chat: str = None):
        """
        Sends a voice message in the current conversation.
        Assumes we are in the conversation in which we want to send the voice message.
        :param duration: the duration in of the voice message to send in millisec.
        :param chat: The chat conversation in which to send this voice recording, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        voice_button = self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/voice_note_btn")
        self._long_press_element(voice_button, duration=duration)

    def send_current_location(self, chat: str = None):
        """
        Send the current location in the current chat.
        Assumes we're in a chat and that the given contact exists.
        :param chat: The chat conversation in which to send the location, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/input_attach_button").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/pickfiletype_location_holder").click()
        sleep(5)  # it takes some time to fix the location
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/send_current_location_btn").click()

    def send_live_location(self, caption=None, chat: str = None):
        """
        Send a live location in the current chat.
        Assumes we're in a chat and that the given contact exists.
        :param caption: Optional caption sent along with the live location
        :param chat: The chat conversation in which to start the live location sharing, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/input_attach_button").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/pickfiletype_location_holder").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/live_location_btn").click()
        dialog = '//android.widget.LinearLayout[@resource-id="com.whatsapp:id/location_new_user_dialog_container"]'
        if self.is_present(dialog):
            self.driver.find_element(by=AppiumBy.XPATH, value="//android.widget.Button[@text='Continue']").click()
        if caption is not None:
            self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/comment").send_keys(caption)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/send").click()

    def stop_live_location(self, need_to_scroll=False, chat: str = None):
        """
        Stops the current live location sharing.
        :param need_to_scroll: Set to True if we need to scroll in the conversation to find the button "Stop Sharing"
        :param chat: The chat conversation in which to stop the live location sharing, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        if need_to_scroll:
            self.scroll_to_find_element(text_contains="Stop sharing").click()
        else:
            self.driver.find_element(by=AppiumBy.XPATH, value="//*[@text='Stop sharing']").click()

        popup_button_xpath = '//android.widget.Button[@content-desc="Stop"]'
        if self.is_present(popup_button_xpath):
            self.driver.find_element(by=AppiumBy.XPATH, value=popup_button_xpath).click()

    def send_contact(self, contact_name: str, chat: str = None):
        """
        Send a contact in the current chat.
        Assumes we're in a chat and that the given contact exists.
        :param contact_name: the name of the contact to send.
        :param chat: The chat conversation in which to send the contact, if not currently in the desired chat.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/input_attach_button").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/pickfiletype_contact_holder").click()
        self.swipe_to_find_element(f'//android.widget.TextView[@resource-id="com.whatsapp:id/name" and @text="{contact_name}"]').click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/next_btn").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/send_btn").click()

    def change_profile_picture(self, photo_dir_name: str = "profile_picture"):
        """
        Change profile picture. Selects the picture in the specified directory.
        :param photo_dir_name: Name of the directory the profile photo is in.
        """
        self.return_to_homescreen()
        self.open_settings_you()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/change_photo_btn").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[@text='Gallery']").click()
        gallery_tab = '//android.widget.LinearLayout[@content-desc="Gallery"]'
        if self.is_present(gallery_tab):
            self.driver.find_element(by=AppiumBy.XPATH, value=gallery_tab).click()
        self.scroll_to_find_element(text_contains=photo_dir_name).click()
        sleep(1)
        self.driver.find_element(by=By.CLASS_NAME, value="android.widget.ImageView").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/ok_btn").click()

    def set_status(self, caption: str = None):
        """
        Sets a status by taking a picture and setting the given caption.
        :param caption: the caption to publish with the status.
        """
        self.return_to_homescreen()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.TextView['
                                       '( @resource-id="com.whatsapp:id/navigation_bar_item_small_label_view"'
                                       'or @resource-id="com.whatsapp:id/navigation_bar_item_large_label_view" )'
                                       'and @text="Updates"]').click()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageButton[@content-desc="New status update"]').click()
        open_camera = '//android.widget.Button[@content-desc="Camera"]'
        if self.is_present(open_camera):
            self.driver.find_element(by=AppiumBy.XPATH, value=open_camera).click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/shutter").click()
        if caption:
            self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/caption").send_keys(caption)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/send").click()
        # TODO: popup that can appear!
        self.return_to_homescreen()

    def set_about(self, about_text: str):
        """
        Set the about section on the WhatsApp profile.
        :param about_text: text in the about
        """
        self.return_to_homescreen()
        self.open_settings_you()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/profile_info_status_card").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/status_tv_edit_icon").click()
        text_box = self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/edit_text")
        text_box.click()
        text_box.clear()
        text_box.send_keys(about_text)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/save_button").click()

    def activate_disappearing_messages(self, chat=None):
        """
        Activates disappearing messages (auto delete) in the current or a given chat.
        Messages will now auto-delete after 24h.
        Assumes that we are in the intended conversation if no group name is given, if a group name is given it is
        assumed that this group exists and that we are at the whatsapp home screen.
        :param chat: Optional: group for which disappearing messages should be activated.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/conversation_contact").click()
        self.scroll_to_find_element(text_contains='Disappearing messages').click()
        self.driver.find_elements(by=AppiumBy.XPATH, value="//*[@class='android.widget.RadioButton']")[0].click()
        if chat is None:
            self.driver.back()
            self.driver.back()
        else:
            self.return_to_homescreen()

    def deactivate_disappearing_messages(self, chat=None):
        """
        Disables disappearing messages (auto delete) in the current or a given chat.
        Assumes that we are in the intended conversation if no group name is given, if a group name is given it is
        assumed that this group exists and that we are at the whatsapp home screen.
        :param chat: Optional: group for which disappearing messages should be activated.
        """
        self._if_chat_go_to_chat(chat)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/conversation_contact").click()
        self.scroll_to_find_element(text_contains='Disappearing messages').click()
        self.driver.find_elements(by=AppiumBy.XPATH, value="//*[@class='android.widget.RadioButton']")[-1].click()
        if chat is None:
            self.driver.back()
            self.driver.back()
        else:
            self.return_to_homescreen()

    def navigate_to_call_tab(self):
        """
        Navigates to the call tab. The 2 resource ids are necessary because they differ when you are or are not on the call tab.
        :return:
        """
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.TextView['
                                       '( @resource-id="com.whatsapp:id/navigation_bar_item_small_label_view"'
                                       'or @resource-id="com.whatsapp:id/navigation_bar_item_large_label_view" )'
                                       'and @text="Calls"]').click()

    def call_contact(self, contact, video_call=False):
        """
        Make a WhatsApp call. The call is made to a given contact name
        :param contact: name of the contact to call.
        :param video_call: False (default) for voice call, True for video call.
        """
        self.return_to_homescreen()
        call_type = "Video call" if video_call else "Voice call"
        self.navigate_to_call_tab()
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageButton[@content-desc="Search"]').click()
        search_bar = self.driver.find_element(by=AppiumBy.XPATH,
                                              value='//android.widget.EditText[@resource-id="com.whatsapp:id/search_view_edit_text"]')
        search_bar.send_keys(contact)
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value=f'(//android.widget.ImageView[@content-desc="{call_type}"])[1]').click()  # Take the top one without checking the name, since we already searched for the contact

    def end_call(self):
        """
        Ends the current call. Assumes the call screen is open.
        """
        end_call_button = '//*[@content-desc="Leave call" or @resource-id="com.whatsapp:id/end_call_button" or @resource-id="com.whatsapp:id/footer_end_call_btn"]'
        if not self.is_present(end_call_button, implicit_wait=1):
            # tap screen to make call button visible
            background = '//android.widget.RelativeLayout[@resource-id="com.whatsapp:id/call_screen"]'
            self.driver.find_element(by=AppiumBy.XPATH, value=background).click()
        self.driver.find_element(by=AppiumBy.XPATH, value=end_call_button).click()

    def answer_call(self):
        """
        Answer when receiving a call via Whatsapp.
        """
        self.open_notifications()
        sleep(2)
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value="//android.widget.Button[@content-desc='Answer' or @content-desc='Video']").click()

    def decline_call(self):
        """
        Declines an incoming Whatsapp call.
        """
        self.open_notifications()
        sleep(2)
        self.driver.find_element(by=AppiumBy.XPATH, value="//android.widget.Button[@content-desc='Decline']").click()

    def create_group(self, subject: str, participants: Union[str, List[str]]):
        """
        Create a new group. Assumes you are in homescreen.
        :param subject: The subject of the group.
        :param participants: The contact(s) you want to add to the group (string or list).
        Note that only 1 participant is implemented for now.
        """
        self.return_to_homescreen()
        self.open_more_options()
        self.driver.find_element(by=By.XPATH, value="//*[@text='New group']").click()

        participants = [participants] if not isinstance(participants, list) else participants
        for participant in participants:
            contacts = self.driver.find_elements(by=By.CLASS_NAME, value="android.widget.TextView")
            participant_to_add = [contact for contact in contacts if contact.text.lower() == participant.lower()][0]
            participant_to_add.click()

        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/next_btn").click()
        text_box = self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/group_name")
        text_box.send_keys(subject)
        image_buttons = self.driver.find_elements(by=By.CLASS_NAME, value="android.widget.ImageButton")
        next_button = [button for button in image_buttons if button.tag_name == "Create"][0]
        next_button.click()
        print("Waiting 5 sec to create group")
        sleep(5)
        if self.currently_at_homescreen():
            print("On homescreen now")
            # Check if creating the group succeeded
            top_conv = self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/single_msg_tv")
            max_attempts = 20
            while "Creating" in top_conv.text or "Couldn't create" in top_conv.text:
                if "Couldn't create" in top_conv.text:
                    print("Couldn't create. Tapping to retry")
                    top_conv.click()
                else:
                    print("Waiting for group to be created.")
                sleep(5)
                max_attempts -= 1
                if max_attempts == 0:
                    raise TimeoutError(
                        f"Could not create group after 20 attempts. Try restarting your emulator and try again.")
        self.return_to_homescreen()

    def set_group_description(self, group_name, description):
        """
        Set the group description.
        :param group_name: Name of the group to set the description for.
        :param description: Description of the group.
        """
        self.return_to_homescreen()
        self.select_chat(group_name)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/conversation_contact").click()
        self.scroll_to_find_element(text_equals="Add group description").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/edit_text").send_keys(description)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/ok_btn").click()
        self.return_to_homescreen()

    def delete_group(self, group_name):
        """
        Leaves and deletes a given group.
        Assumes the group exists, isn't left yet, and that we start from the whatsapp home screen.
        :param group_name: the group to be deleted.
        """
        self.leave_group(group_name)
        self.select_chat(group_name)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/conversation_contact").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[contains(@text,'Delete group')]").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[contains(@text,'Delete group')]").click()
        self.return_to_homescreen()

    def archive_conversation(self, subject):
        """
        Archives a given conversation.
        :param subject: The conversation to archive.
        """
        self.return_to_homescreen()
        conversation = self.get_conversation_row_elements(subject)[0]
        self._long_press_element(conversation)
        self.driver.find_element(by=AppiumBy.ID, value='com.whatsapp:id/menuitem_conversations_archive').click()
        # Wait until the archive popup disappeared
        archived_popup_present = True
        while archived_popup_present:
            print("waiting for archived popup to disappear")
            sleep(5)
            archived_popup_present = 'archived' in self.driver.find_elements(by=AppiumBy.XPATH, value=
            "//*[contains(@text,'archived') or @resource-id='com.whatsapp:id/fab']")[0].text
        print("Archive pop-up gone!")

    def _long_press_element(self, element, duration=1000):
        """
        Press some element for some duration.
        :param element: Element to long press.
        :param duration: Duration of the press in millisec.
        :return:
        """
        location = element.location
        size = element.size

        # Calculate the center of the element
        x = location['x'] + size['width'] // 2
        y = location['y'] + size['height'] // 2
        self.driver.execute_script('mobile: longClickGesture', {'x': x, 'y': y, 'duration': duration})

    def leave_group(self, group_name):
        """
        This method will leave the given group. It will not delete that group.
        This method assumes we start at the whatsapp home screen.
        :param group_name: Name of the group we want to leave.
        """
        self.select_chat(group_name)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/conversation_contact").click()
        self.scroll_to_find_element(text_equals="Exit group").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//android.widget.Button[@text='Exit']").click()
        self.return_to_homescreen()

    def remove_participant_from_group(self, group_name, participant):
        """
        Removes a given participant from a given group chat.
        It is assumed the group chat exists and has the given participant, and that we start at the whatsapp home screen.
        :param group_name: The group
        :param participant: The participant to remove
        """
        self.select_chat(group_name)
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/conversation_contact").click()
        self.scroll_to_find_element(text_equals=participant).click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[starts-with(@text, 'Remove')]").click()
        self.driver.find_element(by=AppiumBy.XPATH, value="//*[@class='android.widget.Button' and @text='OK']").click()
        sleep(5)
        self.return_to_homescreen()

    def forward_message(self, from_chat, message_contains, to_chat):
        """
        Forwards a message from one conversation to another.
        It is assumed the message and both conversations exists, and that we start at the whatsapp home screen.
        :param from_chat: The chat from which the message has to be forwarded
        :param message_contains: the text from the message that has to be forwarded. Uses String.contains(), so only part
        of the message is needed, but be sure the given text is enough to match your intended message uniquely.
        :param to_chat: The chat to which the message has to be forwarded.
        """
        self.select_chat(from_chat)
        chat_message = self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='com.whatsapp:id/conversation_text_row']//*[contains(@text,'{message_contains}')]")
        self._long_press_element(chat_message)
        self.driver.find_element(by=AppiumBy.XPATH, value=
        "//*[@resource-id='com.whatsapp:id/action_mode_bar']//*[@content-desc='Forward']").click()
        self.driver.find_element(by=AppiumBy.XPATH, value=
        f"//*[@resource-id='com.whatsapp:id/contact_list']//*[@text='{to_chat}']").click()
        self.driver.find_element(by=AppiumBy.ID, value="com.whatsapp:id/send").click()

    def open_settings_you(self):
        """
        Open personal settings (or profile).
        """
        self.return_to_homescreen()
        self.open_more_options()
        # Improvement possible: get all elements and filter on text=settings
        self.driver.find_element(by=AppiumBy.XPATH, value=
        "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.ListView/android.widget.LinearLayout[5]/android.widget.LinearLayout").click()
        self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="You").click()

    def open_more_options(self):
        """
        Open more options (hamburger menu) in the home screen.
        """
        self.driver.find_element(by=AppiumBy.XPATH,
                                 value='//android.widget.ImageView[@content-desc="More options"]').click()

    def open_view_once_photo(self, chat=None):
        """
        Open view once photo in the current or specified chat. Should be done right after the photo is sent, to ensure the correct photo is opened, this will be the lowest one.
        :param chat: Optional: The chat in which the photo has to be opened. If not supplied, the photo will be opened in the current chat.
        """
        self._if_chat_go_to_chat(chat)
        most_recent_view_once = \
            self.driver.find_elements(by=AppiumBy.XPATH, value='//*[contains(@resource-id, "view_once_media")]')[-1]
        most_recent_view_once.click()
        self.driver.back()
