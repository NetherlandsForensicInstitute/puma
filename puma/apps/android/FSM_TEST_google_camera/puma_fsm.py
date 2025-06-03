from statemachine import State


class PumaState(State):
    def __init__(self, name: str = "",
                 xpath:str = None,  # TODO: make this a callable
                 initial: bool = False,
                 final: bool = False,
                 parent: 'PumaState' = None): # TODO: somehow automatically create a 'back' transition to this state. Could be in this class, or in the machine class, don't know what is possible
        super().__init__(name=name, initial=initial, final=final, enter=lambda : self._recognize())
        self._xpath = xpath
        if parent:
            self.back = self.to(parent) # TODO: see previous TODO: this doesn't work: the transition doesnt get an event name, andthere is no back() function on the FSM

    def _recognize(self):
        self._say_hello()
        if self._xpath:
            print(f'checking whether xpath expression is valid: {self._xpath}')
        else:
            print('No given xpath expression, no check will happen')

    def _say_hello(self):
        print(f'hello from state {self.name or self.id}')