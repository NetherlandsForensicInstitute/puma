import logging
from pathlib import Path

from puma.utils import LOG_FOLDER, PUMA_INIT_TIMESTAMP


class _GroundTruthFileHandler(logging.FileHandler):
    """
    Writes the ground truth log lines of a device to the ground truth log file.
    """


class _PassOnIfEnabled(logging.Handler):
    """
    Passes ground truth log lines on to the logging configuration of the application, but only the levels it enables.

    The ground truth logger logs INFO and up to the ground truth log file, whatever the logging configuration of the
    application. Passing on all of these lines would show them in an application that only shows warnings, so instead of
    propagating, the lines are passed on to the root logger if it enables their level.
    """

    def emit(self, record: logging.LogRecord):
        root = logging.getLogger()
        if root.isEnabledFor(record.levelno):
            root.handle(record)


def create_gtl_logger(udid: str) -> logging.Logger:
    """
    Create a Puma Ground Truth Logger, specific for one device.
    This logger will log the ground truth of actions taken on this device, including navigation and UI interactions.
    Each log line will include the time and device udid so a clear timeline of events can be tracked on each device.

    There is one logger per device, so all apps on the same device share it. It logs INFO and up to the ground truth log
    file, also when the application using Puma does not configure logging. The lines are also passed on to the logging
    configuration of the application, for the levels it enables.

    :param udid: the device id of the device this logger tracks.
    """
    gtl_logger = logging.getLogger(f'{udid}')
    # the logger is shared by all apps on the device, so it only needs to be set up once
    if any(isinstance(handler, _GroundTruthFileHandler) for handler in gtl_logger.handlers):
        return gtl_logger

    # format of log lines
    formatter = logging.Formatter(fmt=f'%(asctime)s [%(levelname)s] [{udid}] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    # file name of log file
    file_handler = _GroundTruthFileHandler(Path(LOG_FOLDER) / f'{PUMA_INIT_TIMESTAMP}_gtl.log')
    file_handler.setFormatter(formatter)

    gtl_logger.addHandler(file_handler)
    gtl_logger.addHandler(_PassOnIfEnabled())
    gtl_logger.propagate = False
    # a level set by the application is kept
    if gtl_logger.level == logging.NOTSET:
        gtl_logger.setLevel(logging.INFO)

    return gtl_logger
