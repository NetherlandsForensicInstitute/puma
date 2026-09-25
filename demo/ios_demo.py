"""
Demo of Puma on iOS: sending and reading messages in Messages.

Run from the root of the repository, with an Appium server running:

    # on a simulator
    python -m demo.ios_demo --udid <simulator udid>
    # on a real device (see the README for preparing the device)
    python -m demo.ios_demo --udid <device udid> --team-id <team id> --wda-bundle-id com.<you>.WebDriverAgentRunner \
        --conversation "<a contact of your own>"

On a simulator, the demo uses the two conversations a simulator starts with: messages sent in one of them are received
in the other. On a real device, the demo only sends a message when a conversation is given with --conversation.

On a real device, the screen would lock during the demo, and iOS does not start apps on a locked device. Therefore
Auto-Lock is set to Never during the demo, and restored to its original value afterwards.
"""
import argparse
from contextlib import contextmanager

from puma.apps.ios.messages.messages import Messages
from puma.apps.ios.settings.settings import Settings

# The two conversations a simulator starts with. Messages sent in one of them are received in the other.
SIMULATOR_CONVERSATION = "+1 (888) 555-1212"
SIMULATOR_OTHER_CONVERSATION = "+1 (555) 564-8583"


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


def messages_demo(udid: str, capabilities: dict, conversation: str = None):
    messages = Messages(udid, desired_capabilities=capabilities)
    simulator = messages.driver.is_simulator()
    if conversation is None:
        if not simulator:
            say("Messages: skipped, give a conversation of your own with --conversation to send a message")
            return
        conversation = SIMULATOR_CONVERSATION
    say(f"Messages: send a message to {conversation}")
    messages.send_message("Hello from Puma!", conversation=conversation)
    say(f"Messages: the last messages read back from the screen: {messages.get_messages(conversation)[-3:]}")
    if simulator:
        say(f"Messages: the message is received in the other conversation of the simulator: "
            f"{messages.get_messages(SIMULATOR_OTHER_CONVERSATION)[-1]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo of Puma on iOS (Messages)")
    parser.add_argument("--udid", required=True,
                        help="udid of the device, see `xcrun simctl list devices booted` or `xcrun xctrace list devices`")
    parser.add_argument("--team-id", help="real devices only: your Apple developer team id, used to sign WebDriverAgent")
    parser.add_argument("--wda-bundle-id", help="real devices only: a bundle id of your own for WebDriverAgent, "
                                                "needed with a free Apple developer account")
    parser.add_argument("--conversation", help="the conversation to send a message to. Required on real devices, on a "
                                               "simulator one of the conversations it starts with is used")
    args = parser.parse_args()

    capabilities = get_capabilities(args)
    with screen_stays_on(args.udid, capabilities):
        messages_demo(args.udid, capabilities, args.conversation)
    say("Done!")
