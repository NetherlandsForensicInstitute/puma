# Modeling apps as FSM in Puma

Idea: Model the app as an FSM with set numebr of states.
When in an unknown state: try to handle known unpredictable things like popups, if that doesn't work try to restart the
app, and then Puma can navigate the known states at will. This removes the need for ifs and try loops throughout other
Puma code

## Brainstrom results

We've looked into FSM frameworks that exist in PyPi.

### Python State Machine
https://pypi.org/project/python-statemachine/
https://python-statemachine.readthedocs.io/en/latest/index.html
Seems to be the biggest one, quite easy to create an states and transitions.
(Possible) problems:

- it doesn't seem possible to call `setState()` directly, so when our real phone acts unpredicable and Puma recovers
back to a known, state, we can't directly sync the FSM with the real phone.
- Finding the shortest path between 2 states is not built in, we would need to add path finding ourselves

### PyTransitions
https://github.com/pytransitions/transitions

### AutomataLib
https://github.com/caleb531/automata
https://pypi.org/project/automata-lib/