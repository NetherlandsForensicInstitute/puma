import inspect
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from time import sleep
from typing import Callable, Any, List

from puma.apps.android.FSMTEST_util.puma_driver import PumaDriver, PumaClickException


@dataclass
class PopUpHandler:
    recognize_xpath: str
    click: str

    def recognize(self, driver: PumaDriver) -> bool:
        return driver.is_present(self.recognize_xpath)

    def dismiss_popup(self, driver: PumaDriver):
        driver.click(self.click)


def simple_popup_handler(xpath: str):
    return PopUpHandler(xpath, xpath)


known_popups = [simple_popup_handler('//android.widget.ImageView[@content-desc="Dismiss update dialog"]'),
                simple_popup_handler(
                    '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"]'),
                simple_popup_handler(
                    '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]')]


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
    def validate(self, driver: PumaDriver) -> bool:
        pass

    def __repr__(self):
        return f'[{self.name}]'

class FState(State):  # TODO: find decent name for this type of state. DynamicState? ParameterizedState? ContextualState?
    @abstractmethod
    def variable_validate(self, driver: PumaDriver) -> bool:  # TODO: find decent name for this method. validate_with_context? and should we add **kwargs as argument?
        pass


class SimpleState(State):
    def __init__(self, name: str, xpaths: List[str], initial_state: bool = False, parent_state: 'State' = None, ):
        """
        TODO
        :param name:
        :param xpaths:
        :param initial_state:
        :param parent_state:
        """
        super().__init__(name, parent_state=parent_state, initial_state=initial_state)
        self.xpaths = xpaths

    def validate(self, driver: PumaDriver) -> bool:
        return all(driver.is_present(xpath) for xpath in self.xpaths)


@dataclass
class Transition:
    from_state: State
    to_state: State
    ui_actions: Callable[[Any], None]  # TODO: typing

def _shortest_path(start: State, destination: State | str):
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

def click(xpaths: List[str]) -> Callable[[PumaDriver], None]:
    """
    Helper method to create lambdas to construct tranistions
    :param xpaths: XPaths of elements to click
    :return: lambda to be used as a transition action
    """
    def  _click_(driver):
        for xpath in xpaths:
            driver.click(xpath)
    return _click_


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
        new_class.initial_state = next(s for s in states if s.initial_state)

        ## validation
        PumaUIGraphMeta._validate_graph(states)

        return new_class

    @staticmethod
    def _validate_graph(states: List[State]):  # TODO: make unit test for this validation
        # only 1 initial state
        initial_states = [s for s in states if s.initial_state]
        if len(initial_states) == 0:
            raise ValueError(f'Graph needs an initial state')
        elif len(initial_states) > 1:
            raise ValueError(f'Graph can only have 1 initial state, currently more defined: {initial_states}')
        initial_state = initial_states[0]

        # initial state cannot be FState
        if isinstance(initial_state, FState):
            raise ValueError(f'Initial state ({initial_state}) Cannot be an FState')

        # FStates need parent state
        fstate_without_parent = [s for s in states if isinstance(s, FState) and s.parent_state is None]
        if fstate_without_parent:
            raise ValueError(f'FStates without parent are not allowed: {fstate_without_parent}')

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
    sig = inspect.signature(func)
    filtered_args = {
        k: v for k, v in kwargs.items() if k in sig.parameters
    }
    bound_args = sig.bind(**filtered_args)
    bound_args.apply_defaults()
    try:
        return func(**bound_args.arguments)
    except PumaClickException as pce:
        print(f"A problem occurred during a safe function call, recovering.. {pce}")
        return None


class PumaUIGraph(metaclass=PumaUIGraphMeta):  # TODO: rename. PumaAppModel, PumaStateMachine? UiModel? Just PumaActions like before?
    def __init__(self, device_udid: str, app_package: str):
        self.current_state = self.initial_state
        self.driver = PumaDriver(device_udid, app_package)
        self.app_popups = []
        self.try_restart = True

    def go_to_state(self, to_state: State | str, **kwargs) -> bool:
        counter = 0
        if to_state not in self.states:
            raise ValueError(f"{to_state.name} is not a known state in this PumaUiGraph")
        kwargs['driver'] = self.driver
        try:
            self._sanity_check(self.current_state, **kwargs)
        except PumaClickException as pce:
            print(f"Initial sanity check encountered a problem {pce}")
        while self.current_state != to_state and counter < len(self.states) * 2 + 5:
            counter += 1
            try:
                transition = self._find_shortest_path(to_state)[0]
                _safe_func_call(transition.ui_actions, **kwargs)
                self._sanity_check(transition.to_state, **kwargs)
            except PumaClickException as pce:
                print(f"Transition or sanity check failed, recover? {pce}")
        if counter >= len(self.states) * 2 + 5:
            raise ValueError(f"Too many transitions, unrecoverable")
        return True

    def _sanity_check(self, expected_state: State, **kwargs):
        # validate
        valid = expected_state.validate(self.driver)
        var_valid = True
        if isinstance(expected_state, FState):
            var_valid = _safe_func_call(expected_state.variable_validate, **kwargs)

        # handle validation results
        if not valid:
             # state is totally unexpected
            self._recover_state(expected_state)
            self._sanity_check(self.current_state, **kwargs)
        elif not var_valid:
            # correct state, but wrong variant (eg we want a conversation with Alice, but we're in a conversation with Bob)
            # recovery: always go back to the parent state
            self.go_to_state(expected_state.parent_state)
        else:
            self.current_state = expected_state

    def _recover_state(self, expected_state):
        # Ensure app active
        if not self.driver.app_open():
            self.driver.activate_app()

        if self.current_state.validate(self.driver):
            return

        # Pop-ups
        clicked = True
        while clicked:
            clicked = False
            for popup_handler in known_popups + self.app_popups:
                if popup_handler.recognize(self.driver):
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
        self.app_popups.append(popup_handler)

    def _find_shortest_path(self, destination: State | str) -> list[Transition] | None:
        """
        Gets the shortest path (in number of transitions) to the desired state.
        """
        return _shortest_path(self.current_state, destination)


def action(to_state: State):
    def decorator(func):
        def wrapper(*args, **kwargs):
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = bound_args.arguments
            arguments.pop('self')
            puma_ui_graph = args[0]
            puma_ui_graph.go_to_state(to_state, **arguments)

            sig2 = inspect.signature(func)
            filtered_args = {
                k: v for k, v in arguments.items() if k in sig2.parameters
            }

            filtered_args['self'] = puma_ui_graph
            bound_args2 = sig2.bind(**filtered_args)
            bound_args2.apply_defaults()
            try:
                result = func(**bound_args2.arguments)
            except PumaClickException as pce:
                puma_ui_graph._recover_state(to_state) # Dangerous call, but if it fails, do we want to continue?
                puma_ui_graph.go_to_state(to_state, **arguments)
                result = func(**bound_args2.arguments)
            puma_ui_graph.try_restart = True
            return result

        return wrapper

    return decorator


class TestFsm(PumaUIGraph):
    start_state = SimpleState("start state", [], True)
    state1 = SimpleState("state 1", [], parent_state=start_state)
    state1_1 = SimpleState("state 1.1", [], parent_state=state1)
    state2 = SimpleState("state 2", [], parent_state=start_state)

    start_state.to(state1, None)
    state1.to(state1_1, None)
    start_state.to(state2, None)


if __name__ == '__main__':
    print("testing")