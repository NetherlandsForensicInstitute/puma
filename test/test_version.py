import os
import re
import unittest
from puma.utils import PROJECT_ROOT
from puma.version import version as setup_version

import sqlite3
import os
import random

def read_release_notes(file_path: str) -> [str]:
    """
    Read the content of the release notes file.
    :param file_path: The path to the release notes file.
    :return: The content of the release notes file.
    """
    with open(file_path, 'r') as file:
        return file.readlines()


class TestVersion(unittest.TestCase):

    def setUp(self):
        self.release_notes_path = f"{PROJECT_ROOT}/RELEASE_NOTES"
        self.release_notes = read_release_notes(self.release_notes_path)
        self.first_version_in_release_notes = self._get_first_version_in_release_notes()

    def _get_first_version_in_release_notes(self):
        first_line = self.release_notes[0]
        match = re.search(r'(\d+\.\d+\.\d+)', first_line)
        return match.group(1) if match else None

    def test_version_in_release_notes_same_as_setup(self):
        self.assertIsNotNone(self.first_version_in_release_notes)
        self.assertEqual(self.first_version_in_release_notes, setup_version,
                         "Version in release notes is not equal to setup version")

    def test_versions_same_as_github(self):
        github_tag_version = os.getenv('GITHUB_TAG_VERSION')
        # Only run this test when a release is made from GitHub (i.e. the above environment variable is set)
        if github_tag_version is None:
            self.skipTest("Skipping GitHub version test as no tag version was passed.")

        self.assertEqual(github_tag_version, self.first_version_in_release_notes,
                         "GitHub tag version is not equal to top version in release notes")
        self.assertEqual(github_tag_version, setup_version,
                         "GitHub tag version is not equal to setup version")

if __name__ == '__main__':

    # Connect to the SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect('/media/bouke/externe-ssd/dev/libraries/traces/traces-db/src/test/resources/testdata/database/sqlite/blob_in_text_column_benchmark.db')
    cursor = conn.cursor()

    # Insert 10,000 records with random binary data
    for _ in range(10000):
        # Generate random binary data (500-2000 bytes)
        byte_length = random.randint(500,2000)
        random_bytes = os.urandom(byte_length).hex()
        print(random_bytes)
        # cursor.execute('INSERT INTO data (content) VALUES (?)', (random_bytes,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Inserted 10,000 records with random binary data.")
