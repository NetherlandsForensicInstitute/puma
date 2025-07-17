import functools
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def log_action(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        logger.info(f"Action {func.__name__} initiated at {datetime.now().isoformat()}")
        return func(self, *args, **kwargs)
    return wrapper
