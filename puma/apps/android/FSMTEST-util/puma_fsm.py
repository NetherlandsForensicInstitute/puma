from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Any, List


class State(ABC):
    def __init__(self, name: str, initial_state: bool = False):
        self.name = name
        self.initial_state = initial_state
        self.transitions = []

    def to(self, to_state:'State', ui_actions: Callable[[Any], None]):
        self.transitions.append(Transition(self, to_state, ui_actions))

    @abstractmethod
    def validate(self, driver) -> bool:  # TODO: type of driver, or do we want wrapped method?
        pass

    def __repr__(self):
        return f'State {self.name} initial: {self.initial_state}'


class SimpleState(State):
    def __init__(self, name: str, xpaths: List[str], initial_state: bool = False):
        super().__init__(name, initial_state)
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

        ## collect states and transitions
        states = []
        transitions = []
        for key, value in namespace.items():
            if isinstance(value, State):
                states.append(value)
            if isinstance(value, Transition):
                transitions.append(value)

        # Attach the collected bars to the class
        new_class.states = states
        new_class.transitions = [transition for state in states for transition in state.transitions]

        return new_class


class PumaUIGraph(metaclass=PumaUIGraphMeta):
    pass


# Example usage
class TestFsm(PumaUIGraph):
    state1 = SimpleState("State 1", [], True)  # TODO: infer name from attribute name (here: state1)
    state2 = SimpleState("State 2", [])

    state1.to(state2, lambda x:None)


if __name__ == '__main__':
    print(TestFsm.states)
    print(TestFsm.transitions)
