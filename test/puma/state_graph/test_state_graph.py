import unittest

from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import State, ContextualState
from puma.state_graph.state_graph import StateGraphMeta


class TestState(State):

    def validate(self, driver: PumaDriver) -> bool:
        return True


class TestContextualState(ContextualState):

    def validate_context(self, driver: PumaDriver) -> bool:
        return True

    def validate(self, driver: PumaDriver) -> bool:
        return True


class TestStateGraphMeta(unittest.TestCase):
    def test_validate_graph_success(self):
        # Create a valid state graph
        state1 = TestState("State1", initial_state=True)
        state2 = TestState("State2")
        state1.to(state2, None)
        state2.to(state1, None)
        states = [state1, state2]

        # This should not raise any exceptions
        try:
            StateGraphMeta._validate_graph(states)
        except ValueError:
            self.fail("_validate_graph raised ValueError unexpectedly!")

    def test_validate_graph_no_initial_state(self):
        # Create an invalid state graph with no initial state
        state1 = TestState("State1")
        state2 = TestState("State2")
        state1.to(state2, None)
        state2.to(state1, None)
        states = [state1, state2]
        with self.assertRaises(ValueError):
            StateGraphMeta._validate_graph(states)

    def test_validate_graph_multiple_initial_states(self):
        # Create an invalid state graph with multiple initial states
        state1 = TestState("State1", initial_state=True)
        state2 = TestState("State2", initial_state=True)
        state1.to(state2, None)
        state2.to(state1, None)
        states = [state1, state2]
        with self.assertRaises(ValueError):
            StateGraphMeta._validate_graph(states)

    def test_validate_graph_initial_state_is_contextual(self):
        # Create an invalid state graph where the initial state is a ContextualState
        state1 = TestContextualState("State1", initial_state=True)
        state2 = TestState("State2")
        state1.to(state2, None)
        state2.to(state1, None)
        states = [state1, state2]
        with self.assertRaises(ValueError):
            StateGraphMeta._validate_graph(states)

    def test_validate_graph_unreachable_states(self):
        # Create an invalid state graph with unreachable states
        state1 = TestState("State1", initial_state=True)
        state2 = TestState("State2")
        state3 = TestState("State3")
        state1.to(state2, None)
        state2.to(state1, None)
        state2.to(state3, None)
        states = [state1, state2, state3]
        with self.assertRaises(ValueError):
            StateGraphMeta._validate_graph(states)

    def test_validate_graph_contextual_state_without_parent(self):
        # Create an invalid state graph with a ContextualState without a parent
        state1 = TestState("State1", initial_state=True)
        state2 = TestContextualState("State2")
        state1.to(state2, None)
        state2.to(state1, None)
        states = [state1, state2]
        with self.assertRaises(ValueError):
            StateGraphMeta._validate_graph(states)

    def test_validate_graph_duplicate_state_names(self):
        # Create an invalid state graph with duplicate state names
        state1 = TestState("State1", initial_state=True)
        state2 = TestState("State1")
        state1.to(state2, None)
        state2.to(state1, None)
        states = [state1, state2]
        with self.assertRaises(ValueError):
            StateGraphMeta._validate_graph(states)

    def test_validate_graph_duplicate_transitions(self):
        # Create an invalid state graph with duplicate transitions
        state1 = TestState("State1", initial_state=True)
        state2 = TestState("State2")
        state1.to(state2, None)
        state1.to(state2, None)
        state2.to(state1, None)
        states = [state1, state2]
        with self.assertRaises(ValueError):
            StateGraphMeta._validate_graph(states)


if __name__ == '__main__':
    unittest.main()
