"""
Demo of Puma on iOS: a few actions in Safari, Contacts and Apple Maps.

Run from the root of the repository, with an Appium server running:

    # on a simulator
    python -m demo.ios_demo --udid <simulator udid>
    # on a real device (see the README for preparing the device)
    python -m demo.ios_demo --udid <device udid> --team-id <team id> --wda-bundle-id com.<you>.WebDriverAgentRunner

Everything the demo creates is cleaned up afterwards: the bookmark and the contact are deleted, and the simulated
location is reset. A new tab with example.com stays open in Safari.
"""
import argparse
import time

from geopy import Point

from puma.apps.ios.apple_maps.apple_maps import AppleMaps, TransportType
from puma.apps.ios.contacts.contacts import Contacts
from puma.apps.ios.safari.safari import Safari, PrivateBrowsingLockedError


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
        say("Maps: move the device to the Louvre with the route simulator")
        route = maps.get_route_simulator()
        route.update_speed(0)
        route.execute_route_with_points([Point(48.8606, 2.3376)])
        time.sleep(2)
        route.stop_route()
        say("Maps: search for the Eiffel Tower")
        maps.search_place("Eiffel Tower")
        time.sleep(2)
        say("Maps: cycling directions to the Eiffel Tower")
        maps.get_directions("Eiffel Tower", TransportType.BIKE)
    finally:
        # on a real device, the simulated location stays active until it is reset
        say("Maps: resetting the device location")
        try:
            maps.driver.execute_script("mobile: resetSimulatedLocation")
        except Exception as e:
            print(f"Could not reset the location: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo of Puma on iOS (Safari, Contacts and Apple Maps)")
    parser.add_argument("--udid", required=True,
                        help="udid of the device, see `xcrun simctl list devices booted` or `xcrun xctrace list devices`")
    parser.add_argument("--team-id", help="real devices only: your Apple developer team id, used to sign WebDriverAgent")
    parser.add_argument("--wda-bundle-id", help="real devices only: a bundle id of your own for WebDriverAgent, "
                                                "needed with a free Apple developer account")
    args = parser.parse_args()

    capabilities = get_capabilities(args)
    safari_demo(args.udid, capabilities)
    contacts_demo(args.udid, capabilities)
    maps_demo(args.udid, capabilities)
    say("Done!")
