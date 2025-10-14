import logging
from datetime import datetime
from os import makedirs
from os.path import dirname, abspath
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


class GtlFormatter(logging.Formatter):
    def __init__(self, prefix, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = prefix

    def format(self, record):
        # Prepend the prefix to the message
        record.msg = f"{self.prefix} {record.msg}"
        return super().format(record)


# logging helpers
def configure_default_logging():
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logging.basicConfig(
        handlers=[
            logging.FileHandler(Path(LOG_FOLDER) / f'{now}.log'),
            logging.StreamHandler(stdout)
        ],
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')


def configure_gtl_logging():
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    file_handler = logging.FileHandler(Path(LOG_FOLDER) / f'{now}_gtl.log')
    file_handler.setFormatter(GtlFormatter(prefix='PhoneId'))

    stream_handler = logging.StreamHandler(stdout)
    stream_handler.setFormatter(GtlFormatter(prefix='PhoneId'))

    logging.basicConfig(
        handlers=[
            file_handler,
            stream_handler
        ],
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')


def log_error_and_raise_exception(logger, msg):
    logger.error(msg)
    raise Exception(msg)
