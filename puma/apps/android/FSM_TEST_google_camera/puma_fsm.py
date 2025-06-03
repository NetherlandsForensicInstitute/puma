from typing import Callable

from statemachine import State
from statemachine.transition_list import TransitionList


class PumaState(State):
    def __init__(self, name: str = "",
                 xpath: Callable[[str], bool] = None,
                 initial: bool = False,
                 final: bool = False,
                 parent: Callable[['PumaState'], TransitionList] = None):
        super().__init__(name=name, initial=initial, final=final, enter=lambda : self._recognize())
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