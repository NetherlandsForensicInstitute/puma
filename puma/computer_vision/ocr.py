import os.path

from pytesseract import pytesseract

from puma.utils import log_error_and_raise_exception, logger


class BoundingBox:
    """
    Class describing a rectangle in an image.
    properties:
        x,y: the top right corner
        width, height: the dimensions
        middle: a tuple describing the center of the rectangle
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.middle = (x + (width / 2), y + (height / 2))

    def __str__(self):
        return f'BoundingBox([{self.x},{self.y}], [{self.width}x{self.height}], center: {self.middle})'

    def __repr__(self):
        return self.__str__()


class RecognizedText:
    """
    Class describing text recognized by Tesseract.
    properties:
        text: the text that was recognized
        confidence: the confidence reported by tesseract
        bounding_box: the BoundingBox of the area in which the text was recognized
    """

    def __init__(self, text: str, x: int, y: int, width: int, height: int, confidence: int):
        self.text = text
        self.bounding_box = BoundingBox(x, y, width, height)
        self.confidence = confidence

    def __str__(self):
        return f'RecognizedText(text:{self.text}, bounds:{self.bounding_box})'

    def __repr__(self):
        return self.__str__()


def recognize_text(path_to_image: str) -> [RecognizedText]:
    """
    Analyzes an image and returns a list of all text recognized by Teseract
    :param path_to_image: path to the image
    :return: a list of all RecognizedText object
    """
    if not os.path.exists(path_to_image):
        log_error_and_raise_exception(logger, f'Could not analyze image because file does not exist: {path_to_image}')
    data = pytesseract.image_to_data(path_to_image, output_type='dict')
    all_text = []
    for i in range(0, len(data['text']) - 1):
        text = RecognizedText(data['text'][i], data['left'][i], data['top'][i], data['width'][i], data['height'][i],
                              data['conf'][i])
        all_text.append(text)
    return all_text


def find_text(path_to_image: str, text_to_find: str) -> [RecognizedText]:
    """
    Filters the output of recognize_text for a given text to find (case-insensitive).
    :param path_to_image: path to the image
    :param text_to_find: text to find in image
    :return: All RecognizedText objects containing the text to find
    """
    all_text = recognize_text(path_to_image)
    return [found_text for found_text in all_text if text_to_find.lower() in found_text.text.lower()]
