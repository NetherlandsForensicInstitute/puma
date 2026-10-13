import logging
import unittest
from unittest.mock import Mock, patch

from puma.utils.wait import wait_until


class TestWaitUntil(unittest.TestCase):
    def test_condition_met_at_once(self):
        condition = Mock(return_value=True)
        wait_until(condition, timeout=5)
        condition.assert_called_once()

    @patch('puma.utils.wait.sleep')
    def test_condition_met_later(self, sleep):
        condition = Mock(side_effect=[False, False, True])
        wait_until(condition, timeout=5, interval=2)
        self.assertEqual(3, condition.call_count)
        self.assertEqual([2, 2], [call.args[0] for call in sleep.call_args_list])

    def test_condition_is_checked_with_timeout_zero(self):
        wait_until(lambda: True, timeout=0)
        with self.assertRaises(TimeoutError):
            wait_until(lambda: False, timeout=0)

    def test_timeout(self):
        with self.assertRaises(TimeoutError) as error:
            wait_until(lambda: False, timeout=0.2, interval=0.05, description='the thing')
        self.assertIn('the thing', str(error.exception))
        self.assertIn('0.2', str(error.exception))

    @patch('puma.utils.wait.sleep')
    @patch('puma.utils.wait.monotonic', side_effect=[0, 1, 2, 3, 4, 5, 6])
    def test_does_not_sleep_longer_than_the_timeout(self, _, sleep):
        with self.assertRaises(TimeoutError):
            wait_until(lambda: False, timeout=2.5, interval=10)
        self.assertEqual([1.5, 0.5], [call.args[0] for call in sleep.call_args_list])

    def test_exception_in_condition_ends_the_wait(self):
        def condition():
            raise ValueError('broken')
        with self.assertRaises(ValueError):
            wait_until(condition, timeout=5)

    def test_logging(self):
        log = Mock(spec=logging.Logger)
        wait_until(lambda: True, timeout=5, description='the thing', log=log)
        self.assertEqual(['Waiting for the thing', 'Done waiting for the thing'],
                         [call.args[0] for call in log.info.call_args_list])

    def test_no_logging_without_description(self):
        log = Mock(spec=logging.Logger)
        wait_until(lambda: True, timeout=5, log=log)
        log.info.assert_not_called()


if __name__ == '__main__':
    unittest.main()
