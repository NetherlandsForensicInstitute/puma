from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Any, List


def back(driver):
    print(f'calling driver.back()')


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
    def validate(self, driver) -> bool:  # TODO: type of driver, or do we want wrapped method?
        pass

    def __repr__(self):
        return f'State {self.name} initial: {self.initial_state}'


class SimpleState(State):
    def __init__(self, name: str, xpaths: List[str], initial_state: bool = False, parent_state: 'State' = None, ):
        super().__init__(name, parent_state=parent_state, initial_state=initial_state)
        self.xpaths = xpaths

    def validate(self, driver) -> bool:
        for xpath in self.xpaths:
            print(f'checking rule {xpath}')  # TODO: actually check
        return True


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

        return new_class


class PumaUIGraph(metaclass=PumaUIGraphMeta):
    def __init__(self):
        print(f'GRAPH INITIATED, STATES: {self.states}')


# Example usage
class TestFsm(PumaUIGraph):
    conversations = SimpleState("Conversation overview", [],
                                True)  # TODO: infer name from attribute name (here: state1)
    chat_screen = SimpleState("Chat screen", [], parent_state=conversations)
    setting_screen = SimpleState("Settings", [], parent_state=conversations)

    conversations.to(chat_screen, lambda x: None)
    conversations.to(setting_screen, lambda x: None)


if __name__ == '__main__':
    print(TestFsm.states)
    print("transitions: " + str(len(TestFsm.transitions)))
    print('test')
