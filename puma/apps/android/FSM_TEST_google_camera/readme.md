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
- Easy to create transitions and states, possible with either calling `add_transition` for each transition or supplying a dict with all transitions.
- Has some other fancy features (Triggering a transition, Automatic transitions, Transitioning from multiple states, Reflexive transitions from multiple states, Internal transitions, Ordered transitions, Queued transitions, Conditional transitions, Check transitions, Callbacks
)
- Automatic transitions are possible, by calling `to_«state»()`
Problems:

- The states are not compile safe, and a bit magic

- 
### AutomataLib
https://github.com/caleb531/automata
https://pypi.org/project/automata-lib/