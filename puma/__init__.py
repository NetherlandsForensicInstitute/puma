from puma.utils import configure_default_logging
import sys

def _is_running_as_main_package() -> bool:
    """
    Returns True if this package is being run as the main module
    via `python -m yourpackage`.
    """
    main_module = sys.modules.get("__main__")
    return main_module and main_module.__file__.__contains__('puma/apps')

if _is_running_as_main_package():
    configure_default_logging()