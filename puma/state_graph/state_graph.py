from time import sleep
from typing import List

from puma.state_graph import logger
from puma.state_graph.popup_handler import known_popups, PopUpHandler
from puma.state_graph.puma_driver import PumaDriver, PumaClickException

from puma.state_graph.utils import _safe_func_call
from puma.state_graph.state import State, ContextualState, Transition, _shortest_path


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
                value.id = key
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
        # there can only be one initial state
        StateGraphMeta._validate_only_one_initial_state(states)
        # initial state cannot be Contextual state
        StateGraphMeta._validate_initial_state(states)
        # you need to be able to go from  the initial state to each other state and back
        StateGraphMeta._validate_every_state_reachable(states)
        # Contextual states need parent state
        StateGraphMeta._validate_contextual_states(states)
        # No duplicate ids for states
        StateGraphMeta._validate_no_duplicate_ids(states)
        # No duplicate transitions: max one transition between each 2 states
        StateGraphMeta._validate_no_duplicate_transitions(states)

    @staticmethod
    def _validate_only_one_initial_state(states):
        initial_states = [s for s in states if s.initial_state]
        if len(initial_states) == 0:
            raise ValueError(f'Graph needs an initial state')
        elif len(initial_states) > 1:
            raise ValueError(f'Graph can only have 1 initial state, currently more defined: {initial_states}')
        initial_state = initial_states[0]
        return initial_state

    @staticmethod
    def _validate_initial_state(states):
        initial_state = next(s for s in states if s.initial_state)
        if isinstance(initial_state, ContextualState):
            raise ValueError(f'Initial state ({initial_state}) Cannot be an Contextual state')

    @staticmethod
    def _validate_every_state_reachable(states):
        initial_state = next(s for s in states if s.initial_state)
        unreachable_states = [s for s in states if not s.initial_state and not (
                    bool(_shortest_path(initial_state, s)) and bool(_shortest_path(s, initial_state)))]
        if unreachable_states:
            raise ValueError(
                f'Some states cannot be reached from the initial state, or cannot go back to the initial state: {unreachable_states}')

    @staticmethod
    def _validate_contextual_states(states):
        contextual_state_without_parent = [s for s in states if
                                           isinstance(s, ContextualState) and s.parent_state is None]
        if contextual_state_without_parent:
            raise ValueError(f'Contextual states without parent are not allowed: {contextual_state_without_parent}')

    @staticmethod
    def _validate_no_duplicate_ids(states):
        seen = set()
        duplicate_ids = {s.id for s in states if s.id in seen or seen.add(s.id)}
        if duplicate_ids:
            raise ValueError(f"States must have a unique id. Multiple sates have the id {duplicate_ids}")

    @staticmethod
    def _validate_no_duplicate_transitions(states):
        for s in states:
            seen = set()
            duplicates = {t.to_state for t in s.transitions if t.to_state in seen or seen.add(t.to_state)}
            if duplicates:
                raise ValueError(
                    f"State {s} has invalid transitions: multiple transitions defined to neighboring state(s) {duplicates}")


class StateGraph(metaclass=StateGraphMeta):
    """
       A class representing a state graph for managing UI states and transitions in an application.

       This class uses a state machine approach to manage transitions between different states
       of a user interface. It initializes with a device and application package, and provides
       methods to navigate between states, validate states, and handle unexpected states or errors.

   """
    def __init__(self, device_udid: str, app_package: str, appium_server: str = 'http://localhost:4723'):
        """
        Initializes the StateGraph with a device and application package.

        :param device_udid: The unique device identifier.
        :param app_package: The package name of the application.
        """

        self.current_state = self.initial_state
        self.driver = PumaDriver(device_udid, app_package, appium_server=appium_server)
        self.app_popups = []
        self.try_restart = True

    def go_to_state(self, to_state: State | str, **kwargs) -> bool:
        """
        Navigates to a specified state from the current state.

        :param to_state: The destination state or destination state name.
        :param kwargs: Additional keyword arguments to pass to state validation and transition functions.
        :return: True if the transition to the desired state is successful.
        """
        max_transitions = len(self.states) * 2 + 5
        counter = 0
        if to_state not in self.states:
            raise ValueError(f"{to_state.id} is not a known state in this PumaUiGraph")
        kwargs['driver'] = self.driver
        try:
            self._validate_state(self.current_state, **kwargs)
        except PumaClickException as pce:
            logger.warn(f"Initial state validation encountered a problem {pce}")
        while self.current_state != to_state and counter < max_transitions:
            counter += 1
            try:
                transition = self._find_shortest_path(to_state)[0]
                _safe_func_call(transition.ui_actions, **kwargs)
                self._validate_state(transition.to_state, **kwargs)
            except PumaClickException as pce:
                logger.warn(f"Transition or state validation failed, recover? {pce}")
        if counter >= max_transitions:
            logger.error(f"Too many transitions, state is unrecoverable")
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
            self.recover_state(expected_state)
            self._validate_state(self.current_state, **kwargs)
        elif not context_valid:
            # correct state, but wrong context (eg we want a conversation with Alice, but we're in a conversation with Bob)
            # recovery: always go back to the parent state
            self.go_to_state(expected_state.parent_state)
        else:
            self.current_state = expected_state

    def recover_state(self, expected_state):
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
        self._handle_popups()

        if self.current_state.validate(self.driver):
            return

        # Search state
        self._search_state(expected_state)

    def _handle_popups(self):
        clicked = True
        while clicked:
            clicked = False
            for popup_handler in known_popups + self.app_popups:
                if popup_handler.is_popup_window(self.driver):
                    popup_handler.dismiss_popup(self.driver)
                    clicked = True

    def _search_state(self, expected_state: State):
        current_states = [s for s in self.states if s.validate(self.driver)]
        if len(current_states) != 1:
            if not self.try_restart:
                if len(current_states) > 1:
                    raise ValueError("More than one state matches the current UI. Write stricter XPATHs")
                else:
                    raise ValueError("Unknown state, cannot recover.")
            logger.warn(f'Not in a known state. Restarting app {self.driver.app_package} once')
            self.driver.restart_app()
            sleep(3)
            self.try_restart = False
            return
        logger.info(
            f'Was in unknown state, expected {expected_state}. Recognized state, setting current state to: {current_states[0]}')
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
