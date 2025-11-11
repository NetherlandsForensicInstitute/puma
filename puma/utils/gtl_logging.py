import logging
from pathlib import Path
from sys import stdout

from puma.utils import LOG_FOLDER, PUMA_INIT_TIMESTAMP


def create_gtl_logger(udid: str) -> logging.Logger:
    """
    Create a Puma Ground Truth Logger, specific for one device.
    This logger will log the ground truth of actions taken on this device, including navigation and UI interactions.
    Each log line will include the time and device udid so a clear timeline of events can be tracked on each device.

    :param udid: the device id of the device this logger tracks.
    """
    gtl_logger = logging.getLogger(f'{udid}')

    # format of log lines
    formatter = logging.Formatter(fmt=f'%(asctime)s [%(levelname)s] [{udid}] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    # file name of log file
    file_handler = logging.FileHandler(Path(LOG_FOLDER) / f'{PUMA_INIT_TIMESTAMP}_gtl.log')
    file_handler.setFormatter(formatter)

    gtl_logger.addHandler(file_handler)

    return gtl_logger
