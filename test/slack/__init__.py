from unittest.mock import Mock

from puma.apps.android.slack.slack import Slack
from puma.state_graph.puma_driver import Platform
from puma.state_graph.state import State


def slack_without_device(current_state: State = Slack.home_state) -> Slack:
    """
    Returns a Slack app with a mocked driver. It is created without calling __init__, so no device is needed.
    """
    slack = Slack.__new__(Slack)
    slack.current_state = current_state
    slack.app_popups = []
    slack.try_restart = True
    slack.driver = Mock(platform=Platform.ANDROID)
    slack.driver.app_open.return_value = True
    slack.driver.is_keyboard_shown.return_value = False
    slack.gtl_logger = Mock()
    return slack
