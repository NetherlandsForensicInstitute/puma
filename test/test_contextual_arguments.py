import unittest
from unittest.mock import Mock

from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaClickException, PumaDriver, Platform
from puma.state_graph.state import State, ContextualState
from puma.state_graph.state_graph import StateGraph

# Simple model of a state with a contextual value
screen = {'state': 'home', 'conversation': None}
# the conversations go_to_chat was called with
go_to_chat_calls = []


class ScreenState(State):
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def validate(self, driver: PumaDriver) -> bool:
        return screen['state'] == self.name


class ChatState(ScreenState, ContextualState):
    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        return not conversation or screen['conversation'] == conversation


def go_to_chat(driver: PumaDriver, conversation: str):
    go_to_chat_calls.append(conversation)
    if conversation is None:
        raise PumaClickException('no conversation to click')
    screen.update(state='chat', conversation=conversation)


def go_to_photo(driver: PumaDriver, caption: str = None):
    # a transition to a non-contextual state with a content argument, like taking a photo with a caption
    screen.update(state='photo', conversation=None, caption=caption)


def go_home():
    screen.update(state='home', conversation=None, caption=None)


class MockApplication(StateGraph):
    platform = Platform.ANDROID

    home_state = ScreenState('home', initial_state=True) # regular state
    chat_state = ChatState('chat', parent_state=home_state) # contextual state
    photo_state = ScreenState('photo', parent_state=home_state) # regular state
    home_state.to(chat_state, go_to_chat)
    home_state.to(photo_state, go_to_photo)

    # don't call super.__init__ so we do not try to connect to a real device
    def __init__(self):
        self.current_state = self.initial_state
        self.driver = Mock(platform=Platform.ANDROID)
        self.driver.is_present.return_value = False
        self.driver.app_open.return_value = True
        self.driver.back.side_effect = go_home
        self.gtl_logger = Mock()
        self.app_popups = []
        self.try_restart = True
        self.sent_messages = []
        self.sent_photos = []
        self.failures_to_simulate = 0

    @action(chat_state)
    def send_message(self, message_text: str, conversation: str = None):
        if self.failures_to_simulate > 0:
            # simulate an error after which the app is back at its home screen
            self.failures_to_simulate -= 1
            go_home()
            raise PumaClickException('simulated failure')
        self.sent_messages.append((screen['conversation'], message_text))

    @action(photo_state, end_state=home_state)
    def send_photo(self, caption: str = None):
        self.sent_photos.append(caption)
        go_home()


class TestContextualArguments(unittest.TestCase):

    def setUp(self):
        go_home()
        go_to_chat_calls.clear()
        self.application = MockApplication()

    def test_context_parameters_are_detected(self):
        # only one contextual parameter
        self.assertEqual(frozenset({'conversation'}), MockApplication.context_parameters)

    def test_non_contextual_arguments_are_not_remembered(self):
        self.application.send_message('hello', conversation='Alice')
        self.application.send_photo(caption='a caption')
        self.assertEqual({'conversation': 'Alice'}, self.application._last_context)

    def test_arguments_of_transitions_to_non_contextual_states_are_not_reused(self):
        self.application.send_photo(caption='a caption')
        self.application.send_photo()
        self.assertEqual(['a caption', None], self.application.sent_photos)

    def test_action_failure_recovers_with_remembered_conversation(self):
        self.application.send_message('first', conversation='Alice')
        self.application.failures_to_simulate = 1

        self.application.send_message('second')

        self.assertEqual(['Alice', 'Alice'], go_to_chat_calls)
        self.assertEqual([('Alice', 'first'), ('Alice', 'second')], self.application.sent_messages)

    def test_app_restart_before_action_recovers_with_remembered_conversation(self):
        self.application.send_message('first', conversation='Alice')
        go_home()  # the app restarted, but the state graph still thinks it is in the chat

        self.application.send_message('second')

        self.assertEqual(['Alice', 'Alice'], go_to_chat_calls)
        self.assertEqual([('Alice', 'first'), ('Alice', 'second')], self.application.sent_messages)

    def test_given_conversation_replaces_remembered_conversation(self):
        self.application.send_message('first', conversation='Alice')
        self.application.send_message('second', conversation='Bob')
        self.application.failures_to_simulate = 1

        self.application.send_message('third')

        self.assertEqual(['Alice', 'Bob', 'Bob'], go_to_chat_calls)
        self.assertEqual([('Alice', 'first'), ('Bob', 'second'), ('Bob', 'third')], self.application.sent_messages)

    def test_no_navigation_when_already_in_a_chat(self):
        self.application.send_message('first', conversation='Alice')
        # the user is now in a different chat, which the state graph does not know about
        screen['conversation'] = 'Bob'

        self.application.send_message('second')

        # without a conversation, the message is sent in the current chat
        self.assertEqual(['Alice'], go_to_chat_calls)
        self.assertEqual([('Alice', 'first'), ('Bob', 'second')], self.application.sent_messages)


if __name__ == '__main__':
    unittest.main()
