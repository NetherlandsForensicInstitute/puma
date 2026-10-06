from puma.apps.android.slack.xpaths import HOME_HISTORY_BUTTON, HOME_WORKSPACE_SELECTOR, HOME_CHANNEL_BUTTON, \
    CHAT_TITLE, \
    CHAT_BACK_BUTTON, CHAT_TEXT_INPUT, HOME_DIRECT_MESSAGE_BUTTON, CHAT_ATTACHMENTS_BUTTON, CHAT_SEND_BUTTON, \
    ATTACHMENTS_UPLOAD_FILE_BUTTON, ATTACHMENTS_ATTACH_PHOTOS_BUTTON, ATTACHMENTS_MEDIA_STRIP, ATTACHMENTS_PICTURES, \
    ATTACHMENTS_PICTURE, ATTACHMENTS_DONE_BUTTON
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, supported_version
from puma.state_graph.state import SimpleState, ContextualState, State, compose_clicks
from puma.state_graph.state_graph import StateGraph


class SlackChatState(SimpleState, ContextualState):
    """
    State defining a Slack channel screen
    """

    def __init__(self, parent_state: State):
        super().__init__([CHAT_BACK_BUTTON, CHAT_TEXT_INPUT],
                         invalid_xpaths=[ATTACHMENTS_UPLOAD_FILE_BUTTON],
                         parent_state=parent_state,
                         parent_state_transition=SlackChatState.back_to_home)

    @staticmethod
    def back_to_home(driver: PumaDriver):
        # When the keyboard is open, going back only closes the keyboard
        if driver.driver.is_keyboard_shown():
            driver.back()
        driver.back()

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
    attachments_state = SimpleState([ATTACHMENTS_UPLOAD_FILE_BUTTON], parent_state=channel_state)

    home_state.to(channel_state, SlackChatState.go_to_chat)
    channel_state.to(attachments_state, compose_clicks([CHAT_ATTACHMENTS_BUTTON], name='go_to_attachments'))

    @action(channel_state)
    def send_message(self, message: str, channel: str = None, direct_message: str = None):
        self.driver.send_keys(CHAT_TEXT_INPUT, message)
        self.driver.press_enter()

    # The attachments menu is opened in the action itself rather than by starting from the attachments state: the
    # conversation is not visible in the attachments menu, so the context of that state cannot be validated
    @action(channel_state)
    def send_picture(self, picture_id: int = 1, caption: str = None, channel: str = None, direct_message: str = None):
        """
        Sends a picture in the current or selected channel or direct message conversation.

        :param picture_id: The index of the picture to send, 1 being the most recent picture on the device.
        :param caption: The caption to add to the picture.
        :param channel: The name of the channel to send the picture in.
        :param direct_message: The name of the direct message conversation to send the picture in.
        """
        if picture_id < 1:
            raise ValueError(f'The picture index starts at 1, got {picture_id}')
        self.driver.click(CHAT_ATTACHMENTS_BUTTON)
        if not self.driver.is_present(ATTACHMENTS_MEDIA_STRIP, self.driver.implicit_wait) and \
                self.driver.is_present(ATTACHMENTS_ATTACH_PHOTOS_BUTTON):
            # Slack has no access to the photos yet: this opens a permission pop-up, which is handled when the action
            # is retried
            self.driver.click(ATTACHMENTS_ATTACH_PHOTOS_BUTTON)
        self.driver.click(self._find_picture(picture_id))
        self.driver.click(ATTACHMENTS_DONE_BUTTON)
        if caption:
            self.driver.send_keys(CHAT_TEXT_INPUT, caption)
        self.driver.click(CHAT_SEND_BUTTON)

    def _find_picture(self, picture_id: int) -> str:
        """
        Finds a picture in the photo strip of the attachments menu. The strip only shows a few pictures at a time, so it
        is swiped to the left until the picture is shown.

        :param picture_id: The index of the picture, 1 being the most recent picture on the device.
        :return: The XPath of the picture.
        """
        seen_pictures = []
        while True:
            pictures = [element.get_attribute('content-desc') for element in self.driver.get_elements(ATTACHMENTS_PICTURES)]
            new_pictures = [picture for picture in pictures if picture not in seen_pictures]
            if not new_pictures:
                raise PumaClickException(f'Could not find picture {picture_id}, only {len(seen_pictures)} pictures were found')
            seen_pictures += new_pictures
            if len(seen_pictures) >= picture_id:
                return ATTACHMENTS_PICTURE.format(content_desc=seen_pictures[picture_id - 1])
            strip = self.driver.get_element(ATTACHMENTS_MEDIA_STRIP).rect
            y = strip['y'] + strip['height'] / 2
            self.driver.driver.swipe(strip['x'] + strip['width'] * 0.8, y, strip['x'] + strip['width'] * 0.2, y, 500)
