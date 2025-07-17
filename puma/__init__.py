import logging
import sys

from puma.utils import configure_default_logging

MAIN_MODULE = sys.modules.get('__main__')

def _pattern_in_main(pattern):
    if hasattr(MAIN_MODULE, '__file__'):
        return MAIN_MODULE and pattern in MAIN_MODULE.__file__
    return False

def _is_running_as_main() -> bool:
    """
    Returns True if this package is being run as the main module
    via `python -m puma`.
    """
    return _pattern_in_main('puma/apps')

def _is_running_as_test() -> bool:
    return _pattern_in_main('unittest_runner')

def _is_running_in_jupyter_notebook():
    if MAIN_MODULE is not None:
        if not hasattr(MAIN_MODULE, '__file__'):
            return True
        if 'ipykernel' in str(type(MAIN_MODULE)):
            return True
    return False


configure_default_logging()

# Only configure logging when Puma is not run from another application
if (
        _is_running_as_main() or
        _is_running_as_test() or
        _is_running_in_jupyter_notebook()
):
        configure_default_logging()
else:
    logger = logging.getLogger("puma")
    logger.addHandler(logging.NullHandler())
