import csv
import re
import time
from typing import Callable
from dataclasses import astuple, fields
from datetime import datetime
from xml.etree import ElementTree

from puma.apps.android.slack.message_parser import Message, parse_messages, new_items, to_iso_time
from puma.apps.android.slack.xpaths import HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR, HOME_CHANNEL_BUTTON, \
    CHAT_TITLE, CHAT_MEMBER_COUNT, \
    CHAT_BACK_BUTTON, CHAT_TEXT_INPUT, HOME_DIRECT_MESSAGE_BUTTON, CHAT_ATTACHMENTS_BUTTON, CHAT_SEND_BUTTON, \
    ATTACHMENTS_UPLOAD_FILE_BUTTON, ATTACHMENTS_ATTACH_PHOTOS_BUTTON, ATTACHMENTS_MEDIA_STRIP, ATTACHMENTS_PICTURES, \
    ATTACHMENTS_MEDIA_STRIP_ID, ATTACHMENTS_DONE_BUTTON, CHAT_MESSAGES_LIST, CHAT_BEGINNING_OF_CONVERSATION
from puma.state_graph.action import action
from puma.state_graph.locators import xpath_quoted
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, supported_version, Platform
from puma.state_graph.state import SimpleState, ContextualState, State
from puma.state_graph.state_graph import StateGraph

APPLICATION_PACKAGE = 'com.Slack'
CHANNEL_PREFIX = '#'
DIRECT_MESSAGE_PREFIX = '@'


def parse_conversation(conversation: str) -> tuple[bool, str]:
    """
    Parses the name of a conversation, which is written as in Slack: '#general' is a channel and '@Bob' is a direct
    message conversation. A name without a prefix is a direct message conversation.

    :param conversation: The name of the conversation, e.g. '#general', '@Bob' or 'Bob'.
    :return: Whether the conversation is a channel, and the name of the conversation without the prefix.
    """
    name = conversation[1:] if conversation and conversation[0] in (CHANNEL_PREFIX, DIRECT_MESSAGE_PREFIX) \
        else conversation
    if not name:
        raise ValueError(f"'{conversation}' is not the name of a channel or direct message conversation")
    return conversation.startswith(CHANNEL_PREFIX), name


class SlackChatState(SimpleState, ContextualState):
    """
    State defining a Slack conversation screen: a channel or a direct message conversation
    """

    def __init__(self, parent_state: State) -> None:
        super().__init__([CHAT_BACK_BUTTON, CHAT_TEXT_INPUT],
                         invalid_xpaths=[ATTACHMENTS_UPLOAD_FILE_BUTTON],
                         parent_state=parent_state,
                         parent_state_transition=SlackChatState.back_to_home)

    @staticmethod
    def back_to_home(driver: PumaDriver) -> None:
        # When the keyboard is open, going back only closes the keyboard
        driver.close_keyboard()
        driver.back()

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if conversation:
            is_channel, name = parse_conversation(conversation)
            # a channel and a direct message conversation can have the same name, only a channel shows its members,
            # which can appear a moment after the title
            return driver.is_present(CHAT_TITLE.format(chat_title=xpath_quoted(name))) \
                and driver.is_present(CHAT_MEMBER_COUNT, driver.implicit_wait if is_channel else 0) == is_channel
        return True

    @staticmethod
    def go_to_chat(driver: PumaDriver, conversation: str = None) -> None:
        is_channel, name = parse_conversation(conversation)
        if is_channel:
            chat_xpath = HOME_CHANNEL_BUTTON.format(channel_name=xpath_quoted(name))
        else:
            chat_xpath = HOME_DIRECT_MESSAGE_BUTTON.format(direct_message=xpath_quoted(name))
        # The home screen might still be scrolled from an earlier visit, so search down first and then back up
        try:
            driver.swipe_to_find_element(chat_xpath, max_swipes=20, swipe_down=True, stop_at_end=True)
        except PumaClickException:
            driver.swipe_to_find_element(chat_xpath, max_swipes=20, swipe_down=False, stop_at_end=True)
        driver.click(chat_xpath)


@supported_version("26.09.50.0")
class Slack(StateGraph):
    """
    Slack on Android: navigating to channels and direct message conversations, sending messages and pictures, and
    getting and exporting the messages of a conversation.
    """
    platform = Platform.ANDROID

    def __init__(self, device_udid: str, **kwargs) -> None:
        """
        Initializes Slack messenger with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE, **kwargs)

    home_state = SimpleState(
        [HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR],
        invalid_xpaths=[CHAT_BACK_BUTTON],
        initial_state=True
    )
    chat_state = SlackChatState(parent_state=home_state)
    # only recognized, to close an attachments menu that was left open during recovery
    attachments_state = SimpleState([ATTACHMENTS_UPLOAD_FILE_BUTTON], parent_state=chat_state, recognize_only=True)

    home_state.to(chat_state, SlackChatState.go_to_chat)

    @action(chat_state)
    def send_message(self, message: str, conversation: str = None) -> None:
        """
        Sends a text message in the current or selected channel or direct message conversation.

        :param message: The text of the message.
        :param conversation: The name of the conversation: a channel with a '#' prefix (e.g. '#general'), or a direct
        message conversation with an optional '@' prefix (e.g. '@Bob' or 'Bob').
        """
        self.driver.send_keys(CHAT_TEXT_INPUT, message)
        self.driver.press_enter()

    # The attachments menu is opened in the action itself rather than by starting from the attachments state: the
    # conversation is not visible in the attachments menu, so the context of that state cannot be validated
    def send_picture(self, picture_id: int = 1, caption: str = None, conversation: str = None) -> None:
        """
        Sends a picture in the current or selected channel or direct message conversation.

        :param picture_id: The index of the picture to send, 1 being the most recent picture on the device.
        :param caption: The caption to add to the picture.
        :param conversation: The name of the conversation: a channel with a '#' prefix (e.g. '#general'), or a direct
        message conversation with an optional '@' prefix (e.g. '@Bob' or 'Bob').
        """
        # checked before the action, which would navigate and retry on the error
        if picture_id < 1:
            raise ValueError(f'The picture index starts at 1, got {picture_id}')
        self._send_picture(picture_id, caption, conversation)

    @action(chat_state)
    def _send_picture(self, picture_id: int, caption: str, conversation: str) -> None:
        self.driver.click(CHAT_ATTACHMENTS_BUTTON)
        if not self.driver.is_present(ATTACHMENTS_MEDIA_STRIP, self.driver.implicit_wait) and \
                self.driver.is_present(ATTACHMENTS_ATTACH_PHOTOS_BUTTON):
            # Slack has no access to the photos yet: this opens a permission pop-up, which is handled when the action
            # is retried
            self.driver.click(ATTACHMENTS_ATTACH_PHOTOS_BUTTON)
        self.driver.click(self._find_picture(picture_id))
        self.driver.click(ATTACHMENTS_DONE_BUTTON)
        if caption:
            self.driver.send_keys(CHAT_TEXT_INPUT, caption)
        self.driver.click(CHAT_SEND_BUTTON)

    def get_messages(self, conversation: str = None, message_count: int = None) -> list[Message]:
        """
        Returns the messages in the current or selected conversation, oldest first.

        The conversation is scrolled up from the end to collect the messages, until the beginning of the conversation
        is reached. With a message count, only the last X messages are returned, and the scrolling stops when enough
        messages are collected. Extra scrolling might happen to collect extra information on the oldest messages.

        Important: Messages are only collected when they are shown completely: messages that are larger than the screen
        are collected as well, but messages that are almost as large as the screen (larger than 70% of the conversation
        view) can be missed.

        :param conversation: The name of the conversation (channels with a # prefix, DMs with a @ prefix. No prefix is
        interpreted as a DM).
        :param message_count: Optional. The maximum number of messages: only the last X messages of the conversation
        are returned. By default, all messages are returned.
        :return: The messages, with their sender, time, text and attachments.
        """
        # checked before the action, which would navigate and retry on the error
        if message_count is not None and message_count < 1:
            raise ValueError(f'The message count should be at least 1, got {message_count}')
        return self._get_messages(conversation, message_count)

    @action(chat_state)
    def _get_messages(self, conversation: str, message_count: int) -> list[Message]:
        # Slack shows relative dates ('Today') and dates without a year in the time zone of the device
        now = datetime.fromisoformat(self.driver.driver.get_device_time('YYYY-MM-DDTHH:mm:ss'))
        # The keyboard takes up half of the conversation
        self.driver.close_keyboard()
        messages = []
        messages_list = self.driver.get_element(CHAT_MESSAGES_LIST).rect
        visible = messages_list['y'], messages_list['y'] + messages_list['height']
        # the last screen that showed messages, and the distance swiped since
        previous_screen, scrolled = [], 0

        def collect(page_source: str, swiped: int) -> bool:
            """
            Adds the new messages on the current screen above the messages collected so far. Used as the stop condition
            while swiping up: it returns True when enough messages are collected, and the sender of the first of
            these is shown. The sender of a message without a header is the sender of a message above it.
            """
            nonlocal messages, previous_screen, scrolled
            scrolled += swiped
            screen = parse_messages(page_source)
            if screen:
                messages = [message for *_, message in new_items(previous_screen, screen, scrolled, visible)] + messages
                previous_screen, scrolled = screen, 0
            if message_count is None:
                return False
            first_message = len(messages) - message_count
            return first_message >= 0 and any(message.sender for message in messages[:first_message + 1])

        # The conversation is not always at the end, e.g. when it has unread messages
        self._swipe_messages_list(up=False, until=lambda *_: False)
        enough_messages = self._swipe_messages_list(up=True, slow=True, until=collect)
        if not enough_messages and not self.driver.is_present(CHAT_BEGINNING_OF_CONVERSATION):
            self.gtl_logger.warning('Stopped collecting messages before the beginning of the conversation was reached, '
                                    'messages may be missing')
        # Consecutive messages of the same sender have no header, the sender is the sender of the message above. This
        # is filled in afterwards, as the messages on a new screen are compared to the collected messages as shown.
        for previous, message in zip(messages, messages[1:]):
            message.sender = message.sender or previous.sender
        if message_count is not None:
            messages = messages[-message_count:]
        for message in messages:
            if message.time:
                try:
                    message.time = to_iso_time(message.time, now)
                except ValueError:
                    self.gtl_logger.warning(f"Unknown time format '{message.time}', the time is kept as shown in Slack")
        return messages

    def export_messages(self, file_path: str, conversation: str = None, message_count: int = None) -> None:
        """
        Exports the messages in the current or selected channel or direct message conversation to a CSV file, oldest
        first. By default all messages are exported, see get_messages.

        The columns are the sender, the time (ISO 8601, in the time zone of the device), the text and the attachments
        of each message. Slack only shows the time of the first of consecutive messages of the same sender, the time of
        the others is left empty.

        :param file_path: The path of the CSV file to write.
        :param conversation: The name of the conversation: a channel with a '#' prefix (e.g. '#general'), or a direct
        message conversation with an optional '@' prefix (e.g. '@Bob' or 'Bob').
        :param message_count: Optional. The maximum number of messages: only the last messages of the conversation
        are exported. By default, all messages are exported.
        """
        messages = self.get_messages(conversation=conversation, message_count=message_count)
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(field.name for field in fields(Message))
            writer.writerows(astuple(message) for message in messages)
        self.gtl_logger.info(f'Exported {len(messages)} messages to {file_path}')

    def _swipe_messages_list(self, up: bool, until: Callable[[str, int], bool], slow: bool = False,
                             max_swipes: int = 500) -> bool:
        """
        Swipes the messages list up or down until the given condition holds, or until the end of the list is reached.

        :param up: True to swipe towards older messages, False to swipe towards newer messages.
        :param until: Function that is called with the page source of each screen and the distance swiped since the
        previous screen in pixels (0 for the first screen), the swiping stops when it returns True.
        :param slow: True to swipe in short, slow swipes, which is needed when messages are collected while swiping.
        :param max_swipes: The maximum number of swipes.
        :return: True if the condition holds, False if the end of the list or the maximum number of swipes was reached
        first.
        """
        messages_list = self.driver.get_element(CHAT_MESSAGES_LIST).rect
        x = messages_list['x'] + messages_list['width'] / 2
        # The swipes are done in the lower part of the list: Slack can show a tooltip over the top of the list, which is
        # not in the page source, and a swipe that starts on it does not scroll the list.
        if slow:
            # Short, slow swipes without fling: messages are only collected when they are completely shown, so every
            # message must be completely shown on at least one screen. This holds for messages up to 70% of the height
            # of the list.
            start, end, duration = 0.9, 0.6, 1500
        else:
            start, end, duration = 0.9, 0.4, 500
        if up:
            start, end = end, start
        start_y = messages_list['y'] + messages_list['height'] * start
        end_y = messages_list['y'] + messages_list['height'] * end
        page_source = self.driver.driver.page_source
        swiped = 0
        for _ in range(max_swipes):
            if until(page_source, swiped):
                return True
            swiped = round(abs(end_y - start_y))
            self.driver.driver.swipe(x, start_y, x, end_y, duration)
            time.sleep(0.5)
            new_page_source = self.driver.driver.page_source
            if up and new_page_source == page_source:
                # Slack loads older messages while swiping up, give it some time before deciding this is the end
                time.sleep(2)
                new_page_source = self.driver.driver.page_source
            if new_page_source == page_source:
                return False
            page_source = new_page_source
        # the messages collected so far are kept, get_messages warns that messages may be missing
        self.gtl_logger.warning(f'Stopped swiping after {max_swipes} swipes')
        return False

    def _find_picture(self, picture_index: int) -> str:
        """
        Given a picture index n, this method will swipe until that picture is on screen and return the xpath locator for
        the nth picture.

        :param picture_index: The index of the picture, 1 being the most recent picture on the device.
        :return: The XPath of the picture.
        """
        strip = self.driver.get_element(ATTACHMENTS_MEDIA_STRIP).rect
        y = strip['y'] + strip['height'] / 2
        # Short, slow swipes, so the strip stops when the swipe ends and moves as far as the swipe
        start_x, end_x = strip['x'] + strip['width'] * 0.65, strip['x'] + strip['width'] * 0.35
        strip_left, strip_right = strip['x'], strip['x'] + strip['width']
        found, previous_screen, scrolled = 0, [], 0
        while True:
            pictures = _pictures_in_strip(self.driver.driver.page_source)
            # Pictures are told apart by their position, as pictures can have the same description. Only completely
            # shown pictures are counted, as the position of a partly shown picture is cut off.
            shown = [index for index, (left, right, _) in enumerate(pictures)
                     if strip_left < left and right < strip_right]
            # The strip scrolls to the left and shows new pictures on the right, while new_items expects them at low
            # positions: the positions are mirrored
            screen = [(-pictures[index][1], -pictures[index][0], pictures[index][2]) for index in reversed(shown)]
            new_pictures = len(new_items(previous_screen, screen, scrolled, (-strip_right, -strip_left))) \
                if screen else 0
            if not new_pictures:
                raise PumaClickException(f'Could not find picture {picture_index}, only {found} pictures were found')
            if found + new_pictures >= picture_index:
                # the new pictures are the last completely shown pictures
                index = shown[len(shown) - new_pictures + picture_index - found - 1]
                return f'({ATTACHMENTS_PICTURES})[{index + 1}]'
            found += new_pictures
            previous_screen, scrolled = screen, round(start_x - end_x)
            self.driver.driver.swipe(start_x, y, end_x, y, 1500)
            time.sleep(0.5)


def _pictures_in_strip(page_source: str) -> list[tuple[int, int, str]]:
    """
    The pictures in the media strip of the attachments menu, from left to right, as (left, right, description) triples.
    """
    strip = next((element for element in ElementTree.fromstring(page_source).iter()
                  if element.get('resource-id') == ATTACHMENTS_MEDIA_STRIP_ID), None)
    if strip is None:
        return []
    return [(*(int(value) for value in re.findall(r'\d+', picture.get('bounds'))[::2]), picture.get('content-desc'))
            for picture in strip if (picture.get('content-desc') or '').startswith('Photo, ')]

