from puma.apps.android.slack.xpaths import HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR, HOME_CHANNEL_BUTTON, \
    CHAT_TITLE, \
    CHAT_BACK_BUTTON, CHAT_TEXT_INPUT, HOME_DIRECT_MESSAGE_BUTTON
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, supported_version
from puma.state_graph.state import SimpleState, ContextualState, State
from puma.state_graph.state_graph import StateGraph


class SlackChatState(SimpleState, ContextualState):
    """
    State defining a Slack channel screen
    """

    def __init__(self, parent_state: State):
        super().__init__([CHAT_BACK_BUTTON, CHAT_TEXT_INPUT],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, channel: str = None, direct_message: str = None) -> bool:
        if channel or direct_message:
            return driver.is_present(CHAT_TITLE.format(chat_title=(channel or direct_message)))
        return True

    @staticmethod
    def go_to_chat(driver: PumaDriver, channel: str = None, direct_message: str = None):
        if not channel and not direct_message:
            raise ValueError(f'Cannot open a channel without a channel or DM name')
        if channel:
            chat_xpath = HOME_CHANNEL_BUTTON.format(channel_name=channel)
        else:
            chat_xpath = HOME_DIRECT_MESSAGE_BUTTON.format(direct_message=direct_message)
        # The home screen might still be scrolled from an earlier visit, so search down first and then back up
        try:
            driver.swipe_to_find_element(chat_xpath, max_swipes=20, swipe_down=True)
        except PumaClickException:
            driver.swipe_to_find_element(chat_xpath, max_swipes=20, swipe_down=False)
        driver.click(chat_xpath)


@supported_version("26.09.50.0")
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
    def send_message(self, message: str, channel: str = None, direct_message: str = None):
        self.driver.send_keys(CHAT_TEXT_INPUT, message)
        self.driver.press_enter()
