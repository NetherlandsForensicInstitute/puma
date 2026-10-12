import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from puma.utils import gtl_logging


class _RecordHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


class TestGroundTruthLogger(unittest.TestCase):
    def setUp(self):
        log_folder = tempfile.TemporaryDirectory()
        self.addCleanup(log_folder.cleanup)
        log_folder_patch = patch('puma.utils.gtl_logging.LOG_FOLDER', log_folder.name)
        log_folder_patch.start()
        self.addCleanup(log_folder_patch.stop)
        self.log_file = Path(log_folder.name) / f'{gtl_logging.PUMA_INIT_TIMESTAMP}_gtl.log'

        # the logging configuration of an application that only shows warnings
        root = logging.getLogger()
        self.root_records = _RecordHandler()
        root.addHandler(self.root_records)
        self.addCleanup(root.removeHandler, self.root_records)
        self.addCleanup(root.setLevel, root.level)
        root.setLevel(logging.WARNING)

        # a new device for every test, as loggers are global
        self.udid = f'device-{uuid4()}'

    def _create_logger(self) -> logging.Logger:
        gtl_logger = gtl_logging.create_gtl_logger(self.udid)
        self.addCleanup(self._close_handlers, gtl_logger)
        return gtl_logger

    @staticmethod
    def _close_handlers(gtl_logger: logging.Logger):
        for handler in list(gtl_logger.handlers):
            handler.close()
            gtl_logger.removeHandler(handler)

    def _log_lines(self) -> list[str]:
        return self.log_file.read_text().splitlines()

    def test_info_is_written_to_file_when_application_shows_only_warnings(self):
        self._create_logger().info('Pressing back button')
        self.assertEqual(1, len(self._log_lines()))
        self.assertIn(f'[INFO] [{self.udid}] Pressing back button', self._log_lines()[0])

    def test_logger_of_device_is_set_up_once(self):
        # e.g. two apps on the same device
        self._create_logger()
        self._create_logger().info('Pressing back button')
        self.assertEqual(1, len(self._log_lines()))

    def test_lines_are_passed_on_for_levels_the_application_enables(self):
        gtl_logger = self._create_logger()
        gtl_logger.info('Pressing back button')
        gtl_logger.warning('Could not check the version')
        self.assertEqual(['Could not check the version'], [record.getMessage() for record in self.root_records.records])

    def test_info_is_passed_on_when_application_shows_info(self):
        logging.getLogger().setLevel(logging.INFO)
        self._create_logger().info('Pressing back button')
        self.assertEqual(['Pressing back button'], [record.getMessage() for record in self.root_records.records])

    def test_level_set_by_application_is_kept(self):
        logging.getLogger(self.udid).setLevel(logging.WARNING)
        gtl_logger = self._create_logger()
        gtl_logger.info('Pressing back button')
        self.assertEqual([], self._log_lines())


if __name__ == '__main__':
    unittest.main()
