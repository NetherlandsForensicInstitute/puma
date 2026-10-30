import unittest
from datetime import datetime

from puma.apps.android.slack.message_parser import Message, new_items, parse_messages, to_iso_time
from puma.state_graph.puma_driver import PumaClickException

# A Thursday
NOW = datetime(2026, 10, 8, 10, 30)


def _message(top: int, bottom: int, sender: str = None, time: str = None, text: str = None, file: str = None) -> str:
    header = ''
    if sender:
        header = (f'<android.widget.LinearLayout resource-id="com.Slack:id/message_header" bounds="[189,{top}][500,{top + 60}]">'
                  f'<android.widget.TextView resource-id="com.Slack:id/name" text="{sender}" content-desc="" bounds="[189,{top}][340,{top + 60}]"/>'
                  f'<android.widget.TextView resource-id="com.Slack:id/message_time" text="" content-desc="{time}" bounds="[362,{top}][499,{top + 60}]"/>'
                  f'</android.widget.LinearLayout>')
    content = ''
    if text:
        content += f'<android.widget.TextView resource-id="com.Slack:id/msg_text" text="{text}" bounds="[189,{top}][1038,{bottom}]"/>'
    if file:
        content += f'<android.view.ViewGroup resource-id="com.Slack:id/file_frame_layout" content-desc="{file}" bounds="[189,{top}][636,{bottom}]"/>'
    return (f'<android.widget.RelativeLayout resource-id="com.Slack:id/message_layout" bounds="[0,{top}][1080,{bottom}]">'
            f'{header}{content}</android.widget.RelativeLayout>')


def _page(*messages: str) -> str:
    return (f'<hierarchy><androidx.recyclerview.widget.RecyclerView resource-id="com.Slack:id/messages_list" '
            f'bounds="[0,265][1080,2174]">{"".join(messages)}</androidx.recyclerview.widget.RecyclerView></hierarchy>')


def _messages(page: str) -> list[Message]:
    return [message for *_, message in parse_messages(page)]


class TestSlackMessagesParsing(unittest.TestCase):
    def test_parse_messages(self):
        page = _page(_message(300, 500, 'puma w', 'Sep 29th at 2:06 PM', 'Hello!'),
                     _message(500, 600, text='Second message'),
                     _message(600, 1400, 'Puma', 'Today at 4:01 PM', 'Look at this', 'Open image: IMG-1.jpeg.'))
        self.assertEqual([(300, 500), (500, 600), (600, 1400)],
                         [(top, bottom) for top, bottom, _ in parse_messages(page)])
        self.assertEqual([Message('puma w', 'Sep 29th at 2:06 PM', 'Hello!', ''),
                          Message(None, None, 'Second message', ''),
                          Message('Puma', 'Today at 4:01 PM', 'Look at this', 'image: IMG-1.jpeg')],
                         _messages(page))

    def test_parse_messages_removes_zero_width_spaces(self):
        page = _page(_message(300, 500, 'puma w', 'Today at 4:01 PM', 'Hello 👋​'))
        self.assertEqual('Hello 👋', _messages(page)[0].text)
        # Slack also inserts them after hyphens in names
        page = _page(_message(300, 500, 'Anne-​Marie', 'Today at 4:01 PM', 'Hello'))
        self.assertEqual('Anne-Marie', _messages(page)[0].sender)

    def test_parse_messages_without_messages_list(self):
        # e.g. when a pop-up covers the conversation
        with self.assertRaises(PumaClickException):
            _messages('<hierarchy><android.widget.FrameLayout bounds="[0,0][1080,2400]"/></hierarchy>')

    def test_parse_messages_skips_partly_shown_messages(self):
        page = _page(_message(200, 400, 'puma w', 'Today at 4:01 PM', 'Partly shown at the top'),
                     _message(400, 600, text='Shown'),
                     _message(2100, 2174, 'Puma', 'Today at 4:02 PM'))
        self.assertEqual([Message(None, None, 'Shown', '')], _messages(page))

    def test_parse_messages_keeps_messages_larger_than_the_screen(self):
        page = _page(_message(100, 2300, 'puma w', 'Today at 4:01 PM', 'Very long message'))
        self.assertEqual(['Very long message'], [message.text for message in _messages(page)])



def _items(*items: tuple[int, str], height: int = 100) -> list[tuple[int, int, str]]:
    return [(top, top + height, item) for top, item in items]


class TestNewItems(unittest.TestCase):
    """Items are 100 pixels high. The screen was swiped 200 pixels, the items moved 190 pixels unless stated."""

    def test_first_screen(self):
        screen = _items((300, 'a'), (400, 'b'))
        self.assertEqual(screen, new_items([], screen, 0, (250, 550)))

    def test_overlapping_screens(self):
        self.assertEqual(_items((300, 'a'), (400, 'b')),
                         new_items(_items((300, 'c'), (400, 'd')), _items((300, 'a'), (400, 'b'), (490, 'c')), 200,
                                   (250, 650)))

    def test_screens_without_overlap(self):
        # e.g. large pictures, which are not completely shown on both screens
        self.assertEqual(_items((300, 'a')), new_items(_items((300, 'c')), _items((300, 'a')), 200, (250, 450)))

    def test_identical_items(self):
        # the history is [ok, ok, ok, x]: the screens show [ok, x] and then [ok, ok], the third ok is partly shown
        self.assertEqual(_items((400, 'ok'), (500, 'ok')),
                         new_items(_items((400, 'ok'), (500, 'x')), _items((400, 'ok'), (500, 'ok')), 200, (350, 620)))
        # all items are identical
        screen = _items((100, 'ok'), (200, 'ok'), (300, 'ok'))
        self.assertEqual(screen[:2], new_items(screen, screen, 200, (50, 450)))

    def test_scrolled_less_at_the_end_of_the_list(self):
        # the beginning of the list was reached after 90 pixels
        self.assertEqual(_items((300, 'a')), new_items(_items((300, 'b'), (500, 'c')),
                                                       _items((300, 'a'), (390, 'b'), (590, 'c')), 200, (250, 750)))
        # the list did not scroll at all
        screen = _items((300, 'b'), (500, 'c'))
        self.assertEqual([], new_items(screen, screen, 200, (250, 750)))

    def test_scrolled_less_at_the_end_of_the_list_without_other_items(self):
        # As on a device: at the beginning of a channel, the introduction of the channel scrolls into view and the last
        # messages moved 227 pixels. After 573 pixels, the first message would be shown completely at the bottom.
        previous = _items((1443, 'joined'), (1599, 'Hallo!'), (1755, 'joined'), height=156)
        current = _items((1670, 'joined'), (1826, 'Hallo!'), height=156)
        self.assertEqual([], new_items(previous, current, 573, (265, 2174)))
        # the same, but at 573 pixels the first message would be cut off by 3 pixels: a swipe always scrolls a bit less
        previous = _items((1448, 'joined'), (1604, 'Hallo!'), (1760, 'joined'), height=156)
        current = _items((1670, 'joined'), (1826, 'Hallo!'), height=156)
        self.assertEqual([], new_items(previous, current, 573, (265, 2174)))


class TestSlackTimeConversion(unittest.TestCase):
    def test_relative_dates(self):
        self.assertEqual('2026-10-08T16:01:00', to_iso_time('Today at 4:01 PM', NOW))
        self.assertEqual('2026-10-07T00:15:00', to_iso_time('Yesterday at 12:15 AM', NOW))

    def test_weekdays_are_in_the_last_week(self):
        self.assertEqual('2026-10-06T09:00:00', to_iso_time('Tuesday at 9:00 AM', NOW))
        self.assertEqual('2026-10-05T12:00:00', to_iso_time('Monday at 12:00 PM', NOW))
        # today is shown as 'Today', so the same weekday is a week ago
        self.assertEqual('2026-10-01T13:00:00', to_iso_time('Thursday at 1:00 PM', NOW))
        self.assertEqual('2026-10-02T13:00:00', to_iso_time('Friday at 1:00 PM', NOW))

    def test_dates(self):
        self.assertEqual('2026-09-29T14:06:00', to_iso_time('Sep 29th at 2:06 PM', NOW))
        self.assertEqual('2026-10-01T08:05:00', to_iso_time('Oct 1st at 8:05 AM', NOW))
        self.assertEqual('2026-03-22T11:00:00', to_iso_time('March 22nd at 11:00 AM', NOW))

    def test_dates_without_year_in_the_future_are_last_year(self):
        self.assertEqual('2025-12-24T18:00:00', to_iso_time('Dec 24th at 6:00 PM', NOW))

    def test_dates_with_year(self):
        self.assertEqual('2025-09-29T14:06:00', to_iso_time('Sep 29th, 2025 at 2:06 PM', NOW))

    def test_24_hour_clock_and_no_break_spaces(self):
        self.assertEqual('2026-09-29T14:06:00', to_iso_time('Sep 29th at 14:06', NOW))
        self.assertEqual('2026-09-29T14:06:00', to_iso_time('Sep 29th at 2:06 PM', NOW))
        self.assertEqual('2026-09-29T14:06:00', to_iso_time('Sep 29th at 2:06 PM', NOW))

    def test_unknown_formats(self):
        for shown_time in ('Last week', 'Sometime at 2:06 PM', 'Sep 29th at noon'):
            with self.assertRaises(ValueError):
                to_iso_time(shown_time, NOW)


if __name__ == '__main__':
    unittest.main()
