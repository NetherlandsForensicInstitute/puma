import csv
import re
import time
from dataclasses import dataclass, astuple, fields
from datetime import datetime, timedelta
from typing import Optional
from xml.etree import ElementTree

from puma.apps.android.slack.xpaths import HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR, HOME_CHANNEL_BUTTON, \
    CHAT_TITLE, \
    CHAT_BACK_BUTTON, CHAT_TEXT_INPUT, HOME_DIRECT_MESSAGE_BUTTON, CHAT_ATTACHMENTS_BUTTON, CHAT_SEND_BUTTON, \
    ATTACHMENTS_UPLOAD_FILE_BUTTON, ATTACHMENTS_ATTACH_PHOTOS_BUTTON, ATTACHMENTS_MEDIA_STRIP, ATTACHMENTS_PICTURES, \
    ATTACHMENTS_PICTURE, ATTACHMENTS_DONE_BUTTON, CHAT_MESSAGES_LIST, CHAT_BEGINNING_OF_CONVERSATION, MESSAGES_LIST_ID, \
    MESSAGE_ID, MESSAGE_SENDER_ID, MESSAGE_TIME_ID, MESSAGE_TEXT_ID, MESSAGE_FILE_ID, ZERO_WIDTH_SPACE
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, supported_version, Platform
from puma.state_graph.state import SimpleState, ContextualState, State, compose_clicks
from puma.state_graph.state_graph import StateGraph


@dataclass
class Message:
    """
    A message in a Slack conversation.

    :param sender: The name of the sender.
    :param time: The time of the message in ISO 8601 (e.g. '2026-09-29T14:06:00'), in the time zone of the device.
    Slack does not show seconds, so these are always 0. Slack only shows the time of the first of consecutive messages
    of the same sender, the time of the others is None.
    :param text: The text of the message, empty if the message only contains a file.
    :param attachments: The files in the message as described by Slack, e.g. 'image: IMG-20260206-WA0002.jpeg'.
    """
    sender: str
    time: Optional[str]
    text: str
    attachments: str


class SlackChatState(SimpleState, ContextualState):
    """
    State defining a Slack channel screen
    """

    def __init__(self, parent_state: State):
        super().__init__([CHAT_BACK_BUTTON, CHAT_TEXT_INPUT],
                         invalid_xpaths=[ATTACHMENTS_UPLOAD_FILE_BUTTON],
                         parent_state=parent_state,
                         parent_state_transition=SlackChatState.back_to_home)

    @staticmethod
    def back_to_home(driver: PumaDriver):
        # When the keyboard is open, going back only closes the keyboard
        if driver.driver.is_keyboard_shown():
            driver.back()
        driver.back()

    def validate_context(self, driver: PumaDriver, channel: str = None, direct_message: str = None) -> bool:
        if channel or direct_message:
            return driver.is_present(CHAT_TITLE.format(chat_title=(channel or direct_message)))
        return True

    @staticmethod
    def go_to_chat(driver: PumaDriver, channel: str = None, direct_message: str = None):
        if not channel and not direct_message:
            raise ValueError(f'Cannot open a channel without a channel or DM name')
        if channel:
            chat_xpath = HOME_CHANNEL_BUTTON.format(channel_name=channel)
        else:
            chat_xpath = HOME_DIRECT_MESSAGE_BUTTON.format(direct_message=direct_message)
        # The home screen might still be scrolled from an earlier visit, so search down first and then back up
        try:
            driver.swipe_to_find_element(chat_xpath, max_swipes=20, swipe_down=True)
        except PumaClickException:
            driver.swipe_to_find_element(chat_xpath, max_swipes=20, swipe_down=False)
        driver.click(chat_xpath)


@supported_version("26.09.50.0")
class Slack(StateGraph):
    platform = Platform.ANDROID

    def __init__(self, device_udid):
        """
        Initializes Slack messenger with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        """
        package = 'com.Slack'
        StateGraph.__init__(self, device_udid, package)

    home_state = SimpleState(
        [HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR],
        invalid_xpaths=[CHAT_BACK_BUTTON],
        initial_state=True
    )
    chat_state = SlackChatState(parent_state=home_state)
    attachments_state = SimpleState([ATTACHMENTS_UPLOAD_FILE_BUTTON], parent_state=chat_state)

    home_state.to(chat_state, SlackChatState.go_to_chat)
    chat_state.to(attachments_state, compose_clicks([CHAT_ATTACHMENTS_BUTTON], name='go_to_attachments'))

    @action(chat_state)
    def send_message(self, message: str, channel: str = None, direct_message: str = None):
        self.driver.send_keys(CHAT_TEXT_INPUT, message)
        self.driver.press_enter()

    # The attachments menu is opened in the action itself rather than by starting from the attachments state: the
    # conversation is not visible in the attachments menu, so the context of that state cannot be validated
    @action(chat_state)
    def send_picture(self, picture_id: int = 1, caption: str = None, channel: str = None, direct_message: str = None):
        """
        Sends a picture in the current or selected channel or direct message conversation.

        :param picture_id: The index of the picture to send, 1 being the most recent picture on the device.
        :param caption: The caption to add to the picture.
        :param channel: The name of the channel to send the picture in.
        :param direct_message: The name of the direct message conversation to send the picture in.
        """
        if picture_id < 1:
            raise ValueError(f'The picture index starts at 1, got {picture_id}')
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

    @action(chat_state)
    def get_messages(self, channel: str = None, direct_message: str = None) -> list[Message]:
        """
        Returns all messages in the current or selected channel or direct message conversation, oldest first. The
        conversation is scrolled to the beginning, and then scrolled down to collect the messages. Messages are only
        collected when they are shown completely: messages that are larger than the screen are collected as well, but
        messages that are almost as large as the screen (larger than 70% of the conversation view) can be missed.

        :param channel: The name of the channel.
        :param direct_message: The name of the direct message conversation.
        :return: The messages, with their sender, time, text and attachments.
        """
        # Slack shows relative dates ('Today') and dates without a year in the time zone of the device
        now = datetime.fromisoformat(self.driver.driver.get_device_time('YYYY-MM-DDTHH:mm:ss'))
        self._swipe_messages_list(up=True, until=lambda: self.driver.is_present(CHAT_BEGINNING_OF_CONVERSATION))
        messages = []

        def collect() -> bool:
            nonlocal messages
            messages = _merge_messages(messages, _parse_messages(self.driver.driver.page_source))
            return False

        collect()
        self._swipe_messages_list(up=False, until=collect)
        # Consecutive messages of the same sender have no header, the sender is the sender of the message above
        for previous, message in zip(messages, messages[1:]):
            message.sender = message.sender or previous.sender
        for message in messages:
            if message.time:
                try:
                    message.time = _to_iso_time(message.time, now)
                except ValueError:
                    self.gtl_logger.warning(f"Unknown time format '{message.time}', the time is kept as shown in Slack")
        return messages

    def export_messages(self, file_path: str, channel: str = None, direct_message: str = None):
        """
        Exports all messages in the current or selected channel or direct message conversation to a CSV file, oldest
        first. The columns are the sender, the time (ISO 8601, in the time zone of the device), the text and the
        attachments of each message.
        Slack only shows the time of the first of consecutive messages of the same sender, the time of the others is
        left empty.

        :param file_path: The path of the CSV file to write.
        :param channel: The name of the channel.
        :param direct_message: The name of the direct message conversation.
        """
        messages = self.get_messages(channel=channel, direct_message=direct_message)
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(field.name for field in fields(Message))
            writer.writerows(astuple(message) for message in messages)
        self.gtl_logger.info(f'Exported {len(messages)} messages to {file_path}')

    def _swipe_messages_list(self, up: bool, until, max_swipes: int = 500):
        """
        Swipes the messages list up or down until the given condition holds, or until the end of the list is reached.

        :param up: True to swipe towards older messages, False to swipe towards newer messages.
        :param until: Function without arguments, the swiping stops when it returns True.
        :param max_swipes: The maximum number of swipes.
        """
        messages_list = self.driver.get_element(CHAT_MESSAGES_LIST).rect
        x = messages_list['x'] + messages_list['width'] / 2
        if up:
            # fast swipes: no messages are collected while swiping up
            start, end, duration = 0.2, 0.8, 500
        else:
            # Short, slow swipes without fling: messages are only collected when they are completely shown, so every
            # message must be completely shown on at least one screen. This holds for messages up to 70% of the height
            # of the list.
            start, end, duration = 0.65, 0.35, 1500
        start_y = messages_list['y'] + messages_list['height'] * start
        end_y = messages_list['y'] + messages_list['height'] * end
        for _ in range(max_swipes):
            if until():
                return
            page_before = self.driver.driver.page_source
            self.driver.driver.swipe(x, start_y, x, end_y, duration)
            time.sleep(0.5)
            if self.driver.driver.page_source == page_before:
                # Slack loads older messages while swiping up, give it some time before deciding this is the end
                time.sleep(2)
                if self.driver.driver.page_source == page_before:
                    until()
                    return
        raise PumaClickException(f'Did not reach the end of the conversation after {max_swipes} swipes')

    def _find_picture(self, picture_id: int) -> str:
        """
        Finds a picture in the photo strip of the attachments menu. The strip only shows a few pictures at a time, so it
        is swiped to the left until the picture is shown.

        :param picture_id: The index of the picture, 1 being the most recent picture on the device.
        :return: The XPath of the picture.
        """
        seen_pictures = []
        while True:
            pictures = [element.get_attribute('content-desc') for element in self.driver.get_elements(ATTACHMENTS_PICTURES)]
            new_pictures = [picture for picture in pictures if picture not in seen_pictures]
            if not new_pictures:
                raise PumaClickException(f'Could not find picture {picture_id}, only {len(seen_pictures)} pictures were found')
            seen_pictures += new_pictures
            if len(seen_pictures) >= picture_id:
                return ATTACHMENTS_PICTURE.format(content_desc=seen_pictures[picture_id - 1])
            strip = self.driver.get_element(ATTACHMENTS_MEDIA_STRIP).rect
            y = strip['y'] + strip['height'] / 2
            self.driver.driver.swipe(strip['x'] + strip['width'] * 0.8, y, strip['x'] + strip['width'] * 0.2, y, 500)


def _bounds(element: ElementTree.Element) -> tuple[int, int, int, int]:
    return tuple(int(value) for value in re.findall(r'\d+', element.get('bounds')))


def _parse_messages(page_source: str) -> list[Message]:
    """
    Parses the messages shown in a conversation. Messages that are only partly shown are skipped, unless they are too
    large to be shown completely. Messages without a header (the first of consecutive messages of the same sender has
    one) get None as sender.
    """
    messages_list = next(element for element in ElementTree.fromstring(page_source).iter()
                         if element.get('resource-id') == MESSAGES_LIST_ID)
    _, list_top, _, list_bottom = _bounds(messages_list)
    messages = []
    for message_element in messages_list:
        if message_element.get('resource-id') != MESSAGE_ID:
            continue
        _, top, _, bottom = _bounds(message_element)
        if (top <= list_top or bottom >= list_bottom) and bottom - top < list_bottom - list_top:
            continue
        messages.append(_parse_message(message_element))
    return messages


def _parse_message(message_element: ElementTree.Element) -> Message:
    """
    Parses a single message element. A message without a header (the first of consecutive messages of the same sender
    has one) gets None as sender and time.
    """
    sender, message_time, texts, attachments = None, None, [], []
    for element in message_element.iter():
        resource_id = element.get('resource-id')
        if resource_id == MESSAGE_SENDER_ID:
            sender = element.get('text')
        elif resource_id == MESSAGE_TIME_ID:
            message_time = element.get('content-desc')
        elif resource_id == MESSAGE_TEXT_ID:
            # Slack inserts zero-width spaces, e.g. after emoji
            texts.append(element.get('text').replace(ZERO_WIDTH_SPACE, ''))
        elif resource_id == MESSAGE_FILE_ID:
            # e.g. 'Open image: IMG-20260206-WA0002.jpeg.'
            attachments.append(re.sub(r'^Open (.*?)\.?$', r'\1', element.get('content-desc')))
    return Message(sender, message_time, '\n'.join(texts), '\n'.join(attachments))


def _merge_messages(messages: list[Message], new_messages: list[Message]) -> list[Message]:
    """
    Appends the messages on a new screen to the messages found so far. The screens overlap, so the largest overlap
    between the end of the messages and the start of the new messages is not added again.
    """
    for overlap in range(min(len(messages), len(new_messages)), 0, -1):
        if messages[-overlap:] == new_messages[:overlap]:
            return messages + new_messages[overlap:]
    return messages + new_messages


_WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def _to_iso_time(shown_time: str, now: datetime) -> str:
    """
    Converts a time as shown in Slack to ISO 8601, e.g. 'Sep 29th at 2:06 PM' to '2026-09-29T14:06:00'.

    Slack shows the date as 'Today', 'Yesterday', a weekday for the last week, or a month and day, with the year only
    when it is not the current year. The time is shown with a 12-hour or 24-hour clock, depending on the device.

    :param shown_time: The time as shown in Slack, e.g. 'Today at 4:01 PM' or 'Sep 29th, 2025 at 14:06'.
    :param now: The current time on the device, to resolve relative dates and dates without a year.
    :return: The time in ISO 8601, without time zone.
    :raises ValueError: If the time format is unknown.
    """
    # Android puts a (narrow) no-break space before AM/PM
    match = re.fullmatch(r'(?P<date>.+) at (?P<time>.+)', ' '.join(shown_time.split()))
    if not match:
        raise ValueError(f'Unknown time format: {shown_time}')
    time_of_day = _parse_time_of_day(match['time'])
    date = match['date']
    if date == 'Today':
        day = now.date()
    elif date == 'Yesterday':
        day = now.date() - timedelta(days=1)
    elif date in _WEEKDAYS:
        # a day in the last week, today is shown as 'Today'
        day = now.date() - timedelta(days=(now.weekday() - _WEEKDAYS.index(date)) % 7 or 7)
    else:
        day_match = re.fullmatch(r'(?P<month>[A-Z][a-z]+)\.? (?P<day>\d{1,2})(st|nd|rd|th)?(, (?P<year>\d{4}))?', date)
        if not day_match:
            raise ValueError(f'Unknown time format: {shown_time}')
        month = _parse_month(day_match['month'])
        day_of_month = int(day_match['day'])
        if day_match['year']:
            day = datetime(int(day_match['year']), month, day_of_month).date()
        else:
            # without a year, the date is in the current year, unless that date is still to come
            day = datetime(now.year, month, day_of_month).date()
            if day > now.date():
                day = datetime(now.year - 1, month, day_of_month).date()
    return datetime.combine(day, time_of_day).isoformat()


def _parse_time_of_day(shown_time: str):
    for time_format in ('%I:%M %p', '%H:%M'):
        try:
            return datetime.strptime(shown_time, time_format).time()
        except ValueError:
            pass
    raise ValueError(f'Unknown time format: {shown_time}')


def _parse_month(month: str) -> int:
    for month_format in ('%b', '%B'):
        try:
            return datetime.strptime(month, month_format).month
        except ValueError:
            pass
    raise ValueError(f'Unknown month: {month}')
