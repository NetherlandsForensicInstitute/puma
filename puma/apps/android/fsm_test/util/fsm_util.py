from collections import deque

from statemachine import StateMachine, State
from statemachine.transition import Transition

from puma.apps.android.fsm_test.fsm.puma_fsm import PumaState


def action(first_state: PumaState):
    """
    Decorator with parameters, enables the user to execute actions without the need to switch states manually.
    """
    def decorator(func):
        def wrapper(*args):
            while args[0].current_state != first_state:
                shortest_path = find_shortest_path(args[0], first_state)
                print(f'Taking the next step with event {shortest_path[0].event}')
                args[0].send(f"{shortest_path[0].event}", message="hello message")
            result = func(*args)
            print('should have executed the action by now')
            return result
        return wrapper
    return decorator

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
        # if this is a path to the desirted state, return the path
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
