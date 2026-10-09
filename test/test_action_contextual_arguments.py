import importlib
import pkgutil
import unittest

import puma.apps.android
import puma.apps.ios
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, Platform
from puma.state_graph.state import SimpleState, ContextualState, State
from puma.state_graph.state_graph import StateGraph


class ChatState(SimpleState, ContextualState):
    def __init__(self, parent_state: State):
        super().__init__(['chat'], parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, conversation: str = None) -> bool:
        return True


class ChatSettingsState(SimpleState, ContextualState):
    def __init__(self, parent_state: State):
        super().__init__(['chat_settings'], parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, show_media: bool = False) -> bool:
        return True


def go_to_chat(driver: PumaDriver, conversation: str):
    pass


def go_to_chat_settings(driver: PumaDriver):
    pass


def go_to_settings(driver: PumaDriver):
    pass


def create_application(**actions):
    """
    Creates a StateGraph class with a home, settings, chat and chat settings state, and the given actions.
    """
    home_state = SimpleState(['home'], initial_state=True)
    settings_state = SimpleState(['settings'], parent_state=home_state)
    chat_state = ChatState(parent_state=home_state)
    chat_settings_state = ChatSettingsState(parent_state=chat_state)
    home_state.to(settings_state, go_to_settings)
    home_state.to(chat_state, go_to_chat)
    chat_state.to(chat_settings_state, go_to_chat_settings)
    states = dict(home_state=home_state, settings_state=settings_state, chat_state=chat_state,
                  chat_settings_state=chat_settings_state)
    namespace = dict(states, platform=Platform.ANDROID, __module__=__name__)
    for name, (state_name, function) in actions.items():
        namespace[name] = action(states[state_name])(function)
    return type('MockApplication', (StateGraph,), namespace)


class TestActionContextualArguments(unittest.TestCase):

    def test_action_missing_transition_argument_raises(self):
        def send_message(self, message_text: str):
            pass

        with self.assertRaisesRegex(ValueError, r"MockApplication.send_message \(state 'chat_state'\) is missing "
                                                r"contextual arguments \['conversation'\]"):
            create_application(send_message=('chat_state', send_message))

    def test_action_missing_validate_context_argument_raises(self):
        def view_settings(self, conversation: str):
            pass

        with self.assertRaisesRegex(ValueError, r"missing contextual arguments \['show_media'\]"):
            create_application(view_settings=('chat_settings_state', view_settings))

    def test_action_with_contextual_arguments_passes(self):
        def send_message(self, message_text: str, conversation: str):
            pass

        def send_sticker(self, conversation: str = None):
            pass

        def view_settings(self, conversation: str = None, show_media: bool = False):
            pass

        create_application(send_message=('chat_state', send_message), send_sticker=('chat_state', send_sticker),
                           view_settings=('chat_settings_state', view_settings))

    def test_action_with_kwargs_passes(self):
        def send_message(self, message_text: str, **kwargs):
            pass

        create_application(send_message=('chat_state', send_message))

    def test_action_without_contextual_state_on_path_needs_no_arguments(self):
        def change_name(self, name: str):
            pass

        create_application(change_name=('settings_state', change_name), go_home=('home_state', lambda self: None))

    def test_all_violating_actions_are_reported(self):
        def send_message(self, message_text: str):
            pass

        def view_settings(self):
            pass

        with self.assertRaises(ValueError) as context:
            create_application(send_message=('chat_state', send_message),
                               view_settings=('chat_settings_state', view_settings))
        self.assertIn("send_message (state 'chat_state') is missing contextual arguments ['conversation']",
                      str(context.exception))
        self.assertIn("view_settings (state 'chat_settings_state') is missing contextual arguments "
                      "['conversation', 'show_media']", str(context.exception))

    def test_all_applications_have_valid_actions(self):
        for package in (puma.apps.android, puma.apps.ios):
            for module in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
                with self.subTest(module=module.name):
                    importlib.import_module(module.name)


if __name__ == '__main__':
    unittest.main()
