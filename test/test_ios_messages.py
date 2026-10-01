import unittest

from puma.apps.ios.messages.messages import Message, Reaction, Service, _parse_message, _parse_messages, \
    _service_from_text, _title_matches


def _cell(label: str) -> str:
    return (f'<XCUIElementTypeCell type="XCUIElementTypeCell" name="{label}" label="{label}">'
            f'<XCUIElementTypeTextView type="XCUIElementTypeTextView" name="CKBalloonTextView"/>'
            f'</XCUIElementTypeCell>')


def _text(name: str) -> str:
    return f'<XCUIElementTypeStaticText type="XCUIElementTypeStaticText" name="{name}" label="{name}"/>'


class TestMessagesParsing(unittest.TestCase):
    def test_parse_sent_messages(self):
        self.assertEqual(Message(None, 'Hi, how are you?', '14:45', Service.IMESSAGE),
                         _parse_message('Your iMessage, Hi, how are you?, 14:45'))
        self.assertEqual(Message(None, 'Code request', '19:39', Service.SMS),
                         _parse_message('Your Text Message, Code request, 19:39'))
        self.assertTrue(_parse_message('Your iMessage, Hi, 14:45').sent_by_me)

    def test_parse_received_message_uses_given_service(self):
        message = _parse_message('Bob Jansen, Fine, thanks!, 14:46', Service.SMS)
        self.assertEqual(Message('Bob Jansen', 'Fine, thanks!', '14:46', Service.SMS), message)
        self.assertFalse(message.sent_by_me)

    def test_parse_reactions(self):
        message = _parse_message('Your iMessage, Hi, all!, You loved this, Bob liked this, 20:31')
        self.assertEqual('Hi, all!', message.text)
        self.assertEqual([(None, Reaction.HEART), ('Bob', Reaction.THUMBS_UP)], message.reactions)
        received = _parse_message('+1 (555) 564-8583, Test, +1 (555) 564-8583 laughed at this, 20:32', Service.IMESSAGE)
        self.assertEqual(('Test', [('+1 (555) 564-8583', Reaction.HAHA)]), (received.text, received.reactions))
        self.assertEqual([], _parse_message('Bob, I liked this movie, 20:33').reactions)

    def test_parse_replies(self):
        page_source = ('<AppiumAUT>' + _text('iMessage  Encrypted') + _cell('Your iMessage, Test 2, 17:17')
                       + _text('\u200e1 Reply') + _cell('Your iMessage, Reply Preview, Test 2, 17:17')
                       + _cell('Your iMessage, Reply, Puma reply, with comma, 20:38') + '</AppiumAUT>')
        messages = _parse_messages(page_source)
        self.assertEqual(['Test 2', 'Puma reply, with comma'], [message.text for message in messages])
        self.assertEqual([(False, None), (True, 'Test 2')], [(m.is_reply, m.reply_to) for m in messages])
        self.assertEqual(Service.IMESSAGE, messages[1].service)

    def test_service_from_text(self):
        self.assertEqual(Service.IMESSAGE, _service_from_text('iMessage'))
        self.assertEqual(Service.IMESSAGE, _service_from_text('iMessage  Encrypted'))
        self.assertEqual(Service.SMS, _service_from_text('Text Message • SMS'))
        self.assertIsNone(_service_from_text('Yesterday 21:44'))

    def test_parse_messages_takes_service_from_last_separator(self):
        page_source = ('<AppiumAUT><XCUIElementTypeApplication type="XCUIElementTypeApplication">'
                       + _text('Text Message • SMS') + _cell('Bank, Your code is hidden, 17:35')
                       + _text('Yesterday 21:44') + _cell('Bank, Another one, 21:44')
                       + _text('iMessage') + _cell('Bob, Hello, 09:00') + _cell('Your iMessage, Hi Bob, 09:01')
                       + _text('Delivered')
                       + '</XCUIElementTypeApplication></AppiumAUT>')
        self.assertEqual([Message('Bank', 'Your code is hidden', '17:35', Service.SMS),
                          Message('Bank', 'Another one', '21:44', Service.SMS),
                          Message('Bob', 'Hello', '09:00', Service.IMESSAGE),
                          Message(None, 'Hi Bob', '09:01', Service.IMESSAGE)],
                         _parse_messages(page_source))

    def test_parse_messages_without_separator_uses_default_service(self):
        page_source = ('<AppiumAUT>' + _cell('Bob, Hello, 09:00') + _text('iMessage') + _cell('Bob, Hi, 09:01')
                       + '</AppiumAUT>')
        self.assertEqual([Message('Bob', 'Hello', '09:00', None)], _parse_messages(page_source)[:1])
        self.assertEqual([Message('Bob', 'Hello', '09:00', Service.SMS),
                          Message('Bob', 'Hi', '09:01', Service.IMESSAGE)],
                         _parse_messages(page_source, Service.SMS))

    def test_title_matches(self):
        self.assertTrue(_title_matches('Bob', 'Bob Jansen'))
        self.assertTrue(_title_matches('+1 (888) 555-1212', '+1 (888) 555-1212'))
        self.assertFalse(_title_matches('Bob', 'Bobby Jansen'))


if __name__ == '__main__':
    unittest.main()
