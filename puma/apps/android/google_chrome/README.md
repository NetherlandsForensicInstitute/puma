# Google Chrome - Android

Google Chrome is a web browser owned by Google.
Puma supports a few actions in Google Chrome, mostly related to the app functionality.
This does not include interacting with websites.

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.android.chrome)

## Deprecation

This class does not use `StateGraph` as its base class, and has therefore been deprecated since Puma 3.0.0. It can still
be used, but it will not be maintained. If you want to add functionality, please rewrite this class using `StateGraph`
as the abstract base class. Also see the [CONTRIBUTING.md](../../../../CONTRIBUTING.md).

## Prerequisites
- The application is installed on your device

### Initialization is standard:

```python
from puma.apps.android.google_chrome.google_chrome import GoogleChromeActions
phone = GoogleChromeActions("emulator-5554")
```

### Navigating the UI

You can go to a new web page, add a bookmark and enter incognito mode:

```python
phone.go_to("google.com", False)
phone.bookmark_page()
phone.go_to("www.imdb.com", tab_index=True)
phone.load_bookmark()
phone.switch_to_tab()
phone.go_to_incognito("DFRWS is awesome!")
```
