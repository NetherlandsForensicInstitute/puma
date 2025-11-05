# Google Chrome - Android

Google Chrome is a web browser owned by Google.
Puma supports a few actions in Google Chrome, mostly related to the app functionality.
This does not include interacting with websites.

The application can be downloaded in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.android.chrome)

## Prerequisites
- The application is installed on your device

### Initialization is standard:

```python
from puma.apps.android.google_chrome.google_chrome import GoogleChrome
phone = GoogleChrome("emulator-5554")
```

### Navigating the UI

You can go to a new web page, add a bookmark and enter incognito mode:

```python
phone.visit_url("google.com", tab_index=1)
phone.visit_url_new_tab("google.com", tab_index=1)
phone.visit_url_incognito("DFRWS is awesome!")
phone.bookmark_page(tab_index=1)
phone.load_first_bookmark(folder_name="Mobile bookmarks")
phone.delete_bookmark(tab_index=1)
```
