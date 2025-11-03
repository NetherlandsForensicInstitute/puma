import time

from puma.apps.android.google_maps.google_maps import GoogleMapsActions
from puma.apps.android.telegram.telegram import Telegram

if __name__ == '__main__':
    bob_maps = GoogleMapsActions('34281JEHN03866')
    bob_telegram = Telegram('34281JEHN03866')
    charlie_telegram = Telegram('32131JEHN38079')

    # send messages
    bob_telegram.go_to_state(Telegram.chat_state, conversation='Charlie')
    charlie_telegram.go_to_state(Telegram.chat_state, conversation='Bob')

    bob_telegram.send_message('Hey Charlie!',conversation='Charlie')
    bob_telegram.send_message('I\'m heading to the office now')
    bob_telegram.driver.back()
    charlie_telegram.send_message('Ok, see you soon!', conversation='Bob')

    # start navigation
    time.sleep(1)
    bob_maps.activate_app()
    bob_maps.start_route(from_query="Schiphol Airport",
                         to_query="Laan van Ypenburg 6, Den Haag",
                         speed=55)
    bob_maps.route_simulator.update_speed(50, variance_absolute=5)
    time.sleep(10)

    # send a picture from device
    charlie_telegram.send_message('Bob, we might have a problem...')
    charlie_telegram.send_media_from_gallery(media_index=1, caption="The servers don't look great, we need you here ASAP!")

    # change speed
    time.sleep(2)
    bob_telegram.driver.activate_app()
    time.sleep(4)
    bob_maps.activate_app()
    bob_maps.route_simulator.update_speed(180, variance_absolute=10)
    time.sleep(100)

