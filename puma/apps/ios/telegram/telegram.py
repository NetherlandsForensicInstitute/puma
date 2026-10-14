import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from time import sleep
from typing import Optional

from puma.apps.ios.telegram import logger
from puma.apps.ios.telegram.locators import *
from puma.state_graph.action import action
from puma.state_graph.locators import to_by_value
from puma.state_graph.popup_handler import IOSAlertHandler
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, Platform, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

TELEGRAM_BUNDLE_ID = 'ph.telegra.Telegraph'

# The date of a message as shown by Telegram, e.g. '14 Oct 2026 at 13:01'. This depends on the language of the device.
# For messages sent from this device, the date is the second last line of the value, which is used for dates in other
# formats. Only messages of today have been seen.
_DATE = re.compile(r'^\d{1,2} \w{3} \d{4} at \d{2}:\d{2}$')


class TelegramError(Exception):
    """
    Raised when Telegram refuses an action, or when an element needed for an action is not found.
    """
    pass


@dataclass
class Message:
    """
    A message in a chat.

    :param sender: The name of the sender, or None for messages sent from this device.
    :param text: The text of the message. For a photo, this is its caption (if any).
    :param time: The date and time of the message, as shown on the screen (e.g. '14 Oct 2026 at 13:01').
    :param status: The status shown by Telegram, e.g. 'Seen by recipient'. Empty for messages that are sent, but not
    seen yet.
    :param kind: The kind of message, e.g. 'message' or 'photo'. A shared location is a 'message' with the text
    'Location'.
    """
    sender: Optional[str]
    text: str
    time: str
    status: str = ''
    kind: str = 'message'

    @property
    def sent_by_me(self) -> bool:
        return self.sender is None


def _parse_message(name: str, value: str) -> Optional[Message]:
    """
    Parses a message from the name and value of its element: the name is 'Your <kind>' for messages sent from this
    device, the value has the lines of the message: its text, the date and the status.

    :return: The message, or None if the value is not the value of a message.
    """
    lines = (value or '').split('\n')
    dates = [i for i, line in enumerate(lines) if _DATE.match(line)]
    if dates:
        date = dates[-1]
    elif name.startswith(SENT_PREFIX) and len(lines) >= 3:
        date = len(lines) - 2
    else:
        return None
    text = '\n'.join(lines[:date]).strip('\n')
    caption = text.removeprefix(CAPTION_PREFIX) if text.startswith(CAPTION_PREFIX) else text
    status = '\n'.join(lines[date + 1:])
    if name.startswith(SENT_PREFIX):
        return Message(None, caption, lines[date], status, name.removeprefix(SENT_PREFIX))
    # the name of received messages could not be tested yet, as it needs a message sent by someone else
    return Message(name, caption, lines[date], status)


def _parse_messages(page_source: str) -> list[Message]:
    """
    Parses the messages of a chat in the page source. Only the messages near the screen are in the page source.
    """
    messages = []
    for element in ElementTree.fromstring(page_source).iter():
        if element.get('type') in ('XCUIElementTypeOther', 'XCUIElementTypeImage') and element.get('name'):
            message = _parse_message(element.get('name'), element.get('value'))
            if message:
                messages.append(message)
    return messages


def _is_new_message(before: list[Message], after: list[Message], text: str) -> bool:
    """
    Whether a message with a text was added, from the messages on the screen before and after sending it. The status of
    messages changes while waiting (e.g. when the receiver reads them), so it is not compared. The latest message has to
    be a message with the text, and it is new when it has another time than the latest message before, or when there
    are more messages with this text on the screen than before. Two identical messages in the same minute are only
    recognized while the older one has not scrolled off the screen.
    """
    if not after or after[-1].text != text:
        return False
    if not before:
        return True

    def key(message: Message):
        return message.text, message.time, message.kind

    def count(messages: list[Message]):
        return sum(1 for message in messages if message.text == text)
    return key(after[-1]) != key(before[-1]) or count(after) > count(before)


def _pull_down(driver: PumaDriver):
    """
    Pulls a list down to its top. The search field of the overview is hidden behind the navigation bar when the list is
    scrolled down a little, and it cannot be tapped there.
    """
    size = driver.driver.get_window_size()
    driver.execute_script('mobile: dragFromToForDuration', {
        'fromX': size['width'] / 2, 'fromY': size['height'] * 0.35, 'toX': size['width'] / 2,
        'toY': size['height'] * 0.7, 'duration': 0.3})
    sleep(1)


def _open_search(driver: PumaDriver):
    # the field is hidden when the list is scrolled down a little. Pulling down at the top of the list does nothing.
    if driver.get_element(CONVERSATIONS_SEARCH_FIELD).get_attribute('hittable') != 'true':
        _pull_down(driver)
    driver.click(CONVERSATIONS_SEARCH_FIELD)
    driver.wait_until_present(SEARCH_FILTER_CHANNELS, timeout=5, description='the search screen')


def _close_search(driver: PumaDriver):
    driver.click(CONVERSATIONS_SEARCH_FIELD, SEARCH_CLOSE_WIDTH_RATIO)
    driver.wait_until_not_present(SEARCH_FILTER_CHANNELS, timeout=5, description='the search screen to close')


def _close_chat(driver: PumaDriver):
    """
    Closes a chat by swiping from the left edge of the screen, which does not always register on the first try.
    """
    for attempt in range(1, 5):
        if attempt > 1:
            driver.gtl_logger.info(f'The chat is still open, swiping back again (attempt {attempt})')
        driver.back()
        # a swipe on the overview itself does nothing, so a slow swipe followed by another one is harmless. The state
        # itself is used, so this condition cannot differ from the one of the state.
        try:
            driver.wait_until(lambda: Telegram.conversations_state.validate(driver), 3, 0.5)
            return
        except TimeoutError:
            pass
    raise TelegramError('Could not close the chat')


def _search_result(driver: PumaDriver, conversation: str, timeout: float = 10):
    """
    The first search result with exactly the name of a conversation: the topmost element with that name below the search
    field. The results of chats and contacts are above other results, such as public accounts.

    :return: The element, or None if there is no such result.
    """
    def find():
        field = driver.get_element(CONVERSATIONS_SEARCH_FIELD).rect
        bottom = field['y'] + field['height']
        by, value = to_by_value(conversation_row(conversation))
        # get_elements raises a click exception without results, which would make the framework retry the transition
        results = [element for element in driver.driver.find_elements(by=by, value=value)
                   if element.rect['y'] >= bottom]
        return sorted(results, key=lambda element: element.rect['y'])
    results = []
    for _ in range(int(timeout)):
        results = find()
        if results:
            break
        sleep(1)
    if len(results) > 1:
        logger.warning(f'Found {len(results)} search results named "{conversation}", using the first one')
    return results[0] if results else None


class ChatState(SimpleState, ContextualState):
    """
    A state representing an opened chat.
    """

    def __init__(self, parent_state):
        # the sheet of the send media button is shown on top of the chat, and keeps the chat in the element tree
        super().__init__(xpaths=[CHAT_SEND_MEDIA_BUTTON], invalid_xpaths=[ATTACH_GALLERY_TAB],
                         parent_state=parent_state, parent_state_transition=_close_chat)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True
        return driver.is_present(chat_header(conversation))

    @staticmethod
    def open_chat(driver: PumaDriver, conversation: str):
        """
        Opens a chat from the overview, by searching for it. Searching also finds chats that are not on the screen.
        Only the exact name of the chat is opened, as the search also suggests other chats and channels.
        """
        if not conversation:
            raise ValueError('Cannot open a chat without the name of the chat')
        driver.gtl_logger.info(f'Searching for chat "{conversation}"')
        _open_search(driver)
        driver.send_keys(CONVERSATIONS_SEARCH_FIELD, conversation)
        result = _search_result(driver, conversation)
        if result is None:
            _close_search(driver)
            raise TelegramError(f'There is no chat named "{conversation}"')
        driver.gtl_logger.info(f'Opening chat "{conversation}" from the search results')
        result.click()
        driver.wait_until_present(CHAT_SEND_MEDIA_BUTTON, timeout=10, description='the chat to open')


@supported_version("13.0")
class Telegram(StateGraph):
    """
    A class representing Telegram on iOS.

    Chats are identified by their name as shown in the overview: the name of the contact, or the name of the group.
    Telegram cannot be installed on a simulator, so a real device is needed.
    """
    platform = Platform.IOS

    # States
    # The search screen replaces the overview, but keeps the search field in the element tree.
    # The Contacts tab has the same search field as the Chats list, so the title of the Chats list is required. A chat or
    # the send media sheet could keep the overview in the element tree, so they are marked as invalid.
    conversations_state = SimpleState(xpaths=[CONVERSATIONS_SEARCH_FIELD, CONVERSATIONS_TITLE_BUTTON],
                                      invalid_xpaths=[SEARCH_FILTER_CHANNELS, CHAT_SEND_MEDIA_BUTTON,
                                                      ATTACH_GALLERY_TAB],
                                      initial_state=True)
    search_state = SimpleState(xpaths=[CONVERSATIONS_SEARCH_FIELD, SEARCH_FILTER_CHANNELS],
                               parent_state=conversations_state, parent_state_transition=_close_search)
    chat_state = ChatState(parent_state=conversations_state)
    send_media_state = SimpleState(xpaths=[ATTACH_GALLERY_TAB, ATTACH_LOCATION_TAB], parent_state=chat_state,
                                   parent_state_transition=compose_clicks([ATTACH_CLOSE_BUTTON], 'close_send_media'))

    # Transitions
    conversations_state.to(search_state, _open_search)
    conversations_state.to(chat_state, ChatState.open_chat)
    chat_state.to(send_media_state, compose_clicks([CHAT_SEND_MEDIA_BUTTON], 'open_send_media', wait=1))

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Telegram with a device UDID.

        :param device_udid: The unique device identifier of the iOS device.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, TELEGRAM_BUNDLE_ID, **kwargs)
        # With limited access to the photos, iOS regularly asks whether to select more photos. The selection is kept.
        self.add_popup_handlers(IOSAlertHandler([KEEP_CURRENT_SELECTION_BUTTON], [KEEP_CURRENT_SELECTION_BUTTON]))

    @action(chat_state)
    def send_message(self, message: str, conversation: str = None):
        """
        Sends a regular text based message.
        Can be done in a given conversation or the current conversation.

        :param message: the message to send
        :param conversation: the conversation (group or 1 on 1) to send the message in. Not needed when already in a conversation.
        """
        self.driver.send_keys(CHAT_INPUT, message)
        self.driver.gtl_logger.info('Pressing send button')
        self.driver.click(CHAT_SEND_BUTTON)

    @action(send_media_state, end_state=chat_state)
    def send_media_from_gallery(self, media_index: int | list[int], caption: str = None, conversation: str = None):
        """
        Sends one or more photos or videos from the gallery.
        Can be done in a given conversation or the current conversation.

        :param media_index: the index or indices of the media files to send. This is the 1-based index of the
        thumbnails in the media picker, after the camera.
        :param caption: An optional text message attached to the media file(s)
        :param conversation: the conversation (group or 1 on 1) to send the media in. Not needed when already in a
        conversation.
        """
        if not media_index:
            raise ValueError('Cannot send media from gallery without a proper set of indices')
        if isinstance(media_index, int):
            media_index = [media_index]
        self.driver.click(ATTACH_GALLERY_TAB)
        if not self.driver.wait_until_present(GALLERY_CAMERA, timeout=10, description='the gallery'):
            raise TelegramError('The gallery did not open. Does Telegram have access to the photos?')
        selected = 0
        for index in media_index:
            try:
                self.driver.click(gallery_media(index), GALLERY_SELECT_WIDTH_RATIO, GALLERY_SELECT_HEIGHT_RATIO)
                self.gtl_logger.info(f'Selected gallery item with index {index}')
                selected += 1
            except PumaClickException:
                logger.warning(f'Could not select media with index {index}. Are enough media files present?')
        if selected == 0:
            raise PumaClickException(f'Tried to select gallery items with indexes {media_index}, but could not '
                                     f'select any of them.')
        if caption:
            # an element click does not focus the field, a tap on its left side does
            self.driver.click(GALLERY_CAPTION_FIELD, 0.2, 0.5)
            sleep(1)
            self.driver.driver.switch_to.active_element.send_keys(caption)
            self.gtl_logger.info(f'Entered caption {caption}')
        self.driver.click(GALLERY_SEND_BUTTON)
        self.gtl_logger.info('Pressed send button')
        self.driver.wait_until_not_present(ATTACH_GALLERY_TAB, timeout=10, description='the gallery to close')

    @action(send_media_state, end_state=chat_state)
    def send_current_location(self, conversation: str = None):
        """
        Sends the current location.
        Can be done in a given conversation or the current conversation.

        :param conversation: the conversation (group or 1 on 1) to send the message in. Not needed when already in a
        conversation.
        """
        self.driver.click(ATTACH_LOCATION_TAB)
        if not self.driver.wait_until_present(LOCATION_PLACES_HEADER, timeout=15, description='the location screen'):
            raise TelegramError('The location screen did not open. Does Telegram have access to the location?')
        # the options to send the location have no name. They are the two rows above the header of the places: the first
        # one sends the current location, the second one starts sharing the live location, which is never used
        header = self.driver.get_element(LOCATION_PLACES_HEADER).rect
        rows = sorted((row for row in self.driver.get_elements(LOCATION_OPTION_ROWS) if row.rect['y'] < header['y']),
                      key=lambda row: row.rect['y'])
        if len(rows) != 2:
            raise TelegramError(f'Expected 2 options to share the location, but found {len(rows)}. Is the location '
                                f'already being shared?')
        # the chat stays in the element tree under the sheet, so the messages before sending are known
        before = _parse_messages(self.driver.driver.page_source)
        rows[0].click()
        if not self.driver.wait_until_not_present(ATTACH_LOCATION_TAB, timeout=10,
                                                  description='the location screen to close'):
            raise TelegramError('The location screen did not close. Was the location not sent?')
        if not self._wait_for_new_message('Location', before):
            raise TelegramError('The location was not sent')

    def _wait_for_new_message(self, text: str, before: list[Message], timeout: float = 10) -> bool:
        """
        Waits until a message with a text was added to the messages on the screen.
        """
        def new_message():
            return _is_new_message(before, _parse_messages(self.driver.driver.page_source), text)
        try:
            self.driver.wait_until(new_message, timeout, description=f'the message "{text}"')
            return True
        except TimeoutError:
            return False

    @action(chat_state)
    def get_messages(self, conversation: str = None) -> list[Message]:
        """
        Gets the messages of a conversation that are on the screen, which are the latest messages.

        :param conversation: the conversation (group or 1 on 1) to read. Not needed when already in a conversation.
        :return: The messages, the oldest first.
        """
        return _parse_messages(self.driver.driver.page_source)
