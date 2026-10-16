# Puma for agents

Puma is a Python library that executes app-specific actions on mobile devices, such as sending a WhatsApp message, by
operating the UI of the app through [Appium](https://appium.io/). It creates test and reference data for digital
forensics. Each supported app is a class that models the app as a graph of states (screens), transitions between them,
and actions.

## Read first

Read the document that matches your task before you change code. This file summarizes them and adds what they lack.

- Any change: [CONTRIBUTING.md](CONTRIBUTING.md) for issues, branches, pull requests and coding standards
- Adding or changing an app, a state, a transition or a locator: [docs/writing-apps.md](docs/writing-apps.md) for the
  StateGraph, on Android and iOS
- Adding or changing an action: [docs/usage.md](docs/usage.md) for how users call it, which tells you what it should
  look like
- Choosing an app to extend or checking what is supported: [README.md](README.md)
- Seeing the screen of a device, or finding and checking locators: the skill
  [explore-ui](.claude/skills/explore-ui/SKILL.md), which reads the UI straight from the device and is faster than an
  Appium session

## Layout

| Path | Contents |
|------|----------|
| `puma/state_graph/` | The framework: `StateGraph`, states, `@action`, drivers for Android and iOS, pop-up handlers |
| `puma/apps/android/<app>/` | An Android app: `<app>.py`, `xpaths.py`, `README.md` |
| `puma/apps/ios/<app>/` | An iOS app: `<app>.py`, `locators.py`, `README.md` |
| `puma/utils/`, `puma/computer_vision/` | Logging, waiting, OCR and other helpers |
| `test/` | Unit tests. They need no device and run in CI |
| `test_scripts/` | One script per app that tests every action on a real device. Run by hand |
| `docs/`, `tutorial/`, `demo/` | Documentation, the tutorial and the iOS demo |
| `.claude/skills/` | Skills: instructions for agents for specific tasks |

## Commands

```bash
pip install -r requirements.txt -r .github/build_requirements.txt   # in a virtual environment
python -m unittest discover test                                    # the unit tests, as CI runs them
python -m unittest test.test_state_graph                            # one test module
```

CI runs the unit tests on Python 3.10 and 3.11: write syntax and library calls that both support.

The unit tests include a release notes test that reads the issue number from the branch name, so they fail on a
branch whose name does not start with `<issue number>-`. The test is skipped on `main`, on
`dependabot` branches and when no branch is checked out.

The scripts in `test_scripts` need a device, a running Appium server (`appium`) and the UDID of the device filled in at
the top of the script. Keep UDIDs, phone numbers, passwords and other data of a device or account out of commits.

## Working with a device

Devices hold real accounts, so treat every device as someone's phone.

- Reading the screen is always safe. Tap to navigate only. Sending messages, placing calls, deleting data and changing
  settings need a task that asks for them. The exception is auto-lock, which
  [explore-ui](.claude/skills/explore-ui/SKILL.md) has you turn off while exploring and restore afterwards.
- Leave the device as you found it.
- Check that no other script or agent uses the device before you operate it.
- Set the language of the device to English.
- iOS needs a Mac with Xcode. On another system you cannot run or verify iOS code: say so, instead of assuming it works.

## Rules for changes

Process:

- Every change goes through a pull request into `main`; commit and open a pull request when asked to.
- Link every pull request to a GitHub issue with `Closes #244` in the description. If the change has no issue, ask for
  one first.
- Start the pull request title with the issue number: `244: Add AGENTS.md`.
- Create the branch from `main` and start its name with the issue number and a dash: `244-create-agents-md`.
- Add a line to [RELEASE_NOTES](RELEASE_NOTES) as the first line under the top version, so the newest entry comes first.
  Start the line with the issue number. A unit test fails when the issue number of the branch is not in the release
  notes.
- Keep the top version in `RELEASE_NOTES` equal to the version in `puma/version.py`. When that version has already
  been released, add a new version at the top and set the same version in `puma/version.py`. A version is released when
  it is a git tag.

Code:

- Follow PEP 8. Put type hints on all arguments and return values.
- Write pydoc in reStructuredText style (`:param name:`, `:return:`) for every public class and method. Methods that
  start with `_` need none.
- Match the code around your change: its naming, its structure and how much it comments.

Apps:

- An app class extends `StateGraph` and has a `@supported_version` annotation with the app version it supports. A
  release uses this annotation to tag the app.
- An app supports exactly one app version. Update code to the new version and drop support for older versions: change
  `@supported_version`, the README of the app and the table in [README.md](README.md).
- When you update an app to a new version, make all its actions work on that version, not only the one you were asked
  about. Run the test script of the app in `test_scripts`.
- Put locators in `xpaths.py` (Android) or `locators.py` (iOS), named after the state they belong to. On iOS, prefer
  `accessibility_id`, `ios_predicate` and `ios_class_chain` over XPaths.
- Prefer locators in this order: `content-desc`, then `resource-id`, then text, so they survive a change of language and
  texts.
- A new app needs a README, a test script in `test_scripts`, and a row in the table in [README.md](README.md).
  A new action needs a test in the test script of the app, and an entry in the README of the app when it is a major
  feature.
- Classes marked `@deprecated` (those based on `AndroidAppiumActions`) are not maintained. Rewrite their functionality
  with the `StateGraph` instead of extending them.

## Verifying your work

- Run the unit tests for every change.
- A change to an app is verified when it has run on a device with the supported app version. Say which parts you could
  not run there.
