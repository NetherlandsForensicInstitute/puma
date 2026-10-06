import unittest

from puma.apps.android.slack.slack import Message, _merge_messages, _parse_messages


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


class TestSlackMessagesParsing(unittest.TestCase):
    def test_parse_messages(self):
        page = _page(_message(300, 500, 'puma w', 'Sep 29th at 2:06 PM', 'Hello!'),
                     _message(500, 600, text='Second message'),
                     _message(600, 1400, 'Puma', 'Today at 4:01 PM', 'Look at this', 'Open image: IMG-1.jpeg.'))
        self.assertEqual([Message('puma w', 'Sep 29th at 2:06 PM', 'Hello!', ''),
                          Message(None, None, 'Second message', ''),
                          Message('Puma', 'Today at 4:01 PM', 'Look at this', 'image: IMG-1.jpeg')],
                         _parse_messages(page))

    def test_parse_messages_removes_zero_width_spaces(self):
        page = _page(_message(300, 500, 'puma w', 'Today at 4:01 PM', 'Hello 👋​'))
        self.assertEqual('Hello 👋', _parse_messages(page)[0].text)

    def test_parse_messages_skips_partly_shown_messages(self):
        page = _page(_message(200, 400, 'puma w', 'Today at 4:01 PM', 'Partly shown at the top'),
                     _message(400, 600, text='Shown'),
                     _message(2100, 2174, 'Puma', 'Today at 4:02 PM'))
        self.assertEqual([Message(None, None, 'Shown', '')], _parse_messages(page))

    def test_parse_messages_keeps_messages_larger_than_the_screen(self):
        page = _page(_message(100, 2300, 'puma w', 'Today at 4:01 PM', 'Very long message'))
        self.assertEqual(['Very long message'], [message.text for message in _parse_messages(page)])

    def test_merge_overlapping_screens(self):
        a, b, c, d = (Message('Puma', None, text, '') for text in 'abcd')
        self.assertEqual([a, b, c, d], _merge_messages([a, b, c], [b, c, d]))
        self.assertEqual([a, b, c, d], _merge_messages([a, b], [c, d]))
        self.assertEqual([a, b], _merge_messages([a, b], [a, b]))

    def test_merge_keeps_identical_consecutive_messages(self):
        a, b = Message('Puma', None, 'same', ''), Message('Puma', None, 'other', '')
        # the first screen shows two identical messages, the second screen shows the second one and a new message
        self.assertEqual([a, a, b], _merge_messages([a, a], [a, b]))


if __name__ == '__main__':
    unittest.main()
