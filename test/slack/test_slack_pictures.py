import unittest
from unittest.mock import Mock, patch

from puma.apps.android.slack.slack import Slack
from puma.apps.android.slack.xpaths import ATTACHMENTS_MEDIA_STRIP, ATTACHMENTS_PICTURES
from puma.state_graph.puma_driver import PumaClickException
from . import slack_without_device

STRIP_WIDTH = 1080
# As on a device: the pictures start after the camera and gallery buttons
FIRST_PICTURE, PICTURE_WIDTH, PICTURE_PITCH = 591, 252, 274
TOUCH_SLOP = 13


class FakeStrip:
    """
    Simple model of the photo strip in the attachments menu, which can be swiped sideways.
    """

    def __init__(self, descriptions: list[str]):
        self.descriptions = descriptions
        self.offset = 0
        self.max_offset = max(0, FIRST_PICTURE + len(descriptions) * PICTURE_PITCH - STRIP_WIDTH)

    def _shown(self) -> list[tuple[int, int, int]]:
        """(index, left, right) of the pictures that are at least partly shown, left and right cut to the strip."""
        shown = []
        for index in range(len(self.descriptions)):
            left = FIRST_PICTURE + index * PICTURE_PITCH - self.offset
            if left + PICTURE_WIDTH > 0 and left < STRIP_WIDTH:
                shown.append((index, max(left, 0), min(left + PICTURE_WIDTH, STRIP_WIDTH)))
        return shown

    @property
    def page_source(self) -> str:
        pictures = ''.join(f'<android.widget.FrameLayout content-desc="{self.descriptions[index]}" '
                           f'bounds="[{left},1180][{right},1450]"/>' for index, left, right in self._shown())
        return (f'<hierarchy><androidx.recyclerview.widget.RecyclerView resource-id="com.Slack:id/media_recycler_view" '
                f'bounds="[0,1168][{STRIP_WIDTH},1464]">{pictures}'
                '</androidx.recyclerview.widget.RecyclerView></hierarchy>')

    def swipe(self, start_x, start_y, end_x, end_y, duration):
        self.offset = min(self.max_offset, self.offset + round(start_x - end_x) - TOUCH_SLOP)

    def picture(self, xpath: str) -> int:
        """The index (from 0) of the picture an XPath returned by _find_picture points to."""
        prefix = f'({ATTACHMENTS_PICTURES})['
        assert xpath.startswith(prefix) and xpath.endswith(']'), xpath
        return self._shown()[int(xpath[len(prefix):-1]) - 1][0]


@patch('puma.apps.android.slack.slack.time.sleep', lambda seconds: None)
class TestSlackFindPicture(unittest.TestCase):
    def _find(self, descriptions: list[str], picture_id: int) -> int:
        strip = FakeStrip(descriptions)
        slack = slack_without_device(Slack.chat_state)
        slack.driver.driver = strip
        strip_rect = {'x': 0, 'y': 1168, 'width': STRIP_WIDTH, 'height': 296}
        slack.driver.get_element.side_effect = \
            lambda xpath: Mock(rect=strip_rect) if xpath == ATTACHMENTS_MEDIA_STRIP else Mock()
        return strip.picture(slack._find_picture(picture_id))

    def test_pictures(self):
        descriptions = [f'Photo, IMG_{index}.jpg' for index in range(20)]
        for picture_id in (1, 2, 3, 7, 20):
            with self.subTest(picture_id=picture_id):
                self.assertEqual(picture_id - 1, self._find(descriptions, picture_id))

    def test_pictures_with_the_same_description(self):
        # e.g. burst shots, or photos taken in the same minute
        self.assertEqual(1, self._find(['Photo, A', 'Photo, A', 'Photo, B'], 2))
        # the strip ends with other photos, see the limit in new_items
        descriptions = ['Photo, A'] * 6 + ['Photo, B'] + ['Photo, C'] * 6 \
            + [f'Photo, IMG_{index}.jpg' for index in range(4)]
        for picture_id in range(1, 14):
            with self.subTest(picture_id=picture_id):
                self.assertEqual(picture_id - 1, self._find(descriptions, picture_id))

    def test_more_pictures_than_on_the_device(self):
        with self.assertRaises(PumaClickException):
            self._find([f'Photo, IMG_{index}.jpg' for index in range(5)], 6)


if __name__ == '__main__':
    unittest.main()
