import inspect
import re

from puma.state_graph import logger
from puma.state_graph.puma_driver import PumaClickException, Platform


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
        logger.warning(f"A problem occurred during a safe function call, recovering.. {pce}")
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
    pattern = r'^[A-Za-z_][A-Za-z0-9_]+(\.[A-Za-z_][A-Za-z0-9_]*)*$' #Upper case is against Google's conventions, but Google breaks their own convention with GoogleCamera
    return bool(re.fullmatch(pattern, package_name)) and len(package_name) <= 100


def is_valid_bundle_id(bundle_id: str) -> bool:
    # iOS bundle ids may contain alphanumeric characters, hyphens and periods
    pattern = r'^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$'
    return bool(re.fullmatch(pattern, bundle_id)) and len(bundle_id) <= 155


def is_valid_app_id(app_id: str, platform: Platform) -> bool:
    """
    Validates an application identifier: a package name on Android, or a bundle id on iOS.

    :param app_id: The application identifier.
    :param platform: The platform of the application.
    """
    if platform == Platform.IOS:
        return is_valid_bundle_id(app_id)
    return is_valid_package_name(app_id)
