# Safari - iOS

Safari is the web browser built into iOS.
Puma supports a few actions in Safari, mostly related to the app functionality.
This does not include interacting with websites.

Safari is part of iOS, so its version is the iOS version. Puma supports the compact tab layout of Safari in iOS 26, with
the address bar at the bottom of the screen.

## Prerequisites
- An iOS device or simulator running iOS 26

### Initialization is standard:

```python
from puma.apps.ios.safari.safari import Safari
phone = Safari("C14C2402-9144-4BC2-9866-A1DB5AFAD376")
```

### Navigating the UI

You can visit web pages in new, existing and private tabs, and add, load and delete bookmarks:

```python
phone.visit_url_new_tab("example.com")
phone.visit_url("example.org")                # in the last opened tab
phone.visit_url("example.org", tab_index=1)   # in the first tab of the tab overview
phone.visit_url_private("example.net")
phone.bookmark_page()
phone.load_bookmark("Example Domain")         # bookmarks are identified by their title
phone.delete_bookmark("Example Domain")
```

Note that Safari allows bookmarking the same page more than once.

On real devices, private browsing is locked with Face ID after leaving Safari. Puma cannot unlock it: private tab actions
then raise a `PrivateBrowsingLockedError`. To use private tabs, turn off "Require Face ID to Unlock Private Browsing" in
Settings > Apps > Safari.
