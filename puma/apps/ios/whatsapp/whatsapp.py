import re
import xml.etree.ElementTree as ElementTree
from contextlib import contextmanager
from dataclasses import dataclass
from time import sleep, time
from typing import Optional, Union

from selenium.common.exceptions import NoSuchElementException

from puma.apps.ios.whatsapp import logger
from puma.apps.ios.whatsapp.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, Platform, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

WHATSAPP_BUNDLE_ID = 'net.whatsapp.WhatsApp'


class WhatsAppError(Exception):
    """
    Raised when WhatsApp refuses an action, or when an element needed for an action is not found.
    """
    pass


@dataclass
class Message:
    """
    A message in a chat.

    :param sender: The name of the sender, or None for messages sent from this device.
    :param text: The text of the message.
    :param time: The time of the message, as shown on the screen (e.g. '14:45').
    :param status: The status of messages sent from this device: 'Sent', 'Delivered' or 'Read'. None for received
    messages.
    :param is_reply: Whether the message is a reply to another message.
    :param reply_to: The text of the message replied to, for replies.
    :param kind: The kind of message: 'message' for text messages, and e.g. 'contact' for a shared contact, of which the
    text is the name of the contact.
    """
    sender: Optional[str]
    text: str
    time: str
    status: Optional[str] = None
    is_reply: bool = False
    reply_to: Optional[str] = None
    kind: str = 'message'

    @property
    def sent_by_me(self) -> bool:
        return self.sender is None


def _strip(text: str) -> str:
    return text.replace('\u200e', '').strip()


# The start of the label of a message: 'Your <kind>, ' for sent messages, and '<kind>, ' for received messages
_MESSAGE_START = re.compile(r'\u200e(?P<sent>Your )?(?P<kind>[^,\n]+), ')
_STATUSES = ('Sent', 'Delivered', 'Read')
# WhatsApp spells the status Read as 'Red'
_STATUS_SPELLINGS = {'Red': 'Read'}


def _kind(kind: str) -> str:
    """
    The kind of a message, without details: the kind of a shared live location is followed by e.g. ': Live until 17:51'.
    WhatsApp spells it as 'llive location'.
    """
    kind = _strip(kind.split(':')[0]).lower().replace('llive', 'live')
    # stickers are described as 'Sticker with: <description>'
    return 'sticker' if kind == 'sticker with' else kind


def _parse_message(label: str) -> Optional[Message]:
    """
    Parses the label of a message: 'Your <kind>, <text>, <time>, Sent to <chat>, <status>' for sent messages, and
    '<kind>, <text>, <time>, Received from <sender>' for received messages. The text of a message can contain commas,
    so the label is split around the part with the chat or sender. Deleted messages have 'message' as kind without
    'Your', also when they were sent from this device.

    A reply has a label of multiple lines: 'Replying to <sender>.', the label of the message with a period at the end,
    'Quoted message.', and the text of the message replied to.
    """
    lines = label.split('\n')
    if len(lines) >= 3 and lines[0].startswith(REPLY_PREFIX) and _strip(lines[2]) == _strip(REPLY_QUOTED):
        message = _parse_message(lines[1].removesuffix('.'))
        if message:
            message.is_reply = True
            message.reply_to = '\n'.join(lines[3:]) or None
        return message
    start = _MESSAGE_START.match(label)
    if not start:
        return None
    rest = label[start.end():]
    if f', {SENT_TO}' in rest:
        content, _, after = rest.rpartition(f', {SENT_TO}')
        # the status is missing for messages that are not sent yet
        status = _strip(after.split(', ')[1]) if ', ' in after else None
        status = _STATUS_SPELLINGS.get(status, status)
        sender = None
    elif f', {RECEIVED_FROM}' in rest:
        content, _, after = rest.rpartition(f', {RECEIVED_FROM}')
        status = None
        # the sender can be followed by e.g. ', Opened' for an opened view once photo
        sender = _strip(after.split(', \u200e')[0])
    elif start.group('sent'):
        # some messages sent from this device, e.g. voice messages, do not mention the chat
        content, _, status = rest.rpartition(', ')
        status = _STATUS_SPELLINGS.get(_strip(status), _strip(status))
        if status not in _STATUSES:
            content, status = rest, None
        sender = None
    else:
        return None
    text, _, time_ = content.rpartition(', ')
    return Message(sender, _strip(text), time_, status, kind=_kind(start.group('kind')))


def _parse_messages(page_source: str) -> list[Message]:
    """
    Parses the messages in the element tree of a chat, from old to new.
    """
    root = ElementTree.fromstring(page_source)
    table = next((e for e in root.iter() if e.get('name') == 'ChatMessagesTableView'), None)
    if table is None:
        return []
    messages = []
    for cell in table:
        if cell.get('name') != CHAT_MESSAGE_CELL:
            continue
        for element in cell.iter():
            message = _parse_message(element.get('label') or '')
            if message:
                messages.append(message)
                break
    return messages


def _wait_for(driver: PumaDriver, *xpaths: str, timeout: float = 6) -> bool:
    """
    Waits until any of the elements is present. The elements are checked at least once, also with a timeout of 0.
    """
    end = time() + timeout
    while True:
        if any(driver.is_present(xpath) for xpath in xpaths):
            return True
        if time() >= end:
            return False
        sleep(0.5)


def _swipe_row_left(driver: PumaDriver, row: str):
    """
    Swipes a row of a list of chats all the way to the left, which archives the chat, or unarchives an archived chat.
    """
    rect = driver.get_element(row).rect
    y = rect['y'] + rect['height'] / 2
    driver.execute_script('mobile: dragFromToForDuration', {
        'fromX': rect['x'] + rect['width'] - 20, 'fromY': y, 'toX': rect['x'] + 20, 'toY': y, 'duration': 0.2})
    sleep(2)


def _find_row(driver: PumaDriver, row: str, description: str, max_swipes: int = 15):
    """
    Scrolls down a list of chats until a chat is present. Only the chats near the screen are in the element tree.
    """
    for _ in range(max_swipes):
        if driver.is_present(row):
            return
        driver.gtl_logger.info('Scrolling down the list of chats')
        driver._scroll_down()
    if not driver.is_present(row):
        raise WhatsAppError(f'Could not find {description}')


def _swipe_to_find(driver: PumaDriver, xpath: str, max_swipes: int = 4) -> bool:
    """
    Scrolls down until an element is present.

    :return: Whether the element was found.
    """
    if driver.is_present(xpath):
        return True
    try:
        driver.swipe_to_find_element(xpath, max_swipes=max_swipes)
        return True
    except PumaClickException:
        return False


def _tap_visible(driver: PumaDriver, xpath: str):
    """
    Taps the visible element of the elements matching a locator. Lists of contacts contain hidden copies of the same
    contact, e.g. in the list shown before searching.
    """
    elements = driver.get_elements(xpath)
    element = next((e for e in elements if e.get_attribute('visible') == 'true'), elements[-1])
    rect = element.rect
    driver.execute_script('mobile: tap', {'x': rect['x'] + rect['width'] / 2, 'y': rect['y'] + rect['height'] / 2})


def _close_search(driver: PumaDriver):
    driver.gtl_logger.info('Closing the search')
    driver.click(SEARCH_BACK_BUTTON)
    sleep(1)


def _close_chat(driver: PumaDriver):
    """
    Goes back from a chat to the overview. When the chat was opened from the search results, the search is closed as
    well.
    """
    driver.click(BACK_BUTTON)
    sleep(1)
    if driver.is_present(SEARCH_BACK_BUTTON):
        _close_search(driver)


def _close_new_chat(driver: PumaDriver):
    """
    Closes the new chat screen. While searching, the first press of the close button only ends the search.
    """
    for _ in range(2):
        driver.click(NEW_CHAT_CLOSE_BUTTON)
        sleep(1)
        if not driver.is_present(NEW_CHAT_SEARCH_FIELD):
            return


@contextmanager
def _short_idle_timeout(driver: PumaDriver):
    """
    The menu of a message keeps animating, so XCUITest waits up to 10 seconds for the app to become idle before every
    interaction with it. The timeout is lowered while the menu is used.
    """
    timeout = driver.driver.get_settings().get('waitForIdleTimeout', 10)
    driver.set_idle_timeout(1)
    try:
        yield
    finally:
        driver.set_idle_timeout(timeout)


def _scroll_to(driver: PumaDriver, xpath: str, description: str, max_swipes: int = 10) -> int:
    """
    Scrolls up in a chat until an element is present. Only the messages near the screen are in the element tree, so
    older messages have to be scrolled to.

    :return: The number of times scrolled up.
    """
    for swipes in range(max_swipes + 1):
        if driver.is_present(xpath):
            return swipes
        if swipes < max_swipes:
            driver.gtl_logger.info('Scrolling up to older messages')
            driver._scroll_up()
    raise WhatsAppError(f'Could not find {description}')


def _scroll_to_latest(driver: PumaDriver, swipes: int):
    for _ in range(swipes):
        driver.gtl_logger.info('Scrolling down to the latest messages')
        driver._scroll_down()


def _close_message_menu(driver: PumaDriver):
    """
    Closes the menu of a message, by tapping above it. The menu has no button to close it.
    """
    size = driver.driver.get_window_size()
    driver.execute_script('mobile: tap', {'x': size['width'] / 2, 'y': size['height'] * 0.12})
    sleep(1)


class MessageMenuHandler(PopUpHandler):
    """
    Closes the menu of a message when it is left open, e.g. after an interrupted action.
    """

    def __init__(self):
        super().__init__([MESSAGE_MENU], [])

    def dismiss_popup(self, driver: PumaDriver):
        driver.gtl_logger.info('Closing the menu of a message')
        _close_message_menu(driver)


def _close_sticker_tray(driver: PumaDriver):
    """
    Closes the sticker tray by tapping the messages above it. The close button of the tray ignores clicks and taps.
    """
    size = driver.driver.get_window_size()
    driver.execute_script('mobile: tap', {'x': size['width'] / 2, 'y': size['height'] * 0.3})
    sleep(1)


class StickerTrayHandler(PopUpHandler):
    """
    Closes the sticker tray when it is left open.
    """

    def __init__(self):
        super().__init__([STICKER_TRAY], [])

    def dismiss_popup(self, driver: PumaDriver):
        driver.gtl_logger.info('Closing the sticker tray')
        _close_sticker_tray(driver)


class ChatState(SimpleState, ContextualState):
    """
    A state representing an opened chat.
    """

    def __init__(self, parent_state):
        super().__init__(xpaths=[CHAT_MESSAGES_TABLE, CHAT_HEADER],
                         invalid_xpaths=[SCREENS_ON_TOP_OF_CHAT],
                         parent_state=parent_state,
                         parent_state_transition=_close_chat)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True
        return driver.get_element(CHAT_HEADER).get_attribute('label') == conversation

    @staticmethod
    def open_chat(driver: PumaDriver, conversation: str):
        """
        Opens a chat from the overview. When the chat is not on the screen, it is searched for.
        """
        if not conversation:
            raise ValueError('Cannot open a chat without the name of the chat')
        if driver.is_present(conversation_row(conversation)):
            try:
                driver.gtl_logger.info(f'Opening chat "{conversation}"')
                driver.click(conversation_row(conversation))
                sleep(1)
                return
            except (PumaClickException, NoSuchElementException):
                # the list of chats changes when messages come in
                driver.gtl_logger.info(f'Chat "{conversation}" moved, searching for it instead')
        driver.gtl_logger.info(f'Searching for chat "{conversation}"')
        driver.send_keys(CONVERSATIONS_SEARCH_FIELD, conversation)
        if not _wait_for(driver, search_result_chat(conversation), timeout=15):
            _close_search(driver)
            raise WhatsAppError(f'There is no chat named "{conversation}"')
        driver.gtl_logger.info(f'Opening chat "{conversation}" from the search results')
        driver.click(search_result_chat(conversation))
        sleep(1)


class ChatInfoState(SimpleState, ContextualState):
    """
    A state representing the info of a chat: the contact info of a contact, or the group info of a group.
    """

    def __init__(self, parent_state):
        super().__init__(xpaths=[CHAT_INFO, BACK_BUTTON], parent_state=parent_state,
                         parent_state_transition=compose_clicks([BACK_BUTTON], 'close_chat_info'))

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        # the info does not show the name of the chat in a fixed place, so the chat it was opened from is trusted
        return True


@supported_version("26.38.74")
class WhatsApp(StateGraph):
    """
    A class representing WhatsApp Messenger on iOS.

    Chats are identified by their name as shown in the overview: the name of the contact, or the name of the group.
    WhatsApp cannot be installed on a simulator, so a real device is needed.
    """
    platform = Platform.IOS

    # States
    # The new chat screen and the search results are shown on top of the overview, while the overview stays in the
    # element tree. Therefore these are marked as invalid. States are recognized with as few lookups as possible, as
    # every lookup takes seconds when there are many chats.
    # The new chat button is only shown on the overview. A chat is not shown on top of the overview: when a chat is
    # opened, the overview is not in the element tree.
    conversations_state = SimpleState(xpaths=[CONVERSATIONS_NEW_CHAT_BUTTON],
                                      invalid_xpaths=[SCREENS_ON_TOP_OF_OVERVIEW],
                                      initial_state=True)
    new_chat_state = SimpleState(xpaths=[NEW_CHAT_SEARCH_FIELD],
                                 parent_state=conversations_state,
                                 parent_state_transition=_close_new_chat)
    chat_state = ChatState(parent_state=conversations_state)
    chat_settings_state = ChatInfoState(parent_state=chat_state)
    settings_state = SimpleState(xpaths=[SETTINGS_EDIT_PROFILE_BUTTON, SETTINGS_BROADCAST_LISTS],
                                 parent_state=conversations_state,
                                 parent_state_transition=compose_clicks([TAB_CHATS], 'open_chats_tab'))
    profile_state = SimpleState(xpaths=[PROFILE_ABOUT, PROFILE_EDIT_PHOTO_BUTTON], parent_state=settings_state,
                                parent_state_transition=compose_clicks([BACK_BUTTON], 'close_profile'))
    updates_state = SimpleState(xpaths=[UPDATES_TEXT_STATUS_BUTTON, UPDATES_CAMERA_STATUS_BUTTON],
                                invalid_xpaths=[STATUS_TEXT_FIELD],
                                parent_state=conversations_state,
                                parent_state_transition=compose_clicks([TAB_CHATS], 'open_chats_tab'))
    voice_call_state = SimpleState(xpaths=[CALL_END_BUTTON, CALL_VOICE], parent_state=chat_state,
                                   parent_state_transition=compose_clicks([CALL_END_BUTTON], 'end_call'))
    video_call_state = SimpleState(xpaths=[CALL_END_BUTTON, CALL_VIDEO], parent_state=chat_state,
                                   parent_state_transition=compose_clicks([CALL_END_BUTTON], 'end_call'))
    send_location_state = SimpleState(xpaths=[LOCATION_TITLE, LOCATION_CURRENT],
                                      parent_state=chat_state,
                                      parent_state_transition=compose_clicks([LOCATION_CANCEL_BUTTON],
                                                                             'close_location'))

    # Transitions
    conversations_state.to(new_chat_state, compose_clicks([CONVERSATIONS_NEW_CHAT_BUTTON], 'open_new_chat'))
    conversations_state.to(chat_state, chat_state.open_chat)
    conversations_state.to(settings_state, compose_clicks([TAB_YOU], 'open_you_tab'))
    conversations_state.to(updates_state, compose_clicks([TAB_UPDATES], 'open_updates_tab'))
    settings_state.to(profile_state, compose_clicks([SETTINGS_EDIT_PROFILE_BUTTON], 'open_profile'))
    chat_state.to(chat_settings_state, compose_clicks([CHAT_HEADER], 'open_chat_info'))
    chat_state.to(send_location_state, compose_clicks([CHAT_ATTACH_BUTTON, ATTACH_LOCATION], 'open_location'))

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes WhatsApp with a device UDID.

        :param device_udid: The unique device identifier of the iOS device.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, WHATSAPP_BUNDLE_ID, **kwargs)
        self.driver.add_back_button(BACK_BUTTON)
        self.add_popup_handlers(MessageMenuHandler(),
                                PopUpHandler([SELECTION_TOOLBAR, SELECTION_CANCEL_BUTTON], [SELECTION_CANCEL_BUTTON]),
                                PopUpHandler([POPUP_DISAPPEARING_MESSAGES_TEXT], [POPUP_OK_BUTTON]),
                                # the menu of the + button is closed by pressing the + button again
                                PopUpHandler([ATTACH_MENU], [CHAT_ATTACH_BUTTON]),
                                StickerTrayHandler(),
                                # the editor of a text status
                                PopUpHandler([STATUS_TEXT_FIELD, STATUS_CANCEL_BUTTON], [STATUS_CANCEL_BUTTON]))

    def _type_and_send(self, text: str):
        self.driver.gtl_logger.info(f'Typing "{text}"')
        self.driver.send_keys(CHAT_COMPOSER, text)
        # allow time for the preview of a link to load
        if 'http' in text:
            sleep(2)
        self.driver.gtl_logger.info('Pressing send button')
        self.driver.click(CHAT_SEND_BUTTON)
        sleep(1)

    @action(chat_state)
    def send_message(self, message_text: str, conversation: str = None):
        """
        Sends a message in a chat.

        :param message_text: The text of the message.
        :param conversation: The chat to send the message in. Optional: without a chat, the open chat is used.
        """
        self._type_and_send(message_text)

    @action(new_chat_state, end_state=chat_state)
    def create_new_chat(self, conversation: str, first_message: str):
        """
        Starts a chat with a contact by sending a message. When there already is a chat with the contact, the message is
        sent in that chat. The chat is opened afterwards.

        :param conversation: The name of the contact.
        :param first_message: The first message to send.
        """
        self.gtl_logger.info(f'Searching for contact "{conversation}"')
        self.driver.send_keys(NEW_CHAT_SEARCH_FIELD, conversation)
        if not _wait_for(self.driver, new_chat_contact(conversation), timeout=20):
            raise WhatsAppError(f'There is no contact named "{conversation}" on WhatsApp')
        self.gtl_logger.info(f'Choosing contact "{conversation}"')
        _tap_visible(self.driver, new_chat_contact(conversation))
        if not _wait_for(self.driver, CHAT_COMPOSER):
            raise WhatsAppError(f'The chat with "{conversation}" did not open')
        self._type_and_send(first_message)

    @action(chat_state)
    def get_messages(self, conversation: str = None) -> list[Message]:
        """
        Reads the messages shown in a chat, from old to new. Only the messages on or near the screen are returned.

        :param conversation: The chat to read. Optional: without a chat, the open chat is used.
        :return: The messages. Messages sent from this device have None as sender.
        """
        return _parse_messages(self.driver.driver.page_source)

    @contextmanager
    def _message_menu(self, xpath: str, description: str):
        """
        Opens the menu of a message by long pressing it. Afterwards, the chat is scrolled back to the latest messages.
        """
        swipes = _scroll_to(self.driver, xpath, description)
        try:
            with _short_idle_timeout(self.driver):
                self.gtl_logger.info(f'Long pressing {description} to open its menu')
                self.driver.long_click_element(xpath, duration=1)
                if not _wait_for(self.driver, MESSAGE_MENU, timeout=4):
                    raise WhatsAppError(f'Could not open the menu of {description}')
                yield
        finally:
            _scroll_to_latest(self.driver, swipes)

    @action(chat_state)
    def reply_to_message(self, message_to_reply_to: str, reply_text: str, conversation: str = None):
        """
        Replies to a message.

        :param message_to_reply_to: The text of the message to reply to. When multiple messages contain the text, the
        last one is used.
        :param reply_text: The text of the reply.
        :param conversation: The chat of the message. Optional: without a chat, the open chat is used.
        """
        with self._message_menu(any_message(message_to_reply_to), f'message "{message_to_reply_to}"'):
            self.gtl_logger.info('Choosing Reply')
            self.driver.click(MESSAGE_MENU_REPLY)
        sleep(1)
        self._type_and_send(reply_text)

    @action(chat_state)
    def delete_message_for_everyone(self, message_text: str, conversation: str = None):
        """
        Deletes a message sent from this device for everyone in the chat. This is possible until about 2 days after
        sending the message.

        :param message_text: The text of the message. When multiple messages contain the text, the last one is used.
        :param conversation: The chat of the message. Optional: without a chat, the open chat is used.
        """
        with self._message_menu(sent_message(message_text), f'message "{message_text}"'):
            self.gtl_logger.info('Choosing Delete')
            self.driver.click(MESSAGE_MENU_DELETE)
        _wait_for(self.driver, SELECTION_DELETE_BUTTON)
        self.gtl_logger.info('Pressing delete button')
        self.driver.click(SELECTION_DELETE_BUTTON)
        if not _wait_for(self.driver, DELETE_FOR_EVERYONE_BUTTON, timeout=3):
            self.driver.click(SELECTION_CANCEL_BUTTON)
            raise WhatsAppError(f'Message "{message_text}" cannot be deleted for everyone anymore')
        self.gtl_logger.info('Choosing Delete for everyone')
        self.driver.click(DELETE_FOR_EVERYONE_BUTTON)
        sleep(1)

    def _is_marked(self, message_text: str, status: str, implicit_wait: float) -> bool:
        return _wait_for(self.driver, sent_message_with_status(message_text, status), timeout=implicit_wait)

    @action(chat_state)
    def is_message_marked_sent(self, message_text: str, conversation: str = None, implicit_wait: float = 5) -> bool:
        """
        Checks whether a message sent from this device is marked as sent (one grey check mark).

        :param message_text: The text of the message.
        :param conversation: The chat of the message. Optional: without a chat, the open chat is used.
        :param implicit_wait: How long to wait for the status, in seconds.
        :return: Whether the message is marked as sent.
        """
        return self._is_marked(message_text, 'Sent', implicit_wait)

    @action(chat_state)
    def is_message_marked_delivered(self, message_text: str, conversation: str = None,
                                    implicit_wait: float = 5) -> bool:
        """
        Checks whether a message sent from this device is marked as delivered (two grey check marks).

        :param message_text: The text of the message.
        :param conversation: The chat of the message. Optional: without a chat, the open chat is used.
        :param implicit_wait: How long to wait for the status, in seconds.
        :return: Whether the message is marked as delivered.
        """
        return self._is_marked(message_text, 'Delivered', implicit_wait)

    @action(chat_state)
    def is_message_marked_read(self, message_text: str, conversation: str = None, implicit_wait: float = 10) -> bool:
        """
        Checks whether a message sent from this device is marked as read (two blue check marks). This is only shown when
        both people have read receipts turned on.

        :param message_text: The text of the message.
        :param conversation: The chat of the message. Optional: without a chat, the open chat is used.
        :param implicit_wait: How long to wait for the status, in seconds.
        :return: Whether the message is marked as read.
        """
        return self._is_marked(message_text, 'Read', implicit_wait)

    @action(chat_state)
    def forward_message(self, conversation: str, message_contains: str, to_chat: str):
        """
        Forwards a message from one chat to another.

        :param conversation: The chat of the message.
        :param message_contains: A part of the text of the message. When multiple messages contain the text, the last
        one is used.
        :param to_chat: The chat to forward the message to.
        """
        with self._message_menu(any_message(message_contains), f'message "{message_contains}"'):
            self.gtl_logger.info('Choosing Forward')
            self.driver.click(MESSAGE_MENU_FORWARD)
        _wait_for(self.driver, SELECTION_FORWARD_BUTTON)
        self.gtl_logger.info('Pressing forward button')
        self.driver.click(SELECTION_FORWARD_BUTTON)
        _wait_for(self.driver, FORWARD_SEARCH_FIELD)
        self.gtl_logger.info(f'Searching for chat "{to_chat}"')
        self.driver.send_keys(FORWARD_SEARCH_FIELD, to_chat)
        if not _wait_for(self.driver, forward_chat(to_chat), timeout=20):
            raise WhatsAppError(f'Cannot forward to "{to_chat}": the chat was not found')
        self.gtl_logger.info(f'Choosing chat "{to_chat}"')
        _tap_visible(self.driver, forward_chat(to_chat))
        _wait_for(self.driver, FORWARD_SEND_BUTTON)
        self.gtl_logger.info('Pressing forward button')
        self.driver.click(FORWARD_SEND_BUTTON)
        sleep(2)

    @action(chat_state)
    def send_contact(self, contact_name: str, conversation: str = None):
        """
        Sends a contact in a chat.

        :param contact_name: The name of the contact to send.
        :param conversation: The chat to send the contact in. Optional: without a chat, the open chat is used.
        """
        self.gtl_logger.info('Pressing the + button')
        self.driver.click(CHAT_ATTACH_BUTTON)
        _wait_for(self.driver, ATTACH_CONTACT)
        self.gtl_logger.info('Choosing Contact')
        self.driver.click(ATTACH_CONTACT)
        _wait_for(self.driver, PICKER_SEARCH_FIELD)
        self.gtl_logger.info(f'Searching for contact "{contact_name}"')
        self.driver.click(PICKER_SEARCH_FIELD)
        self.driver.send_keys(PICKER_SEARCH_FIELD, contact_name)
        if not _wait_for(self.driver, picker_contact(contact_name), timeout=20):
            raise WhatsAppError(f'There is no contact named "{contact_name}"')
        _tap_visible(self.driver, picker_contact(contact_name))
        self.gtl_logger.info('Pressing Next')
        self.driver.click(PICKER_NEXT_BUTTON)
        _wait_for(self.driver, SHARE_CONTACT_SEND_BUTTON)
        self.gtl_logger.info('Pressing Send')
        self.driver.click(SHARE_CONTACT_SEND_BUTTON)
        sleep(1)

    @action(send_location_state, end_state=chat_state)
    def send_current_location(self, conversation: str = None):
        """
        Sends the current location of the device in a chat.

        :param conversation: The chat to send the location in. Optional: without a chat, the open chat is used.
        """
        # it takes some time to determine the location
        sleep(3)
        self.gtl_logger.info('Choosing Send your current location')
        self.driver.click(LOCATION_CURRENT)
        sleep(2)

    @action(send_location_state, end_state=chat_state)
    def send_live_location(self, caption: str = None, conversation: str = None):
        """
        Shares the live location of the device in a chat, for 1 hour. The other people in the chat can follow the
        location while it is shared.

        :param caption: Optional caption sent along with the live location.
        :param conversation: The chat to share the location in. Optional: without a chat, the open chat is used.
        """
        self.gtl_logger.info('Choosing Share live location')
        self.driver.click(LOCATION_LIVE)
        _wait_for(self.driver, CAPTION_SEND_BUTTON)
        if caption:
            self.gtl_logger.info(f'Entering caption "{caption}"')
            self.driver.send_keys(CAPTION_FIELD, caption)
        self.gtl_logger.info('Pressing Send')
        self.driver.click(CAPTION_SEND_BUTTON)
        sleep(2)

    @action(chat_state)
    def stop_live_location(self, conversation: str = None):
        """
        Stops sharing the live location in a chat.

        :param conversation: The chat to stop sharing the location in. Optional: without a chat, the open chat is used.
        """
        swipes = _scroll_to(self.driver, STOP_SHARING_BUTTON, 'the live location that is shared')
        self.gtl_logger.info('Pressing Stop sharing')
        self.driver.click(STOP_SHARING_BUTTON)
        _wait_for(self.driver, STOP_SHARING_CONFIRM_BUTTON, timeout=3)
        self.gtl_logger.info('Confirming Stop sharing')
        self.driver.click(STOP_SHARING_CONFIRM_BUTTON)
        sleep(1)
        _scroll_to_latest(self.driver, swipes)

    def _set_disappearing_messages(self, option: str):
        self.gtl_logger.info('Opening Disappearing messages')
        self.driver.swipe_to_click_element(CHAT_INFO_DISAPPEARING_MESSAGES)
        # the first time, an explanation is shown
        if _wait_for(self.driver, POPUP_DISAPPEARING_MESSAGES_TEXT, DISAPPEARING_MESSAGES_TIMER, timeout=3) and \
                self.driver.is_present(POPUP_DISAPPEARING_MESSAGES_TEXT):
            self.gtl_logger.info('Dismissing the explanation of disappearing messages')
            self.driver.click(POPUP_OK_BUTTON)
            _wait_for(self.driver, DISAPPEARING_MESSAGES_TIMER)
        self.gtl_logger.info(f'Choosing {option}')
        self.driver.click(disappearing_messages_option(option))
        sleep(1)
        self.driver.click(BACK_BUTTON)
        sleep(1)

    @action(chat_settings_state)
    def activate_disappearing_messages(self, conversation: str = None):
        """
        Turns on disappearing messages in a chat: new messages disappear after 24 hours.

        :param conversation: The chat. Optional: without a chat, the open chat is used.
        """
        self._set_disappearing_messages('24 hours')

    @action(chat_settings_state)
    def deactivate_disappearing_messages(self, conversation: str = None):
        """
        Turns off disappearing messages in a chat.

        :param conversation: The chat. Optional: without a chat, the open chat is used.
        """
        self._set_disappearing_messages('Off')

    @action(chat_state)
    def send_voice_message(self, duration: int = 2, conversation: str = None):
        """
        Records and sends a voice message, by holding the microphone button. This records sound with the microphone of
        the device.

        :param duration: The duration of the voice message, in seconds.
        :param conversation: The chat to send the voice message in. Optional: without a chat, the open chat is used.
        """
        self.gtl_logger.info(f'Holding the microphone button for {duration} seconds')
        # a long click with Selenium actions does not start recording, a touch and hold does
        button = self.driver.get_element(CHAT_VOICE_MESSAGE_BUTTON)
        self.driver.execute_script('mobile: touchAndHold', {'elementId': button.id, 'duration': duration})
        sleep(2)

    @action(chat_state)
    def send_media(self, index: int = 1, conversation: str = None, caption: str = None, view_once: bool = False):
        """
        Sends a photo or video from the photo library in a chat.

        :param index: Which photo or video to send: 1 for the newest, 2 for the one before, and so on.
        :param conversation: The chat to send the media in. Optional: without a chat, the open chat is used.
        :param caption: Optional caption sent along with the media.
        :param view_once: Whether the media can only be viewed once.
        """
        self.gtl_logger.info('Pressing the + button')
        self.driver.click(CHAT_ATTACH_BUTTON)
        _wait_for(self.driver, ATTACH_PHOTOS)
        self.gtl_logger.info('Choosing Photos')
        self.driver.click(ATTACH_PHOTOS)
        if not _wait_for(self.driver, MEDIA_PICKER_ASSETS):
            raise WhatsAppError('The photo library did not open')
        # the media are shown in a grid, from new to old
        assets = sorted(self.driver.get_elements(MEDIA_PICKER_ASSETS), key=lambda e: (e.rect['y'], e.rect['x']))
        if index < 1 or index > len(assets):
            self.driver.click(MEDIA_PICKER_CANCEL_BUTTON)
            raise WhatsAppError(f'Cannot choose media {index}, only {len(assets)} are shown')
        self.gtl_logger.info(f'Choosing media {index}')
        assets[index - 1].click()
        _wait_for(self.driver, MEDIA_PICKER_SEND_BUTTON)
        if caption:
            self.gtl_logger.info(f'Entering caption "{caption}"')
            self.driver.send_keys(MEDIA_PICKER_CAPTION, caption)
        if view_once:
            self.gtl_logger.info('Turning on view once')
            self.driver.click(MEDIA_PICKER_VIEW_ONCE_BUTTON)
            sleep(1)
        self.gtl_logger.info('Pressing Send')
        self.driver.click(MEDIA_PICKER_SEND_BUTTON)
        sleep(3)

    @action(chat_state)
    def send_sticker(self, conversation: str = None):
        """
        Sends the first sticker of the sticker tray (the most recently used sticker) in a chat.

        :param conversation: The chat to send the sticker in. Optional: without a chat, the open chat is used.
        """
        self.gtl_logger.info('Opening the sticker tray')
        self.driver.click(CHAT_STICKERS_BUTTON)
        if not _wait_for(self.driver, STICKERS):
            raise WhatsAppError('There are no stickers in the sticker tray')
        self.gtl_logger.info('Choosing the first sticker')
        self.driver.click(STICKERS)
        sleep(2)
        if self.driver.is_present(STICKER_TRAY):
            self.gtl_logger.info('Closing the sticker tray')
            _close_sticker_tray(self.driver)

    @action(chat_state)
    def send_emoji(self, conversation: str = None, emoji: str = '\U0001F44D'):
        """
        Sends an emoji in a chat.

        :param conversation: The chat to send the emoji in. Optional: without a chat, the open chat is used.
        :param emoji: The emoji to send, a thumbs up by default.
        """
        self._type_and_send(emoji)

    @action(conversations_state)
    def archive_conversation(self, conversation: str):
        """
        Archives a chat, by swiping it to the left in the overview.

        :param conversation: The chat to archive.
        """
        _find_row(self.driver, conversation_row(conversation), f'chat "{conversation}"')
        self.gtl_logger.info(f'Swiping chat "{conversation}" to the left to archive it')
        _swipe_row_left(self.driver, conversation_row(conversation))
        if self.driver.is_present(conversation_row(conversation)):
            raise WhatsAppError(f'Chat "{conversation}" was not archived')

    @action(conversations_state)
    def unarchive_conversation(self, conversation: str):
        """
        Moves an archived chat back to the overview, by swiping it to the left in the list of archived chats.

        :param conversation: The archived chat.
        """
        self.gtl_logger.info('Opening the archived chats')
        # the archived chats are at the top of the overview
        for _ in range(10):
            if self.driver.is_present(CONVERSATIONS_ARCHIVED):
                break
            self.driver._scroll_up()
        self.driver.click(CONVERSATIONS_ARCHIVED)
        _wait_for(self.driver, ARCHIVED_TABLE)
        _find_row(self.driver, archived_row(conversation), f'archived chat "{conversation}"')
        self.gtl_logger.info(f'Swiping chat "{conversation}" to the left to unarchive it')
        _swipe_row_left(self.driver, archived_row(conversation))
        if self.driver.is_present(archived_row(conversation)):
            raise WhatsAppError(f'Chat "{conversation}" was not unarchived')
        self.driver.click(BACK_BUTTON)
        sleep(1)

    def _choose_contacts(self, contacts: list[str]):
        """
        Chooses contacts in the contact picker, by searching for each of them.
        """
        for contact in contacts:
            self.gtl_logger.info(f'Searching for contact "{contact}"')
            self.driver.click(PICKER_SEARCH_FIELD)
            self.driver.send_keys(PICKER_SEARCH_FIELD, contact)
            # searching a long list of contacts can take a while
            if not _wait_for(self.driver, picker_contact(contact), timeout=20):
                raise WhatsAppError(f'There is no contact named "{contact}"')
            self.gtl_logger.info(f'Choosing contact "{contact}"')
            _tap_visible(self.driver, picker_contact(contact))
            sleep(1)

    @action(new_chat_state, end_state=chat_state)
    def create_group(self, conversation: str, members: Union[str, list[str]]):
        """
        Creates a group. The group is opened afterwards.

        :param conversation: The name of the group.
        :param members: The contact, or contacts, to add to the group.
        """
        members = [members] if isinstance(members, str) else members
        self.gtl_logger.info('Choosing New group')
        self.driver.click(NEW_CHAT_NEW_GROUP)
        _wait_for(self.driver, PICKER_SEARCH_FIELD)
        self._choose_contacts(members)
        self.gtl_logger.info('Pressing Next')
        self.driver.click(PICKER_NEXT_BUTTON)
        _wait_for(self.driver, GROUP_CREATE_BUTTON)
        self.gtl_logger.info(f'Entering group name "{conversation}"')
        self.driver.send_keys(GROUP_NAME_FIELD, conversation)
        self.gtl_logger.info('Pressing Create')
        self.driver.click(GROUP_CREATE_BUTTON)
        if not _wait_for(self.driver, CHAT_COMPOSER, timeout=10):
            raise WhatsAppError(f'Group "{conversation}" was not created')

    @action(chat_settings_state)
    def set_group_description(self, conversation: str, description: str):
        """
        Sets the description of a group.

        :param conversation: The name of the group.
        :param description: The description.
        """
        self.gtl_logger.info('Opening the menu of the group info')
        self.driver.click(GROUP_INFO_MENU)
        _wait_for(self.driver, GROUP_MENU_EDIT_DESCRIPTION)
        self.gtl_logger.info('Choosing Edit description')
        self.driver.click(GROUP_MENU_EDIT_DESCRIPTION)
        _wait_for(self.driver, TEXT_INPUT_FIELD)
        self.gtl_logger.info(f'Entering description "{description}"')
        self.driver.send_keys(TEXT_INPUT_FIELD, description)
        self.gtl_logger.info('Pressing Save')
        self.driver.click(TEXT_INPUT_SAVE_BUTTON)
        sleep(2)

    @action(chat_settings_state)
    def remove_member_from_group(self, conversation: str, member: str):
        """
        Removes a member from a group. Only group admins can remove members.

        :param conversation: The name of the group.
        :param member: The name of the member to remove.
        """
        self.gtl_logger.info(f'Opening member "{member}"')
        self.driver.swipe_to_click_element(group_member(member))
        _wait_for(self.driver, GROUP_REMOVE_MEMBER_BUTTON)
        self.gtl_logger.info('Choosing Remove from group')
        self.driver.click(GROUP_REMOVE_MEMBER_BUTTON)
        _wait_for(self.driver, GROUP_REMOVE_CONFIRM_BUTTON)
        self.gtl_logger.info('Confirming Remove')
        self.driver.click(GROUP_REMOVE_CONFIRM_BUTTON)
        sleep(2)

    def _exit_group(self, exit_button: str):
        self.gtl_logger.info('Choosing Exit group')
        self.driver.swipe_to_click_element(GROUP_EXIT)
        _wait_for(self.driver, exit_button)
        self.driver.click(exit_button)
        sleep(2)

    @action(chat_settings_state)
    def leave_group(self, conversation: str = None):
        """
        Leaves a group, without deleting it.

        :param conversation: The name of the group.
        """
        self._exit_group(GROUP_EXIT_BUTTON)

    @action(chat_settings_state, end_state=conversations_state)
    def delete_group(self, conversation: str):
        """
        Leaves a group, when not left yet, and deletes it from this device.

        :param conversation: The name of the group.
        """
        if _swipe_to_find(self.driver, GROUP_DELETE, max_swipes=3):
            self.gtl_logger.info('Choosing Delete group')
            self.driver.click(GROUP_DELETE)
            _wait_for(self.driver, GROUP_DELETE_CONFIRM_BUTTON)
            self.gtl_logger.info('Confirming Delete group')
            self.driver.click(GROUP_DELETE_CONFIRM_BUTTON)
        else:
            self.gtl_logger.info('Leaving and deleting the group')
            self._exit_group(GROUP_EXIT_AND_DELETE_BUTTON)
        sleep(2)

    def group_exists(self, conversation: str, members: Union[str, list[str]]) -> bool:
        """
        Checks whether a group exists with the given members. Logs a warning when the group or a member is not found.

        :param conversation: The name of the group.
        :param members: The expected member, or members, besides yourself.
        :return: Whether the group exists with all expected members.
        """
        members = [members] if isinstance(members, str) else members
        try:
            self.go_to_state(self.chat_settings_state, conversation=conversation)
        except WhatsAppError as e:
            self.gtl_logger.warning(f'Group "{conversation}" was not found: {e}')
            return False
        missing = [member for member in members if not _swipe_to_find(self.driver, group_member(member))]
        if missing:
            self.gtl_logger.warning(f'Group "{conversation}" does not contain {missing}')
        return not missing

    @action(profile_state)
    def set_about(self, about_text: str, duration: str = None):
        """
        Sets the about of the profile, which is shown to contacts. WhatsApp shows the about for a limited time only, by
        default 1 day.

        :param about_text: The about.
        :param duration: Optional: how long the about is shown: '1 hour', '8 hours', '1 day', '2 days' or '1 week'.
        """
        self.gtl_logger.info('Opening About')
        self.driver.click(PROFILE_ABOUT)
        _wait_for(self.driver, ABOUT_FIELD)
        if self.driver.is_present(ABOUT_CLEAR_BUTTON):
            self.gtl_logger.info('Clearing the current about')
            self.driver.click(ABOUT_CLEAR_BUTTON)
        self.gtl_logger.info(f'Entering about "{about_text}"')
        self.driver.send_keys(ABOUT_FIELD, about_text)
        if duration:
            self.gtl_logger.info(f'Choosing duration {duration}')
            self.driver.click(ABOUT_DURATION_BUTTON)
            _wait_for(self.driver, about_duration(duration))
            self.driver.click(about_duration(duration))
            sleep(1)
        self.gtl_logger.info('Pressing Save')
        self.driver.click(ABOUT_SAVE_BUTTON)
        sleep(2)

    @action(updates_state)
    def add_status(self, caption: str):
        """
        Adds a text status, which is shown to your contacts for 24 hours.

        :param caption: The text of the status.
        """
        self.gtl_logger.info('Pressing the text status button')
        self.driver.click(UPDATES_TEXT_STATUS_BUTTON)
        _wait_for(self.driver, STATUS_TEXT_FIELD)
        self.gtl_logger.info(f'Typing status "{caption}"')
        self.driver.get_element(STATUS_TEXT_FIELD).send_keys(caption)
        _wait_for(self.driver, STATUS_SEND_BUTTON)
        self.gtl_logger.info('Pressing Send')
        self.driver.click(STATUS_SEND_BUTTON)
        sleep(3)

    @action(updates_state)
    def delete_status(self):
        """
        Deletes all your status updates, also for everyone who received them.
        """
        self.gtl_logger.info('Opening My status')
        self.driver.click(UPDATES_MY_STATUS)
        if not _wait_for(self.driver, MY_STATUS_UPDATES):
            self.driver.click(BACK_BUTTON)
            return
        self.gtl_logger.info('Pressing Edit')
        self.driver.click(MY_STATUS_EDIT_BUTTON)
        sleep(1)
        for update in self.driver.get_elements(MY_STATUS_UPDATES):
            update.click()
        self.gtl_logger.info('Pressing delete button')
        self.driver.click(MY_STATUS_DELETE_BUTTON)
        _wait_for(self.driver, MY_STATUS_DELETE_CONFIRM_BUTTON)
        self.gtl_logger.info('Confirming delete')
        self.driver.click(MY_STATUS_DELETE_CONFIRM_BUTTON)
        sleep(2)
        if self.driver.is_present(BACK_BUTTON):
            self.driver.click(BACK_BUTTON)
            sleep(1)

    @action(chat_settings_state)
    def view_contact_profile_picture(self, conversation: str):
        """
        Views the profile picture of a contact, full screen. The picture is closed again afterwards. For contacts
        without a profile picture, nothing is shown.

        :param conversation: The chat with the contact.
        """
        self.gtl_logger.info('Opening the profile picture')
        self.driver.click(CONTACT_INFO_PROFILE_PICTURE)
        if _wait_for(self.driver, PROFILE_PICTURE_CLOSE_BUTTON, timeout=3):
            sleep(2)
            self.gtl_logger.info('Closing the profile picture')
            self.driver.click(PROFILE_PICTURE_CLOSE_BUTTON)
            sleep(1)
        else:
            self.gtl_logger.info('The contact has no profile picture')


    @action(chat_state, end_state=voice_call_state)
    def start_voice_call(self, conversation: str):
        """
        Starts a voice call with a contact or group.

        :param conversation: The chat to call.
        """
        self.gtl_logger.info('Pressing the voice call button')
        self.driver.click(CHAT_VOICE_CALL_BUTTON)
        _wait_for(self.driver, CALL_END_BUTTON)

    @action(chat_state, end_state=video_call_state)
    def start_video_call(self, conversation: str):
        """
        Starts a video call with a contact. This uses the camera of the device.

        :param conversation: The chat to call.
        """
        self.gtl_logger.info('Pressing the video call button')
        self.driver.click(CHAT_VIDEO_CALL_BUTTON)
        _wait_for(self.driver, CALL_END_BUTTON)

    def _end_call(self):
        """
        Ends a call. In a video call, the buttons are hidden after a few seconds: they stay in the element tree, but
        move off the screen. Tapping the screen shows them again.
        """
        size = self.driver.driver.get_window_size()
        rect = self.driver.get_element(CALL_END_BUTTON).rect
        if rect['y'] + rect['height'] > size['height']:
            self.gtl_logger.info('Tapping the screen to show the buttons of the call')
            self.driver.execute_script('mobile: tap', {'x': size['width'] / 2, 'y': size['height'] / 2})
            sleep(1)
            rect = self.driver.get_element(CALL_END_BUTTON).rect
        self.gtl_logger.info('Pressing the end call button')
        self.driver.execute_script('mobile: tap', {'x': rect['x'] + rect['width'] / 2,
                                                   'y': rect['y'] + rect['height'] / 2})
        sleep(2)

    @action(voice_call_state, end_state=chat_state)
    def end_voice_call(self, conversation: str = None):
        """
        Ends the current voice call. The chat of the call is shown afterwards.
        """
        self._end_call()

    @action(video_call_state, end_state=chat_state)
    def end_video_call(self, conversation: str = None):
        """
        Ends the current video call. The chat of the call is shown afterwards.
        """
        self._end_call()

    def in_connected_call(self, implicit_wait: float = 5) -> bool:
        """
        Checks whether there is a connected call: a voice or video call that has been answered.

        :param implicit_wait: How long to wait for the call to be connected, in seconds.
        :return: Whether a call is connected.
        """
        end = time() + implicit_wait
        while True:
            if self.driver.is_present(CALL_END_BUTTON) and not self.driver.is_present(CALL_NOT_CONNECTED):
                return True
            if time() >= end:
                return False
            sleep(0.5)

    def _press_incoming_call_button(self, button: str, description: str, timeout: float):
        """
        Presses a button of an incoming call. Incoming calls are shown by iOS, so the buttons are looked up in the call
        screen of iOS instead of in WhatsApp.
        """
        self.driver.driver.update_settings({'defaultActiveApplication': INCOMING_CALL_APP})
        try:
            if not _wait_for(self.driver, button, timeout=timeout):
                raise WhatsAppError('There is no incoming call')
            self.gtl_logger.info(f'Pressing {description}')
            self.driver.click(button)
        finally:
            self.driver.driver.update_settings({'defaultActiveApplication': 'auto'})
        sleep(2)

    # This method is not an @action, since an incoming call is not tied to a state.
    def answer_call(self, timeout: float = 30):
        """
        Answers an incoming WhatsApp call. WhatsApp shows the call afterwards.

        :param timeout: How long to wait for an incoming call, in seconds.
        """
        self._press_incoming_call_button(INCOMING_CALL_ACCEPT_BUTTON, 'Accept', timeout)

    # This method is not an @action, since an incoming call is not tied to a state.
    def decline_call(self, timeout: float = 30):
        """
        Declines an incoming WhatsApp call.

        :param timeout: How long to wait for an incoming call, in seconds.
        """
        self._press_incoming_call_button(INCOMING_CALL_DECLINE_BUTTON, 'Decline', timeout)

    @action(profile_state)
    def change_profile_picture(self, index: int = 1):
        """
        Changes the profile picture to a photo from the photo library.

        :param index: Which photo to use: 1 for the newest, 2 for the one before, and so on.
        """
        self.gtl_logger.info('Pressing Edit photo')
        self.driver.click(PROFILE_EDIT_PHOTO_BUTTON)
        _wait_for(self.driver, PROFILE_CHOOSE_PHOTO)
        self.gtl_logger.info('Choosing Choose photo')
        self.driver.click(PROFILE_CHOOSE_PHOTO)
        if not _wait_for(self.driver, SYSTEM_PHOTOS):
            raise WhatsAppError('The photo library did not open')
        photos = sorted(self.driver.get_elements(SYSTEM_PHOTOS), key=lambda e: (e.rect['y'], e.rect['x']))
        if index < 1 or index > len(photos):
            raise WhatsAppError(f'Cannot choose photo {index}, only {len(photos)} are shown')
        self.gtl_logger.info(f'Choosing photo {index}')
        photos[index - 1].click()
        _wait_for(self.driver, CROP_CHOOSE_BUTTON)
        self.gtl_logger.info('Confirming the photo')
        self.driver.click(CROP_CHOOSE_BUTTON)
        sleep(3)

    @action(new_chat_state, end_state=chat_state)
    def send_broadcast(self, receivers: list[str], broadcast_text: str):
        """
        Sends a broadcast: a message sent to multiple contacts, who receive it in their chat with you. The broadcast
        list is opened afterwards. Only contacts who have you in their address book receive the message.

        :param receivers: The names of the contacts to send the message to, at least 2.
        :param broadcast_text: The text to send.
        """
        if len(receivers) < 2:
            raise WhatsAppError(f'A broadcast needs at least 2 receivers, got: {receivers}')
        self.gtl_logger.info('Choosing New broadcast')
        self.driver.click(NEW_CHAT_NEW_BROADCAST)
        _wait_for(self.driver, PICKER_SEARCH_FIELD)
        self._choose_contacts(receivers)
        self.gtl_logger.info('Pressing Create')
        self.driver.click(PICKER_NEXT_BUTTON)
        if not _wait_for(self.driver, CHAT_COMPOSER, timeout=10):
            raise WhatsAppError('The broadcast list was not created')
        self._type_and_send(broadcast_text)

    @action(chat_state)
    def open_view_once_photo(self, conversation: str):
        """
        Opens the last view once photo received in a chat, and closes it again. A view once photo can only be opened
        once: afterwards, it is shown as opened.

        :param conversation: The chat of the photo.
        """
        swipes = _scroll_to(self.driver, RECEIVED_VIEW_ONCE_PHOTO, 'a view once photo')
        self.gtl_logger.info('Opening the view once photo')
        self.driver.get_elements(RECEIVED_VIEW_ONCE_PHOTO)[-1].click()
        if not _wait_for(self.driver, MEDIA_VIEWER_IMAGE):
            raise WhatsAppError('The view once photo did not open')
        sleep(2)
        self.gtl_logger.info('Closing the view once photo')
        self.driver.click(BACK_BUTTON)
        sleep(1)
        _scroll_to_latest(self.driver, swipes)
