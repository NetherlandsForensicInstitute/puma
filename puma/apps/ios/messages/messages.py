from time import sleep

from puma.apps.ios.messages import logger
from puma.apps.ios.messages.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler
from puma.state_graph.puma_driver import PumaDriver, Platform, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

MESSAGES_BUNDLE_ID = 'com.apple.MobileSMS'


class MessagesError(Exception):
    """
    Raised when Messages refuses an action, e.g. sending a message to a recipient that cannot be reached.
    """
    pass


def _parse_message(label: str) -> tuple[str, str]:
    """
    Splits the label of a message cell into the sender and the text. The text can contain commas, so the sender is split
    off at the first comma, and the time at the last comma.
    """
    sender, rest = label.split(', ', 1)
    text = rest.rsplit(', ', 1)[0]
    return sender, text


def _title_matches(title: str, conversation: str) -> bool:
    """
    Whether the title of an opened conversation belongs to a conversation. For contacts, the title only shows the first
    name (e.g. 'Bob' for the conversation 'Bob Jansen'), while the overview shows the full name.
    """
    return title == conversation or conversation.startswith(f'{title} ')


def _swipe_left(driver: PumaDriver, element: str):
    """
    Swipes a row in a list to the left, which reveals the delete button.
    """
    rect = driver.get_element(element).rect
    y = rect['y'] + rect['height'] / 2
    driver.execute_script('mobile: dragFromToForDuration', {
        'fromX': rect['x'] + rect['width'] - 20, 'fromY': y, 'toX': rect['x'] + 60, 'toY': y, 'duration': 0.2})
    sleep(1)


def _close_new_message(driver: PumaDriver):
    driver.click(CANCEL_BUTTON)
    sleep(1)


class ConversationState(SimpleState, ContextualState):
    """
    A state representing an opened conversation.
    """

    def __init__(self, parent_state):
        # the parent transition is the default back action, which uses the back button in the navigation bar
        super().__init__(xpaths=[CONVERSATION_TITLE, MESSAGE_BODY_FIELD], invalid_xpaths=[NEW_MESSAGE_NAVIGATION_BAR],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        if not conversation:
            return True
        return _title_matches(driver.get_element(CONVERSATION_TITLE).get_attribute('label'), conversation)

    @staticmethod
    def open_conversation(driver: PumaDriver, conversation: str):
        driver.click(conversation_row(conversation))
        sleep(1)


@supported_version("26.6")
class Messages(StateGraph):
    """
    A class representing the Messages application on iOS.

    Conversations are identified by their name as shown in the overview: the name of the contact (e.g. 'Bob Jansen'),
    the phone number or email address, or the name of the group.

    On a simulator, messages cannot be sent to new recipients. The two conversations the simulator starts with do work:
    messages sent in one of them are received in the other.
    """
    platform = Platform.IOS

    # States
    # The welcome screen and the new message screen are shown on top of the overview, while the overview stays in the
    # element tree. Therefore these are marked as invalid.
    conversations_state = SimpleState(xpaths=[CONVERSATION_LIST, COMPOSE_BUTTON],
                                      invalid_xpaths=[APPLE_INTELLIGENCE_WELCOME_TEXT, NEW_MESSAGE_NAVIGATION_BAR,
                                                      RECENTLY_DELETED_TEXT],
                                      initial_state=True)
    new_message_state = SimpleState(xpaths=[NEW_MESSAGE_NAVIGATION_BAR, RECIPIENT_FIELD],
                                    parent_state=conversations_state,
                                    parent_state_transition=_close_new_message)
    conversation_state = ConversationState(parent_state=conversations_state)

    # Transitions
    conversations_state.to(new_message_state, compose_clicks([COMPOSE_BUTTON], 'open_new_message'))
    conversations_state.to(conversation_state, conversation_state.open_conversation)

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Messages with a device UDID.

        :param device_udid: The unique device identifier of the iOS device or simulator.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, MESSAGES_BUNDLE_ID, **kwargs)
        self.add_popup_handlers(PopUpHandler([APPLE_INTELLIGENCE_WELCOME_TEXT], [CONTINUE_BUTTON]),
                                PopUpHandler([RECENTLY_DELETED_TEXT], [OK_BUTTON]))

    @action(new_message_state, end_state=conversation_state)
    def start_conversation(self, recipient: str, message: str):
        """
        Starts a conversation by sending a message to a recipient. When there already is a conversation with the
        recipient, the message is sent in that conversation. The conversation is opened afterwards.

        :param recipient: The name of a contact, or a phone number or email address.
        :param message: The message to send.
        """
        self.driver.send_keys(RECIPIENT_FIELD, recipient)
        sleep(2)
        if self.driver.is_present(recipient_suggestion(recipient)):
            self.driver.click(recipient_suggestion(recipient))
        else:
            # not a contact: confirm the phone number or email address as recipient
            self.driver.press_enter()
        sleep(1)
        self.driver.click(MESSAGE_BODY_FIELD)
        self.driver.driver.switch_to.active_element.send_keys(message)
        sleep(1)
        self.driver.click(SEND_BUTTON)
        sleep(2)
        # when the message is sent, the new message screen turns into the conversation
        if self.driver.is_present(NEW_MESSAGE_NAVIGATION_BAR):
            _close_new_message(self.driver)
            raise MessagesError(f'Cannot send a message to "{recipient}". Note that messages cannot be sent to new '
                                f'recipients on a simulator.')
        logger.info(f'Started conversation with {recipient}')

    @action(conversation_state)
    def send_message(self, message: str, conversation: str):
        """
        Sends a message in a conversation.

        :param message: The message to send.
        :param conversation: The name of the conversation.
        """
        self.driver.send_keys(MESSAGE_BODY_FIELD, message)
        self.driver.click(SEND_BUTTON)
        logger.info(f'Sent message to {conversation}')

    @action(conversation_state)
    def get_messages(self, conversation: str) -> list[tuple[str, str]]:
        """
        Returns the text messages in a conversation that are shown on the screen, with their sender. Photos and other
        attachments are not included.

        :param conversation: The name of the conversation.
        :return: The messages as (sender, text), e.g. [('Your iMessage', 'Hi!'), ('Bob Jansen', 'Hello')]. Messages sent
        from this device have SENT_BY_ME as sender.
        """
        if not self.driver.is_present(MESSAGE_CELLS):
            return []
        return [_parse_message(element.get_attribute('label')) for element in self.driver.get_elements(MESSAGE_CELLS)]

    @action(conversations_state)
    def delete_conversation(self, conversation: str):
        """
        Deletes a conversation, including all its messages. Deleted conversations are moved to Recently Deleted, where
        they are kept for 30 days.

        :param conversation: The name of the conversation.
        """
        for _ in range(2):
            self._delete_conversation(conversation)
            if not self.driver.is_present(conversation_row(conversation)):
                logger.info(f'Deleted conversation {conversation}')
                return
            # the confirmation sometimes ignores the tap, while it is still appearing
            logger.info(f'Conversation {conversation} was not deleted, trying again')
        raise MessagesError(f'Could not delete conversation "{conversation}"')

    def _delete_conversation(self, conversation: str):
        _swipe_left(self.driver, conversation_cell(conversation))
        self.driver.click(SWIPE_DELETE_BUTTON)
        # Deleting has to be confirmed. The confirmation ignores taps while it is appearing, so wait until it is shown.
        # The button is clicked instead of accepted through the alert API, as that does not work when the confirmation
        # also offers to report spam.
        for _ in range(10):
            if self.driver.is_present(CONFIRM_DELETE_BUTTON):
                break
            sleep(0.5)
        else:
            raise MessagesError(f'Deleting conversation "{conversation}" was not asked to be confirmed')
        sleep(2)
        self.driver.click(CONFIRM_DELETE_BUTTON)
        sleep(2)
        # the first time, Messages explains that deleted conversations are kept in Recently Deleted for 30 days
        if self.driver.is_present(RECENTLY_DELETED_TEXT):
            self.driver.click_alert_button(OK_LABEL)
            sleep(1)
