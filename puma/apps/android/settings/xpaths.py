# Note that some titles contain a non-breaking hyphen (U+2011) instead of a normal hyphen, e.g. 'Wi‑Fi'.
_TITLE = '*[@resource-id="android:id/title"]'
_SUMMARY = '*[@resource-id="android:id/summary"]'

# Main screen
MAIN_SEARCH_BAR = '//*[@resource-id="com.android.settings:id/search_bar_title"]'
MAIN_HOMEPAGE = '//*[@resource-id="com.android.settings:id/homepage_container"]'

# Internet
INTERNET_USE_WIFI = 'Use Wi‑Fi'
INTERNET_NETWORKS_HEADER = f'//{_TITLE}[@text="Networks"]'
# The screen for entering the password of a network, its title is the name of the network
WIFI_PASSWORD_INPUT = '//android.widget.EditText[@resource-id="com.android.settings:id/password"]'
WIFI_PASSWORD_CONNECT = '//android.widget.Button[@resource-id="android:id/button1"]'
WIFI_PASSWORD_CANCEL = '//android.widget.Button[@resource-id="android:id/button2"]'

# Display & touch
DISPLAY_BRIGHTNESS_LEVEL = 'Brightness level'
# The brightness slider is shown in a dialog of the System UI, not of the Settings app. Its text is its value.
BRIGHTNESS_SLIDER = '//android.widget.SeekBar[@package="com.android.systemui"]'

# Screen timeout
SCREEN_TIMEOUT_SELECTED_OPTION = (f'//android.widget.RadioButton[@checked="true"]'
                                  f'/ancestor::*[.//{_TITLE}][1]//{_TITLE}')


def toolbar(title: str) -> str:
    """
    The toolbar on top of a settings screen, which contains the title of the screen.
    """
    return f'//*[@resource-id="com.android.settings:id/collapsing_toolbar" and @content-desc="{title}"]'


def list_entry(title: str) -> str:
    """
    An entry in a list of settings, by its title.
    """
    return f'//{_TITLE}[@text="{title}"]'


def summary_of(title: str) -> str:
    """
    The summary shown below the title of an entry in a list of settings, e.g. '71%' for 'Brightness level'.
    """
    return f'{list_entry(title)}/following-sibling::{_SUMMARY}'


def row_switch(title: str) -> str:
    """
    The switch in the same row as an entry in a list of settings.
    """
    return f'{list_entry(title)}/ancestor::*[.//android.widget.Switch][1]//android.widget.Switch'


def wifi_connected(ssid: str) -> str:
    return f'{summary_of(ssid)}[starts-with(@text, "Connected")]'
