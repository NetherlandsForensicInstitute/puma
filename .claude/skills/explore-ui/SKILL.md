---
name: explore-ui
description: Read and operate the UI of a connected phone directly over adb (Android) or WebDriverAgent (iOS), without an Appium session. Use to see what is on the screen, find or check XPaths and locators, map the states and transitions of an app, add or update a Puma app for a new app version, or debug a state or locator that no longer matches.
---

# Exploring the UI of a device

Puma drives apps through Appium at runtime. To find out what a screen looks like and which locators work, skip Appium:
starting a session takes several seconds and each lookup is a round trip, while reading the hierarchy straight from the
device is fast and gives the whole screen at once.

Explore with this skill, then finish by running the code through Puma (see [Finishing](#finishing)).

## Pick the platform

Read the reference for the platform of the device, and only that one:

- Android: [references/android.md](references/android.md), with [scripts/ui.py](scripts/ui.py) for the hierarchy,
  XPath checks and taps
- iOS: [references/ios.md](references/ios.md), through the HTTP API of WebDriverAgent

## Before you start

The device is a real phone, often with real accounts on it. Reading the screen is always safe. A tap is only safe when
you know what the element does, so tap to navigate and leave anything that sends, calls, deletes or changes settings to
tasks that ask for it.

1. Check that nobody else uses the device. A running Puma script breaks when you tap.
2. Unlock the device, switch its screen on and set its language to English.
3. Turn auto-lock off for the exploration, because a locked screen makes every read fail and iOS does not start apps on
   a locked device. This is the one setting you change unasked, since you restore it. Note the current value first,
   so you put that value back and not a default.
   - iOS: Settings > Display & Brightness > Auto-Lock > Never.
   - Android: Settings > Display > Screen timeout, or `adb shell settings get system screen_off_timeout` to read the
     value and `adb shell settings put system screen_off_timeout <ms>` to set it.
4. When you are done, restore auto-lock and go back to the home screen. Do this also when the exploration fails halfway.

## Finishing

Exploring gives you locators and the order of screens. It does not prove the Puma code works: a locator is done when it
works in a Puma run on the device.

- Put locators in `xpaths.py` (Android) or `locators.py` (iOS) of the app, following
  [Writing Puma apps](../../../docs/writing-apps.md).
- Prefer `content-desc`, then `resource-id`, then text: texts and content descriptions change with the language of the
  device and with app versions, and resource ids change with app versions.
- Run the test script of the app in `test_scripts`, or the action you changed.
