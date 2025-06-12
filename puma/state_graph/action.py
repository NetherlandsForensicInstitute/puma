import inspect

from puma.state_graph import logger
from puma.state_graph.puma_driver import PumaClickException
from puma.state_graph.state import State


def action(to_state: State):
    """
    Decorator to wrap a function with logic to ensure a specific state before execution.

    This decorator ensures that the application is in the specified state before executing
    the wrapped function. It is useful for performing actions within an app, such as sending
    a message, while ensuring the correct state. If a PumaClickException occurs during the
    execution of the function, it attempts to recover the state and retry the function execution.

    :param to_state: The target state to ensure before executing the decorated function.
    :return: A decorator function that wraps the provided function with state assurance logic.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            """
            Wrapper function that ensures the correct state and handles exception recovery.

            :param args: Positional arguments to pass to the decorated function.
            :param kwargs: Keyword arguments to pass to the decorated function.
            :return: The result of the decorated function.
            """
            bound_args = inspect.signature(func).bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = bound_args.arguments
            arguments.pop('self')
            puma_ui_graph = args[0]
            puma_ui_graph.go_to_state(to_state, **arguments)

            try:
                logger.info(f"[{puma_ui_graph.driver.options.udid}] Executing action {func.__name__} with arguments: {args} and key word arguments: {kwargs} for application: {puma_ui_graph.__class__.__name__}")
                result = func(*args, **kwargs)
            except PumaClickException as pce:
                puma_ui_graph._recover_state(to_state) # Dangerous call, but if it fails, do we want to continue?
                puma_ui_graph.go_to_state(to_state, **arguments)
                result = func(*args, **kwargs)
            puma_ui_graph.try_restart = True
            return result

        return wrapper

    return decorator
