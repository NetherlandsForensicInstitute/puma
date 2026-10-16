---
name: explore-ui
description: Explore the UI of an app on a connected phone directly over adb (Android) or WebDriverAgent (iOS), without starting an Appium session. Use this when you need to see what is on the screen of the device, find or check XPaths and locators, work out the states and transitions of an app, add or update a Puma app for a new app version, or debug why a state or locator no longer matches.
---

# Exploring the UI of a device

Puma drives apps through Appium at runtime. To find out what a screen looks like and which locators work, you do not
need Appium: starting a session takes several seconds, and each lookup is a round trip. Reading the UI hierarchy
straight from the device is faster, needs no Appium server, and gives you the whole screen at once.

Use this to explore. The code you write still runs through Appium, so finish by running it with Puma (see
[Finishing](#finishing)).

## Before you start

- You are operating a real phone, often with real accounts on it. Reading the screen is always fine. Tapping only
  navigates when you know what the element does: do not send messages, place calls, delete things or change settings
  unless the task asks for it.
- Check that nobody else is using the device. If a Puma script is running against it, your taps break that run.
- Leave the device as you found it: go back to the home screen when you are done.
- The device must be unlocked with its screen on, and its language set to English.

## Android

`adb devices` lists the connected devices. With more than one, pass the serial: `adb -s <serial> ...` and
`python ui.py -s <serial> ...`.

### Reading the screen

[scripts/ui.py](scripts/ui.py) dumps the hierarchy with `uiautomator dump` and prints it in the shape of the Appium
page source: the class of an element is its tag, so XPaths that match here are the XPaths you put in `xpaths.py`.

```bash
python .claude/skills/explore-ui/scripts/ui.py tree                      # elements with a text, content-desc or resource-id
python .claude/skills/explore-ui/scripts/ui.py tree --package org.telegram.messenger
python .claude/skills/explore-ui/scripts/ui.py tree --all                # every element
python .claude/skills/explore-ui/scripts/ui.py xml > screen.xml          # the full hierarchy
python .claude/skills/explore-ui/scripts/ui.py focus                     # package and activity in the foreground
```

`tree` prints one line per element, indented by depth, starting with the window in focus:

```
mCurrentFocus=Window{2586439 u0 com.android.settings/com.android.settings.Settings}
    w.TextView text='Network & internet' id='android:id/title' [221,644][601,700]
    w.ImageButton desc='Navigate up' [21,118][168,265] clickable
```

`w.` stands for `android.widget.`, `v.` for `android.view.`. `[left,top][right,bottom]` are the bounds in pixels.

A dump takes two to three seconds. Start with `tree`; use `--all` or `xml` when you need the structure around an
element (parents, siblings) to build an XPath.

### Checking XPaths

`find` evaluates XPaths against the current screen, `tap` taps the first match. Both need lxml (`pip install lxml`),
which is not a dependency of Puma: install it in your own environment.

```bash
python .claude/skills/explore-ui/scripts/ui.py find "//android.widget.TextView[@resource-id='android:id/title']" "//*[@content-desc='Navigate up']"
python .claude/skills/explore-ui/scripts/ui.py tap "//*[@content-desc='Navigate up']"
```

Pass several XPaths to `find` to check them against one dump, for example all XPaths of a state. A state needs XPaths
that all match on its screen, and that do not all match on any other screen: check both.

Appium evaluates XPath 2.0, lxml only XPath 1.0. `ui.py` adds the XPath 2.0 functions Puma uses (`lower-case`,
`upper-case`, `ends-with`, `matches`). Other XPath 2.0 features are reported as an invalid XPath here, while they may
work in Appium.

Quoting, as shells change XPaths before `ui.py` sees them. `find` prints each XPath as it received it, so check that
line when you get 0 matches you did not expect.

- Use double quotes around the XPath and single quotes inside it. Windows PowerShell removes double quotes inside an
  argument.
- In Git Bash on Windows, put `MSYS_NO_PATHCONV=1` in front of the command. Without it, Git Bash rewrites arguments that
  look like a path: `//android.widget.Button` arrives as `/android.widget.Button` and matches nothing, and
  `adb shell ls /sdcard` looks in `C:/Program Files/Git/sdcard`.

### Operating the device

```bash
adb shell monkey -p <package> -c android.intent.category.LAUNCHER 1   # open an app
adb shell am force-stop <package>                                     # close an app
adb shell input tap <x> <y>
adb shell input swipe 540 1800 540 600 300                            # scroll down: x1 y1 x2 y2 duration in ms
adb shell input swipe <x> <y> <x> <y> 1500                            # long press
adb shell input text 'hello'                                          # type in the focused field, %s for a space
adb shell input keyevent KEYCODE_BACK                                 # also KEYCODE_HOME, KEYCODE_ENTER, KEYCODE_DEL
adb shell am start -a android.intent.action.VIEW -d <url>             # open a url
adb shell "dumpsys package <package> | grep versionName"              # the installed version of an app (the first line)
adb shell pm list packages -3                                         # installed apps
adb shell wm size                                                     # screen size
```

After each action, dump again: the previous dump says nothing about the new screen. `ui.py tree` shows the window in
focus first, which tells you whether you are still in the app, or in a pop-up or another app.

When the hierarchy does not explain what you see (images, canvas or web content without texts), take a screenshot and
look at it:

```bash
adb exec-out screencap -p > screen.png
```

In Windows PowerShell this corrupts the file. Use this instead:

```powershell
adb shell screencap -p /sdcard/screen.png; adb pull /sdcard/screen.png; adb shell rm /sdcard/screen.png
```

### When the dump fails

- **An Appium session exists.** Android allows one UI automation connection at a time. After a Puma script has run,
  the UiAutomator2 server of Appium (`io.appium.uiautomator2.server`) stays on the device, and `uiautomator dump` is
  killed. This does not harm the Appium session. `ui.py` then reads the page source from that server instead, and says
  so on stderr. This only works as long as the Appium session exists. If `ui.py` reports that it could not dump the
  hierarchy and you are sure no script is using the device, stop the server with
  `adb shell am force-stop io.appium.uiautomator2.server`. This breaks a Puma script that is still running; a script
  started afterwards starts the server again.
- **The screen does not become idle.** `uiautomator dump` waits for the UI to stop changing, and fails with
  `could not get idle state` on screens that keep animating (video, a camera preview, a spinner). Wait, pause the
  animation, or fall back to a screenshot.
- **The screen is off or locked.** The dump then shows the lock screen or nothing.

### Differences with Appium

- The Appium page source has extra attributes (`displayed`, `a11y-important`, `heading` and others) that
  `uiautomator dump` does not have. Do not use them in XPaths you have only tested here.
- `adb shell input tap` taps a position, as does a click in Puma (the center of the element). An element that is
  covered by another element receives neither.
- WebViews are only in the hierarchy as far as the app exposes them to accessibility.

## iOS

Verified on a real iPhone (iPhone 15 Pro, iOS 26.6.2, WebDriverAgent 16.12.10): reading the screen, all four locator
strategies, tapping, clicking, dragging, the home button and launching an app. Not verified: creating a WDA session,
`touchAndHold`, `terminate` and the `simctl` commands. Check those before relying on them, and correct this file when
they are wrong.

iOS needs a Mac with Xcode. There is no counterpart of `uiautomator dump`: the UI hierarchy is only available through
WebDriverAgent (WDA), the XCTest app that Appium installs on the device. WDA is an HTTP server, and it keeps running
after the Appium session that started it has ended. You can ask it for the screen directly, and operate the device
through it, without Appium.

Puma gives each device its own local WDA port:

```bash
python -c "from puma.state_graph.ios_driver import wda_ports; print(wda_ports('<udid>')[0])"
curl -s http://127.0.0.1:<port>/status
```

If `/status` does not answer, WDA is not running or the port is no longer forwarded. Running any Puma iOS app once
(for example a test in `test_scripts`) starts WDA and forwards the port. See [Setting up iOS](../../../docs/setup-ios.md)
for the UDID and signing.

```bash
curl -s http://127.0.0.1:<port>/source | python -c "import sys, json; print(json.load(sys.stdin)['value'])" > screen.xml
curl -s "http://127.0.0.1:<port>/source?format=description"    # compact text tree
curl -s http://127.0.0.1:<port>/wda/activeAppInfo              # bundle id of the app in the foreground
curl -s http://127.0.0.1:<port>/screenshot | python -c "import sys, json, base64; open('screen.png', 'wb').write(base64.b64decode(json.load(sys.stdin)['value']))"
```

The XML of `/source` is the Appium page source: tags are element types (`XCUIElementTypeButton`), with `name`,
`label`, `value`, `enabled`, `visible` and the position as attributes. Use it to choose locators. Prefer
`accessibility_id`, `ios_predicate` and `ios_class_chain` over XPaths (see
[iOS applications](../../../docs/writing-apps.md#ios-applications)). Print names and labels with `repr()`: they can contain
invisible characters.

Serializing the hierarchy is slow on iOS (seconds on a full screen), and only elements on or near the screen are in
it.

On a simulator, `xcrun simctl` can also do the following without WDA. It cannot read the hierarchy or tap:

```bash
xcrun simctl list devices booted
xcrun simctl launch <udid> <bundle id>
xcrun simctl terminate <udid> <bundle id>
xcrun simctl openurl <udid> <url>
xcrun simctl io <udid> screenshot screen.png
xcrun simctl listapps <udid>
```

### Operating the device

WDA also taps, types and finds elements over HTTP, so you do not need Puma or Appium for this either. Unlike reading
the screen, these requests need a WDA session id in the url. WDA has one session at a time:

- `/status` returns the id of the current session as `sessionId`, next to `value` and not inside it. If there is one,
  use it. The session of a Puma run stays valid after the run has ended.
- Only when there is none, create one. Creating a session ends the current one, which breaks an Appium session that
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

Checking a locator, and clicking the element it finds. `using` is `accessibility id`, `predicate string`,
`class chain` or `xpath`, the strategies of `accessibility_id`, `ios_predicate`, `ios_class_chain` and plain XPaths
in Puma:

```bash
curl -s -X POST $S/elements -d '{"using": "predicate string", "value": "type == \"XCUIElementTypeButton\" AND name == \"Done\""}'
curl -s -X POST $S/element/<element id>/click
curl -s $S/element/<element id>/rect
```

`/elements` returns an id for each match, so the number of ids is the number of matches. An `accessibility id` often
matches more than one element, for example a table cell and its label: check the rects, as the first match is not always
the one you want to click. This is the same lookup
Appium does at runtime, so a locator that matches here matches in Puma.

Coordinates are in points: the screen size in points is in `curl -s $S/window/size`, and a screenshot is two or three
times as large.

## Finishing

Exploring gives you locators and the order of screens. It does not prove the Puma code works.

- Put locators in `xpaths.py` (Android) or `locators.py` (iOS) of the app, following
  [Writing Puma apps](../../../docs/writing-apps.md).
- Texts and content descriptions change with the language of the device and with app versions; resource ids change
  with app versions. Prefer `content-desc`, then `resource-id`, then text.
- Run the code through Puma on the device: the test script of the app in `test_scripts`, or the action you changed.
  A locator is done when it works there.
