import inspect

from puma.state_graph.state import State


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
            bound_args = inspect.signature(func).bind(*args, **kwargs)
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
