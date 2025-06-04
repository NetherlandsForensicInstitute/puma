import datetime
import logging
from collections import deque
from time import sleep
from typing import Callable, Any

from appium.webdriver.common.appiumby import AppiumBy
from statemachine import StateMachine, State
from statemachine.transition import Transition

from puma.apps.android.fsm_test.fsm.puma_fsm import PumaState


def action(first_state: PumaState, validate_call: Callable[[Any], None] = None):
    """
    Decorator with parameters, enables the user to execute actions without the need to switch states manually.
    """
    def decorator(func):
        def wrapper(*args):
            if args[0].current_state == first_state and validate_call:
                validate_result = validate_call(*args)
                if not validate_result:
                    args[0].driver.back()
                    sleep(1) #TODO: FIX THIS
                    args[0].back()
            while args[0].current_state != first_state:
                shortest_path = find_shortest_path(args[0], first_state)
                print(f'Taking the next step with event {shortest_path[0].event}')
                args[0].send(f"{shortest_path[0].event}", *args)
            logging.log(20, f"Executing action {str(func)} at {datetime.datetime.now()}") #TODO: Replace with correct logging?
            result = func(*args)
            print('should have executed the action by now')
            return result
        return wrapper
    return decorator

def validation(func):
    def wrapper(*args):
        valid = func(*args)
        while not valid:
            print("not valid")
            in_permission = args[0].appium_actions.is_present('//android.widget.Button[@package="com.google.android.permissioncontroller"]')
            if in_permission:
                xpath = '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_foreground_only_button"]' # TODO: Create 'or' for this
                xpath2 = '//android.widget.Button[@resource-id="com.android.permissioncontroller:id/permission_allow_button"]'
                print("Clicking permission")
                if args[0].appium_actions.is_present(xpath):
                    button = args[0].driver.find_element(by=AppiumBy.XPATH, value=xpath)
                    button.click()
                elif args[0].appium_actions.is_present(xpath2):
                    button = args[0].driver.find_element(by=AppiumBy.XPATH, value=xpath2)
                    button.click()
            else:
                print("hello") #TODO: implement search
            valid = func(*args)
        print("valid")
        return valid
    return wrapper
#
def transition(func):
    def wrapper(*args, **kwargs):
        print("entering transition")
        result = func(*args, **kwargs)
        return result
    return wrapper

def make_back_action(back, state):
    """
    Adds the transition to the provided TransitionList from the current state to the provided state.
    """
    return lambda self: back.add_transitions(self.to(state))

def find_shortest_path(machine: StateMachine, destination: State | str) -> list[Transition] | None:
    """
    Gets the shortest path (in number of transitions) to the desired state.
    """
    start = machine.current_state
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
            queue.append((transition.target, path + [transition]))
    return None
