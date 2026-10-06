import unittest

from puma.apps.ios.whatsapp.whatsapp import Message, _parse_message, _parse_messages

SENT = '\u200eYour message, {text}, 16:08, \u200eSent to Bob, \u200e{status}'
RECEIVED = '\u200emessage, {text}, 16:05, \u200eReceived from Bob'


def _cell(label: str, cell: str = 'WAMessageBubbleTableViewCell') -> str:
    return (f'<XCUIElementTypeCell type="XCUIElementTypeCell" name="{cell}">'
            f'<XCUIElementTypeOther type="XCUIElementTypeOther" name="{label}" label="{label}"/>'
            f'</XCUIElementTypeCell>')


class TestWhatsAppParsing(unittest.TestCase):
    def test_parse_sent_message(self):
        message = _parse_message(SENT.format(text='Hi, how are you?', status='Delivered'))
        self.assertEqual(Message(None, 'Hi, how are you?', '16:08', 'Delivered'), message)
        self.assertTrue(message.sent_by_me)
        self.assertEqual('message', message.kind)

    def test_parse_received_message(self):
        message = _parse_message(RECEIVED.format(text='Fine, thanks!'))
        self.assertEqual(Message('Bob', 'Fine, thanks!', '16:05'), message)
        self.assertFalse(message.sent_by_me)

    def test_parse_statuses(self):
        for status in ('Sent', 'Delivered', 'Read'):
            self.assertEqual(status, _parse_message(SENT.format(text='Hi', status=status)).status)
        # WhatsApp spells Read as Red
        self.assertEqual('Read', _parse_message(SENT.format(text='Hi', status='Red')).status)

    def test_parse_deleted_message(self):
        message = _parse_message('\u200emessage, \u200eYou deleted this message., 16:43, \u200eSent to Bob')
        self.assertEqual((None, 'You deleted this message.', None), (message.sender, message.text, message.status))

    def test_parse_reply(self):
        label = ('\u200eReplying to \u200eYou.\n'
                 '\u200eYour message, A reply, 16:44, \u200eSent to Bob, \u200eDelivered.\n'
                 '\u200eQuoted message.\nThe question, with a comma')
        message = _parse_message(label)
        self.assertEqual(('A reply', 'Delivered', True, 'The question, with a comma'),
                         (message.text, message.status, message.is_reply, message.reply_to))

    def test_parse_other_kinds(self):
        contact = _parse_message('\u200eYour contact, Alice, 16:49, \u200eSent to Bob, \u200eSent')
        self.assertEqual(('contact', 'Alice'), (contact.kind, contact.text))
        location = _parse_message('\u200eYour location, 16:51, \u200eSent to Bob, \u200eSent')
        self.assertEqual(('location', '', '16:51'), (location.kind, location.text, location.time))
        # WhatsApp spells live location with a double l
        live = _parse_message('\u200eYour llive location: \u200eLlive until 17:51, A caption, 16:51, '
                              '\u200eSent to Bob, \u200eSent')
        self.assertEqual(('live location', 'A caption'), (live.kind, live.text))
        photo = _parse_message('\u200eYour photo, A caption, 16:55, \u200eSent to Bob, \u200eSent')
        self.assertEqual(('photo', 'A caption'), (photo.kind, photo.text))

    def test_parse_received_kinds(self):
        photo = _parse_message('\u200eView once photo, 13:37, \u200eReceived from Bob, \u200eOpened')
        self.assertEqual(('view once photo', 'Bob'), (photo.kind, photo.sender))
        call = _parse_message('\u200eVoice call , \u200e7 sec, 10:56, \u200eReceived from Bob')
        self.assertEqual(('voice call', '7 sec', 'Bob'), (call.kind, call.text, call.sender))

    def test_parse_voice_message_without_chat(self):
        message = _parse_message('\u200eYour voice message, \u200eDuration: 2 seconds, 16:58, \u200eSent')
        self.assertEqual(('voice message', 'Duration: 2 seconds', '16:58', 'Sent'),
                         (message.kind, message.text, message.time, message.status))
        self.assertTrue(message.sent_by_me)

    def test_ignore_other_labels(self):
        self.assertIsNone(_parse_message('\u200e\u200eMessages and calls are end-to-end encrypted.'))
        self.assertIsNone(_parse_message('\u200eToday'))

    def test_parse_messages_of_chat(self):
        source = ('<AppiumAUT><XCUIElementTypeTable type="XCUIElementTypeTable" name="ChatMessagesTableView">'
                  + _cell('\u200e\u200eMessages and calls are end-to-end encrypted.')
                  + _cell(RECEIVED.format(text='Hello'))
                  + _cell('\u200e1 unread message', cell='\u200e1 unread message')
                  + _cell(SENT.format(text='Hi', status='Read'))
                  + '</XCUIElementTypeTable></AppiumAUT>')
        self.assertEqual([Message('Bob', 'Hello', '16:05'), Message(None, 'Hi', '16:08', 'Read')],
                         _parse_messages(source))


if __name__ == '__main__':
    unittest.main()
