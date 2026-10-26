# Safari - iOS

Safari is the web browser built into iOS, developed by Apple.
Puma supports part of the features of Safari.
For detailed information on each method, see the method its PyDoc documentation.

Safari is part of iOS, so its version is the iOS version. Puma supports the compact tab layout of Safari in iOS 26,
with the address bar at the bottom of the screen.

## Prerequisites

- An iOS device or simulator running iOS 26, set up as described in [Setting up iOS](../../../../docs/setup-ios.md)
- Device language needs to be set to English

## Initialization

Initialization is standard:

```python
from puma.apps.ios.safari.safari import Safari

phone = Safari("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
```

On a real device, also pass the signing settings for WebDriverAgent as `desired_capabilities`, see
[Setting up iOS](../../../../docs/setup-ios.md).

## Visiting web pages

You can visit web pages in new, existing and private tabs. Interacting with the websites themselves is not supported.

```python
phone.visit_url_new_tab("example.com")
phone.visit_url("example.org")                # in the last opened tab
phone.visit_url("example.org", tab_index=1)   # in the first tab of the tab overview
phone.visit_url_private("example.net")
```

On real devices, private browsing is locked with Face ID after leaving Safari. Puma cannot unlock it: private tab actions
then raise a `PrivateBrowsingLockedError`. To use private tabs, turn off "Require Face ID to Unlock Private Browsing" in
Settings > Apps > Safari.

## Bookmarks

Bookmarks are identified by their title:

```python
phone.bookmark_page()
phone.load_bookmark("Example Domain")
phone.delete_bookmark("Example Domain")
```

Note that Safari allows bookmarking the same page more than once.
