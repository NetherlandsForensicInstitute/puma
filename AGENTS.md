# Puma for agents

Puma is a Python library that executes app-specific actions on mobile devices, such as sending a WhatsApp message, by
operating the UI of the app through [Appium](https://appium.io/). It is used to create test and reference data for
digital forensics. Each supported app is a class that models the app as a graph of states (screens), transitions
between them, and actions.

Read these before changing code. This file only summarizes them.

- [README.md](README.md): what Puma is, and the supported apps
- [CONTRIBUTING.md](CONTRIBUTING.md): issues, branches, pull requests and coding standards
- [docs/writing-apps.md](docs/writing-apps.md): the StateGraph, and how to add or change an app, on Android and iOS
- [docs/usage.md](docs/usage.md): how Puma is used, which tells you what an action should look like to its users

## Layout

| Path | Contents |
|------|----------|
| `puma/state_graph/` | The framework: `StateGraph`, states, `@action`, drivers for Android and iOS, pop-up handlers |
| `puma/apps/android/<app>/` | An Android app: `<app>.py`, `xpaths.py`, `README.md` |
| `puma/apps/ios/<app>/` | An iOS app: `<app>.py`, `locators.py`, `README.md` |
| `puma/utils/`, `puma/computer_vision/` | Logging, waiting, OCR and other helpers |
| `test/` | Unit tests. They need no device, and run in CI |
| `test_scripts/` | One script per app that tests every action on a real device. Run by hand only |
| `docs/`, `tutorial/`, `demo/` | Documentation, the tutorial and the iOS demo |
| `.claude/skills/` | Skills: instructions for agents for specific tasks |

## Commands

```bash
pip install -r requirements.txt -r .github/build_requirements.txt   # in a virtual environment
python -m unittest discover test                                    # the unit tests, as CI runs them
python -m unittest test.test_state_graph                            # one test module
```

CI runs the unit tests on Python 3.10 and 3.11, so do not use newer syntax or library features.

The scripts in `test_scripts` need a device, a running Appium server (`appium`) and the UDID of the device filled in
at the top of the script. Do not commit a UDID, phone number, password or other data of a device or account.

## Working with a device

- To see what is on the screen of a device, and to find or check locators, follow the skill
  [explore-ui](.claude/skills/explore-ui/SKILL.md). It reads the UI directly from the device, which is faster than
  starting an Appium session.
- Devices hold real accounts. Do not send messages, place calls, delete data or change settings unless the task asks
  for it, and leave the device as you found it. The one exception is auto-lock, which the
  [explore-ui](.claude/skills/explore-ui/SKILL.md) skill has you turn off while exploring and restore afterwards.
- Check that no other script or agent is using the device before you operate it.
- The language of the device must be English.
- iOS needs a Mac with Xcode. On another system you cannot run or verify iOS code: say so, instead of assuming it
  works.

## Rules for changes

Process:

- Every change goes through a pull request. Never push to `main`.
- Every pull request is linked to a GitHub issue (`Closes #244` in the description). If there is no issue for the
  change, ask for one first.
- The title of every pull request starts with the issue number: `244: Add AGENTS.md`.
- The branch is created from `main`, and its name starts with the issue number and a dash: `244-create-agents-md`.
- Every pull request adds a line to [RELEASE_NOTES](RELEASE_NOTES), as the first line under the top version: the newest
  entry comes first. The line starts with the issue number. A unit test fails when the issue number of the branch is
  not in the release notes.
- The top version in `RELEASE_NOTES` must be equal to the version in `puma/version.py`. When that version has already
  been released, add a new version at the top and set the same version in `puma/version.py`.
- Commit and open pull requests only when asked to.

Code:

- Follow PEP 8. Put type hints on all arguments and return values.
- Write pydoc in reStructuredText style (`:param name:`, `:return:`) for every public class and method. Methods that
  start with `_` do not need it.
- Match the code around your change: its naming, its structure and how much it comments.

Apps:

- An app class extends `StateGraph` and has a `@supported_version` annotation with the app version it supports. This
  annotation is used to tag the app on a release.
- An app supports exactly one app version. Do not make code backwards compatible with older app versions: update it to
  the new version, and update `@supported_version`, the README of the app and the table in [README.md](README.md).
- When you update an app to a new version, all its actions must work on that version, not only the one you were asked
  about. Run the test script of the app in `test_scripts`.
- Locators go in `xpaths.py` (Android) or `locators.py` (iOS), named after the state they belong to. On iOS, prefer
  `accessibility_id`, `ios_predicate` and `ios_class_chain` over XPaths.
- Prefer locators that do not depend on the language or on texts that change: `content-desc`, then `resource-id`,
  then text.
- A new app also needs a README, a test script in `test_scripts`, and a row in the table in [README.md](README.md).
  A new action needs a test in the test script of the app, and an entry in the README of the app when it is a major
  feature.
- Classes marked `@deprecated` (those based on `AndroidAppiumActions`) are not maintained. Do not add functionality
  to them: rewrite the functionality with the `StateGraph`.

## Verifying your work

- Run the unit tests for every change.
- A change to an app is only verified when it has run on a device with the supported app version. If you could not do
  that, say which parts you did not verify.
