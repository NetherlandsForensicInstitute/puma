"""
Demo of Puma on iOS: a few actions in Safari, Contacts, Apple Maps, Calendar and Reminders.

Run from the root of the repository, with an Appium server running:

    # on a simulator
    python -m demo.ios_demo --udid <simulator udid>
    # on a real device (see the README for preparing the device)
    python -m demo.ios_demo --udid <device udid> --team-id <team id> --wda-bundle-id com.<you>.WebDriverAgentRunner
    # only some of the apps
    python -m demo.ios_demo --udid <udid> --apps calendar reminders

Everything the demo creates is cleaned up afterwards: the bookmark, contact, event, reminders and list are deleted, and
the simulated location is reset. A new tab with example.com stays open in Safari.

On a real device, the screen would lock during the demo, and iOS does not start apps on a locked device. Therefore
Auto-Lock is set to Never during the demo, and restored to its original value afterwards.
"""
import argparse
import time
from contextlib import contextmanager
from datetime import datetime, timedelta

from puma.apps.ios.apple_maps.apple_maps import AppleMaps, TransportType
from puma.apps.ios.calendar.calendar import Calendar
from puma.apps.ios.contacts.contacts import Contacts
from puma.apps.ios.reminders.reminders import Reminders
from puma.apps.ios.safari.safari import Safari, PrivateBrowsingLockedError
from puma.apps.ios.settings.settings import Settings


def say(text):
    print(f"\n>>> {text}", flush=True)


def get_capabilities(args) -> dict:
    """
    Real devices need the signing settings for WebDriverAgent. With a free Apple developer account, WebDriverAgent needs
    a bundle id of your own.
    """
    if not args.team_id:
        return {}
    capabilities = {
        "appium:xcodeOrgId": args.team_id,
        "appium:xcodeSigningId": "Apple Development",
        "appium:allowProvisioningDeviceRegistration": True,
    }
    if args.wda_bundle_id:
        capabilities["appium:updatedWDABundleId"] = args.wda_bundle_id
    return capabilities


def describe_auto_lock(seconds) -> str:
    return 'Never' if seconds is None else f'{seconds} seconds'


@contextmanager
def screen_stays_on(udid: str, capabilities: dict):
    """
    Keeps the screen of a real device on during the demo, by setting Auto-Lock to Never. Afterwards, Auto-Lock is
    restored to its original value, also when the demo fails. Simulators do not lock, so nothing changes on a simulator.
    """
    settings = Settings(udid, desired_capabilities=capabilities)
    if settings.driver.is_simulator():
        yield
        return
    original = settings.get_auto_lock()
    say(f"Settings: Auto-Lock is {describe_auto_lock(original)}, setting it to Never during the demo")
    settings.set_auto_lock(None)
    try:
        yield
    finally:
        say(f"Settings: restoring Auto-Lock to {describe_auto_lock(original)}")
        settings.set_auto_lock(original)


def safari_demo(udid: str, capabilities: dict):
    safari = Safari(udid, desired_capabilities=capabilities)
    say("Safari: open example.com in a new tab")
    safari.visit_url_new_tab("example.com")
    say("Safari: bookmark it, then open it again from the bookmarks")
    safari.bookmark_page()
    safari.load_bookmark("Example Domain")
    say("Safari: clean up the bookmark")
    safari.delete_bookmark("Example Domain")
    say("Safari: visit a page in a private tab")
    try:
        safari.visit_url_private("wikipedia.org")
    except PrivateBrowsingLockedError as e:
        say(f"Safari: skipped private tab: {e}")


def contacts_demo(udid: str, capabilities: dict):
    contacts = Contacts(udid, desired_capabilities=capabilities)
    say("Contacts: add Alice Demo")
    contacts.add_contact("Alice", "Demo", phone_number="+31612345678", email="alice@example.com", company="NFI")
    say(f"Contacts: details read back from the screen: {contacts.get_contact_details('Alice Demo')}")
    time.sleep(2)
    say("Contacts: delete Alice Demo")
    contacts.delete_contact("Alice Demo")


def maps_demo(udid: str, capabilities: dict):
    maps = AppleMaps(udid, desired_capabilities=capabilities)
    try:
        say("Maps: search for the Eiffel Tower")
        maps.search_place("Eiffel Tower")
        time.sleep(2)
        say("Maps: cycle from the Louvre to the Eiffel Tower (4 km), at 100 km/h to keep the demo short")
        maps.start_route("Louvre, Paris", "Eiffel Tower, Paris", 100, TransportType.BIKE)
        route = maps.get_route_simulator()
        time.sleep(15)
        say("Maps: speeding up to 250 km/h")
        route.update_speed(250)
        arrived = route.wait_until_route_finished(timeout=90)
        say("Maps: arrived at the Eiffel Tower" if arrived else "Maps: not there yet, stopping the route")
        time.sleep(3)
    finally:
        # on a real device, the simulated location stays active until it is reset
        say("Maps: stopping the route and resetting the device location")
        try:
            maps.stop_route()
        except Exception as e:
            print(f"Could not reset the location: {e}")


def calendar_demo(udid: str, capabilities: dict):
    calendar = Calendar(udid, desired_capabilities=capabilities)
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=30, second=0, microsecond=0)
    say("Calendar: plan a meeting tomorrow at 14:30")
    calendar.add_event("Puma demo meeting", tomorrow, tomorrow + timedelta(hours=1), location="NFI The Hague")
    say(f"Calendar: details read back from the screen: {calendar.get_event_details('Puma demo meeting')}")
    time.sleep(2)
    say("Calendar: delete the meeting")
    calendar.delete_event("Puma demo meeting")


def reminders_demo(udid: str, capabilities: dict):
    reminders = Reminders(udid, desired_capabilities=capabilities)
    due = (datetime.now() + timedelta(days=2)).replace(hour=9, minute=0)
    say("Reminders: add a reminder, and one with notes and a due date")
    reminders.add_reminder("Puma demo: buy milk")
    reminders.add_reminder("Puma demo: dentist", notes="Bring insurance card", due=due, due_time=True)
    say(f"Reminders: reminders read back from the screen: {reminders.get_reminders()}")
    say("Reminders: complete one, delete the other")
    reminders.complete_reminder("Puma demo: buy milk")
    reminders.delete_reminder("Puma demo: dentist")
    say("Reminders: make a shopping list")
    reminders.add_list("Puma demo groceries")
    reminders.add_reminder("Apples", list_name="Puma demo groceries")
    reminders.add_reminder("Bread", list_name="Puma demo groceries")
    say(f"Reminders: the list: {reminders.get_reminders(list_name='Puma demo groceries')}")
    time.sleep(2)
    say("Reminders: clean up the list")
    reminders.delete_list("Puma demo groceries")


DEMOS = {
    "safari": safari_demo,
    "contacts": contacts_demo,
    "maps": maps_demo,
    "calendar": calendar_demo,
    "reminders": reminders_demo,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo of Puma on iOS (Safari, Contacts, Apple Maps, Calendar and Reminders)")
    parser.add_argument("--udid", required=True,
                        help="udid of the device, see `xcrun simctl list devices booted` or `xcrun xctrace list devices`")
    parser.add_argument("--team-id", help="real devices only: your Apple developer team id, used to sign WebDriverAgent")
    parser.add_argument("--wda-bundle-id", help="real devices only: a bundle id of your own for WebDriverAgent, "
                                                "needed with a free Apple developer account")
    parser.add_argument("--apps", nargs="+", choices=DEMOS.keys(), default=list(DEMOS.keys()),
                        help="the apps to demo, all apps by default")
    args = parser.parse_args()

    capabilities = get_capabilities(args)
    with screen_stays_on(args.udid, capabilities):
        for app in args.apps:
            DEMOS[app](args.udid, capabilities)
    say("Done!")
