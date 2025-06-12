import inspect
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from time import sleep
from typing import Callable, List

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from puma.apps.android.FSMTEST_util.puma_driver import PumaDriver, PumaClickException

# TODO move parts to their own files
class PopUpHandler:
    """
    Handler for popup windows in Android applications.
    """

    def __init__(self, recognize_xpath: str, dismiss_xpath: str):
        """
        Popup handler.

        :param recognize_xpath: The XPath to use for recognizing popup windows.
        :param click: The XPath for the element to dismiss the popup.
        """
        self.recognize_xpath = recognize_xpath
        self.dismiss_xpath = dismiss_xpath

    def is_popup_window(self, driver: PumaDriver) -> bool:
        """
        Check if a popup is present in the current window

        :param driver: The PumaDriver instance to use for searching the window.
        return: Whether the popup window was found or not.
        """
        return driver.is_present(self.recognize_xpath)

    def dismiss_popup(self, driver: PumaDriver):
        """
        Dismiss a popup window using the provided xpath.

        :param driver: The PumaDriver instance to use for searching and clicking the button.
        """
        driver.click(self.dismiss_xpath)


def simple_popup_handler(xpath: str):
    """
    Utility method to create a popup handler that uses the same XPath for both recognizing and dismissing the popup.
    :param xpath: xpath of the element to click
    :return: PopUpHandler for the provided xpath
    """
    return PopUpHandler(xpath, xpath)


known_popups = [simple_popup_handler('//android.widget.ImageView[@content-desc="Dismiss update dialog"]'),
                simple_popup_handler(
                    '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"]'),
                simple_popup_handler(
                    '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]')]


def back(driver: PumaDriver):
    """
    Utility method for calling the back action in Android devices.
    :param driver: PumaDriver
    """
    print(f'calling driver.back() with driver {driver}')
    driver.back()


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


class StateGraphMeta(type):
    """
    Metaclass for creating and validating StateGraph classes.

    This metaclass is responsible for collecting states and transitions defined within a class,
    and performing validation to ensure the integrity of the state graph. It ensures that there
    is exactly one initial state, that all states are reachable from the initial state, and
    that there are no duplicate state names or transitions.
    """
    def __new__(cls, name, bases, namespace):
        """
        Creates a new class using the StateGraphMeta metaclass.

        This method collects states and transitions from the class namespace and performs
        validation on the state graph.

        :param name: The name of the class being created.
        :param bases: The base classes of the class being created.
        :param namespace: The namespace dictionary containing the class attributes.
        :return: The newly created class.
        """
        new_class = super().__new__(cls, name, bases, namespace)

        # Skip validation for the base PumaUIGraph class
        if name == 'StateGraph':
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
        new_class.initial_state = next(s for s in states if s.initial_state)

        ## validation
        StateGraphMeta._validate_graph(states)

        return new_class

    @staticmethod
    def _validate_graph(states: List[State]):        # TODO: make unit test for this validation
        """
        Validates the state graph to ensure it meets specific criteria.

        This method checks for the presence of exactly one initial state, ensures that
        the initial state is not a ContextualState, verifies that all ContextualStates
        have a parent state, and checks that all states are reachable from the initial
        state and vice versa. It also ensures there are no duplicate state names or
        transitions.

        :param states: A list of states in the state graph.
        :raises ValueError: If any of the validation checks fail.
        """
        # TODO extract method for each validation
        # only 1 initial state
        initial_states = [s for s in states if s.initial_state]
        if len(initial_states) == 0:
            raise ValueError(f'Graph needs an initial state')
        elif len(initial_states) > 1:
            raise ValueError(f'Graph can only have 1 initial state, currently more defined: {initial_states}')
        initial_state = initial_states[0]

        # initial state cannot be Contextual state
        if isinstance(initial_state, ContextualState):
            raise ValueError(f'Initial state ({initial_state}) Cannot be an Contextual state')

        # Contextual states need parent state
        contextual_state_without_parent = [s for s in states if isinstance(s, ContextualState) and s.parent_state is None]
        if contextual_state_without_parent:
            raise ValueError(f'Contextual states without parent are not allowed: {contextual_state_without_parent}')

        #you need to be able to go from  the initial state to each other state and back
        unreachable_states = [s for s in states if not s.initial_state and not(bool(_shortest_path(initial_state, s)) and bool(_shortest_path(s, initial_state)))]
        if unreachable_states:
            raise ValueError(f'Some states cannot be reached from the initial state, or cannot go back to the initial state: {unreachable_states}')
        # No duplicate names for states
        seen = set()
        duplicate_names = {s.name for s in states if s.name in seen or seen.add(s.name)}
        if duplicate_names:
            raise ValueError(f"States must have a unique name. Multiple sates are named {duplicate_names}")
        # No duplicate transitions: only one transition between each 2 states
        for s in states:
            seen = set()
            duplicates = {t.to_state for t in s.transitions if t.to_state in seen or seen.add(t.to_state)}
            if duplicates:
                raise ValueError(f"State {s} has invalid transitions: multiple transitions defined to neighboring state(s) {duplicates}")


def _safe_func_call(func, **kwargs):
    """
        Safely calls a function with the provided keyword arguments.

        This function filters the provided keyword arguments to only include those that are
        defined in the function's signature. It then attempts to call the function with these
        filtered arguments. If a PumaClickException occurs during the function call, it catches
        the exception, prints an error message, and returns None.

        :param func: The function to be called.
        :param kwargs: Arbitrary keyword arguments to pass to the function.
        :return: The result of the function call, or None if an exception occurs.
        """
    signature = inspect.signature(func)
    filtered_args = {
        k: v for k, v in kwargs.items() if k in signature.parameters
    }
    bound_args = signature.bind(**filtered_args)
    bound_args.apply_defaults()
    try:
        return func(**bound_args.arguments)
    except PumaClickException as pce:
        print(f"A problem occurred during a safe function call, recovering.. {pce}")
        return None


class StateGraph(metaclass=StateGraphMeta):
    """
       A class representing a state graph for managing UI states and transitions in an application.

       This class uses a state machine approach to manage transitions between different states
       of a user interface. It initializes with a device and application package, and provides
       methods to navigate between states, validate states, and handle unexpected states or errors.

   """
    def __init__(self, device_udid: str, app_package: str):
        """
        Initializes the StateGraph with a device and application package.

        :param device_udid: The unique device identifier.
        :param app_package: The package name of the application.
        """

        self.current_state = self.initial_state
        self.driver = PumaDriver(device_udid, app_package)
        self.app_popups = []
        self.try_restart = True

    def go_to_state(self, to_state: State | str, **kwargs) -> bool:
        """
        Navigates to a specified state from the current state.

        :param to_state: The destination state or destination state name.
        :param kwargs: Additional keyword arguments to pass to state validation and transition functions.
        :return: True if the transition to the desired state is successful.
        """
        counter = 0
        if to_state not in self.states:
            raise ValueError(f"{to_state.name} is not a known state in this PumaUiGraph")
        kwargs['driver'] = self.driver
        try:
            self._validate_state(self.current_state, **kwargs)
        except PumaClickException as pce:
            print(f"Initial state validation encountered a problem {pce}")
        while self.current_state != to_state and counter < len(self.states) * 2 + 5:
            counter += 1
            try:
                transition = self._find_shortest_path(to_state)[0]
                _safe_func_call(transition.ui_actions, **kwargs)
                self._validate_state(transition.to_state, **kwargs)
            except PumaClickException as pce:
                print(f"Transition or state validation failed, recover? {pce}")
        if counter >= len(self.states) * 2 + 5:
            raise ValueError(f"Too many transitions, unrecoverable")
        return True

    def _validate_state(self, expected_state: State, **kwargs):
        """
        Validates the current state against an expected state.

        This method checks if the current state matches the expected state and handles
        any discrepancies by attempting to recover the expected state or context.

        :param expected_state: The state that is expected to be the current state.
        :param kwargs: Additional keyword arguments for context validation.
        """
        # validate
        valid = expected_state.validate(self.driver)
        context_valid = True
        if isinstance(expected_state, ContextualState):
            context_valid = _safe_func_call(expected_state.validate_context, **kwargs)

        # handle validation results
        if not valid:
             # state is totally unexpected
            self._recover_state(expected_state)
            self._validate_state(self.current_state, **kwargs)
        elif not context_valid:
            # correct state, but wrong context (eg we want a conversation with Alice, but we're in a conversation with Bob)
            # recovery: always go back to the parent state
            self.go_to_state(expected_state.parent_state)
        else:
            self.current_state = expected_state

    def _recover_state(self, expected_state): #TODO extract methods? #TODO make non-private
        """
        Attempts to recover the expected state if the current state is not the expected state.

        This method ensures the application is active, handles popups, and attempts to
        identify and recover the current state if it does not match the expected state.

        :param expected_state: The state that is expected to be the current state.
        """
        # Ensure app active
        if not self.driver.app_open():
            self.driver.activate_app()

        if self.current_state.validate(self.driver):
            return

        # popups
        clicked = True
        while clicked:
            clicked = False
            for popup_handler in known_popups + self.app_popups:
                if popup_handler.is_popup_window(self.driver):
                    popup_handler.dismiss_popup(self.driver)
                    clicked = True

        if self.current_state.validate(self.driver):
            return

        # Search state
        current_states = [s for s in self.states if s.validate(self.driver)]
        if len(current_states) != 1:
            if not self.try_restart:
                if len(current_states) > 1:
                    raise ValueError("More than one state matches the current UI. Write stricter XPATHs")
                else:
                    raise ValueError("Unknown state, cannot recover.")
            print(f'Not in a known state. Restarting app {self.driver.app_package} once')
            self.driver.restart_app()
            sleep(3)
            self.try_restart = False
            return
        print(f'Was in unknown state, expected {expected_state}. Recovered: now in state {current_states[0]}') # TODO improve this logging. make clear that the recovery entails just knowing in which state it is
        self.current_state = current_states[0]

    def add_popup_handler(self, popup_handler: PopUpHandler):
        """
        Adds a popup handler to manage application popups.

        :param popup_handler: The popup handler to be added.
        """
        self.app_popups.append(popup_handler)

    def _find_shortest_path(self, destination: State | str) -> list[Transition] | None:
        """
        Finds the shortest path in terms of transitions to the desired state.

        :param destination: The destination state or state name.
        :return: A list of transitions representing the shortest path to the destination state, or None if no path is found.
        """
        return _shortest_path(self.current_state, destination)

    def draw_graph(self):
        G = nx.DiGraph()
        nodes = [s.name for s in self.states]
        edges = [(s.name, t.to_state.name) for s in self.states for t in s.transitions]
        edge_labels = {(s.name, t.to_state.name): t.ui_actions.__name__ for s in self.states for t in s.transitions}
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)

        pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=2000)
        nx.draw_networkx_labels(G, pos, font_size=15)
        # Draw curved edges
        for (u, v) in edges:
            rad = 0.2 if (v, u) in G.edges else 0.0  # Curve only if there's a reverse edge
            nx.draw_networkx_edges(
                G, pos,
                edgelist=[(u, v)],
                connectionstyle=f'arc3,rad={rad}',
                edge_color='gray',
                arrows=True
            )
        label_pos = {}
        # for (u, v), label in edge_labels.items():
        #     rad = 0.2 if (v, u) in G.edges else 0.0
        #     label_pos[(u, v)] = self.curved_edge_label_pos(pos, u, v, rad=rad)

        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')
        plt.title("Graph")
        plt.show()

    # Function to offset edge label positions
    def curved_edge_label_pos(pos, u, v, rad=0.2):
        # Midpoint of the edge
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        xm, ym = (x1 + x2) / 2, (y1 + y2) / 2

        # Compute direction perpendicular to the edge
        dx = x2 - x1
        dy = y2 - y1
        d = np.hypot(dx, dy)
        if d == 0:
            return (xm, ym)

        # Normalize perpendicular vector
        perp_dx = -dy / d
        perp_dy = dx / d

        # Offset midpoint in the perpendicular direction
        offset = rad * 0.5  # adjust factor to control label distance
        return (xm + offset * perp_dx, ym + offset * perp_dy)

def action(to_state: State):
    """
    Decorator to wrap a function with logic to ensure a specific state before execution.

    This decorator ensures that the application is in the specified state before executing
    the wrapped function. It is useful for performing actions within an app, such as sending
    a message, while ensuring the correct state. If a PumaClickException occurs during the
    execution of the function, it attempts to recover the state and retry the function execution.

    :param to_state: The target state to ensure before executing the decorated function.
    :return: A decorator function that wraps the provided function with state assurance logic.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            """
            Wrapper function that ensures the correct state and handles exception recovery.

            :param args: Positional arguments to pass to the decorated function.
            :param kwargs: Keyword arguments to pass to the decorated function.
            :return: The result of the decorated function.
            """
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = bound_args.arguments
            arguments.pop('self')
            puma_ui_graph = args[0]
            puma_ui_graph.go_to_state(to_state, **arguments)

            try:
                result = func(*args, **kwargs)
            except PumaClickException as pce:
                puma_ui_graph._recover_state(to_state) # Dangerous call, but if it fails, do we want to continue?
                puma_ui_graph.go_to_state(to_state, **arguments)
                result = func(*args, **kwargs)
            puma_ui_graph.try_restart = True
            return result

        return wrapper

    return decorator
