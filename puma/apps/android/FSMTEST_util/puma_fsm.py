import inspect
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import Callable, Any, List, Dict

from appium.webdriver.common.appiumby import AppiumBy

from puma.apps.android.FSMTEST_util.puma_driver import PumaDriver



def back(driver: PumaDriver):
    driver.back()
    print(f'calling driver.back() with driver {driver}')


class State(ABC):
    def __init__(self, name: str, parent_state: 'State' = None, initial_state: bool = False):
        if initial_state and parent_state:
            raise ValueError(f'Error creating state {name}: initial state cannot have a parent state')
        self.name = name
        self.initial_state = initial_state
        self.parent_state = parent_state
        self.transitions = []

        if parent_state:
            self.to(parent_state, back)

    def to(self, to_state: 'State', ui_actions: Callable[[Any], None]):
        self.transitions.append(Transition(self, to_state, ui_actions))

    @abstractmethod
    def validate(self, driver: PumaDriver) -> bool | str:  # TODO: type of driver, or do we want wrapped method?
        pass

    def __repr__(self):
        return f'State {self.name} initial: {self.initial_state}'


class SimpleState(State):
    def __init__(self, name: str, xpaths: List[str], initial_state: bool = False, parent_state: 'State' = None, ):
        super().__init__(name, parent_state=parent_state, initial_state=initial_state)
        self.xpaths = xpaths

    def validate(self, driver: PumaDriver, conversation: str = None) -> bool | str:
        return all(driver.is_present(xpath) for xpath in self.xpaths)


@dataclass
class Transition:
    from_state: State
    to_state: State
    ui_actions: Callable[[Any], None]  # TODO: typing


class PumaUIGraphMeta(type):
    def __new__(cls, name, bases, namespace):
        # Create the class
        new_class = super().__new__(cls, name, bases, namespace)

        # Skip validation for the base PumaUIGraph class
        if name == 'PumaUIGraph':
            return new_class

        ## collect states and transitions
        states = []
        transitions = []
        for key, value in namespace.items():
            if isinstance(value, State):
                states.append(value)
            if isinstance(value, Transition):
                transitions.append(value)
        new_class.states = states
        new_class.transitions = [transition for state in states for transition in state.transitions]

        ## validation
        # only 1 initial state
        initial_states = [s for s in states if s.initial_state]
        if len(initial_states) == 0:
            raise ValueError(f'Graph needs an initial state')
        elif len(initial_states) > 1:
            raise ValueError(f'Graph can only have 1 initial state, currently more defined: {initial_states}')
        new_class.initial_state = initial_states[0]
        # every state except initial state needs transitions
        # TODO: states might need their incoming transitions? Then we can easily check this

        return new_class

def _safe_func_call(func, **kwargs):
    sig = inspect.signature(func)
    filtered_args = {
        k: v for k, v in kwargs.items() if k in sig.parameters
    }
    bound_args = sig.bind(**filtered_args)
    bound_args.apply_defaults()
    return func(**bound_args.arguments)

class PumaUIGraph(metaclass=PumaUIGraphMeta):
    def __init__(self, driver: PumaDriver):
        self.current_state = self.initial_state
        self.driver = driver

    def go_to_state(self, to_state: State | str, **kwargs):
        if to_state not in self.states:
            raise ValueError(f"{to_state.name} is not a known state in this PumaUiGraph")
        kwargs['driver'] = self.driver
        self._validate(self.current_state, **kwargs)
        transitions = self._find_shortest_path(to_state)
        for transition in transitions:
            _safe_func_call(transition.ui_actions, **kwargs)
            self._validate(transition.to_state, **kwargs)
            self.current_state = transition.to_state

    def _validate(self, state: State, **kwargs):
        valid = _safe_func_call(state.validate, **kwargs)
        if valid == True:
            return
        elif isinstance(valid, str):
            self.go_to_state(state.parent_state)
        else:
            print("not valid, do stuff, popups....") #TODO: More stuff to do
            self.driver.back() #TODO: TeleGuard hack


    def _find_shortest_path(self, destination: State | str) -> list[Transition] | None:
        """
        Gets the shortest path (in number of transitions) to the desired state.
        """
        start = self.current_state
        visited = set()
        queue = deque([(start, [])])

        while queue:
            state, path = queue.popleft()
            # if this is a path to the desired state, return the path
            if state == destination or state.name == destination:
                return path
            # we do not want cycles: skip paths to already visited states
            if state in visited:
                continue
            visited.add(state)
            # take a step in all possible directions
            for transition in state.transitions:
                queue.append((transition.to_state, path + [transition]))
        return None


def action(to_state: State):
    def decorator(func):
        def wrapper(*args, **kwargs):
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = bound_args.arguments
            arguments.pop('self')
            args[0].go_to_state(to_state, **arguments)

            sig2 = inspect.signature(func)
            filtered_args = {
                k: v for k, v in arguments.items() if k in sig2.parameters
            }

            filtered_args['self'] = args[0]
            bound_args2 = sig2.bind(**filtered_args)
            bound_args2.apply_defaults()
            result = func(**bound_args2.arguments)
            return result
        return wrapper
    return decorator


# Example usage
HAMBURGER_MENU = '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.view.View[3]'
class ConversationsState(SimpleState):

    def __init__(self):
        super().__init__("Conversation screen", ['//android.view.View[@content-desc="TeleGuard"]', HAMBURGER_MENU], initial_state=True)

    def go_to_settings(self, driver: PumaDriver):
        print(f"click on settings button with driver {driver}")
        driver.click(HAMBURGER_MENU)
        driver.click('//android.widget.ImageView[@content-desc="Settings"]')

    def go_to_chat(self, driver: PumaDriver, conversation:str):
        """
        Switches from chats to a chat screen
        """
        xpath = f'//android.widget.ImageView[contains(lower-case(@content-desc), "{conversation.lower()}")] | \
                        //android.view.View[contains(lower-case(@content-desc), "{conversation.lower()}")]'

        driver.driver.find_elements(by=AppiumBy.XPATH, value=xpath)[-1].click() #TODO Fix this, there should a ticket somewhere (#104)
        print(f'Clicking on conversation {conversation} with driver {driver}')


class ChatState(State):
    def __init__(self, parent_state):
        super().__init__("Chat screen", parent_state)

    def validate(self, driver: PumaDriver, conversation: str = None) -> bool | str:
        # 2 checks: 1) in conversation 2) in correct conversation
        print(f'Check in conversation with xpath "//xpath/in_conversation" with driver {driver}')
        if not driver.is_present('//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[4]'):
            return False
        if conversation:
            content_desc = driver.get_element('//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.widget.ImageView[2]').get_attribute('content-desc')
            if conversation.lower() in content_desc.lower():
                return True
            return content_desc.lower()
        return True

APPLICATION_PACKAGE = 'ch.swisscows.messenger.teleguardapp'

class TestFsm(PumaUIGraph):
    # TODO: infer name from attribute name (here: state1)
    conversations = ConversationsState()
    chat_screen = ChatState(conversations)
    chat_management = SimpleState("Chat management", [], parent_state=chat_screen)
    setting_screen = SimpleState("Settings", [], parent_state=conversations)

    conversations.to(chat_screen, conversations.go_to_chat)
    chat_screen.to(chat_management, lambda x: None)
    conversations.to(setting_screen, conversations.go_to_settings)

    def __init__(self,
                 device_udid,
                 desired_capabilities: Dict[str, str] = None,
                 implicit_wait=1,
                 appium_server='http://localhost:4723'):
        """
        Class with an API for TeleGuard using Appium. Can be used with an emulator or real device attached to the computer.
        """
        self.driver = PumaDriver(device_udid, APPLICATION_PACKAGE)
        self.driver.activate_app() # TODO: Activate app should be part of the navigation code
        PumaUIGraph.__init__(self, self.driver)

    @action(chat_screen)
    def send_message(self, msg: str, conversation: str = None):
        """
        Sends a message
        """
        print(f"Sending message {msg}")
        text_field = '//android.widget.EditText'
        self.driver.click(text_field)
        self.driver.send_keys(text_field, msg)
        # text_box_el.click()
        # text_box_el.send_keys(msg)
        self.driver.click('//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.widget.ImageView[3]')


if __name__ == '__main__':
    print(TestFsm.states)
    print("transitions: " + str(len(TestFsm.transitions)))
    print('test')

    t = TestFsm('34281JEHN03866')
    print(len(t._find_shortest_path(TestFsm.chat_management)))
    t.go_to_state(TestFsm.setting_screen)
    # print(f"Currently in state [{t.current_state}]")
    #
    # t.go_to_state(TestFsm.chat_screen, conversation='Alice')
    # print(f"Currently in state [{t.current_state}]")
    t.send_message("Hello Bob", conversation="bob")
    t.send_message("Test", conversation='TeleGuard')
