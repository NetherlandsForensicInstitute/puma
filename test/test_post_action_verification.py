import unittest
from unittest.mock import Mock

from puma.state_graph.puma_driver import PumaClickException
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, State
from puma.state_graph.state_graph import StateGraph
from puma.utils import gtl_logging


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

    def instance_verify_username_equals(self, new_name):
        return self.username == new_name

    @staticmethod
    def static_verify_username_equals(app, new_name):
        return app.username == new_name


class TestVerifyWith(unittest.TestCase):

    def setUp(self):
        # used to capture values inside passed 'verify_with' functions
        self.captures = []

    def test_verify_with_callable_is_called(self):
        # test if the verify_with is called by just capturing a boolean
        def should_be_called():
            self.captures.append(True)
            return True

        application = MockApplication()
        application.change_username(new_name='Capture this', verify_with=should_be_called)

        self.assertEqual(self.captures[0], True)

    def test_verify_with_not_callable_raises_exception(self):
        application = MockApplication()

        with self.assertRaisesRegex(TypeError, "'verify_with' must be a callable"):
            application.change_username(new_name='This is illegal', verify_with='not a callable')

    def test_verify_with_using_static_method(self):
        mock_logger = gtl_logging.create_gtl_logger('mock_udid')

        with self.assertLogs(mock_logger, level='INFO') as logs:
            application = MockApplication(gtl_logger=mock_logger)
            application.change_username(new_name='NewName', verify_with=MockApplication.static_verify_username_equals)

            self.assertIn("INFO:mock_udid:Action 'change_username' succeeded", logs.output)

    def test_verify_with_using_instance_method(self):
        mock_logger = gtl_logging.create_gtl_logger('mock_udid')

        with self.assertLogs(mock_logger, level='INFO') as logs:
            application = MockApplication(gtl_logger=mock_logger)
            application.change_username(new_name='NewName', verify_with=application.instance_verify_username_equals)

            self.assertIn("INFO:mock_udid:Action 'change_username' succeeded", logs.output)

    def test_verify_with_raises_puma_click_exception_is_logged(self):
        def verification_throws_puma_click_exception():
            raise PumaClickException('puma click exception')

        mock_logger = gtl_logging.create_gtl_logger('mock_udid')

        with self.assertLogs(mock_logger, level='INFO') as logs:
            application = MockApplication(gtl_logger=mock_logger)
            application.change_username(new_name='MyName', verify_with=verification_throws_puma_click_exception)

            # assert we logged what happened
            self.assertIn("WARNING:mock_udid:Verifying with 'verification_throws_puma_click_exception' failed due to exception: puma click exception", logs.output)
            # assert the action happened, i.e. our username has changed
            self.assertEqual(application.username, 'MyName')

    def test_verify_with_raises_generic_exception_is_propagated(self):
        def verification_throws_puma_click_exception():
            raise Exception('generic exception')

        application = MockApplication()

        with self.assertRaisesRegex(Exception, 'generic exception'):
            application.change_username(new_name='MyName', verify_with=verification_throws_puma_click_exception)

    def test_state_graph_is_passed_to_verify_with(self):
        # test if the verify_with receives the app by capturing it inside the function
        def should_receive_app(app):
            self.captures.append(app)
            return True

        application = MockApplication()
        application.change_username(new_name='ignore', verify_with=should_receive_app)

        self.assertIs(self.captures[0], application)

    def test_app_and_context_are_passed_to_verify_with(self):
        # test if the verify_with receives both by capturing them inside the function
        def should_receive_both(app, conversation):
            self.captures.append(app)
            self.captures.append(conversation)
            return True

        application = MockApplication()
        application.send_message(conversation='Bob', message='ignore', verify_with=should_receive_both)

        self.assertIs(self.captures[0], application)
        self.assertEqual(self.captures[1], 'Bob')

    def test_app_and_context_and_argument_are_passed_to_verify_with(self):
        # test if the verify_with receives all by capturing them inside the function
        def should_receive_all(app, conversation, message):
            self.captures.append(app)
            self.captures.append(conversation)
            self.captures.append(message)
            return True

        application = MockApplication()
        application.send_message(conversation='Bob', message='Hello', verify_with=should_receive_all)

        # our verify_with should have received the conversation
        self.assertIs(self.captures[0], application)
        self.assertEqual(self.captures[1], 'Bob')
        self.assertEqual(self.captures[2], 'Hello')

    def test_verify_with_logs_and_succeeds(self):
        def log_warning_and_return_true(app):
            gtl_logger = app.gtl_logger
            gtl_logger.info('post verification succeeded')
            return True

        mock_logger = gtl_logging.create_gtl_logger('mock_udid')

        with self.assertLogs(mock_logger, level='INFO') as logs:
            application = MockApplication(gtl_logger=mock_logger)
            application.change_username(new_name='MyName', verify_with=log_warning_and_return_true)

            # assert we called the gtl_logger we passed to our application, and it logged the expected message
            self.assertIn('INFO:mock_udid:post verification succeeded', logs.output)
            # assert the action happened, i.e. our username has changed
            self.assertEqual(application.username, 'MyName')

    def test_verify_with_logs_and_fails_still_executed_action(self):
        # failed verification should still result in the action being executed

        def log_warning_and_return_false(app):
            app.gtl_logger.warn('post verification failed')
            return False

        mock_logger = gtl_logging.create_gtl_logger('mock_udid')

        with self.assertLogs(mock_logger, level='WARN') as logs:
            application = MockApplication(gtl_logger=mock_logger)
            application.change_username(new_name='NewName', verify_with=log_warning_and_return_false)

            # assert we called the gtl_logger we passed to our application, and it logged the expected message
            self.assertIn('WARNING:mock_udid:post verification failed', logs.output)
            # assert the action still happened, i.e. our username has changed
            self.assertEqual(application.username, 'NewName')

    def test_verify_with_logs_and_fails_still_executes_following_action(self):
        # failed verification should still result in follow-up actions being executed

        def log_warning_and_return_false(app):
            app.gtl_logger.warn('post verification failed')
            return False

        mock_logger = gtl_logging.create_gtl_logger('mock_udid')

        with self.assertLogs(mock_logger, level='WARN') as logs:
            application = MockApplication(gtl_logger=mock_logger)
            application.change_username(new_name='OldName', verify_with=log_warning_and_return_false)
            application.change_username(new_name='NewName')

            # assert we called the gtl_logger we passed to our application, and it logged the expected message
            self.assertIn('WARNING:mock_udid:post verification failed', logs.output)
            # assert the follow up action still happened, i.e. our username has changed
            self.assertEqual(application.username, 'NewName')

    def test_verify_with_can_change_states_but_framework_returns_to_simple_state_before(self):
        # inside we move away from the settings_state simple state
        def change_states_and_return():
            application.go_to_state(application.main_state)
            return True

        application = MockApplication()
        application.change_username(new_name='ignore', verify_with=change_states_and_return)

        self.assertIs(application.current_state, application.settings_state)

    def test_verify_with_can_change_states_but_framework_returns_to_contextual_state_before(self):
        # inside we move away from the chat contextual state
        def change_states_and_return():
            application.go_to_state(application.main_state)
            return True

        application = MockApplication()
        application.send_message(conversation='ignore', message='ignore', verify_with=change_states_and_return)

        self.assertIs(application.current_state, application.chat_state)

    def test_verify_with_can_change_states_and_manually_returns_to_contextual_state_before(self):
        # inside we move away and back to the chat contextual state
        def change_states_and_return():
            application.go_to_state(application.main_state)
            application.go_to_state(application.chat_state)
            return True

        application = MockApplication()
        application.send_message(conversation='ignore', message='ignore', verify_with=change_states_and_return)

        self.assertIs(application.current_state, application.chat_state)

    def test_action_decorated_function_cant_have_parameter_named_verify_with(self):
        @action(MockApplication.settings_state)
        def this_should_throw_exception(verify_with):
            pass

        with self.assertRaisesRegex(Exception, "can't contain a parameter named 'verify_with'"):
            this_should_throw_exception()
