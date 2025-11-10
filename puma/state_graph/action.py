import inspect
from typing import Callable

from build.lib.puma.state_graph.puma_driver import PumaClickException
from puma.state_graph.state import State
from puma.state_graph.utils import safe_func_call, filter_arguments


def _assert_verify_with_function_is_valid(verify_with):
    """
    Validate that the 'verify_with' passed to the action is valid, else throw an error.

    :param verify_with: the object passed as 'verify_with'
    :raises TypeError: if the verification function is not a callable
    """
    if not isinstance(verify_with, Callable):
        raise TypeError(f"'verify_with' must be a callable, instead is: {type(verify_with)}")

    # TODO: enforce signature, e.g. must be func(driver, gtl_logger) and optional extra args?


def _execute_post_action_verification(puma_ui_graph, verify_with, arguments, gtl_logger):
    """
    Run the given post action verification function and log the results. Returns to the current state
    of the graph at the end of the verification execution.

    :param puma_ui_graph: the application state graph, in the state after the execution of the action
    :param verify_with: the post action verification function
    :param arguments: the bound arguments of the action which will be passed to the verification
    :param gtl_logger: logger to log the results to
    """
    # store current state, so we can return to it at the end
    state_before_verify_with = puma_ui_graph.current_state

    # run the post action if present, catching any domain exceptions,
    # since these should not interrupt the rest of the actions
    bound_args = filter_arguments(verify_with, driver=puma_ui_graph.driver, gtl_logger=gtl_logger, **arguments)
    try:
        success = verify_with(**bound_args.arguments)
    except PumaClickException as e:
        gtl_logger.warn(f'Verifying with "{verify_with.__name__}" failed due to exception: {str(e)}')
    else:
        # enforce type here, since we have no typed API call to enforce it with
        if not isinstance(success, bool):
            raise ValueError(f"result of 'verify_with' should be a bool, instead is: {type(success)}, with value: {success}")

        gtl_logger.info(f"Action {'succeeded' if success else 'failed'}")

    # always return to our original state, even if verification failed
    puma_ui_graph.go_to_state(state_before_verify_with, **arguments)


def action(state: State, end_state: State = None):
    """
    Decorator to wrap a function with logic to ensure a specific state before execution.

    This decorator ensures that the application is in the specified state before executing
    the wrapped function. It is useful for performing actions within an app, such as sending
    a message, while ensuring the correct state. If a PumaClickException occurs during the
    execution of the function, it attempts to recover the state and retry the function execution.

    An action can be verified by passing a function as a named argument with name 'verify_with'
    to the function which is decorated. If the 'verify_with' function has a parameter named 'driver',
    the active PumaDriver will be injected. Similarly, if it has a parameter named 'gtl_logger',
    the active ground truth logger will be injected. This function will be called at the end of the action's execution.
    Inside the verification function you can change to other states,
    the framework will ensure it returns to the state it was at the end of the action. The return value of
    the 'verify_with' function must be a bool signaling if the action was executed correctly. This will be logged
    by the framework.

    :param state: The target state to ensure before executing the decorated function.
    :param end_state: Defines if this action ends in a different state (Optional)
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
            verify_with = None
            if 'verify_with' in kwargs.keys():
                verify_with = kwargs.pop('verify_with')
                _assert_verify_with_function_is_valid(verify_with)

            # check that our decorated function has no parameter verify_with, else it would be passed automatically
            action_signature = inspect.signature(func)
            if 'verify_with' in action_signature.parameters:
                raise ValueError("an action (decorated) function can't contain a parameter named 'verify_with'")

            bound_args = action_signature.bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = bound_args.arguments
            arguments.pop('self')
            puma_ui_graph = args[0]
            # get the ground truth logger to log these actions
            gtl_logger = puma_ui_graph.gtl_logger
            try:
                puma_ui_graph.try_restart = True
                puma_ui_graph.go_to_state(state, **arguments)
                try:
                    gtl_logger.info(
                        f"Executing action {func.__name__} with arguments: {args[1:]} and keyword arguments: {kwargs} for application: {puma_ui_graph.__class__.__name__}")
                    result = func(*args, **kwargs)
                except:
                    gtl_logger.info(f"Failed to execute action {func.__name__}.")
                    puma_ui_graph.recover_state(state)
                    puma_ui_graph.go_to_state(state, **arguments)
                    gtl_logger.info(f'Retrying action {func.__name__}')
                    result = func(*args, **kwargs)

                if verify_with is not None:
                    gtl_logger.info(f"Verifying action with {verify_with.__name__} using arguments: {args[1:]} and keyword arguments: {kwargs} for application: {puma_ui_graph.__class__.__name__}")
                    _execute_post_action_verification(puma_ui_graph, verify_with, arguments, gtl_logger)

                puma_ui_graph.try_restart = True
                gtl_logger.info(
                    f"Successfully executed action {func.__name__} with arguments: {args[1:]} and keyword arguments: {kwargs} for application: {puma_ui_graph.__class__.__name__}")
                if end_state:
                    puma_ui_graph.current_state = end_state
                return result
            except Exception as e:
                gtl_logger.error("Unexpected exception", e)
                raise e


        return wrapper

    return decorator
