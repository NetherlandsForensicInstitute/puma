import functools
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def log_action(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        module_name = func.__module__
        logger = logging.getLogger(module_name)
        logger.info(f"Action {func.__name__} initiated")
        return func(self, *args, **kwargs)
    return wrapper
