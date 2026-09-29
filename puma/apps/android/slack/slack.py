from puma.apps.android.slack.xpaths import HISTORY_BUTTON, WORKSPACE_SELECTOR, CHANNEL_BUTTON, CHANNEL_TITLE, \
    CHANNEL_BACK_BUTTON, CHANNEL_TEXT_INPUT
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, State
from puma.state_graph.state_graph import StateGraph

class SlackChannelState(SimpleState, ContextualState):
    """
    State defining a Slack channel screen
    """

    def __init__(self, parent_state: State):
        super().__init__([CHANNEL_BACK_BUTTON, CHANNEL_TEXT_INPUT],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, channel: str = None) -> bool:
        if not channel:
            return True
        return driver.is_present(CHANNEL_TITLE.format(channel=channel))

    @staticmethod
    def go_to_chat(driver: PumaDriver, channel: str):
        if not channel:
            raise ValueError(f'Cannot open a channel without a channel name')
        driver.click(CHANNEL_BUTTON.format(channel=channel))


class Slack(StateGraph):
    def __init__(self, device_udid):
        """
        Initializes Slack messenger with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        """
        package = 'com.Slack'
        StateGraph.__init__(self, device_udid, package)

    home_state = SimpleState(
        [HISTORY_BUTTON, WORKSPACE_SELECTOR],
        initial_state=True
    )
    channel_state = SlackChannelState(parent_state=home_state)

    home_state.to(channel_state, SlackChannelState.go_to_chat)

    @action(channel_state)
    def send_message(self, message: str, channel: str = None):
        self.driver.send_keys(CHANNEL_TEXT_INPUT, message)
        self.driver.press_enter()
