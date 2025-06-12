from abc import ABC, abstractmethod
from typing import Callable, List

from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.transition import Transition


class State(ABC):
    """
    Abstract class representing a state. Each state represents a window in the UI.
    """
    def __init__(self, name: str, parent_state: 'State' = None, initial_state: bool = False):
        """
        Initializes a new State instance.

        :param name: The name of the state.
        :param parent_state: The parent state of this state, or None if it has no parent.
        :param initial_state: Whether this is the initial state of the FSM.
        """
        if initial_state and parent_state:
            raise ValueError(f'Error creating state {name}: initial state cannot have a parent state')
        self.name = name
        self.initial_state = initial_state
        self.parent_state = parent_state
        self.transitions = []

        if parent_state:
            self.to(parent_state, back)

    def to(self, to_state: 'State', ui_actions: Callable[..., None]):
        """
        Transition to another state.

        :param to_state: The next state to transition to.
        :param ui_actions: A list of UI action functions to perform the transition.
        """
        self.transitions.append(Transition(self, to_state, ui_actions))

    @abstractmethod
    def validate(self, driver: PumaDriver) -> bool:
        """
        Abstract method to validate the state.

        :param driver: The PumaDriver instance to use.
        """
        pass


class ContextualState(State):
    @abstractmethod
    def validate_context(self, driver: PumaDriver) -> bool:
        """
        Abstract method to validate the contextual state.

        :param driver: The PumaDriver instance to use.
        """
        pass


class SimpleState(State):
    """
    Simple State. This is a standard state which can be validated by providing a list of XPaths.
    """
    def __init__(self, name: str, xpaths: List[str], initial_state: bool = False, parent_state: 'State' = None, ):
        """
        Initializes a new SimpleState instance.

        :param name: The name of the state.
        :param xpaths: A list of XPaths which are all present on the state window.
        :param initial_state: Whether this is the initial state.
        :param parent_state: The parent state of this state, or None if it has no parent.
        """
        super().__init__(name, parent_state=parent_state, initial_state=initial_state)
        self.xpaths = xpaths

    def validate(self, driver: PumaDriver) -> bool:
        """
        Validates if all XPaths are present on the screen.
        :param driver: The PPumaDriver instance to use.
        :return a boolean
        """
        return all(driver.is_present(xpath) for xpath in self.xpaths)


def back(driver: PumaDriver):
    """
    Utility method for calling the back action in Android devices.
    :param driver: PumaDriver
    """
    print(f'calling driver.back() with driver {driver}')
    driver.back()
