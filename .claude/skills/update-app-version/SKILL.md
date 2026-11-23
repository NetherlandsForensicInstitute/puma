---
name: update-app-version
description: Update a Puma app to support a newer version of the real app (WhatsApp, Telegram, TeleGuard, Snapchat, the App Store and others) - check every action on the device, fix the locators that changed, and update @supported_version, the READMEs and the release notes. Use when an issue asks to support a new app version, when Puma warns that the installed version differs from the supported version, or when actions fail after the app was updated.
---

# Supporting a new app version

An app class in Puma supports exactly one version of the real app. Updating means: every action works on the new
version, the old version is dropped, and the version is recorded in three places. Often no code changes are needed,
only the version: then the work is proving that every action still works.

## 1. Find the versions

- Supported: the `@supported_version('...')` annotation on the app class.
- Installed on Android: `adb -s <serial> shell "dumpsys package <package> | grep versionName"` (the first line). On
  iOS, `PumaDriver.get_app_version()`; Puma logs a warning with both versions when the app starts.
- The issue names the version to support. When the device has another version, say so and stop: support only a version
  you can run.

## 2. Run every action on the device

The test script of the app in `test_scripts/test_<app>.py` tests every action. It needs a running Appium server
(`appium`), and the UDIDs and account data filled in at the top. Fill them in locally and never commit them.

The test script sends messages, makes calls and changes data. Before you run it, check with the user that the devices
hold test accounts that may be used for this, and that no other script or agent uses them. Many scripts need two
devices (Alice and Bob) that know each other.

Run the whole script, or one test at a time (`python -m unittest test_scripts.test_teleguard.TestTeleGuard.test_send_message`)
to find which actions fail. Write down each action and its result: it goes in the pull request.

## 3. Fix what fails

Use [debug-puma](../debug-puma/SKILL.md) for each failure. Usually an attribute changed:

1. Open the screen where the action failed, and run `ui.py states <app class>` from
   [explore-ui](../explore-ui/SKILL.md) (Android). It lists the XPaths of each state that are missing on the screen.
2. Find the new attribute with `ui.py tree` and check the new XPath with `ui.py find` on this screen and on the screens
   next to it.
3. Change the locator in `xpaths.py` or `locators.py`. Keep the preference `content-desc`, `resource-id`, text.

Do not keep support for the old version: no `|` with the old XPath, no version checks. Users of an older version use an
older release of Puma. A screen that is new in this version (a new pop-up, an extra step) gets a state, a transition or
a `PopUpHandler` as in [add-feature](../add-feature/SKILL.md).

Fix every action, not only the one the issue mentions, and run the whole test script again after the last fix.

## 4. Record the version

- `@supported_version('<new version>')` on the app class.
- The row of the app in the table in [README.md](../../../README.md), and the README of the app if it names the version.
- A line in [RELEASE_NOTES](../../../RELEASE_NOTES), first under the top version:
  `330. TeleGuard: support newest version 4.0.12`. Add what else changed for users, e.g.
  `292. Whatsapp: support newest version 2.26.40.76, including fixing PumaDriver.long_click_element()`, and say
  `Contains breaking changes` when an action was renamed or its arguments changed.
- The pull request lists each action that was run on the device, with the device model and the app version, and says
  which actions could not be run and why. When no code changed, say so. See [pull-request](../pull-request/SKILL.md).

Commit messages and the pull request title follow the issue: `330: TeleGuard: support newest version 4.0.12`.
