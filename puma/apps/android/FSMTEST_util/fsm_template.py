from puma.apps.android.FSMTEST_util.puma_driver import PumaDriver
from puma.apps.android.FSMTEST_util.puma_fsm import StateGraph, SimpleState, action, click

APPLICATION_PACKAGE = "INSERT YOUR PACKAGE HERE"

# define here custom methods to navigate to a certain state

class TemplateApp(StateGraph):

    # Define states
    state1 = SimpleState("State 1",
                         xpaths=["xpath1", "xpath2"],
                         initial_state=True)
    state2 = SimpleState("State 2",
                         xpaths=["xpath1"],
                         parent_state=state1)

    # Define transitions. Only forward transitions are needed, back transitions are added automatically
    state1.to(state2, click(['xpath1', 'xpath2']))

    # init
    def __init__(self, device_udid):
        StateGraph.__init__(self, self.driver)
        self.driver = PumaDriver(device_udid, APPLICATION_PACKAGE)

    # Define your actions
    @action(state1)
    def action_1(self):
        ...


if __name__ == "__main__":
    app = TemplateApp(device_udid="INSERT YOUR DEVICE ID HERE")
    app.action_1()




