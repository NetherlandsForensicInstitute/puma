# Modeling apps as FSM in Puma

Idea: Model the app as an FSM with set numebr of states.
When in an unknown state: try to handle known unpredictable things like popups, if that doesn't work try to restart the
app, and then Puma can navigate the known states at will. This removes the need for ifs and try loops throughout other
Puma code

## Brainstrom results

We would like the code to work like before: create AppAction instances, on which you can then call actions like
`send_message`. The difference would be that these methods now start with a navigation step that is done by the Puma
framework. Essentially it's a bit like the `_if_chat_go_to_chat()` helper method we already built for some chat apps,
but more generic: at the start of a defined action, you define from what state it should be called, after which
Appium commands can then be executed.

The goal is to make this navigation itself as robust as possible, leveraging FSMs. We've looked into FSM frameworks
that exist in PyPi:

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

We noted that all FSMs have an incompatibility with how Appium behaves: they work! they do not anticipate unexpected
states and crashes. This means we cannot actually model our code with an FSM. But we could still use the FSM to guide
the process: the AppActions object could contain an FSM which basically models the state of the app, telling us "This is
the state I expect the app to be in right now", and "this is how you go to other states from here".

this would result in some sort of two-tiered approach: our Actions object has the FSM describing what it expects, and
it has the real situation on the device. These two need to be kept in sync, which Puma will do.