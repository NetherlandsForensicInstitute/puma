import io

from PIL import Image
from selenium.webdriver.remote.webelement import WebElement


def show_elements_as_picture_popups(elements: WebElement | list[WebElement]):
    """
    Generate a pup-up image for each element, showing exactly and only the UI part of
    given element. Useful for debugging, for example when you select a set of elements
    using XPATH and you want to see which ones matched.

    :param elements: elements to show
    """
    elements = elements if isinstance(elements, list) else [elements]
    for element in elements:
        image = Image.open(io.BytesIO(element.screenshot_as_png))
        image.show(title=element.id)
