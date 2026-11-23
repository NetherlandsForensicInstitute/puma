---
name: pull-request
description: Prepare, review, or handle the review of a Puma pull request the way the project does it - issue, branch, release notes, version, commit messages, the pull request description with what was tested on a device, review comments ordered by impact, and replies that say what was fixed in which commit. Use when committing or opening a pull request, when asked to review a pull request, or when asked to process review comments.
---

# Pull requests in Puma

The rules are in [AGENTS.md](../../../AGENTS.md#rules-for-changes) and [CONTRIBUTING.md](../../../CONTRIBUTING.md).
This skill is how they are applied. Commit, push, open a pull request, post a review or reply to a comment only when
the user asks for it: each of these is visible to others.

## Prepare

1. **Issue.** Every change has one. If there is none, ask the user for it, or offer to open it with labels for the
   platform (`Android`, `iOS`), the app (`WhatsApp`) and the type (`bug`, `enhancement`, `documentation`).
2. **Branch** from `main`, named `<issue>-<short-description>`: `330-teleguard-4.0.12`. The release notes test reads
   the issue number from it.
3. **Release notes.** One line per issue, first under the top version in [RELEASE_NOTES](../../../RELEASE_NOTES), and
   written for users: `<issue>. <App or area>: <what changed for them>`, e.g.
   `328. TeleGuard: return the contact name instead of its initials when getting conversations with unread messages`.
   When a later commit changes the same issue, change its line instead of adding one.
4. **Version.** The top version in `RELEASE_NOTES` equals `version` in `puma/version.py`. Released versions are git
   tags without a `v` (`git tag -l 6.1.0`). When the top version is already tagged, add a new version block at the
   top and set the same version in `puma/version.py`.
5. **Commits** start with the issue number: `330: TeleGuard: support newest version 4.0.12`. The body says why, when
   the title does not.
6. **Tests.** `python -m unittest discover test` passes. Run what changed on a device with the supported app version.

## Describe

Title: `<issue>: <what it does>`. Description:

```markdown
Closes #328

<The problem, with a concrete example of the wrong result. The cause. What the change does about it.>

## Testing

- Unit tests: <new tests>, all pass.
- <Device model> with <App> <version>: <each action that was run, and its result>.
- Not run: <what could not be run and why, e.g. iOS (no Mac), sending to a real contact>.
```

Be exact about what was verified on a device and what was not; a reviewer relies on it. Mention costs a change adds
(e.g. "a lookup that fails takes 0.28 s longer") and anything you changed on the device and restored. End with the
attribution line the session asks for.

## Review

When asked to review a pull request:

- Read the code the change touches, not only the diff: callers of a changed helper in other apps, the states and
  transitions around a changed action.
- Order comments by impact. First what loses or misplaces data (a message sent in the wrong conversation, an export
  that fails as a whole, duplicates after a retry), then changes to shared code that affect other apps, then the rest,
  then style.
- Make each comment concrete: the input or situation, what goes wrong, and a suggested change. For example, "When the
  current conversation is `#bob`, `send_message('hi', conversation='@Bob')` passes the context check and posts in the
  channel."
- Check the project rules: type hints and pydoc, lines under 120 characters, locators in `xpaths.py` or `locators.py`,
  values in XPaths escaped with `xpath_quoted`, a release notes line, a test in `test_scripts` for each new action, a
  unit test for new logic, `@supported_version` and README updated.
- Run the unit tests and say how many passed.
- For work that remains after a round of review, write a comment that starts with `**To do: <what>**`, explains it,
  and ends with `Done when <the test or check that proves it>`.
- In the summary of a later round, list the comments that are still open, with links, and ask for a short reply on
  those that will stay as they are.

## Handle a review

- Address every comment: fix it, or reply why not. A comment that is fixed later in a separate issue says so.
- Push the fixes, then reply on each thread with the commit and what changed: `Fixed in 3a23762: parse_messages now
  raises a PumaClickException saying the list of messages is not shown, with a test.` When an agent wrote the fix, end
  the reply with `_🤖 Addressed by [Claude Code](https://claude.com/claude-code)_`.
- A suggestion that changes shared code for one app is usually better as an opt-in argument: say which you chose.
- Run the unit tests again, and on a device what the fixes changed.
