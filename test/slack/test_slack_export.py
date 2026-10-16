import csv
import os
import tempfile
import unittest
from unittest.mock import Mock

from puma.apps.android.slack.message_parser import Message
from puma.apps.android.slack.slack import Slack

HEADER = ['sender', 'time', 'text', 'attachments']


class TestSlackExportMessages(unittest.TestCase):
    """
    Tests the CSV file written by export_messages. The messages are collected by get_messages, which is mocked here so
    no device is needed.
    """

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.file_path = os.path.join(directory.name, 'export.csv')

    def _export(self, messages: list[Message], **kwargs) -> list[list[str]]:
        """Exports the given messages, and returns the rows of the CSV file."""
        # created without calling __init__, so we do not try to connect to a real device
        self.slack = Slack.__new__(Slack)
        self.slack.get_messages = Mock(return_value=messages)
        self.slack.gtl_logger = Mock()
        self.slack.export_messages(self.file_path, **kwargs)
        with open(self.file_path, newline='', encoding='utf-8') as file:
            return list(csv.reader(file))

    def test_export_messages(self):
        rows = self._export([Message('Alice', '2026-09-29T14:06:00', 'Hi Bob!', ''),
                             Message('Bob', '2026-09-29T14:07:00', 'Hi Alice', '')])
        self.assertEqual([HEADER,
                          ['Alice', '2026-09-29T14:06:00', 'Hi Bob!', ''],
                          ['Bob', '2026-09-29T14:07:00', 'Hi Alice', '']], rows)

    def test_messages_are_exported_in_the_given_order(self):
        messages = [Message('Alice', None, f'message {index}', '') for index in range(50)]
        rows = self._export(messages)
        self.assertEqual([f'message {index}' for index in range(50)], [row[2] for row in rows[1:]])

    def test_message_without_time(self):
        # Slack only shows the time of the first of consecutive messages of the same sender
        rows = self._export([Message('Alice', '2026-09-29T14:06:00', 'First', ''), Message('Alice', None, 'Second', '')])
        self.assertEqual(['Alice', '', 'Second', ''], rows[2])

    def test_message_without_sender(self):
        # the sender is not known when the beginning of the conversation could not be reached
        rows = self._export([Message(None, None, 'First', '')])
        self.assertEqual(['', '', 'First', ''], rows[1])

    def test_message_with_attachments(self):
        rows = self._export([Message('Alice', '2026-09-29T14:06:00', 'Look at this', 'image: IMG-1.jpeg'),
                             Message('Alice', None, '', 'image: IMG-2.jpeg\nimage: IMG-3.jpeg')])
        self.assertEqual(['Alice', '2026-09-29T14:06:00', 'Look at this', 'image: IMG-1.jpeg'], rows[1])
        # a message with only pictures has no text, multiple attachments are separated by a newline
        self.assertEqual(['Alice', '', '', 'image: IMG-2.jpeg\nimage: IMG-3.jpeg'], rows[2])

    def test_text_with_special_characters(self):
        texts = ['Hello, world', 'She said "hi"', 'Two\nlines', 'Semicolon; and tab\there', "It's fine", ' spaces ',
                 '=1+1']
        rows = self._export([Message('Alice', None, text, '') for text in texts])
        self.assertEqual(texts, [row[2] for row in rows[1:]])
        self.assertTrue(all(len(row) == 4 for row in rows))

    def test_text_with_emoji_and_non_ascii_characters(self):
        texts = ['Hello everyone! 👋 Welcome', 'Café ☕', 'Привет', '日本語']
        rows = self._export([Message('Zoë', None, text, '') for text in texts])
        self.assertEqual(texts, [row[2] for row in rows[1:]])
        self.assertEqual('Zoë', rows[1][0])

    def test_file_is_utf_8(self):
        self._export([Message('Zoë', None, 'Café ☕ 👋', '')])
        with open(self.file_path, 'rb') as file:
            content = file.read()
        self.assertIn('Zoë,,Café ☕ 👋,'.encode('utf-8'), content)

    def test_conversation_without_messages(self):
        self.assertEqual([HEADER], self._export([]))

    def test_existing_file_is_overwritten(self):
        self._export([Message('Alice', None, 'First export', ''), Message('Alice', None, 'Another message', '')])
        rows = self._export([Message('Bob', None, 'Second export', '')])
        self.assertEqual([HEADER, ['Bob', '', 'Second export', '']], rows)

    def test_arguments_are_passed_to_get_messages(self):
        self._export([], conversation='#general', message_count=20)
        self.slack.get_messages.assert_called_once_with(conversation='#general', message_count=20)

    def test_all_messages_of_the_current_conversation_are_exported_by_default(self):
        self._export([])
        self.slack.get_messages.assert_called_once_with(conversation=None, message_count=None)

    def test_number_of_exported_messages_is_logged(self):
        self._export([Message('Alice', None, 'First', ''), Message('Alice', None, 'Second', '')])
        self.slack.gtl_logger.info.assert_called_once()
        self.assertIn('2 messages', self.slack.gtl_logger.info.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
