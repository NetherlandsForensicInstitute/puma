import unittest
from unittest.mock import Mock

from puma.state_graph.action import action
from puma.state_graph.state import SimpleState
from puma.state_graph.state_graph import StateGraph
from puma.utils import gtl_logging


class MockApplication(StateGraph):
    main_state = SimpleState(['xpath'], initial_state=True)

    # don't call super.__init__ so we do not try to connect to a real device
    def __init__(self, driver=Mock(), gtl_logger=Mock()):
        self.current_state = self.initial_state
        self.driver = driver
        self.gtl_logger = gtl_logger

    @action(main_state)
    def action_throws_generic_exception(self):
        raise Exception('test generic exception')


class TestAction(unittest.TestCase):

    def test_generic_exception_during_action_is_logged_and_propagated(self):
        mock_logger = gtl_logging.create_gtl_logger('mock_udid')

        with self.assertLogs(mock_logger, level='ERROR') as logs:
            application = MockApplication(gtl_logger=mock_logger)

            # assert a generic exception is propagated, since it is not a domain exception (i.e. PumaClickException)
            with self.assertRaisesRegex(Exception, 'test generic exception'):
                application.action_throws_generic_exception()

            # check that we have an error log (and sanity check we only have one)
            self.assertEqual(len(logs.output), 1)
            # the error should be logged by the action
            self.assertIn('ERROR:mock_udid:Unexpected exception while executing an action', logs.output[0])
            # and contain information about the reason
            self.assertIn('test generic exception', logs.output[0])