import importlib
import inspect
import pkgutil
import unittest

import puma.apps
from puma.state_graph.state_graph import StateGraph


def state_graph_apps() -> list[type]:
    """Every StateGraph application under puma.apps."""
    apps = []
    for module_info in pkgutil.walk_packages(puma.apps.__path__, puma.apps.__name__ + '.'):
        module = importlib.import_module(module_info.name)
        for _, value in inspect.getmembers(module, inspect.isclass):
            if issubclass(value, StateGraph) and value is not StateGraph and value.__module__ == module.__name__:
                apps.append(value)
    return apps


class TestAppKwargs(unittest.TestCase):
    def test_every_app_accepts_appium_options(self):
        """
        Every application passes optional arguments such as desired_capabilities and appium_server on to the
        StateGraph, so they can be set for any application.
        """
        apps = state_graph_apps()
        self.assertTrue(apps)
        for app in apps:
            with self.subTest(app=app.__name__):
                parameters = inspect.signature(app.__init__).parameters
                accepts_kwargs = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters.values())
                self.assertTrue(accepts_kwargs or 'desired_capabilities' in parameters,
                                f'{app.__name__}.__init__ does not accept desired_capabilities; add **kwargs and pass '
                                f'them to StateGraph.__init__')


if __name__ == '__main__':
    unittest.main()
