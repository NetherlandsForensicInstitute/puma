import inspect
import re

from puma.state_graph import logger
from puma.state_graph.puma_driver import PumaClickException


def safe_func_call(func, **kwargs):
    """
    Safely calls a function with the provided keyword arguments.

    This function filters the provided keyword arguments to only include those that are
    defined in the function's signature. It then attempts to call the function with these
    filtered arguments. If a PumaClickException occurs during the function call, it catches
    the exception, prints an error message, and returns None.

    :param func: The function to be called.
    :param kwargs: Arbitrary keyword arguments to pass to the function.
    :return: The result of the function call, or None if an exception occurs.
    """
    bound_args = filter_arguments(func, **kwargs)
    try:
        return func(**bound_args.arguments)
    except PumaClickException as pce:
        logger.warn(f"A problem occurred during a safe function call, recovering.. {pce}")
        return None


def filter_arguments(func, **kwargs) -> inspect.BoundArguments:
    signature = inspect.signature(func)
    filtered_args = {
        k: v for k, v in kwargs.items() if k in signature.parameters
    }
    bound_args = signature.bind(**filtered_args)
    bound_args.apply_defaults()
    return bound_args

def is_valid_package_name(package_name: str) -> bool:
    pattern = r'^[a-z_][a-z0-9_]+(\.[a-z_][a-z0-9_]*)*$'
    return bool(re.fullmatch(pattern, package_name)) and len(package_name) <= 100