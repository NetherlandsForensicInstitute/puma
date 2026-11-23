---
name: add-feature
description: Write new Puma code the way the project writes it - a new action, state or transition in an app, a new app for Android or iOS, or a change to the framework in puma/state_graph or puma/utils. Use when adding or changing functionality, to get the structure, locators, argument checks, tests, docs and release notes right the first time. Holds the lessons of earlier reviews.
---

# Adding a feature to Puma

[Writing Puma apps](../../../docs/writing-apps.md) explains the StateGraph; read it first. This skill is the checklist
on top of it, with what reviews of earlier pull requests asked for. Use [explore-ui](../explore-ui/SKILL.md) to find
the locators, and [pull-request](../pull-request/SKILL.md) to deliver the change.

## Start from what exists

- Read an app of the same kind and copy its shape: TeleGuard (small, Android, contextual chat state), WhatsApp (large,
  Android), Slack (Android, parsing separated from the UI, tested without a device), Telegram for iOS.
- Use the helpers of `PumaDriver` ([puma_driver.py](../../../puma/state_graph/puma_driver.py)) before you write your
  own: `click`, `is_present`, `wait_until_present`, `wait_until_not_present`, `wait_until`, `get_element(s)`,
  `send_keys`, `long_click_element`, `swipe_left`, `swipe_to_find_element`, `swipe_to_click_element`,
  `close_keyboard`, `wait_until_keyboard_shown`, `open_url`. They work on Android and iOS, check for pop-ups when an
  element is missing, and log to the ground truth log.
- Never wait with `time.sleep` where a wait for an element or a condition is possible.
- Do not extend classes marked `@deprecated`. Rewrite what you need with the `StateGraph`.

## States and transitions

- Validate a state with elements that only that screen has. Run `ui.py states <app class>` (explore-ui, Android) on
  the new screen and on the screens next to it: exactly one state may match.
- The `parent_state` of a state is where back leads in the app, not where you came from. When a chat is opened through
  a search screen, but back goes to the overview, the overview is the parent and the search screen has the transition
  to the chat.
- Give the transition to a `ContextualState` the context as an argument, with the same name as in `validate_context`
  and the actions (`conversation`, not `chat` in one place and `conversation` in another).
- `validate_context` must fail for every other context, including look-alikes: a channel and a direct message with the
  same name, a name that contains the other name.
- Mark states that Puma only needs to recognize `recognize_only=True`. They cannot have actions.

## Locators

- Put them in `xpaths.py` (Android) or `locators.py` (iOS), named after their state: `CHAT_SEND_BUTTON`, pop-ups start
  with `POPUP_`. Locators with a value are format strings (Android) or small functions (iOS).
- Prefer `content-desc`, then `resource-id`, then text. On iOS prefer `accessibility_id`, `ios_predicate` and
  `ios_class_chain` over XPaths.
- Put every value that comes from the caller (a name, a message) through `xpath_quoted` (XPath) or `quoted` (iOS
  predicate or class chain) from `puma/state_graph/locators.py`, so a name with a quote works.
- Compare texts case-insensitively: `lower-case(@text)` in XPaths, `[c]` in predicates.
- Match patterns strictly: an XPath for "1,234 members" must not also match "Team member". Test such XPaths on real
  texts with `elementpath` in a unit test.

## Actions

- `@action(state)` on a method with type hints and reStructuredText pydoc (`:param name:`, `:return:`). Contextual
  arguments the action does not use itself are optional (`conversation: str = None`), so the action also runs in the
  current chat.
- Check arguments **before** the action starts: the `@action` wrapper retries after any exception, so an invalid
  argument raised inside the action navigates twice before it fails. Write a public method that checks the arguments
  and calls a private `@action` method that does the work:

  ```python
  def send_picture(self, conversation: str, picture_id: int = 1):
      """..."""
      if picture_id < 1:
          raise ValueError(f'picture_id starts at 1, got {picture_id}')
      self._send_picture(conversation, picture_id)

  @action(chat_state)
  def _send_picture(self, conversation: str, picture_id: int):
      ...
  ```

- An action that fails after it did something visible (sent a message) is run again by the wrapper. Do the step that
  can fail before the step that sends, when you can.
- Return data as values (a list, a dataclass), not printed text. Put parsing of screen texts in plain functions that
  take strings or elements, so they can be tested without a device.
- Long actions that collect data return what they collected with a warning when they hit a limit, instead of raising and
  losing everything.
- Tell items apart by position, not by text or description: two messages "ok" or two photos with the same description
  are different items.
- Log the steps of an action with several screens with `self.gtl_logger.info(...)`. Navigation and the start and end of
  each action are already logged.
- Close what the action opened (the keyboard, a menu) when the next action cannot start from it.

## Changing the framework

Code in `puma/state_graph` and `puma/utils` is used by every app.

- Grep the callers in `puma/apps` before you change a helper, and keep their behaviour: add new behaviour behind an
  argument with a default that does what the code did before, e.g. `swipe_to_find_element(..., stop_at_end=False)`.
- Make it work on both platforms, or say in the pydoc which platform it is for. On iOS, Appium calls that Android
  supports may raise (`hide_keyboard` on a number pad): catch, log a warning and return `False`.
- Add a unit test in `test/` for each platform the change affects.

## Tests and docs

- Logic gets a unit test in `test/`, without a device: see [debug-puma](../debug-puma/SKILL.md#reproduce-without-a-device)
  for how to test an app with a mocked driver.
- Every new action gets a test in the test script of the app in `test_scripts`; a new app gets a test script. Leave the
  UDIDs and account data in it empty.
- A major feature (stickers, calls, pictures) goes in the README of the app; a new app gets a README and a row in the
  table in [README.md](../../../README.md).
- Keep lines under 120 characters, PEP 8, type hints on every argument and return value.
- Run the unit tests, and the new action on a device with the supported app version. Say which parts you did not run on
  a device, and that iOS code is unverified when you have no Mac.
