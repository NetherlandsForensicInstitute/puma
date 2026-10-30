"""
Parsing of the messages in a Slack conversation, as used for getting and exporting messages.
"""
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, TypeVar
from xml.etree import ElementTree

from puma.apps.android.slack.xpaths import MESSAGES_LIST_ID, MESSAGE_ID, MESSAGE_SENDER_ID, MESSAGE_TIME_ID, \
    MESSAGE_TEXT_ID, MESSAGE_FILE_ID, ZERO_WIDTH_SPACE
from puma.state_graph.puma_driver import PumaClickException

# A swipe scrolls a little less than its length, as Android ignores the first pixels of a swipe: measured 9 to 13 pixels
SWIPE_SLOP = 10
SCROLL_TOLERANCE = 30
_Item = TypeVar('_Item')

_WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


@dataclass
class Message:
    """
    A message in a Slack conversation.

    :param sender: The name of the sender, or None if it is not known because the beginning of the conversation was not
    reached.
    :param time: The time of the message in ISO 8601 (e.g. '2026-09-29T14:06:00'), in the time zone of the device.
    Slack does not show seconds, so these are always 0. Slack only shows the time of the first of consecutive messages
    of the same sender, the time of the others is None.
    :param text: The text of the message, empty if the message only contains a file.
    :param attachments: The files in the message as described by Slack, e.g. 'image: IMG-20260206-WA0002.jpeg'.
    """
    sender: Optional[str]
    time: Optional[str]
    text: str
    attachments: str


def parse_messages(page_source: str) -> list[tuple[int, int, Message]]:
    """
    Parses the messages shown in a conversation. Messages that are only partly shown are skipped, unless they are too
    large to be shown completely. Messages without a header (the first of consecutive messages of the same sender has
    one) get None as sender. The time of the messages is the time as shown in Slack, see to_iso_time.

    :param page_source: The page source of the conversation screen.
    :return: The messages that are shown, from top to bottom, each with the position of its top and bottom.
    :raises PumaClickException: If the list of messages is not in the page source, e.g. when a pop-up covers it.
    """
    messages_list = next((element for element in ElementTree.fromstring(page_source).iter()
                          if element.get('resource-id') == MESSAGES_LIST_ID), None)
    if messages_list is None:
        raise PumaClickException('The list of messages is not shown in the conversation')
    _, list_top, _, list_bottom = _bounds(messages_list)
    messages = []
    for message_element in messages_list:
        if message_element.get('resource-id') != MESSAGE_ID:
            continue
        _, top, _, bottom = _bounds(message_element)
        if (top <= list_top or bottom >= list_bottom) and bottom - top < list_bottom - list_top:
            continue
        messages.append((top, bottom, _parse_message(message_element)))
    return messages


def new_items(previous: list[tuple[int, int, _Item]], current: list[tuple[int, int, _Item]], scrolled: int,
              visible: tuple[int, int]) -> list[tuple[int, int, _Item]]:
    """
    Returns the items on the current screen that were not on the previous screen, using where the items are. The items
    on both screens are (start, end, item) triples, sorted by position, of the items that are shown completely.
    Scrolling moved the items `scrolled` pixels towards higher positions, which shows new items at lower positions. As
    the items are compared by position, identical items, such as two messages 'ok', are told apart.

    :param previous: The items on the previous screen. When this is empty, all current items are new.
    :param current: The items on the current screen.
    :param scrolled: The distance that was swiped since the previous screen, in pixels.
    :param visible: The start and end of the part of the screen in which items are shown.
    :return: The new items, as (start, end, item) triples.
    """
    # shortcut: at the end of the list a swipe scrolls less, which is found from the items on both screens. When the
    # items both screens show are identical and equally large, such as a run of 'ok' at the very beginning of a
    # conversation, the swiped distance can fit as well, and too many items are new. Upgrade if this shows up in
    # exports, e.g. by checking whether the list reached its end.
    if not previous:
        return current
    # where the first item of the previous screen is now: everything before it is new
    first_known = previous[0][0] + _shift(previous, current, scrolled, visible)
    return [(start, end, item) for start, end, item in current if start < first_known - SCROLL_TOLERANCE]


def _shift(previous: list[tuple[int, int, _Item]], current: list[tuple[int, int, _Item]], scrolled: int,
           visible: tuple[int, int]) -> int:
    """
    The distance the items moved between two screens. This is the swiped distance, unless the items on the screens
    contradict it: at the end of the list, a swipe scrolls less. The shift is then the one that moves most items of the
    previous screen onto the same item on the current screen.
    """
    swiped = scrolled - SWIPE_SLOP
    def fit(shift: int) -> tuple[int, int]:
        """
        The number of items of the previous screen that land on the same item when moved, and the number that should
        be shown completely when moved, but are not.
        """
        matches = conflicts = 0
        for start, end, item in previous:
            if any(abs(other_start - start - shift) <= SCROLL_TOLERANCE and other == item
                   for other_start, _, other in current):
                matches += 1
            # the items can have moved a little less than the shift, never more
            elif visible[0] < start + shift - SCROLL_TOLERANCE and end + shift < visible[1]:
                conflicts += 1
        return matches, conflicts

    def preference(shift: int) -> tuple[bool, int, int]:
        matches, conflicts = fit(shift)
        as_swiped = abs(shift - swiped) <= SCROLL_TOLERANCE and not conflicts
        return not as_swiped, conflicts - matches, abs(shift - swiped)

    candidates = {swiped} | {other_start - start for start, _, item in previous for other_start, _, other in current
                             if other == item
                             and -SCROLL_TOLERANCE <= other_start - start <= scrolled + SCROLL_TOLERANCE}
    return min(candidates, key=preference)


def to_iso_time(shown_time: str, now: datetime) -> str:
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
    time_of_day = _strptime(match['time'], ('%I:%M %p', '%H:%M')).time()
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
        month = _strptime(day_match['month'], ('%b', '%B')).month
        day_of_month = int(day_match['day'])
        if day_match['year']:
            day = datetime(int(day_match['year']), month, day_of_month).date()
        else:
            # without a year, the date is in the current year, unless that date is still to come
            day = datetime(now.year, month, day_of_month).date()
            if day > now.date():
                day = datetime(now.year - 1, month, day_of_month).date()
    return datetime.combine(day, time_of_day).isoformat()


def _bounds(element: ElementTree.Element) -> tuple[int, int, int, int]:
    return tuple(int(value) for value in re.findall(r'\d+', element.get('bounds')))


def _parse_message(message_element: ElementTree.Element) -> Message:
    """
    Parses a single message element. A message without a header (the first of consecutive messages of the same sender
    has one) gets None as sender and time.
    """
    sender, message_time, texts, attachments = None, None, [], []
    for element in message_element.iter():
        resource_id = element.get('resource-id')
        # Slack inserts zero-width spaces, e.g. after emoji and after hyphens in names
        if resource_id == MESSAGE_SENDER_ID:
            sender = element.get('text').replace(ZERO_WIDTH_SPACE, '')
        elif resource_id == MESSAGE_TIME_ID:
            message_time = element.get('content-desc')
        elif resource_id == MESSAGE_TEXT_ID:
            texts.append(element.get('text').replace(ZERO_WIDTH_SPACE, ''))
        elif resource_id == MESSAGE_FILE_ID:
            # e.g. 'Open image: IMG-20260206-WA0002.jpeg.'
            attachments.append(re.sub(r'^Open (.*?)\.?$', r'\1', element.get('content-desc')))
    return Message(sender, message_time, '\n'.join(texts), '\n'.join(attachments))


def _strptime(value: str, formats: tuple[str, ...]) -> datetime:
    """Parses the value with the first of the formats that matches."""
    for value_format in formats:
        try:
            return datetime.strptime(value, value_format)
        except ValueError:
            pass
    raise ValueError(f'Unknown format: {value}')
