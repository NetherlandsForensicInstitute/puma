import logging
from datetime import datetime
from os import makedirs, environ
from os.path import dirname, abspath, isdir, expanduser
from pathlib import Path
from sys import stdout

logger = logging.getLogger(__name__)


#####################
# LOGGING INIT CODE #
#####################

# define needed folders
PROJECT_ROOT = dirname(dirname(dirname(abspath(__file__))))
LOG_FOLDER = Path(PROJECT_ROOT) / 'logs'
makedirs(LOG_FOLDER, exist_ok=True)
CACHE_FOLDER = Path(PROJECT_ROOT) / 'cache'
makedirs(CACHE_FOLDER, exist_ok=True)


# logging helpers
def configure_default_logging():
    now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    logging.basicConfig(
        handlers=[
            logging.FileHandler(Path(LOG_FOLDER) / f'{now}.log'),
            logging.StreamHandler(stdout)
        ],
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')


def log_error_and_raise_exception(logger, msg):
    logger.error(msg)
    raise Exception(msg)
