import unittest
from unittest.mock import Mock

from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, State
from puma.state_graph.state_graph import StateGraph
from puma.utils import gtl_logging

# TODO-CC:
#   * require driver + logger as parameters of verification function?
#   * pass State to post_action function (either static method first arg, or instance method 'self')
#   * changing states in post_action currently manual, also use state annotations? (e.g. @post_action(state))

class MockChatState(SimpleState, ContextualState):

    def __init__(self, parent_state: State):
        super().__init__(xpaths=['xpath'], parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        return True


class MockApplication(StateGraph):
    main_state = SimpleState(['xpath'], initial_state=True)
    settings_state = SimpleState(['xpath'], parent_state=main_state)
    chat_state = MockChatState(parent_state=main_state)

    main_state.to(settings_state, lambda: print('opening setting screen'))
    main_state.to(chat_state, lambda: print('opening chat'))

    # don't call super.__init__ so we do not try to connect to a real device
    def __init__(self, driver=Mock(), gtl_logger=Mock()):
        self.current_state = self.initial_state
        self.driver = driver
        self.gtl_logger = gtl_logger

        self.username = None
        self.messages = {}

    @action(settings_state)
    def change_username(self, new_name: str):
        self.username = new_name

    @action(chat_state)
    def send_message(self, message: str, conversation: str = None, ):
        if conversation not in self.messages:
            self.messages = []
        self.messages.append(message)


class TestPostAction(unittest.TestCase):

    def test_post_action_callable_is_called(self):
        application = MockApplication()

        captures = []
        # test if the post_action is called by capturing the passed argument
        application.change_username(new_name='Capture this', post_action=
        lambda new_name: captures.append(new_name))

        self.assertEqual(captures[0], 'Capture this')

    def test_post_action_not_callable_raises_exception(self):
        application = MockApplication()

        with self.assertRaisesRegex(TypeError, 'post_action must be a callable'):
            application.change_username(new_name='This is illegal', post_action='not a callable')

    def test_driver_is_passed_to_post_action(self):
        driver_to_pass = Mock(name='passed_mock_driver')
        application = MockApplication(driver_to_pass)

        captures = []
        # test if the post_action receives the driver by capturing it inside the post_action lambda
        application.change_username(new_name='ignore', post_action=lambda driver: captures.append(driver))

        self.assertIs(captures[0], driver_to_pass)
        self.assertRegex(str(captures[0]), 'passed_mock_driver')

    def test_driver_and_context_are_passed_to_post_action(self):
        driver_to_pass = Mock(name='passed_mock_driver')
        application = MockApplication(driver_to_pass)

        captures = []
        # test if the post_action receives both by capturing them inside the post_action lambda
        application.send_message(conversation='Bob', message='ignore', post_action=
            lambda driver, conversation: (captures.append(conversation), captures.append(driver)))

        self.assertEqual(captures[0], 'Bob')
        self.assertIs(captures[1], driver_to_pass)
        self.assertRegex(str(captures[1]), 'passed_mock_driver')

    def test_driver_and_context_and_argument_are_passed_to_post_action(self):
        driver_to_pass = Mock(name='passed_mock_driver')
        application = MockApplication(driver_to_pass)

        captures = []
        # test if the post_action receives all by capturing them inside the post_action lambda
        application.send_message(conversation='Bob', message='Hello', post_action=
            lambda driver, conversation, message: (captures.append(conversation),
                                                   captures.append(driver),
                                                   captures.append(message)))

        # our post_action should have received the conversation
        self.assertEqual(captures[0], 'Bob')
        self.assertIs(captures[1], driver_to_pass)
        self.assertRegex(str(captures[1]), 'passed_mock_driver')
        self.assertEqual(captures[2], 'Hello')

    def test_post_action_fail_logs_and_continues(self):
        mock_logger = gtl_logging.create_gtl_logger('mock_udid')

        with self.assertLogs(mock_logger, level='WARN') as logs:
            application = MockApplication(gtl_logger=mock_logger)
            application.change_username(new_name='MyName', post_action=
                lambda gtl_logger, new_name: gtl_logger.warn('post verification failed'))

            # assert we called the gtl_logger we passed to our application, and it logged the expected message
            self.assertEqual(logs.output, ['WARNING:mock_udid:post verification failed'])
            # assert the action still happened, i.e. our username has changed
            self.assertEqual(application.username, 'MyName')

    def test_post_action_changes_state_and_does_not_return_throws_exception(self):
        application = MockApplication()

        with self.assertRaisesRegex(Exception, 'post_action did not return to original state'):
            application.change_username(new_name='ignore', post_action=
                lambda: application.go_to_state(application.main_state))

    def test_post_action_can_change_states_but_return_to_simple_state_before(self):
        application = MockApplication()

        def change_states_and_return():
            application.go_to_state(application.main_state)
            application.go_to_state(application.settings_state)

        application.change_username(new_name='ignore', post_action=change_states_and_return)

        self.assertIs(application.current_state, application.settings_state)

    def test_post_action_can_change_states_but_return_to_contextual_state_before(self):
        application = MockApplication()

        def change_states_and_return():
            application.go_to_state(application.main_state)
            application.go_to_state(application.chat_state)

        application.send_message(conversation='ignore', message='ignore', post_action=change_states_and_return)

        self.assertIs(application.current_state, application.chat_state)

    def test_action_decorated_function_contains_post_action_parameter_throws_exception(self):
        @action(MockApplication.settings_state)
        def this_should_throw_exception(post_action):
            pass

        with self.assertRaisesRegex(Exception, "can't contain a parameter named 'post_action'"):
            this_should_throw_exception()
