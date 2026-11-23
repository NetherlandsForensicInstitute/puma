---
name: debug-puma
description: Find the cause of a failing Puma app, action, state or transition and fix it at its root. Use when an action raises (PumaClickException, "Unknown state, cannot recover", "More than one state matches the current UI", "Too many transitions"), when an app class fails to import with a ValueError or TypeError, when an action does the wrong thing without an error (wrong conversation, wrong picture, missing or duplicated data), or when a test script fails.
---

# Debugging Puma

Find out where the failure is before you change code: in the app (a locator, a state, a transition, an action) or in
the framework (`puma/state_graph`). Most failures are a locator that no longer matches the screen. Fix the cause once,
where it is, and prove the fix with a unit test where the cause is logic, and on a device where it is the UI.

## How an action runs

Knowing this explains most logs. A method decorated with `@action(state)` (see [action.py](../../../puma/state_graph/action.py)):

1. Navigates to `state` with `go_to_state`: it follows the shortest path of transitions, and validates the state after
   each transition. When a validation fails, it calls `recover_state` and tries again, up to a limit
   (`Too many transitions, state is unrecoverable`).
2. Runs the action. When the action raises **any** exception, it calls `recover_state`, navigates to the state again and
   runs the action a second time. An exception in the second run is raised to the caller.

`recover_state` opens the app if it is closed, dismisses known pop-ups (`known_popups_for` and the handlers added with
`add_popup_handler`), and then looks for the state that matches the screen. When none or more than one state matches,
it restarts the app once; the next time it raises.

What follows from this:

- An error in an action shows up twice in the log. The first one is the cause; the second is the retry.
- A half-done action is done again: when an action fails after it sent a message, the retry sends it again. Puma
  creates reference data, so a duplicate is a wrong result, not a cosmetic one.
- A `ValueError` for an invalid argument, raised inside the action, costs two navigations and a recovery before it
  reaches the caller. Check arguments before the action (see [add-feature](../add-feature/SKILL.md)).
- `driver.is_present(xpath)` waits 0 seconds unless you pass a wait. An element that appears a moment after the screen
  opens is reported missing. Pass `self.driver.implicit_wait`, or use `wait_until_present`.

## Read the logs

Puma writes two logs per run in `logs/` at the root of the repository: `<timestamp>.log` with everything, and
`<timestamp>_gtl.log` with the ground truth: every navigation step and action on the device. In your own script, call
`configure_default_logging()` from `puma.utils` to see the log on the console. Set the level of the `puma` logger to
`DEBUG` to see which XPath made a state validation fail (`required xpath not found`).

| Message | Cause | Look at |
|---------|-------|---------|
| `PumaClickException` | An element was not found to click, or to read | The locator, and whether a pop-up, the keyboard or a slow screen hides it |
| `Unknown state, cannot recover` | No state matches the screen, also after a restart | A changed locator, or a screen or pop-up the app does not know |
| `More than one state matches the current UI` | The XPaths of two states match the same screen | Add an XPath that only one of them has, or use `invalid_xpaths` |
| `Too many transitions, state is unrecoverable` | A transition does not arrive in the state it claims | The transition, and the XPaths of its target state |
| `Installed version ... differs from the supported version` | The app on the device is another version | Use [update-app-version](../update-app-version/SKILL.md) |
| `ValueError` or `TypeError` when the app class is defined | The graph is invalid: a state that cannot be reached, an action without the contextual arguments of its state, a missing platform | The message names the states or the action |

## See the screen

Use [explore-ui](../explore-ui/SKILL.md) to see what is on the screen where the action failed, without Appium. On
Android, `ui.py states <app class>` shows which states match the current screen and which XPaths are missing, which
answers the first three rows of the table at once. Leave the device on the screen where the failure happened before you
look: run the failing action, then read the screen.

## Causes found before

These caused bugs in Puma. Check for them first:

- **A changed attribute in a new app version**, e.g. a new `resource-id`. Fix the locator in `xpaths.py` or
  `locators.py`; do not keep the old one next to it.
- **A pop-up**: a first-use dialog, a permission request, a review prompt. Add a `PopUpHandler` to the app when it can
  appear again; ask the user to dismiss it by hand when it appears once.
- **The on-screen keyboard** hides or moves elements, and the first back press only closes it. Use
  `self.driver.close_keyboard()` or `wait_until_keyboard_shown`.
- **Invisible characters** in texts: zero-width spaces in names (Slack puts them after hyphens), `‎` and `\xa0`
  on iOS. Print attributes with `repr()`; strip them when you parse.
- **Quotes in names**: a name with `"` breaks an XPath built with an f-string. Use `xpath_quoted` (XPath) or `quoted`
  (iOS predicates and class chains) from `puma/state_graph/locators.py`.
- **Case**: apps change the case of texts between versions. Compare with `lower-case()` in XPaths and `[c]` in
  predicates.
- **Two things with the same name or description**: a channel and a direct message called Bob, two photos with the same
  content-desc. A context check that only compares the name passes for the wrong one, and the wrong item is used
  without an error. Tell them apart by something else on the screen, or by position.
- **A content-desc with several lines**, where the first line is not always the name (TeleGuard shows initials first
  when a contact has no picture). Test the parsing against real content-descs.
- **A screen that is still loading**: lists that load older items while you scroll, a member count fetched after the
  title. Wait for the element instead of assuming it is there, and never with `time.sleep` when a wait for an element
  is possible.

## Reproduce without a device

A bug in logic (parsing, merging, context checks, argument handling) gets a unit test in `test/` that fails before the
fix. Examples:

- Pure functions that take the strings of the screen, such as `TeleGuard._extract_name` in
  [test_android_teleguard.py](../../../test/test_android_teleguard.py), tested with content-descs copied from a device.
- An app without a device: create it with `App.__new__(App)` and a `Mock` driver, as `slack_without_device` in
  [test/slack/__init__.py](../../../test/slack/__init__.py) does, and give the mock the behaviour of the screen, as
  `FakeSlackScreen` in [test_slack_navigation.py](../../../test/slack/test_slack_navigation.py) does.
- An XPath against a piece of XML: evaluate it with `elementpath` (XPath 2.0, in `.github/build_requirements.txt`) on
  the XML of the element, as `TestChatMemberCount` does.

Copy texts from the device into tests only when they are not personal data: use test accounts with names like Alice and
Bob.

## Fix

- Fix the cause in the code that has it. When that is shared code (`puma/state_graph`, `puma/utils`), grep every caller
  in `puma/apps` first: a change to `swipe_to_find_element` or `PumaDriver.click` changes every app. Keep the default
  behaviour the same and make new behaviour opt-in with an argument, unless the default is the bug.
- A failure that would lose collected data, such as a long export that hits a limit, returns what it has with a warning
  instead of raising, as raising also triggers the retry.
- Run the unit tests, and the failing action on a device with the supported app version. Say what you could not run.
