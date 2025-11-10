from puma.apps.android.whatsapp.xpaths import *
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, ContextualState, State


class WhatsAppChatState(SimpleState, ContextualState):
    """
    A state representing a chat screen in the application.

    This class extends both SimpleState and ContextualState to represent a chat screen
    and validate its context based on the conversation name.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the ChatState with a parent state.

        :param parent_state: The parent state of this chat state.
        """
        super().__init__(xpaths=[CHAT_CONTACT_HEADER,
                                 CHAT_ROOT_LAYOUT],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates the context of the chat state.

        This method checks if the current chat screen matches the expected conversation name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the conversation to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not conversation:
            return True

        return driver.is_present(CHAT_CONTACT_HEADER_TEXT.format(conversation=conversation.lower()))


    @staticmethod
    def open_chat_settings(driver: PumaDriver, conversation: str):
        driver.click(CHAT_CONTACT_HEADER_WITH_NAME.format(conversation=conversation))


class WhatsAppChatSettingsState(SimpleState, ContextualState):
    """
    A state representing a chat settings screen in the application.

    This class extends both SimpleState and ContextualState to represent a chat settings screen
    and validate its context based on the contact or group name.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the ChatSettingsState with a parent state.

        :param parent_state: The parent state of this chat state.
        """
        super().__init__(xpaths=[CHAT_SETTINGS_CONTACT_NAME,
                                 CHAT_SETTINGS_NOTIFICATIONS,
                                 CHAT_SETTINGS_MEDIA_VISIBILITY],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates the context of the chat settings state.

        This method checks if the current chat settings screen matches the expected contact or group name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the conversation to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not conversation:
            return True

        return driver.is_present(CHAT_SETTINGS_CONTACT_NAME_TEXT.format(conversation=conversation.lower()))


class WhatsAppVoiceCallState(SimpleState, ContextualState):
    """
    A state representing a call screen in the application.

    This class extends both SimpleState and ContextualState to represent a call screen
    and validate its context based on the contact.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the CallState with a parent state.

        :param parent_state: The parent state of this call state.
        """
        super().__init__(xpaths=[CALL_END_CALL_BUTTON,
                                 CALL_SCREEN_BACKGROUND,
                                 VOICE_CALL_CAMERA_BUTTON],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates the context of the call state.

        This method checks if the current call screen matches the expected contact name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the call recipient to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not conversation:
            return True

        return driver.is_present(CALL_CONTACT_HEADER_TEXT.format(conversation=conversation.lower()))


class WhatsAppVideoCallState(SimpleState, ContextualState):
    """
    A state representing a call screen in the application.

    This class extends both SimpleState and ContextualState to represent a call screen
    and validate its context based on the contact.
    """

    def __init__(self, parent_state: State):
        """
        Initializes the CallState with a parent state.

        :param parent_state: The parent state of this call state.
        """
        super().__init__(xpaths=[CALL_END_CALL_BUTTON,
                                 CALL_SCREEN_BACKGROUND,
                                 VIDEO_CALL_CAMERA_BUTTON,
                                 VIDEO_CALL_SWITCH_CAMERA],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        """
        Validates the context of the call state.

        This method checks if the current call screen matches the expected contact name.

        :param driver: The PumaDriver instance used to interact with the application.
        :param conversation: The name of the call recipient to validate against.
        :return: True if the context is valid, False otherwise.
        """
        if not conversation:
            return True

        return driver.is_present(CALL_CONTACT_HEADER_TEXT.format(conversation=conversation.lower()))
