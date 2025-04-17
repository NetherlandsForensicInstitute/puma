# Google Chrome - Android

Google Chrome is a web browser owned by Google.
Puma supports a few actions in Google Chrome, mostly related to the app functionality.
This does not include interacting with websites.

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.android.chrome)

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
phone.go_to("google.com")
phone.bookmark_page()
phone.go_to("www.imdb.com", new_tab=True)
phone.load_bookmark()
phone.switch_to_tab()
phone.go_to_incognito("DFRWS is awesome!")
```
