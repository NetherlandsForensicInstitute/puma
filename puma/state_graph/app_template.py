from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver
from puma.state_graph.state import SimpleState, compose_clicks
from puma.state_graph.state_graph import StateGraph

APPLICATION_PACKAGE = "INSERT YOUR PACKAGE HERE"


# define here custom methods to navigate to a certain state

class TemplateApp(StateGraph):
    # Define states
    state1 = SimpleState(xpaths=["xpath1", "xpath2"],
                         initial_state=True)
    state2 = SimpleState(xpaths=["xpath1"],
                         parent_state=state1)

    # Define transitions. Only forward transitions are needed, back transitions are added automatically
    state1.to(state2, compose_clicks(['xpath1', 'xpath2']))

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
