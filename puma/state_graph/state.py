from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import Callable, List

from puma.state_graph import logger
from puma.state_graph.puma_driver import PumaDriver


class State(ABC):
    """
    Abstract class representing a state. Each state represents a window in the UI.
    """

    def __init__(self, initial_state: bool = False, parent_state: 'State' = None, parent_state_transition: Callable[..., None] = None):
        """
        Initializes a new State instance.

        :param initial_state: Whether this is the initial state of the FSM.
        :param parent_state: The parent state of this state, or None if it has no parent.
        :param parent_state_transition: How to transition back to the parent state. By default, this is a press on the back button.
        """
        self.id = None  # set in metaclass
        if initial_state and parent_state:
            raise ValueError(f'Error creating state: initial state cannot have a parent state')
        self.initial_state = initial_state
        self.parent_state = parent_state
        self.transitions = []

        if parent_state:
            if parent_state_transition is None:
                self.to(parent_state, back)
            else:
                self.to(parent_state, parent_state_transition)

    def to(self, to_state: 'State', ui_actions: Callable[..., None]):
        """
        Define the transition from this state to another state.

        :param to_state: The next state to transition to.
        :param ui_actions: A list of UI action functions to perform the transition.
        """
        self.transitions.append(Transition(self, to_state, ui_actions))

    def from_states(self, from_states: List['State'], ui_actions: Callable[..., None]):
        """
        Define the transition from a set of other states to this state.
        This method is convenient when a state can be reached from many other states with the same UI actions.

        :param from_states: The next state to transition to.
        :param ui_actions: A list of UI action functions to perform the transition.
        """
        for state in from_states:
            state.to(self, ui_actions)

    @abstractmethod
    def validate(self, driver: PumaDriver) -> bool:
        """
        Abstract method to validate the state.

        :param driver: The PumaDriver instance to use.
        """
        pass

    def __repr__(self):
        return f"{self.id}"


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
    Simple State. This is a standard state which can be validated by providing a list of present XPaths.
    """

    def __init__(self, xpaths: List[str], invalid_xpaths: list[str] = [], initial_state: bool = False, parent_state: 'State' = None, parent_state_transition: Callable[..., None] = None):
        """
        Initializes a new SimpleState instance.

        :param xpaths: A list of XPaths which are all present on the state window.
        "param invalid_xpaths: A list of xpaths which cannot be present in the state window.
        :param initial_state: Whether this is the initial state.
        :param parent_state: The parent state of this state, or None if it has no parent.
        :param parent_state_transition: How to transition back to the parent state. By default, this is a press on the back button.
        """
        super().__init__(initial_state=initial_state, parent_state=parent_state, parent_state_transition=parent_state_transition)
        if not xpaths:
            raise ValueError(f'Cannot create a SimpleState without any xpath validation expressions.')
        self.present_xpaths = xpaths
        self.invalid_xpaths = invalid_xpaths

    def validate(self, driver: PumaDriver) -> bool:
        """
        Validates if all XPaths are present on the screen.

        :param driver: The PumaDriver instance to use.
        :return: True if all XPaths are present, otherwise False.
        """
        return (all(driver.is_present(xpath) for xpath in self.present_xpaths)
                and all((not driver.is_present(xpath)) for xpath in self.invalid_xpaths))


def back(driver: PumaDriver):
    """
    Utility method for calling the back action in Android devices.

    :param driver: The PumaDriver instance to use.
    """
    logger.info(f'calling driver.back() with driver {driver}')
    driver.back()

@dataclass
class Transition:
    """
    A class representing a transition between states.

    This class encapsulates the details of a transition, including the starting state,
    the destination state, and any associated UI actions that should be executed
    to perform the transition.

    :param from_state: The starting state of the transition.
    :param to_state: The destination state of the transition.
    :param ui_actions: A function to be called with optional arguments during the transition,
                        typically to perform UI-related actions.
    """
    from_state: State
    to_state: State
    ui_actions: Callable[..., None]


def compose_clicks(xpaths: List[str], name: str = 'click') -> Callable[[PumaDriver], None]:
    """
    Helper function to create a lambda for constructing transitions by clicking elements.

    This function generates a lambda function that, when executed, will click on a series
    of elements specified by their XPaths.

    :param xpaths: A list of XPaths of the elements to be clicked.
    :param name: The name to give this lambda function.
    :return: A lambda function that takes a driver and performs the clicking actions.
    """
    def _click_(driver):
        for xpath in xpaths:
            driver.click(xpath)
    _click_.__name__ = name
    return _click_


def _shortest_path(start: State, destination: State | str) -> list[Transition] | None:
    """
       Finds the shortest path between two states.

       This function uses a breadth-first search algorithm to find the shortest path
       from the starting state to the destination state. The destination can be specified
       either as a State object or as a string representing the name of the state.

       :param start: The starting state for the path search.
       :param destination: The destination state or state name for the path search.
       :return: A list of transitions representing the shortest path from the start
                state to the destination state. Returns None if no path is found.
       """
    visited = set()
    queue = deque([(start, [])])
    while queue:
        state, path = queue.popleft()
        # if this is a path to the desired state, return the path
        if state == destination or state.id == destination:
            return path
        # we do not want cycles: skip paths to already visited states
        if state in visited:
            continue
        visited.add(state)
        # take a step in all possible directions
        for transition in state.transitions:
            queue.append((transition.to_state, path + [transition]))
    return None
