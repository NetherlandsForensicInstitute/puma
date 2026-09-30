from puma.apps.android.slack.xpaths import HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR, HOME_CHANNEL_BUTTON, \
    CHAT_TITLE, \
    CHAT_BACK_BUTTON, CHAT_TEXT_INPUT
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, State
from puma.state_graph.state_graph import StateGraph


class SlackChatState(SimpleState, ContextualState):
    """
    State defining a Slack channel screen
    """

    def __init__(self, parent_state: State):
        super().__init__([CHAT_BACK_BUTTON, CHAT_TEXT_INPUT],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, channel: str = None) -> bool:
        if not channel:
            return True
        return driver.is_present(CHAT_TITLE.format(chat_title=channel))

    @staticmethod
    def go_to_chat(driver: PumaDriver, channel: str = None, direct_message: str = None):
        if not channel and not direct_message:
            raise ValueError(f'Cannot open a channel without a channel or DM name')
        if channel:
            driver.click(HOME_CHANNEL_BUTTON.format(channel_name=channel))
        elif direct_message:
            driver.click(HOME_HISTORY_BUTTON.format(direct_message=direct_message))


class Slack(StateGraph):
    def __init__(self, device_udid):
        """
        Initializes Slack messenger with a device UDID.

        :param device_udid: The unique device identifier for the Android device.
        """
        package = 'com.Slack'
        StateGraph.__init__(self, device_udid, package)

    home_state = SimpleState(
        [HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR],
        invalid_xpaths=[CHAT_BACK_BUTTON],
        initial_state=True
    )
    channel_state = SlackChatState(parent_state=home_state)

    home_state.to(channel_state, SlackChatState.go_to_chat)

    @action(channel_state)
    def send_message(self, message: str, channel: str = None):
        self.driver.send_keys(CHAT_TEXT_INPUT, message)
        self.driver.press_enter()
