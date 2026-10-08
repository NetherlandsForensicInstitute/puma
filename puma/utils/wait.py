import logging
from time import monotonic, sleep
from typing import Callable

logger = logging.getLogger(__name__)


def wait_until(condition: Callable[[], bool], timeout: float, interval: float = 1, description: str = None,
               log: logging.Logger = None):
    """
    Polls a condition until it returns True. The condition is checked at least once, also with a timeout of 0. An
    exception raised by the condition is not caught, it ends the wait.

    :param condition: A function without arguments, returning whether the thing waited for has happened.
    :param timeout: The maximum time to wait, in seconds.
    :param interval: The time between two checks of the condition, in seconds.
    :param description: What is waited for, e.g. 'app com.whatsapp to be installed'. It is used in the log lines and in
    the error message. Without a description nothing is logged, which is meant for short waits that are part of a larger
    action.
    :param log: The logger used for the log lines. Pass the ground truth logger of the device (driver.gtl_logger) to
    make the wait visible in the ground truth log.
    :raises TimeoutError: If the condition was not met within the timeout.
    """
    log = log or logger
    if description:
        log.info(f'Waiting for {description}')
    end = monotonic() + timeout
    while not condition():
        remaining = end - monotonic()
        if remaining <= 0:
            raise TimeoutError(f'Timed out after {timeout} seconds waiting for {description or "the condition"}')
        sleep(min(interval, remaining))
    if description:
        log.info(f'Done waiting for {description}')
