from collections import deque
from dataclasses import dataclass
from typing import Callable, List

from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import State


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


def compose_clicks(xpaths: List[str]) -> Callable[[PumaDriver], None]:
    """
    Helper function to create a lambda for constructing transitions by clicking elements.

    This function generates a lambda function that, when executed, will click on a series
    of elements specified by their XPaths.

    :param xpaths: A list of XPaths of the elements to be clicked.
    :return: A lambda function that takes a driver and performs the clicking actions.
    """
    def  _click_(driver):
        for xpath in xpaths:
            driver.click(xpath)
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
