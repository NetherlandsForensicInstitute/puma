GOOGLE_MAPS_PACKAGE = 'com.google.android.apps.maps'

# The close button of the card of a place and of the directions
CARD_CLOSE_BUTTON = f'//android.widget.Button[@resource-id="{GOOGLE_MAPS_PACKAGE}:id/terra_navigation_header_close_button"]'

HOME_SEARCH_BOX = '//android.widget.EditText[@content-desc="Search here"]'
HOME_EXPLORE_TAB = f'//android.widget.FrameLayout[@resource-id="{GOOGLE_MAPS_PACKAGE}:id/explore_tab_strip_button"]'

SEARCH_EDIT_TEXT = f'//android.widget.EditText[@resource-id="{GOOGLE_MAPS_PACKAGE}:id/search_omnibox_edit_text"]'
SEARCH_FIRST_SUGGESTION = f'//*[@resource-id="{GOOGLE_MAPS_PACKAGE}:id/typed_suggest_container"]/*[1]'

PLACE_DIRECTIONS_BUTTON = '//android.widget.Button[starts-with(@content-desc, "Directions to")]'

DIRECTIONS_START_LOCATION = '//android.widget.TextView[starts-with(@content-desc, "Start location")]'
DIRECTIONS_DRIVING_MODE = '//android.widget.LinearLayout[starts-with(@content-desc, "Driving mode")]'
DIRECTIONS_START_BUTTON = '//android.widget.Button[@content-desc="Start"]'

NAVIGATION_TIME_REMAINING = f'//android.widget.TextView[@resource-id="{GOOGLE_MAPS_PACKAGE}:id/navigation_time_remaining_label"]'
NAVIGATION_CLOSE_BUTTON = '//android.widget.ImageView[@content-desc="Close navigation"]'


def transport_mode_button(mode: str) -> str:
    """
    :param mode: The start of the content description of the transport mode, such as 'Driving mode'.
    :return: The XPath of the button that selects the transport mode in the directions.
    """
    return f'//android.widget.LinearLayout[starts-with(@content-desc, "{mode}")]'


def selected_transport_mode_button(mode: str) -> str:
    """
    :param mode: The start of the content description of the transport mode, such as 'Driving mode'.
    :return: The XPath of the button of the transport mode, if that transport mode is selected.
    """
    return f'//android.widget.LinearLayout[starts-with(@content-desc, "{mode}") and @selected="true"]'
