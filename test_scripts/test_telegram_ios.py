import unittest
from time import sleep

from puma.apps.ios.telegram.telegram import Telegram

# Fill in the udid below. Run `xcrun xctrace list devices` to see the udids. Telegram cannot be installed on a
# simulator.
device_udids = {
    "Alice": ""
}
# Real devices need the signing settings of WebDriverAgent, see docs/setup-ios.md
desired_capabilities = {
    # "appium:xcodeOrgId": "<your team id>",
    # "appium:xcodeSigningId": "Apple Development",
}

# The contact the test messages are sent to
CONTACT = "Bob"


class TestTelegramIOS(unittest.TestCase):
    """
    With this test, you can check whether all Appium functionality works for the current version of Telegram on iOS.
    The test can only be run manually, as you need a real iOS device with Telegram.

    Prerequisites:
    - All prerequisites mentioned in the README.
    - Alice: an iOS device with Telegram registered, with CONTACT in its contacts.
    - At least one photo that Telegram has access to, and access to the location.
    - Note that some tests send a photo and the location of the device to CONTACT.
    - For the recovery tests, a screen with someone else than CONTACT is not used, to not touch other chats.
    """

    @classmethod
    def setUpClass(self):
        if not device_udids["Alice"]:
            print("No udid was configured for Alice. Please add at the top of the script.\nExiting....")
            exit(1)
        self.alice = Telegram(device_udids["Alice"], desired_capabilities=desired_capabilities)

    def test_send_and_read_messages(self):
        self.alice.send_message("Puma test, with a comma", conversation=CONTACT)
        sent = self.alice.get_messages(CONTACT)[-1]
        self.assertEqual((None, "Puma test, with a comma", "message"), (sent.sender, sent.text, sent.kind))

    def test_send_message_in_open_conversation(self):
        self.alice.send_message("Puma test, first", conversation=CONTACT)
        self.alice.send_message("Puma test, second")
        self.assertEqual("Puma test, second", self.alice.get_messages()[-1].text)

    def test_send_media_from_gallery(self):
        self.alice.send_media_from_gallery(1, caption="Puma test, photo", conversation=CONTACT)
        sent = self.alice.get_messages()[-1]
        self.assertEqual(("Puma test, photo", "photo"), (sent.text, sent.kind))

    def test_send_current_location(self):
        self.alice.send_current_location(conversation=CONTACT)
        self.assertEqual("Location", self.alice.get_messages()[-1].text)

    def _open_tab(self, tab: str):
        """
        Opens a tab of Telegram. The tab bar is not in the element tree, so the tabs are tapped at fixed fractions of
        the screen: Contacts, Calls, Chats and Settings are spread over the width of the tab bar.
        """
        driver = self.alice.driver
        size = driver.driver.get_window_size()
        x = {"Contacts": 0.17, "Calls": 0.39, "Chats": 0.61, "Settings": 0.83}[tab]
        driver.driver.execute_script("mobile: tap", {"x": size["width"] * x, "y": size["height"] * 0.93})
        sleep(2.5)

    def test_recover_when_telegram_is_on_another_tab(self):
        # a new Telegram object does not know where the app was left, so it has to recognize that it is not on the
        # chats list: the Contacts tab has a search field just like the chats list
        for tab in ("Contacts", "Settings", "Calls"):
            self._open_tab(tab)
            alice = Telegram(device_udids["Alice"], desired_capabilities=desired_capabilities)
            alice.send_message(f"Puma test, after the {tab} tab", conversation=CONTACT)
            self.assertEqual(f"Puma test, after the {tab} tab", alice.get_messages()[-1].text)

    def test_recover_more_than_once_with_the_same_object(self):
        # the framework restarts the app only once, but Telegram can end up on another tab again later
        for tab in ("Contacts", "Settings", "Contacts"):
            self._open_tab(tab)
            self.alice.send_message(f"Puma test, again after the {tab} tab", conversation=CONTACT)
            self.assertEqual(f"Puma test, again after the {tab} tab", self.alice.get_messages()[-1].text)

    def test_recover_when_telegram_is_in_a_chat(self):
        self.alice.send_message("Puma test, open the chat", conversation=CONTACT)
        alice = Telegram(device_udids["Alice"], desired_capabilities=desired_capabilities)
        alice.send_message("Puma test, after a new object", conversation=CONTACT)
        self.assertEqual("Puma test, after a new object", alice.get_messages()[-1].text)

    def test_unknown_conversation(self):
        from puma.apps.ios.telegram.telegram import TelegramError
        with self.assertRaises(TelegramError):
            self.alice.send_message("Puma test", conversation="A name nobody has, 5f0e1a")


if __name__ == '__main__':
    unittest.main()
