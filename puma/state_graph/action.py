import inspect
from typing import Callable

from puma.state_graph.state import State
from puma.state_graph.utils import safe_func_call

def action(state: State, end_state: State = None):
    """
    Decorator to wrap a function with logic to ensure a specific state before execution.

    This decorator ensures that the application is in the specified state before executing
    the wrapped function. It is useful for performing actions within an app, such as sending
    a message, while ensuring the correct state. If a PumaClickException occurs during the
    execution of the function, it attempts to recover the state and retry the function execution.

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

            # check if a post_action is present, extract from kwargs
            # and validate it is a callable, since we will call it later on
            post_action = None
            if 'post_action' in kwargs.keys():
                post_action = kwargs.pop('post_action')
                if not isinstance(post_action, Callable):
                    raise TypeError(f'post_action must be a callable, instead is: {type(post_action)}')

            # check that our decorated function has no parameter post_action, else it would be passed automatically
            action_signature = inspect.signature(func)
            if 'post_action' in action_signature.parameters:
                raise Exception(f"an action (decorated function) can't contain a parameter named 'post_action'")

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

                # # run the post action if present, ignoring any domain exceptions
                # state_before_post_action = puma_ui_graph.current_state
                # if post_action is not None:
                #     safe_func_call(post_action, driver=puma_ui_graph.driver, gtl_logger=gtl_logger, **kwargs)
                #
                # if puma_ui_graph.current_state != state_before_post_action:
                #     raise Exception(f'post_action did not return to original state: '
                #                     f'expected to be in {state_before_post_action}, actually in {puma_ui_graph.current_state}')

                state_before_post_action = puma_ui_graph.current_state
                if post_action is not None:
                    # run the post action if present, ignoring any domain exceptions
                    safe_func_call(post_action, driver=puma_ui_graph.driver, gtl_logger=gtl_logger, **kwargs)
                    # return to our original state
                    puma_ui_graph.go_to_state(state_before_post_action, **arguments)

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
