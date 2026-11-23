import unittest
from unittest.mock import Mock

from puma.apps.android.teleguard.teleguard import TeleGuard


def _extract_name(content_description: str) -> str:
    row = Mock()
    row.get_attribute.return_value = content_description
    return TeleGuard._extract_name(None, row)


class TestTeleGuardExtractName(unittest.TestCase):
    def test_initials_of_two_words(self):
        self.assertEqual('Alice Puma', _extract_name('AP\nAlice Puma\n09:57\nPuma check: unread test\n1'))

    def test_initial_of_one_word(self):
        self.assertEqual('Bob', _extract_name('B\nBob\n09:57\nHi\n1'))
        self.assertEqual('bob', _extract_name('B\nbob\n09:57\nHi\n1'))

    def test_profile_picture_has_no_initials(self):
        self.assertEqual('Bob', _extract_name('Bob\n09:57\nHi\n1'))
        self.assertEqual('AP', _extract_name('AP\n09:57\nHi\n1'))


if __name__ == '__main__':
    unittest.main()
