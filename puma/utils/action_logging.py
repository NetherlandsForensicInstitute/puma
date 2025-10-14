import logging
from datetime import datetime
from pathlib import Path
from sys import stdout

from puma.utils import LOG_FOLDER


def create_gtl_logger(udid: str) -> logging.Logger:
    gtl_logger = logging.getLogger(f'{udid}')

    # format of log lines
    formatter = logging.Formatter(f'%(asctime)s - DEVICE {udid} - %(levelname)s - %(message)s')
    # file name of log file
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_handler = logging.FileHandler(Path(LOG_FOLDER) / f'{now}_gtl.log')
    file_handler.setFormatter(formatter)
    # also log to stdout
    stream_handler = logging.StreamHandler(stdout)
    stream_handler.setFormatter(formatter)

    gtl_logger.addHandler(file_handler)
    gtl_logger.addHandler(stream_handler)

    return gtl_logger
