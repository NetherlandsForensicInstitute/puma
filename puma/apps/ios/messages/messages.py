import re
import xml.etree.ElementTree as ElementTree
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from time import sleep, time
from typing import Optional

from puma.apps.ios.messages import logger
from puma.apps.ios.messages.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.puma_driver import PumaDriver, Platform, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

MESSAGES_BUNDLE_ID = 'com.apple.MobileSMS'


class MessagesError(Exception):
    """
    Raised when Messages refuses an action, e.g. sending a message to a recipient that cannot be reached.
    """
    pass


class Service(Enum):
    """
    The service a message is sent with.
    """
    IMESSAGE = 'iMessage'
    SMS = 'SMS'


class Reaction(Enum):
    """
    The reactions (tapbacks) that can be given to a message.
    """
    HEART = 'heart'
    THUMBS_UP = 'thumbsUp'
    THUMBS_DOWN = 'thumbsDown'
    HAHA = 'ha'
    EMPHASIZE = 'exclamation'
    QUESTION = 'questionMark'


# Reactions are shown in the label of a message, e.g. 'Bob loved this'. This depends on the language of the device.
_REACTION_VERBS = {
    'loved': Reaction.HEART,
    'liked': Reaction.THUMBS_UP,
    'disliked': Reaction.THUMBS_DOWN,
    'laughed at': Reaction.HAHA,
    'emphasized': Reaction.EMPHASIZE,
    'questioned': Reaction.QUESTION,
}
_REACTION = re.compile(r', (?P<who>[^,]+?) (?P<verb>' + '|'.join(_REACTION_VERBS) + r') this$')
_REACTION_BY_ME = 'You'


@dataclass
class Message:
    """
    A message in a conversation.

    :param sender: The name of the sender, or None for messages sent from this device.
    :param text: The text of the message.
    :param time: The time of the message, as shown on the screen (e.g. '14:45').
    :param service: The service of the message, or None if it is not known.
    :param reactions: The reactions (tapbacks) to the message, as (who, reaction). Reactions from this device have None
    as who.
    :param is_reply: Whether the message is a reply to another message.
    :param reply_to: The text of the message replied to, if it is shown in the conversation.
    """
    sender: Optional[str]
    text: str
    time: str
    service: Optional[Service]
    reactions: list[tuple[Optional[str], Reaction]] = field(default_factory=list)
    is_reply: bool = False
    reply_to: Optional[str] = None

    @property
    def sent_by_me(self) -> bool:
        return self.sender is None


def _service_from_text(text: str) -> Optional[Service]:
    """
    The service shown in a text, such as the separator above messages or the placeholder of the message field, e.g.
    'iMessage' or 'Text Message • SMS'.
    """
    # on real devices, the separator can also show that iMessage is encrypted, e.g. 'iMessage  Encrypted'
    if text.startswith(CONVERSATION_SERVICE_IMESSAGE):
        return Service.IMESSAGE
    if text.startswith(CONVERSATION_SERVICE_SMS):
        return Service.SMS
    return None


def _parse_message(label: str, service: Optional[Service] = None) -> Message:
    """
    Parses the label of a message cell, '<sender>, <text>, <time>'. The text can contain commas, so the sender is split
    off at the first comma, and the time at the last comma. For messages sent from this device, the label shows the
    service instead of the sender. For other messages, the given service is used.

    :param label: The label of the message cell.
    :param service: The service of the message, as shown in the separator above it.
    """
    sender, rest = label.split(', ', 1)
    text, message_time = rest.rsplit(', ', 1)
    is_reply = text.startswith(f'{CONVERSATION_REPLY}, ')
    if is_reply:
        text = text[len(CONVERSATION_REPLY) + 2:]
    # reactions are added to the end of the text, e.g. 'Hi!, You loved this, Bob liked this'
    reactions = []
    while match := _REACTION.search(text):
        who = None if match.group('who') == _REACTION_BY_ME else match.group('who')
        reactions.insert(0, (who, _REACTION_VERBS[match.group('verb')]))
        text = text[:match.start()]
    if sender == CONVERSATION_SENT_BY_ME_IMESSAGE:
        return Message(None, text, message_time, Service.IMESSAGE, reactions, is_reply)
    if sender == CONVERSATION_SENT_BY_ME_SMS:
        return Message(None, text, message_time, Service.SMS, reactions, is_reply)
    return Message(sender, text, message_time, service, reactions, is_reply)


def _is_reply_preview(label: str) -> bool:
    return label.split(', ', 2)[1:2] == [CONVERSATION_REPLY_PREVIEW]


def _parse_messages(page_source: str, default_service: Optional[Service] = None) -> list[Message]:
    """
    Parses the messages in the page source of a conversation. The service of received messages is taken from the last
    separator above them, which is only shown when the service changes. In longer conversations, that separator is no
    longer in the page source. The default service is used for received messages without a separator above them.
    """
    messages = []
    service = default_service
    reply_preview = None
    for element in ElementTree.fromstring(page_source).iter():
        element_type = element.get('type')
        name = element.get('name') or ''
        if element_type == 'XCUIElementTypeStaticText' and _service_from_text(name):
            service = _service_from_text(name)
        elif element_type == 'XCUIElementTypeCell' and any(
                child.get('name') == CONVERSATION_MESSAGE_BALLOON for child in element.iter()):
            label = element.get('label')
            if _is_reply_preview(label):
                # the preview of the message replied to is shown above the reply, it is not a message of its own
                sender, rest = label.split(', ', 1)
                reply_preview = _parse_message(f'{sender}, {rest.split(", ", 1)[1]}').text
                continue
            message = _parse_message(label, service)
            if message.is_reply:
                message.reply_to = reply_preview
            reply_preview = None
            messages.append(message)
    return messages


def _title_matches(title: str, conversation: str) -> bool:
    """
    Whether the title of an opened conversation belongs to a conversation. For contacts, the title only shows the first
    name (e.g. 'Bob' for the conversation 'Bob Jansen'), while the overview shows the full name.
    """
    return title == conversation or conversation.startswith(f'{title} ')


def _swipe_left(driver: PumaDriver, element: str):
    """
    Swipes a row in a list to the left, which reveals the delete button.
    """
    rect = driver.get_element(element).rect
    y = rect['y'] + rect['height'] / 2
    driver.execute_script('mobile: dragFromToForDuration', {
        'fromX': rect['x'] + rect['width'] - 20, 'fromY': y, 'toX': rect['x'] + 60, 'toY': y, 'duration': 0.2})
    sleep(1)


def _close_new_message(driver: PumaDriver):
    driver.click(NEW_MESSAGE_CANCEL_BUTTON)
    sleep(1)


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


def _search(driver: PumaDriver, query: str = ''):
    """
    Searches for conversations and messages, and waits for the search results.
    """
    driver.gtl_logger.info(f'Searching for "{query}"')
    driver.click(CONVERSATIONS_SEARCH_FIELD)
    sleep(1)
    driver.send_keys(CONVERSATIONS_SEARCH_FIELD, query)
    _wait_for(driver, SEARCH_RESULTS_CONVERSATIONS, SEARCH_RESULTS_NO_RESULTS)
    # the results are updated a few times while searching
    sleep(2)


def _close_search(driver: PumaDriver):
    driver.click(SEARCH_RESULTS_CLOSE_BUTTON)
    sleep(1)


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


def _scroll_to_message(driver: PumaDriver, message_text: str, max_swipes: int = 10) -> int:
    """
    Scrolls up to the last message containing a text. Only the messages near the screen are in the element tree, so
    older messages have to be scrolled to.

    :return: The number of times scrolled up.
    """
    for swipes in range(max_swipes + 1):
        if driver.is_present(message_cell(message_text)):
            return swipes
        if swipes < max_swipes:
            driver.gtl_logger.info('Scrolling up to older messages')
            driver._scroll_up()
    raise MessagesError(f'Could not find message "{message_text}"')


def _scroll_to_latest(driver: PumaDriver, swipes: int):
    """
    Scrolls back down to the latest messages, after scrolling up to an older message.
    """
    for _ in range(swipes):
        driver.gtl_logger.info('Scrolling down to the latest messages')
        driver._scroll_down()


@contextmanager
def _message_menu(driver: PumaDriver, message_text: str):
    """
    Opens the menu of the last message containing a text, by long pressing it. Afterwards, the conversation is scrolled
    back down to the latest messages.
    """
    swipes = _scroll_to_message(driver, message_text)
    try:
        with _short_idle_timeout(driver):
            _open_message_menu(driver, message_text)
            yield
    finally:
        _scroll_to_latest(driver, swipes)


def _open_message_menu(driver: PumaDriver, message_text: str):
    """
    Opens the menu of a message that is in the element tree, by long pressing it.
    """
    driver.gtl_logger.info(f'Long pressing message "{message_text}" to open its menu')
    driver.long_click_element(message_cell(message_text), duration=1)
    if not _wait_for(driver, CONVERSATION_MESSAGE_MENU, timeout=4):
        raise MessagesError(f'Could not open the menu of message "{message_text}"')


def _close_message_menu(driver: PumaDriver):
    """
    Closes the menu of a message, by tapping next to it. The menu has no button to close it.
    """
    size = driver.driver.get_window_size()
    driver.execute_script('mobile: tap', {'x': size['width'] * 0.08, 'y': size['height'] * 0.75})
    sleep(1)


class MessageMenuHandler(PopUpHandler):
    """
    Closes the menu of a message when it is left open, e.g. after an interrupted action.
    """

    def __init__(self):
        super().__init__([CONVERSATION_MESSAGE_MENU], [])

    def dismiss_popup(self, driver: PumaDriver):
        driver.gtl_logger.info('Closing the menu of a message')
        _close_message_menu(driver)


def _close_conversation(driver: PumaDriver):
    """
    Goes back from a conversation to the overview. When the conversation was opened from the search results, going back
    shows the search results, so the search is closed as well.
    """
    driver.back()
    sleep(1)
    if driver.is_present(SEARCH_RESULTS_CLOSE_BUTTON):
        driver.gtl_logger.info('Closing the search results')
        _close_search(driver)


class ConversationState(SimpleState, ContextualState):
    """
    A state representing an opened conversation.
    """

    def __init__(self, parent_state):
        super().__init__(xpaths=[CONVERSATION_TITLE, CONVERSATION_MESSAGE_BODY_FIELD],
                         invalid_xpaths=[NEW_MESSAGE_NAVIGATION_BAR, CONVERSATION_MESSAGE_MENU, REPLY_CLOSE_BUTTON],
                         parent_state=parent_state,
                         parent_state_transition=_close_conversation)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True
        return _title_matches(driver.get_element(CONVERSATION_TITLE).get_attribute('label'), conversation)

    @staticmethod
    def open_conversation(driver: PumaDriver, conversation: str):
        """
        Opens a conversation from the overview. When the conversation is not shown in the overview, e.g. because it is
        further down the list, it is searched for.
        """
        if not conversation:
            raise ValueError('Cannot open a conversation without a conversation name')
        if driver.is_present(conversation_row(conversation)):
            driver.click(conversation_row(conversation))
        else:
            _search(driver, conversation)
            if not driver.is_present(search_result_conversation(conversation)):
                _close_search(driver)
                raise MessagesError(f'There is no conversation named "{conversation}"')
            driver.gtl_logger.info(f'Opening conversation "{conversation}" from the search results')
            driver.click(search_result_conversation(conversation))
        sleep(1)


@supported_version("26.6")
class Messages(StateGraph):
    """
    A class representing the Messages application on iOS.

    Conversations are identified by their name as shown in the overview: the name of the contact (e.g. 'Bob Jansen'),
    the phone number or email address, or the name of the group.

    On a simulator, messages cannot be sent to new recipients. The two conversations the simulator starts with do work:
    messages sent in one of them are received in the other.
    """
    platform = Platform.IOS

    # States
    # The welcome screen, the new message screen and the search results are shown on top of the overview, while the
    # overview stays in the element tree. Therefore these are marked as invalid.
    conversations_state = SimpleState(xpaths=[CONVERSATIONS_LIST, CONVERSATIONS_COMPOSE_BUTTON],
                                      invalid_xpaths=[POPUP_APPLE_INTELLIGENCE_WELCOME_TEXT, NEW_MESSAGE_NAVIGATION_BAR,
                                                      POPUP_RECENTLY_DELETED_TEXT, SEARCH_RESULTS_CLOSE_BUTTON],
                                      initial_state=True)
    # A conversation opened from the search results is shown on top of the search results. After going back from it,
    # searching is still active, but the list of results is not always shown. Therefore searching is recognized by the
    # button that closes it.
    search_results_state = SimpleState(xpaths=[SEARCH_RESULTS_CLOSE_BUTTON, CONVERSATIONS_SEARCH_FIELD],
                                       invalid_xpaths=[CONVERSATION_TITLE],
                                       parent_state=conversations_state,
                                       parent_state_transition=_close_search)
    new_message_state = SimpleState(xpaths=[NEW_MESSAGE_NAVIGATION_BAR, NEW_MESSAGE_RECIPIENT_FIELD],
                                    parent_state=conversations_state,
                                    parent_state_transition=_close_new_message)
    conversation_state = ConversationState(parent_state=conversations_state)

    # Transitions
    conversations_state.to(new_message_state, compose_clicks([CONVERSATIONS_COMPOSE_BUTTON], 'open_new_message'))
    conversations_state.to(conversation_state, conversation_state.open_conversation)
    conversations_state.to(search_results_state, _search)

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Messages with a device UDID.

        :param device_udid: The unique device identifier of the iOS device or simulator.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, MESSAGES_BUNDLE_ID, **kwargs)
        self.add_popup_handlers(PopUpHandler([POPUP_APPLE_INTELLIGENCE_WELCOME_TEXT], [POPUP_CONTINUE_BUTTON]),
                                PopUpHandler([POPUP_RECENTLY_DELETED_TEXT], [POPUP_OK_BUTTON]),
                                MessageMenuHandler(),
                                PopUpHandler([REPLY_CLOSE_BUTTON, CONVERSATION_TITLE], [REPLY_CLOSE_BUTTON]))

    @action(new_message_state, end_state=conversation_state)
    def start_conversation(self, recipient: str, message: str):
        """
        Starts a conversation by sending a message to a recipient. When there already is a conversation with the
        recipient, the message is sent in that conversation. The conversation is opened afterwards.

        :param recipient: The name of a contact, or a phone number or email address.
        :param message: The message to send.
        """
        self.gtl_logger.info(f'Entering recipient "{recipient}"')
        self.driver.send_keys(NEW_MESSAGE_RECIPIENT_FIELD, recipient)
        sleep(2)
        if self.driver.is_present(recipient_suggestion(recipient)):
            self.gtl_logger.info(f'Selecting contact "{recipient}" from the suggestions')
            self.driver.click(recipient_suggestion(recipient))
        else:
            # not a contact: confirm the phone number or email address as recipient
            self.gtl_logger.info(f'Confirming "{recipient}" as recipient')
            self.driver.press_enter()
        sleep(1)
        self.gtl_logger.info('Entering message text')
        self.driver.click(CONVERSATION_MESSAGE_BODY_FIELD)
        self.driver.driver.switch_to.active_element.send_keys(message)
        sleep(1)
        self.gtl_logger.info('Pressing send button')
        self.driver.click(CONVERSATION_SEND_BUTTON)
        sleep(2)
        # when the message is sent, the new message screen turns into the conversation
        if self.driver.is_present(NEW_MESSAGE_NAVIGATION_BAR):
            self.gtl_logger.warning(f'Could not send a message to "{recipient}", closing the new message screen')
            _close_new_message(self.driver)
            raise MessagesError(f'Cannot send a message to "{recipient}". Note that messages cannot be sent to new '
                                f'recipients on a simulator.')
        logger.info(f'Started conversation with {recipient}')

    @action(conversation_state)
    def send_message(self, message: str, conversation: str = None):
        """
        Sends a message in a conversation.

        :param message: The message to send.
        :param conversation: Optional. The name of the conversation. Defaults to the conversation that is open.
        """
        self.driver.send_keys(CONVERSATION_MESSAGE_BODY_FIELD, message)
        self.gtl_logger.info('Pressing send button')
        self.driver.click(CONVERSATION_SEND_BUTTON)
        logger.info(f'Sent message to {conversation}')

    @action(conversation_state)
    def get_messages(self, conversation: str = None) -> list[Message]:
        """
        Returns the text messages in a conversation that are shown on the screen. Photos and other attachments are not
        included, and in long conversations only the most recent messages are returned.

        :param conversation: Optional. The name of the conversation. Defaults to the conversation that is open.
        :return: The messages, with their sender, time and service (iMessage or SMS). Messages sent from this device
        have None as sender. The service of received messages is shown in the conversation only when it changes. When
        that is no longer on the screen, the service of the conversation (see get_service) is used.
        """
        current_service = _service_from_text(
            self.driver.get_element(CONVERSATION_MESSAGE_BODY_FIELD).get_attribute('placeholderValue') or '')
        return _parse_messages(self.driver.driver.page_source, current_service)

    @action(conversation_state)
    def get_service(self, conversation: str = None) -> Optional[Service]:
        """
        Returns the service the next message in a conversation is sent with, as shown in the empty message field.

        :param conversation: Optional. The name of the conversation. Defaults to the conversation that is open.
        :return: The service (iMessage or SMS), or None if it is not known.
        """
        return _service_from_text(
            self.driver.get_element(CONVERSATION_MESSAGE_BODY_FIELD).get_attribute('placeholderValue') or '')

    @action(conversation_state)
    def reply_to_message(self, message_to_reply_to: str, reply_text: str, conversation: str = None):
        """
        Replies to a message. The reply is shown below the message it replies to. Only available for iMessage.

        :param message_to_reply_to: The text of the message to reply to. When multiple messages contain this text, the
        last one is used.
        :param reply_text: The text of the reply.
        :param conversation: Optional. The name of the conversation. Defaults to the conversation that is open.
        """
        swipes = _scroll_to_message(self.driver, message_to_reply_to)
        with _short_idle_timeout(self.driver):
            _open_message_menu(self.driver, message_to_reply_to)
            if not self.driver.is_present(CONVERSATION_MENU_REPLY):
                _close_message_menu(self.driver)
                _scroll_to_latest(self.driver, swipes)
                raise MessagesError(f'Cannot reply to message "{message_to_reply_to}". Replying is only available for '
                                    f'iMessage, and not on a simulator.')
            self.gtl_logger.info('Pressing reply')
            self.driver.click(CONVERSATION_MENU_REPLY)
            sleep(1)
        self.driver.send_keys(CONVERSATION_MESSAGE_BODY_FIELD, reply_text)
        self.gtl_logger.info('Pressing send button')
        self.driver.click(CONVERSATION_SEND_BUTTON)
        sleep(1)
        self.gtl_logger.info('Closing the reply')
        self.driver.click(REPLY_CLOSE_BUTTON)
        sleep(1)
        _scroll_to_latest(self.driver, swipes)

    @action(conversation_state)
    def react_to_message(self, message_text: str, reaction: Reaction, conversation: str = None):
        """
        Reacts to a message with a tapback, e.g. a heart or a thumbs up.

        :param message_text: The text of the message to react to. When multiple messages contain this text, the last
        one is used.
        :param reaction: The reaction.
        :param conversation: Optional. The name of the conversation. Defaults to the conversation that is open.
        """
        with _message_menu(self.driver, message_text):
            self.gtl_logger.info(f'Selecting reaction {reaction.name}')
            self.driver.click(tapback(reaction.value))
            sleep(1)

    def _last_sent_message_text(self) -> Optional[str]:
        sent = [message for message in _parse_messages(self.driver.driver.page_source) if message.sent_by_me]
        return sent[-1].text if sent else None

    def _has_status(self, message_text: str, statuses: list[str], implicit_wait: float) -> Optional[bool]:
        """
        Whether the last message sent from this device has one of the given statuses. The status is only shown below the
        last message sent from this device, so for other messages the status is unknown.
        """
        if self._last_sent_message_text() != message_text:
            self.gtl_logger.warning(f'Message "{message_text}" is not the last message sent from this device, its '
                                    f'status is not shown')
            return None
        return _wait_for(self.driver, *statuses, timeout=implicit_wait)

    @action(conversation_state)
    def is_message_marked_delivered(self, message_text: str, conversation: str = None,
                                    implicit_wait: float = 5) -> Optional[bool]:
        """
        Checks whether a message sent from this device has been delivered (or read).

        :param message_text: The text of the message. This has to be the last message sent from this device, as iOS
        only shows the status of that message.
        :param conversation: Optional. The name of the conversation. Defaults to the conversation that is open.
        :param implicit_wait: The number of seconds to wait for the message to be delivered.
        :return: Whether the message has been delivered, or None if the message is not the last message sent from this
        device.
        """
        return self._has_status(message_text, [CONVERSATION_STATUS_DELIVERED, CONVERSATION_STATUS_READ], implicit_wait)

    @action(conversation_state)
    def is_message_marked_read(self, message_text: str, conversation: str = None,
                               implicit_wait: float = 10) -> Optional[bool]:
        """
        Checks whether a message sent from this device has been read. This is only shown when the recipient shares read
        receipts.

        :param message_text: The text of the message. This has to be the last message sent from this device, as iOS
        only shows the status of that message.
        :param conversation: Optional. The name of the conversation. Defaults to the conversation that is open.
        :param implicit_wait: The number of seconds to wait for the message to be read.
        :return: Whether the message has been read, or None if the message is not the last message sent from this
        device.
        """
        return self._has_status(message_text, [CONVERSATION_STATUS_READ], implicit_wait)

    @action(conversation_state)
    def is_message_marked_not_delivered(self, message_text: str, conversation: str = None) -> Optional[bool]:
        """
        Checks whether sending a message from this device failed, e.g. an SMS that could not be delivered.

        :param message_text: The text of the message. This has to be the last message sent from this device, as iOS
        only shows the status of that message.
        :param conversation: Optional. The name of the conversation. Defaults to the conversation that is open.
        :return: Whether the message could not be delivered, or None if the message is not the last message sent from
        this device.
        """
        return self._has_status(message_text, [CONVERSATION_STATUS_NOT_DELIVERED], implicit_wait=0)

    @action(conversations_state, end_state=search_results_state)
    def search_conversations(self, query: str) -> list[str]:
        """
        Searches for conversations. Like in the app, the names of the conversations and their participants are
        searched. Only the conversations shown in the search results are returned: when there are many, the app shows
        the first few, followed by 'See All'.

        :param query: The text to search for.
        :return: The names of the conversations found.
        """
        _search(self.driver, query)
        if not self.driver.is_present(SEARCH_RESULTS_CONVERSATIONS):
            return []
        return [cell.get_attribute('name') for cell in self.driver.get_elements(SEARCH_RESULTS_CONVERSATIONS)]

    @action(conversations_state)
    def delete_conversation(self, conversation: str):
        """
        Deletes a conversation, including all its messages. Deleted conversations are moved to Recently Deleted, where
        they are kept for 30 days.

        :param conversation: The name of the conversation.
        """
        for _ in range(2):
            self._delete_conversation(conversation)
            if not self.driver.is_present(conversation_row(conversation)):
                logger.info(f'Deleted conversation {conversation}')
                return
            # the confirmation sometimes ignores the tap, while it is still appearing
            self.gtl_logger.warning(f'Conversation "{conversation}" was not deleted, trying again')
        raise MessagesError(f'Could not delete conversation "{conversation}"')

    def _delete_conversation(self, conversation: str):
        self.gtl_logger.info(f'Swiping conversation "{conversation}" to the left to reveal the delete button')
        _swipe_left(self.driver, conversation_cell(conversation))
        self.gtl_logger.info('Pressing delete button')
        self.driver.click(CONVERSATIONS_SWIPE_DELETE_BUTTON)
        # Deleting has to be confirmed. The confirmation ignores taps while it is appearing, so wait until it is shown.
        # The button is clicked instead of accepted through the alert API, as that does not work when the confirmation
        # also offers to report spam.
        for _ in range(10):
            if self.driver.is_present(CONVERSATIONS_CONFIRM_DELETE_BUTTON):
                break
            sleep(0.5)
        else:
            raise MessagesError(f'Deleting conversation "{conversation}" was not asked to be confirmed')
        sleep(2)
        self.gtl_logger.info('Confirming deletion')
        self.driver.click(CONVERSATIONS_CONFIRM_DELETE_BUTTON)
        sleep(2)
        # the first time, Messages explains that deleted conversations are kept in Recently Deleted for 30 days
        if self.driver.is_present(POPUP_RECENTLY_DELETED_TEXT):
            self.gtl_logger.info('Dismissing explanation of Recently Deleted')
            self.driver.click_alert_button(POPUP_OK_LABEL)
            sleep(1)
