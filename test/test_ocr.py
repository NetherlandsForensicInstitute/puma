import unittest
from unittest.mock import patch

from puma.computer_vision.ocr import recognize_text, find_text

# The output of pytesseract.image_to_data for an image with the words 'Hello' and 'World'. The first rows are the page,
# block, paragraph and line Tesseract found, which have no text of their own.
TESSERACT_DATA = {
    'level': [1, 2, 3, 4, 5, 5],
    'text': ['', '', '', ' ', 'Hello', 'World'],
    'left': [0, 10, 10, 10, 10, 80],
    'top': [0, 20, 20, 20, 20, 20],
    'width': [200, 130, 130, 130, 60, 60],
    'height': [100, 30, 30, 30, 30, 30],
    'conf': [-1, -1, -1, -1, 96, 91],
}


@patch('puma.computer_vision.ocr.os.path.exists', return_value=True)
@patch('puma.computer_vision.ocr.pytesseract.image_to_data', return_value=TESSERACT_DATA)
class TestOcr(unittest.TestCase):
    def test_recognize_text_returns_all_words(self, *_):
        recognized = recognize_text('screenshot.png')
        self.assertEqual(['Hello', 'World'], [text.text for text in recognized])

    def test_recognize_text_bounding_box_and_confidence(self, *_):
        world = recognize_text('screenshot.png')[1]
        self.assertEqual((80, 20, 60, 30), (world.bounding_box.x, world.bounding_box.y, world.bounding_box.width,
                                            world.bounding_box.height))
        self.assertEqual((110, 35), world.bounding_box.middle)
        self.assertEqual(91, world.confidence)

    def test_find_text_finds_last_word(self, *_):
        found = find_text('screenshot.png', 'world')
        self.assertEqual(['World'], [text.text for text in found])


if __name__ == '__main__':
    unittest.main()
