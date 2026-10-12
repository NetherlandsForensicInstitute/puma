import logging
import unittest
from unittest.mock import Mock

from puma.apps.android.slack.slack import Slack, parse_conversation
from puma.apps.android.slack.xpaths import HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR, HOME_CHANNEL_BUTTON, \
    HOME_DIRECT_MESSAGE_BUTTON, CHAT_BACK_BUTTON, CHAT_TEXT_INPUT, CHAT_TITLE
from puma.state_graph.puma_driver import Platform

# A workspace with a channel and a direct message conversation that have the same name
CHANNELS = ['general', 'random', 'bob']
DIRECT_MESSAGES = ['Bob', 'Alice']


class FakeSlackScreen:
    """
    Simple model of the Slack screens, to see in which conversation a message is sent without a device.
    """

    def __init__(self):
        self.state = 'home'
        self.conversation = None
        self.sent = []

    def is_present(self, xpath, *args, **kwargs) -> bool:
        if xpath in (HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR):
            return self.state == 'home'
        if xpath in (CHAT_BACK_BUTTON, CHAT_TEXT_INPUT):
            return self.state == 'chat'
        if self.state == 'chat':
            # the title does not show whether the conversation is a channel
            return xpath.lower() == CHAT_TITLE.format(chat_title=self.conversation[1:]).lower()
        return False

    def click(self, xpath, *args, **kwargs):
        # names are matched case-insensitively, as the XPaths do
        for name in CHANNELS:
            if xpath.lower() == HOME_CHANNEL_BUTTON.format(channel_name=name).lower():
                self.state, self.conversation = 'chat', f'#{name}'
        for name in DIRECT_MESSAGES:
            if xpath.lower() == HOME_DIRECT_MESSAGE_BUTTON.format(direct_message=name).lower():
                self.state, self.conversation = 'chat', f'@{name}'

    def back(self):
        self.state, self.conversation = 'home', None

    def send_keys(self, xpath, text):
        self.sent.append((self.conversation, text))


def _fake_slack(screen: FakeSlackScreen) -> Slack:
    # created without calling __init__, so we do not try to connect to a real device
    slack = Slack.__new__(Slack)
    slack.current_state = slack.initial_state
    slack.app_popups = []
    slack.try_restart = True
    slack.driver = Mock(platform=Platform.ANDROID)
    slack.driver.is_present.side_effect = screen.is_present
    slack.driver.click.side_effect = screen.click
    slack.driver.back.side_effect = screen.back
    slack.driver.send_keys.side_effect = screen.send_keys
    slack.driver.driver.is_keyboard_shown.return_value = False
    slack.driver.app_open.return_value = True
    slack.gtl_logger = logging.getLogger('test_slack_navigation')
    return slack


class TestParseConversation(unittest.TestCase):
    def test_channel(self):
        self.assertEqual((True, 'general'), parse_conversation('#general'))

    def test_direct_message(self):
        self.assertEqual((False, 'Bob'), parse_conversation('@Bob'))

    def test_without_prefix_is_a_direct_message(self):
        self.assertEqual((False, 'Bob'), parse_conversation('Bob'))
        self.assertEqual((False, 'general'), parse_conversation('general'))

    def test_only_the_first_character_is_a_prefix(self):
        self.assertEqual((True, '#general'), parse_conversation('##general'))
        self.assertEqual((False, 'bob@work'), parse_conversation('bob@work'))

    def test_empty_name(self):
        for conversation in ('#', '@'):
            with self.assertRaises(ValueError):
                parse_conversation(conversation)


class TestSlackNavigation(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)
        self.screen = FakeSlackScreen()
        self.slack = _fake_slack(self.screen)

    def _send(self, message: str, **kwargs) -> str:
        self.slack.send_message(message, **kwargs)
        return self.screen.sent[-1][0]

    def test_channel_then_direct_message(self):
        self.assertEqual('#general', self._send('a', conversation='#general'))
        self.assertEqual('@Bob', self._send('b', conversation='@Bob'))

    def test_direct_message_then_channel_then_direct_message(self):
        self.assertEqual('@Bob', self._send('a', conversation='Bob'))
        self.assertEqual('#general', self._send('b', conversation='#general'))
        self.assertEqual('@Alice', self._send('c', conversation='@Alice'))

    def test_without_prefix_opens_the_direct_message_conversation(self):
        # there is a channel #bob and a direct message conversation with Bob
        self.assertEqual('@Bob', self._send('a', conversation='bob'))

    def test_without_conversation_stays_in_the_current_conversation(self):
        self.assertEqual('#general', self._send('a', conversation='#general'))
        self.assertEqual('#general', self._send('b'))

    def test_unknown_conversation(self):
        with self.assertRaises(ValueError):
            self._send('a', conversation='#does-not-exist')
        self.assertEqual([], self.screen.sent)


if __name__ == '__main__':
    unittest.main()
