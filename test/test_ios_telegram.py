import unittest
from unittest.mock import Mock, patch

from puma.state_graph.puma_driver import Platform
from puma.state_graph.state_graph import StateGraph
from puma.apps.ios.telegram.locators import chat_header, conversation_row, quoted, gallery_media
from puma.apps.ios.telegram.telegram import Telegram, Message, _is_new_message, _parse_message, _parse_messages


def _element(element_type: str, name: str, value: str) -> str:
    value = value.replace('\n', '&#10;')
    return f'<XCUIElementType{element_type} type="XCUIElementType{element_type}" name="{name}" value="{value}"/>'


class TestTelegramParsing(unittest.TestCase):
    def test_parse_sent_message(self):
        self.assertEqual(Message(None, 'Hi alice', '14 Oct 2026 at 12:55', 'Seen by recipient'),
                         _parse_message('Your message', 'Hi alice\n14 Oct 2026 at 12:55\nSeen by recipient'))
        self.assertTrue(_parse_message('Your message', 'Hi\n1 Oct 2026 at 09:05\n').sent_by_me)

    def test_status_is_empty_until_seen(self):
        message = _parse_message('Your message', 'Puma test 1\n14 Oct 2026 at 13:01\n')
        self.assertEqual('', message.status)

    def test_date_in_another_format(self):
        # only messages of today were seen, other days could show e.g. 'Yesterday at 13:01': the date is then the second
        # last line of a sent message
        message = _parse_message('Your message', 'Hi\nYesterday at 13:01\nSeen by recipient')
        self.assertEqual(Message(None, 'Hi', 'Yesterday at 13:01', 'Seen by recipient'), message)
        self.assertEqual('Two\nlines', _parse_message('Your message', 'Two\nlines\n13:01\n').text)
        self.assertIsNone(_parse_message('Alice NFI', 'Hi\nYesterday at 13:01\nSeen'))

    def test_text_can_have_multiple_lines_and_dates(self):
        message = _parse_message('Your message', 'Line one\n14 Oct 2026 at 12:00\nLine three\n14 Oct 2026 at 13:01\n')
        self.assertEqual('Line one\n14 Oct 2026 at 12:00\nLine three', message.text)
        self.assertEqual('14 Oct 2026 at 13:01', message.time)

    def test_parse_photo_with_caption(self):
        message = _parse_message('Your photo', '\nCaption: Puma, caption\n14 Oct 2026 at 13:06\nSeen by recipient')
        self.assertEqual(Message(None, 'Puma, caption', '14 Oct 2026 at 13:06', 'Seen by recipient', 'photo'), message)

    def test_parse_photo_without_caption(self):
        message = _parse_message('Your photo', '\n14 Oct 2026 at 13:06\n')
        self.assertEqual(('', 'photo'), (message.text, message.kind))

    def test_parse_shared_location(self):
        message = _parse_message('Your message', 'Location\n14 Oct 2026 at 13:06\nSeen by recipient')
        self.assertEqual(('Location', 'message'), (message.text, message.kind))

    def test_other_elements_are_no_messages(self):
        self.assertIsNone(_parse_message('Alice NFI', 'online'))
        self.assertIsNone(_parse_message('Alice NFI', 'Outgoing Message\nRead\nLocation'))
        self.assertIsNone(_parse_message('Your message', None))

    def test_parse_messages_in_page_source(self):
        page_source = ('<AppiumAUT>' + _element('Other', 'Alice NFI', 'online')
                       + _element('Other', 'Your message', 'Hi alice\n14 Oct 2026 at 12:55\nSeen by recipient')
                       + _element('Image', 'Your photo', '\nCaption: A photo\n14 Oct 2026 at 13:06\n')
                       + _element('Button', 'Send media', '') + '</AppiumAUT>')
        self.assertEqual(['Hi alice', 'A photo'], [message.text for message in _parse_messages(page_source)])


class TestTelegramLocators(unittest.TestCase):
    def test_quoted_escapes_quotes(self):
        self.assertEqual('"Alice NFI"', quoted('Alice NFI'))
        self.assertEqual('"Say \\"hi\\""', quoted('Say "hi"'))
        self.assertEqual('"a\\\\b"', quoted('a\\b'))

    def test_conversation_locators_use_the_name(self):
        self.assertIn('label == "Alice NFI"', conversation_row('Alice NFI'))
        self.assertIn('label == "Alice NFI"', chat_header('Alice NFI'))
        self.assertTrue(gallery_media(2).endswith('[2]'))


def _chat(*messages: tuple[str, str, str]) -> list[Message]:
    """
    The messages in the page source of a chat, from (text, time, status) of messages sent from this device.
    """
    page_source = '<AppiumAUT>' + ''.join(
        _element('Other', 'Your message', f'{text}\n14 Oct 2026 at {time}\n{status}') for text, time, status in messages
    ) + '</AppiumAUT>'
    return _parse_messages(page_source)


class TestNewMessage(unittest.TestCase):
    def test_new_message_with_another_time(self):
        before = _chat(('Hi', '13:00', 'Seen by recipient'))
        after = _chat(('Hi', '13:00', 'Seen by recipient'), ('Location', '13:01', ''))
        self.assertTrue(_is_new_message(before, after, 'Location'))

    def test_previous_location_that_is_read_in_the_meantime_is_no_new_message(self):
        # the status changes while waiting, which is no new message
        before = _chat(('Hi', '13:00', 'Seen by recipient'), ('Location', '13:01', ''))
        after = _chat(('Hi', '13:00', 'Seen by recipient'), ('Location', '13:01', 'Seen by recipient'))
        self.assertFalse(_is_new_message(before, after, 'Location'))

    def test_two_locations_in_the_same_minute(self):
        before = _chat(('Hi', '13:00', 'Seen by recipient'), ('Location', '13:01', ''))
        after = _chat(('Hi', '13:00', 'Seen by recipient'), ('Location', '13:01', ''), ('Location', '13:01', ''))
        self.assertTrue(_is_new_message(before, after, 'Location'))

    def test_latest_message_has_another_text(self):
        before = _chat(('Hi', '13:00', ''))
        self.assertFalse(_is_new_message(before, _chat(('Hi', '13:00', ''), ('Other', '13:01', '')), 'Location'))
        self.assertFalse(_is_new_message(before, [], 'Location'))

    def test_first_message_of_a_chat(self):
        self.assertTrue(_is_new_message([], _chat(('Location', '13:01', '')), 'Location'))


class TestUnknownScreen(unittest.TestCase):
    def _telegram(self) -> Telegram:
        # __init__ is not called, as it connects to a device. No element is ever present, so no state validates.
        telegram = Telegram.__new__(Telegram)
        telegram.current_state = Telegram.conversations_state
        telegram.driver = Mock(platform=Platform.IOS)
        telegram.driver.is_present.return_value = False
        telegram.driver.app_open.return_value = True
        telegram.gtl_logger = Mock()
        telegram.app_popups = []
        telegram.try_restart = True
        return telegram

    def test_restarts_once_per_action_when_no_state_is_ever_recognized(self):
        telegram = self._telegram()
        with patch('puma.state_graph.state_graph.sleep'):
            with self.assertRaisesRegex(ValueError, 'Unknown state'):
                telegram.send_message('Hi', conversation='Alice NFI')
            self.assertEqual(1, telegram.driver.restart_app.call_count)
            # the next action may restart again, once
            with self.assertRaisesRegex(ValueError, 'Unknown state'):
                telegram.send_message('Hi', conversation='Alice NFI')
            self.assertEqual(2, telegram.driver.restart_app.call_count)

    def test_telegram_does_not_override_the_recovery_of_the_framework(self):
        self.assertIs(StateGraph.recover_state, Telegram.recover_state)
