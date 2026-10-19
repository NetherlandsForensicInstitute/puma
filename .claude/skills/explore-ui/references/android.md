# Exploring an Android device

`adb devices` lists the connected devices. With more than one, pass the serial to both tools: `adb -s <serial> ...` and
`python ui.py -s <serial> ...`.

## Reading the screen

[ui.py](../scripts/ui.py) dumps the hierarchy with `uiautomator dump` and prints it in the shape of the Appium page
source: the class of an element is its tag, so an XPath that matches here goes into `xpaths.py` as it is.

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

## Checking XPaths

`find` evaluates XPaths against the current screen, `tap` taps the first match. Both need lxml (`pip install lxml`),
which is not a dependency of Puma: install it in your own environment.

```bash
python .claude/skills/explore-ui/scripts/ui.py find "//android.widget.TextView[@resource-id='android:id/title']" "//*[@content-desc='Navigate up']"
python .claude/skills/explore-ui/scripts/ui.py tap "//*[@content-desc='Navigate up']"
```

Pass all XPaths of a state to one `find`, so they are checked against one dump. A state is done when all its XPaths
match on its own screen and not all of them match on any other screen: check both.

Appium evaluates XPath 2.0, lxml only XPath 1.0. `ui.py` adds the XPath 2.0 functions Puma uses (`lower-case`,
`upper-case`, `ends-with`, `matches`). Other XPath 2.0 features are reported as an invalid XPath here, while they may
work in Appium.

Shells change XPaths before `ui.py` sees them. `find` prints each XPath as it received it: read that line when you get
0 matches you did not expect.

- Put double quotes around the XPath and single quotes inside it. Windows PowerShell removes double quotes inside an
  argument.
- In Git Bash on Windows, put `MSYS_NO_PATHCONV=1` in front of the command. Without it, Git Bash rewrites arguments that
  look like a path: `//android.widget.Button` arrives as `/android.widget.Button` and matches nothing, and
  `adb shell ls /sdcard` looks in `C:/Program Files/Git/sdcard`.

## Operating the device

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

Dump again after each action: the previous dump says nothing about the new screen. `ui.py tree` shows the window in
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

## When the dump fails

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

## Differences with Appium

- The Appium page source has extra attributes (`displayed`, `a11y-important`, `heading` and others) that
  `uiautomator dump` does not have. Use only the attributes `ui.py tree` prints in XPaths you test here.
- `adb shell input tap` taps a position, as does a click in Puma (the center of the element). An element that is
  covered by another element receives neither.
- WebViews are only in the hierarchy as far as the app exposes them to accessibility.
