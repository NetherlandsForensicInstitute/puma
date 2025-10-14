import logging
from pathlib import Path
from sys import stdout

from puma import PUMA_INIT_TIMESTAMP
from puma.utils import LOG_FOLDER


def create_gtl_logger(udid: str) -> logging.Logger:
    gtl_logger = logging.getLogger(f'{udid}')

    # format of log lines
    formatter = logging.Formatter(f'%(asctime)s - DEVICE {udid} - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # file name of log file
    file_handler = logging.FileHandler(Path(LOG_FOLDER) / f'{PUMA_INIT_TIMESTAMP}_gtl.log')
    file_handler.setFormatter(formatter)
    # also log to stdout
    stream_handler = logging.StreamHandler(stdout)
    stream_handler.setFormatter(formatter)

    gtl_logger.addHandler(file_handler)
    gtl_logger.addHandler(stream_handler)

    # TODO: make this a setting when we build the configuration of the GTL logger?
    # propagate is True by default, which causes all gtl logs to also be in the default log file, additionally to being in the gtl log file
    # gtl_logger.propagate = False

    return gtl_logger
