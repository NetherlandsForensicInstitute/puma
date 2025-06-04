from typing import Callable, Any

from statemachine import State
from statemachine.transition_list import TransitionList


class PumaState(State):
    def __init__(self, name: str = "",
                 xpath: Callable[[Any], bool] = None,
                 initial: bool = False,
                 final: bool = False,
                 parent: Callable[['PumaState'], TransitionList] = None):
        """
        Class that extends the statemachine state for Puma specific support.
        """
        super().__init__(name=name, initial=initial, final=final)
        self._xpath = xpath
        if parent:
           parent(self)

    def _recognize(self):
        self._say_hello()
        if self._xpath:
            print(f'checking whether xpath expression is valid: {self._xpath}')
        else:
            print('No given xpath expression, no check will happen')

    def _say_hello(self):
        print(f'hello from state {self.name or self.id}')