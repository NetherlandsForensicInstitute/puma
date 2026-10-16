# Exploring an iOS device

iOS needs a Mac with Xcode. On another system you cannot run any of this: say so, instead of assuming it works.

Verified on a real iPhone (iPhone 15 Pro, iOS 26.6.2, WebDriverAgent 16.12.10): reading the screen, all four locator
strategies, tapping, clicking, dragging, the home button and launching an app. Not verified: creating a WDA session,
`touchAndHold`, `terminate` and the `simctl` commands. Check those before relying on them, and correct this file when
they are wrong.

There is no counterpart of `uiautomator dump`: the UI hierarchy is only available through WebDriverAgent (WDA), the
XCTest app that Appium installs on the device. WDA is an HTTP server, and it keeps running after the Appium session that
started it has ended. You can ask it for the screen directly, and operate the device through it, without Appium.

## Connecting to WDA

Puma gives each device its own local WDA port:

```bash
python -c "from puma.state_graph.ios_driver import wda_ports; print(wda_ports('<udid>')[0])"
curl -s http://127.0.0.1:<port>/status
```

`xcrun xctrace list devices` lists the UDIDs (not the identifiers of `xcrun devicectl list devices`). If `/status` does
not answer, WDA is not running or the port is no longer forwarded. Running any Puma iOS app once (for example a test in
`test_scripts`) starts WDA and forwards the port. See [Setting up iOS](../../../../docs/setup-ios.md) for the UDID and
signing.

## Reading the screen

```bash
curl -s http://127.0.0.1:<port>/source | python -c "import sys, json; print(json.load(sys.stdin)['value'])" > screen.xml
curl -s "http://127.0.0.1:<port>/source?format=description"    # compact text tree
curl -s http://127.0.0.1:<port>/wda/activeAppInfo              # bundle id of the app in the foreground
curl -s http://127.0.0.1:<port>/screenshot | python -c "import sys, json, base64; open('screen.png', 'wb').write(base64.b64decode(json.load(sys.stdin)['value']))"
```

The XML of `/source` is the Appium page source: tags are element types (`XCUIElementTypeButton`), with `name`,
`label`, `value`, `enabled`, `visible` and the position as attributes. Use it to choose locators. Prefer
`accessibility_id`, `ios_predicate` and `ios_class_chain` over XPaths (see
[iOS applications](../../../../docs/writing-apps.md#ios-applications)). Print names and labels with `repr()`: they can
contain invisible characters.

Serializing the hierarchy is slow on iOS (seconds on a full screen), and only elements on or near the screen are in it.

On a simulator, `xcrun simctl` does the following without WDA. It cannot read the hierarchy or tap:

```bash
xcrun simctl list devices booted
xcrun simctl launch <udid> <bundle id>
xcrun simctl terminate <udid> <bundle id>
xcrun simctl openurl <udid> <url>
xcrun simctl io <udid> screenshot screen.png
xcrun simctl listapps <udid>
```

## Operating the device

WDA also taps, types and finds elements over HTTP, so you do not need Puma or Appium for this either. Unlike reading
the screen, these requests need a WDA session id in the url. WDA has one session at a time:

- `/status` returns the id of the current session as `sessionId`, next to `value` and not inside it. If there is one,
  use it. The session of a Puma run stays valid after the run has ended.
- Create a session only when there is none. Creating a session ends the current one, which breaks an Appium session that
  is still in use.

```bash
WDA=http://127.0.0.1:<port>
curl -s $WDA/status                                             # "sessionId" is the current session, if any
curl -s -X POST $WDA/session -d '{"capabilities": {}}'          # create a session, only when there is none
S=$WDA/session/<session id>

curl -s -X POST $S/wda/tap -d '{"x": 200, "y": 400}'            # coordinates in points, not pixels
curl -s -X POST $S/wda/touchAndHold -d '{"x": 200, "y": 400, "duration": 1.5}'
curl -s -X POST $S/wda/dragfromtoforduration -d '{"fromX": 200, "fromY": 600, "toX": 200, "toY": 200, "duration": 0.3}'
curl -s -X POST $S/wda/keys -d '{"value": ["hello"]}'           # type in the focused field
curl -s -X POST $S/wda/pressButton -d '{"name": "home"}'
curl -s -X POST $S/wda/apps/launch -d '{"bundleId": "<bundle id>"}'
curl -s -X POST $S/wda/apps/terminate -d '{"bundleId": "<bundle id>"}'
```

Check a locator, and click the element it finds. `using` is `accessibility id`, `predicate string`, `class chain` or
`xpath`, the strategies of `accessibility_id`, `ios_predicate`, `ios_class_chain` and plain XPaths in Puma:

```bash
curl -s -X POST $S/elements -d '{"using": "predicate string", "value": "type == \"XCUIElementTypeButton\" AND name == \"Done\""}'
curl -s -X POST $S/element/<element id>/click
curl -s $S/element/<element id>/rect
```

`/elements` returns an id for each match, so the number of ids is the number of matches. This is the same lookup
Appium does at runtime, so a locator that matches here matches in Puma. An `accessibility id` often matches more than
one element, for example a table cell and its label: check the rects, as the first match is not always the one you want
to click.

Coordinates are in points: the screen size in points is in `curl -s $S/window/size`, and a screenshot is two or three
times as large.
