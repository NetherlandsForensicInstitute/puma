import random
from time import sleep

from puma.apps.android.teleguard.teleguard import TeleGuard

BLACK_PIXEL = ''

if __name__ == '__main__':
    teleguard = TeleGuard(BLACK_PIXEL)

    with open('hello_messages.txt', 'r') as f:
        hello_messages = f.read().splitlines()
    with open('chat_responses.txt', 'r') as f:
        responses = f.read().splitlines()

    while True:
        # check for invites
        if teleguard.invite_received():
            name = teleguard.accept_invite()
            teleguard.send_message(random.choice(hello_messages), conversation=name)
        # check for unread messages
        conversations_with_unread_messages = teleguard.conversations_with_unread_messages()
        for conversation in conversations_with_unread_messages:
            teleguard.send_message(random.choice(responses), conversation=conversation)
        teleguard.go_to_state(teleguard.conversations_state)
        print('nothing to do, sleeping...')
        sleep(5)
