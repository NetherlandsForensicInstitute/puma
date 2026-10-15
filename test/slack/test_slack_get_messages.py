import logging
import unittest
from unittest.mock import Mock, patch

from puma.apps.android.slack.message_parser import Message
from puma.apps.android.slack.slack import Slack
from puma.apps.android.slack.xpaths import CHAT_BACK_BUTTON, CHAT_TEXT_INPUT, CHAT_MESSAGES_LIST, \
    CHAT_BEGINNING_OF_CONVERSATION
from puma.state_graph.puma_driver import Platform
from .test_slack_messages import _message, _page

LIST_TOP, LIST_BOTTOM = 265, 2174
LIST_HEIGHT = LIST_BOTTOM - LIST_TOP
# Space above the first and below the last message, as in Slack
PADDING = 100


class FakeConversation:
    """
    Simple model of a Slack conversation screen that can be swiped, which shows the part of the messages that fits in
    the messages list. Messages are (sender, time, text, height): sender and time are None for a message without a
    header.
    """

    def __init__(self, messages: list[tuple]):
        self.messages = messages
        self.content_height = sum(height for *_, height in messages) + 2 * PADDING
        self.max_offset = max(0, self.content_height - LIST_HEIGHT)
        # a conversation opens at the end
        self.offset = self.max_offset
        self.lowest_offset = self.offset
        # the conversation cannot be scrolled above this offset, as if older messages are not loaded
        self.min_offset = 0

    @property
    def page_source(self) -> str:
        elements = []
        position = PADDING
        for sender, time, text, height in self.messages:
            top = LIST_TOP + position - self.offset
            bottom = top + height
            position += height
            if bottom > LIST_TOP and top < LIST_BOTTOM:
                # the part of a message outside the list is not shown
                elements.append(_message(max(top, LIST_TOP), min(bottom, LIST_BOTTOM), sender, time, text))
        return _page(*elements)

    def swipe(self, start_x, start_y, end_x, end_y, duration):
        self.offset = min(self.max_offset, max(self.min_offset, self.offset + round(start_y - end_y)))
        self.lowest_offset = min(self.lowest_offset, self.offset)

    def is_present(self, xpath, *args, **kwargs) -> bool:
        if xpath in (CHAT_BACK_BUTTON, CHAT_TEXT_INPUT):
            return True
        if xpath == CHAT_BEGINNING_OF_CONVERSATION:
            return self.offset == 0
        return False

    @property
    def screens_scrolled_up(self) -> float:
        return (self.max_offset - self.lowest_offset) / LIST_HEIGHT


def _slack_in_conversation(conversation: FakeConversation) -> Slack:
    # created without calling __init__, so we do not try to connect to a real device
    slack = Slack.__new__(Slack)
    slack.current_state = Slack.chat_state
    slack.app_popups = []
    slack.try_restart = True
    slack.driver = Mock(platform=Platform.ANDROID)
    slack.driver.is_present.side_effect = conversation.is_present
    slack.driver.app_open.return_value = True
    slack.driver.is_keyboard_shown.return_value = False
    slack.driver.get_element.side_effect = lambda xpath: Mock(
        rect={'x': 0, 'y': LIST_TOP, 'width': 1080, 'height': LIST_HEIGHT}) if xpath == CHAT_MESSAGES_LIST else Mock()
    slack.driver.driver = conversation
    conversation.get_device_time = lambda time_format: '2026-10-08T10:30:00'
    slack.gtl_logger = Mock()
    return slack


def _conversation_messages(long_run: bool = False) -> tuple[list[tuple], list[Message]]:
    """
    A conversation between Alice and Bob of 40 messages in groups of 4 messages of the same sender, of which only the
    first has a header. Returns the messages as shown on the screen, and the messages that should be returned.

    :param long_run: Whether Bob sends 30 more messages at the end, so the header of these messages is more than two
    screens away from the end of the conversation.
    """
    # the sender and whether the message has a header
    messages = [(('Alice', 'Bob')[(index // 4) % 2], index % 4 == 0) for index in range(40)]
    if long_run:
        messages += [('Bob', False)] * 30
    shown, expected = [], []
    for index, (sender, has_header) in enumerate(messages):
        # some large messages, like pictures
        height = 900 if index % 7 == 3 and index < 40 else 200
        day, hour, minute = 1 + index // 10, 2 + index // 60, index % 60
        shown.append((sender if has_header else None, f'Oct {day}th at {hour}:{minute:02} PM' if has_header else None,
                      f'message {index}', height))
        iso_time = f'2026-10-{day:02}T{12 + hour}:{minute:02}:00'
        expected.append(Message(sender, iso_time if has_header else None, f'message {index}', ''))
    return shown, expected


@patch('puma.apps.android.slack.slack.time.sleep', lambda seconds: None)
class TestSlackGetMessages(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)
        shown, self.expected = _conversation_messages()
        self.conversation = FakeConversation(shown)
        self.slack = _slack_in_conversation(self.conversation)

    # Getting all messages

    def test_get_all_messages(self):
        self.assertEqual(self.expected, self.slack.get_messages())
        self.slack.gtl_logger.warning.assert_not_called()

    def test_get_all_messages_of_short_conversation(self):
        conversation = FakeConversation([('Alice', 'Today at 9:00 AM', 'Hi', 200), (None, None, 'How are you?', 200)])
        self.assertEqual([Message('Alice', '2026-10-08T09:00:00', 'Hi', ''), Message('Alice', None, 'How are you?', '')],
                         _slack_in_conversation(conversation).get_messages())

    def test_get_all_messages_when_conversation_is_not_at_the_end(self):
        # e.g. a conversation with unread messages opens at the first unread message
        self.conversation.offset = self.conversation.max_offset // 3
        self.assertEqual(self.expected, self.slack.get_messages())

    def test_get_all_messages_warns_when_the_beginning_is_not_reached(self):
        # the older messages are not loaded
        self.conversation.min_offset = self.conversation.max_offset // 2
        messages = self.slack.get_messages()
        self.assertLess(len(messages), len(self.expected))
        self.assertEqual([message.text for message in self.expected[-len(messages):]],
                         [message.text for message in messages])
        # the sender of the first messages is shown above the part that could be reached
        self.assertIsNone(messages[0].sender)
        self.slack.gtl_logger.warning.assert_called_once()

    # Getting the last messages

    def test_get_last_message(self):
        self.assertEqual(self.expected[-1:], self.slack.get_messages(message_count=1))

    def test_get_last_messages(self):
        for message_count in (2, 4, 5, 13):
            with self.subTest(message_count=message_count):
                self.conversation.offset = self.conversation.max_offset
                self.assertEqual(self.expected[-message_count:], self.slack.get_messages(message_count=message_count))
        self.slack.gtl_logger.warning.assert_not_called()

    def test_get_last_messages_does_not_scroll_to_the_beginning(self):
        self.slack.get_messages(message_count=3)
        self.assertLess(self.conversation.screens_scrolled_up, 1)

    def test_get_last_messages_when_conversation_is_not_at_the_end(self):
        self.conversation.offset = self.conversation.max_offset // 3
        self.assertEqual(self.expected[-3:], self.slack.get_messages(message_count=3))

    def test_message_count_larger_than_conversation(self):
        self.assertEqual(self.expected, self.slack.get_messages(message_count=1000))
        self.slack.gtl_logger.warning.assert_not_called()

    def test_message_count_equal_to_conversation(self):
        self.assertEqual(self.expected, self.slack.get_messages(message_count=len(self.expected)))

    def test_invalid_message_count(self):
        for message_count in (0, -1):
            with self.assertRaises(ValueError):
                self.slack.get_messages(message_count=message_count)

    def test_keyboard_is_closed_before_collecting_messages(self):
        # the keyboard takes up half of the conversation, e.g. after sending a message
        self.slack.driver.close_keyboard.side_effect = lambda: self.assertEqual(0, self.slack.driver.driver.swipes)
        self.conversation.swipes = 0
        original_swipe = self.conversation.swipe

        def count_swipes(*args):
            self.conversation.swipes += 1
            original_swipe(*args)

        self.conversation.swipe = count_swipes
        self.assertEqual(self.expected[-1:], self.slack.get_messages(message_count=1))
        self.slack.driver.close_keyboard.assert_called_once_with()

    # The sender of messages without a header

    def test_sender_is_shown_on_the_screen(self):
        # the last message has no header, its sender is shown three messages up on the same screen
        messages = self.slack.get_messages(message_count=1)
        self.assertEqual([Message('Bob', None, 'message 39', '')], messages)
        self.assertEqual(0, self.conversation.screens_scrolled_up)

    def test_scrolls_up_until_the_sender_is_shown(self):
        # the last 30 messages have no header, the sender is shown more than two screens up
        shown, expected = _conversation_messages(long_run=True)
        conversation = FakeConversation(shown)
        messages = _slack_in_conversation(conversation).get_messages(message_count=2)
        self.assertEqual(expected[-2:], messages)
        self.assertEqual(['Bob', 'Bob'], [message.sender for message in messages])
        self.assertGreater(conversation.screens_scrolled_up, 2)
        # but not further than needed
        self.assertLess(conversation.screens_scrolled_up, 4)

    def test_all_messages_have_a_sender(self):
        shown, expected = _conversation_messages(long_run=True)
        for message_count in (None, 1, 10, 35):
            with self.subTest(message_count=message_count):
                messages = _slack_in_conversation(FakeConversation(shown)).get_messages(message_count=message_count)
                self.assertEqual(expected if message_count is None else expected[-message_count:], messages)
                self.assertTrue(all(message.sender for message in messages))


if __name__ == '__main__':
    unittest.main()
