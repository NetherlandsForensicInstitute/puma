from puma.apps.android.snapchat.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler, simple_popup_handler
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, supported_version
from puma.state_graph.state import SimpleState, ContextualState, State, compose_clicks
from puma.state_graph.state_graph import StateGraph

APPLICATION_PACKAGE = 'com.snapchat.android'


def open_chat(driver: PumaDriver, conversation: str):
    """
    Opens the chat with a friend through the search screen, which also finds friends without a recent conversation.

    :param driver: The PumaDriver instance used to interact with the application.
    :param conversation: The name of the friend.
    """
    if not conversation:
        raise ValueError('Cannot open a chat without the name of a conversation')
    driver.click(CONVERSATIONS_SEARCH_BUTTON)
    driver.send_keys(SEARCH_TEXT_FIELD, conversation)
    driver.click(SEARCH_FRIEND_RESULT.format(conversation=conversation))
    driver.wait_until_present(CHAT_TEXT_FIELD, description='chat to open')


def close_chat(driver: PumaDriver):
    """
    Leaves a chat. The first back press only closes the keyboard, and a chat opened from search returns to the search
    screen, which is closed as well.

    :param driver: The PumaDriver instance used to interact with the application.
    """
    if driver.is_keyboard_shown():
        driver.back()
        driver.wait_until_keyboard_shown(shown=False)
    driver.back()
    if driver.is_present(SEARCH_CANCEL_BUTTON, implicit_wait=1):
        driver.click(SEARCH_CANCEL_BUTTON)


def discard_snap(driver: PumaDriver):
    """
    Leaves the preview of a snap without sending it. Snapchat asks to confirm this when the snap was edited.

    :param driver: The PumaDriver instance used to interact with the application.
    """
    driver.click(SNAP_PREVIEW_DISCARD_BUTTON)
    if driver.is_present(POPUP_DISCARD_SNAP_BUTTON, implicit_wait=1):
        driver.click(POPUP_DISCARD_SNAP_BUTTON)


def leave_send_to(driver: PumaDriver):
    """
    Leaves the send to screen. The first press on the back button only clears the search text, if there is any.

    :param driver: The PumaDriver instance used to interact with the application.
    """
    driver.click(SEND_TO_BACK_BUTTON)
    if driver.is_present(SEND_TO_BACK_BUTTON, implicit_wait=1):
        driver.click(SEND_TO_BACK_BUTTON)


class SnapchatChatState(SimpleState, ContextualState):
    """
    The chat with a friend.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the chat state.

        :param parent_state: The parent state of this chat state.
        """
        super().__init__(xpaths=[CHAT_TEXT_FIELD, CHAT_MESSAGE_LIST, CHAT_CAMERA_BUTTON],
                         parent_state=parent_state,
                         parent_state_transition=close_chat)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates that the chat is the chat with the given friend.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the friend.
        :return: True if the chat is the chat with the friend, or no friend was given. False otherwise.
        """
        if not conversation:
            return True
        return driver.is_present(CHAT_TITLE.format(conversation=conversation))


class SnapchatChatCameraState(SimpleState, ContextualState):
    """
    The camera opened from a chat, which sends snaps to that chat.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the chat camera state.

        :param parent_state: The chat state this camera was opened from.
        """
        super().__init__(xpaths=[CAMERA_PAGE, CAMERA_CAPTURE_BUTTON, CHAT_CAMERA_CLOSE_BUTTON],
                         invalid_xpaths=[POPUP_CAMERA_PERMISSION_TITLE],
                         parent_state=parent_state,
                         parent_state_transition=compose_clicks([CHAT_CAMERA_CLOSE_BUTTON], 'close_camera'))

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates that the camera sends snaps to the given friend.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the friend.
        :return: True if the camera sends snaps to the friend, or no friend was given. False otherwise.
        """
        if not conversation:
            return True
        return driver.is_present(CHAT_CAMERA_RECIPIENT.format(conversation=conversation))


class SnapchatChatSnapPreviewState(SimpleState, ContextualState):
    """
    The preview of a snap taken with the camera of a chat, before it is sent to that chat.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the chat snap preview state.

        :param parent_state: The chat camera state the snap was taken with.
        """
        super().__init__(xpaths=[SNAP_PREVIEW_FRAME, SNAP_PREVIEW_DISCARD_BUTTON, CHAT_SNAP_PREVIEW_MORE_FRIENDS_BUTTON],
                         invalid_xpaths=[POPUP_DIALOG],
                         parent_state=parent_state,
                         parent_state_transition=discard_snap)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates that the snap is sent to the given friend.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the friend.
        :return: True if the snap is sent to the friend, or no friend was given. False otherwise.
        """
        if not conversation:
            return True
        return driver.is_present(CHAT_SNAP_PREVIEW_SEND_BUTTON.format(conversation=conversation))


@supported_version('14.28.0.54')
class Snapchat(StateGraph):
    """
    A class representing a state graph for managing UI states and transitions in the Snapchat application.

    This class uses a state machine approach to manage transitions between different states
    of the Snapchat user interface. It provides methods to navigate between states, validate states,
    and handle unexpected states or errors.
    """
    camera_state = SimpleState([CAMERA_PAGE, CAMERA_CAPTURE_BUTTON, NAVIGATION_CAMERA_TAB],
                               invalid_xpaths=[POPUP_CAMERA_PERMISSION_TITLE],
                               initial_state=True)
    conversations_state = SimpleState([CONVERSATIONS_TITLE, CONVERSATIONS_SEARCH_BUTTON, NAVIGATION_CHAT_TAB],
                                      parent_state=camera_state,
                                      parent_state_transition=compose_clicks([NAVIGATION_CAMERA_TAB], 'open_camera_tab'))
    chat_state = SnapchatChatState(parent_state=conversations_state)
    chat_camera_state = SnapchatChatCameraState(parent_state=chat_state)
    chat_snap_preview_state = SnapchatChatSnapPreviewState(parent_state=chat_camera_state)
    snap_preview_state = SimpleState([SNAP_PREVIEW_FRAME, SNAP_PREVIEW_DISCARD_BUTTON, SNAP_PREVIEW_SEND_TO_BUTTON],
                                     invalid_xpaths=[POPUP_DIALOG],
                                     parent_state=camera_state,
                                     parent_state_transition=discard_snap)
    # Only reached during send_snap_to. Pressing back returns to the preview the snap was taken in.
    send_to_state = SimpleState([SEND_TO_SEARCH_FIELD, SEND_TO_BACK_BUTTON],
                                parent_state=snap_preview_state,
                                parent_state_transition=leave_send_to,
                                recognize_only=True)

    camera_state.to(conversations_state, compose_clicks([NAVIGATION_CHAT_TAB], 'open_chat_tab'))
    conversations_state.to(chat_state, open_chat)
    chat_state.to(chat_camera_state, compose_clicks([CHAT_CAMERA_BUTTON], 'open_chat_camera'))
    chat_camera_state.to(chat_snap_preview_state, compose_clicks([CAMERA_CAPTURE_BUTTON], 'take_snap', wait=2))
    camera_state.to(snap_preview_state, compose_clicks([CAMERA_CAPTURE_BUTTON], 'take_snap', wait=2))

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Snapchat with a device UDID.

        This class provides an API for interacting with the Snapchat application.
        It can be used with an emulator or a real device attached to the computer.

        :param device_udid: The unique device identifier for the Android device.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, APPLICATION_PACKAGE, **kwargs)
        self.add_popup_handlers(simple_popup_handler(POPUP_LOCATION_ALLOW_BUTTON),
                                PopUpHandler([POPUP_CREATE_AVATAR_TITLE], [POPUP_CREATE_AVATAR_NOT_NOW_BUTTON]),
                                PopUpHandler([POPUP_AUTO_SAVE_STORY_TITLE], [POPUP_CANCEL_BUTTON]),
                                simple_popup_handler(POPUP_DISCARD_SNAP_BUTTON),
                                PopUpHandler([POPUP_CAMERA_PERMISSION_TITLE], [POPUP_CAMERA_PERMISSION_ALLOW_BUTTON]))

    @action(chat_state)
    def send_message(self, message: str, conversation: str = None):
        """
        Sends a text message in a chat with a friend.

        :param message: The message to send.
        :param conversation: The name of the friend to send the message to. Not needed when already in that chat.
        """
        self.driver.send_keys(CHAT_TEXT_FIELD, message)
        self.driver.press_enter()

    @action(camera_state)
    def flip_camera(self):
        """
        Switches between the front and the rear camera. Snapchat remembers the camera that was used last, also for the
        camera opened from a chat.
        """
        self.driver.click(CAMERA_FLIP_BUTTON)

    @action(chat_snap_preview_state, end_state=chat_state)
    def send_snap(self, conversation: str = None, caption: str = None):
        """
        Takes a photo and sends it as a snap to a friend, from the chat with that friend.

        :param conversation: The name of the friend to send the snap to. Not needed when already in that chat.
        :param caption: An optional caption to put on the photo.
        """
        if caption:
            self._add_caption(caption)
        self.gtl_logger.info(f'Sending the snap to {conversation}' if conversation else 'Sending the snap')
        if conversation:
            self.driver.click(CHAT_SNAP_PREVIEW_SEND_BUTTON.format(conversation=conversation))
        else:
            self.driver.click(f'{CHAT_SNAP_PREVIEW_MORE_FRIENDS_BUTTON}/following-sibling::android.view.ViewGroup')

    @action(snap_preview_state, end_state=camera_state)
    def send_snap_to(self, recipients: list[str] = None, caption: str = None, my_story: bool = False,
                     public_story: bool = False):
        """
        Takes a photo with the camera tab and sends it as a snap to one or more friends, and/or posts it to a story.

        :param recipients: The names of the friends to send the snap to. Optional when posting to a story.
        :param caption: An optional caption to put on the photo.
        :param my_story: Whether to post the snap to My Story, which is visible to friends only.
        :param public_story: Whether to post the snap to the public story, which is visible to everyone. The first time,
        Snapchat introduces the public story and the public profile, which is accepted. Cannot be combined with my_story.
        """
        if my_story and public_story:
            raise ValueError('Cannot post a snap to both My Story and the public story: Snapchat allows only one of them')
        if not recipients and not my_story and not public_story:
            raise ValueError('Cannot send a snap without recipients or posting it to a story')
        recipients = recipients or []
        if caption:
            self._add_caption(caption)
        self.driver.click(SNAP_PREVIEW_SEND_TO_BUTTON)
        # The stories are at the top of the list, which changes when searching for friends, so they are selected first
        if my_story:
            self.gtl_logger.info('Selecting My Story')
            self.driver.click(SEND_TO_MY_STORY)
            if self.driver.is_present(SEND_TO_ADD_TO_STORY_CONFIRM_BUTTON, implicit_wait=1):
                self.driver.click(SEND_TO_ADD_TO_STORY_CONFIRM_BUTTON)
        elif public_story:
            self.gtl_logger.info('Selecting the public story')
            self.driver.click(SEND_TO_PUBLIC_STORY)
            if self.driver.is_present(SEND_TO_PUBLIC_STORY_INTRODUCTION_OKAY_BUTTON, implicit_wait=1):
                self.driver.click(SEND_TO_PUBLIC_STORY_INTRODUCTION_OKAY_BUTTON)
        for recipient in recipients:
            self._select_recipient(recipient)
        self.gtl_logger.info('Sending the snap')
        self.driver.click(SEND_TO_SEND_BUTTON)
        # Snapchat returns to the camera after sending. The first time a snap is posted to a story, it first asks to
        # save these snaps in Memories, which is declined.
        self.driver.wait_until_present(NAVIGATION_CAMERA_TAB, POPUP_AUTO_SAVE_STORY_TITLE, description='camera to open')
        if self.driver.is_present(POPUP_AUTO_SAVE_STORY_TITLE):
            self.driver.click(POPUP_CANCEL_BUTTON)
            self.driver.wait_until_present(NAVIGATION_CAMERA_TAB, description='camera to open')

    def _add_caption(self, caption: str):
        self.gtl_logger.info('Adding a caption to the snap')
        self.driver.click(SNAP_PREVIEW_CAPTION_BUTTON)
        self.driver.send_keys(SNAP_PREVIEW_CAPTION_TEXT_FIELD, caption)
        # Closes the keyboard and the caption editor, and keeps the caption
        self.driver.back()
        self.driver.wait_until_keyboard_shown(shown=False)

    def _select_recipient(self, recipient: str):
        if self.driver.is_present(SEND_TO_SELECTED_RECIPIENT.format(recipient=recipient)):
            return
        self.gtl_logger.info(f'Selecting {recipient} as recipient')
        self.driver.send_keys(SEND_TO_SEARCH_FIELD, recipient)
        self.driver.click(SEND_TO_RECIPIENT.format(recipient=recipient))
        if not self.driver.is_present(SEND_TO_SELECTED_RECIPIENT.format(recipient=recipient), implicit_wait=2):
            raise PumaClickException(f'Could not select {recipient} as recipient of the snap')
