from puma.state_graph.locators import accessibility_id, ios_predicate

# Home
HOME_SEARCH_FIELD = accessibility_id('MapsSearchTextField')
HOME_PROFILE_BUTTON = accessibility_id('userProfileButton')
HOME_SEARCH_SUGGESTION = ios_predicate('type == "XCUIElementTypeCell" AND name == "Maps.PlaceTableViewCell"')
# Search results, shown when searching for a category (e.g. 'coffee') instead of a single place
HOME_FIRST_SEARCH_RESULT = '(//XCUIElementTypeTable[@name="ResultsViewTable"]//XCUIElementTypeButton[@name="SearchCell"])[1]'
# Cards
CARD_CLOSE_BUTTON = accessibility_id('CardButtonTypeClose')
# Place
PLACE_DIRECTIONS_BUTTON = accessibility_id('ActionRowItemTypeDirections')
# Directions
DIRECTIONS_TRANSPORT_TYPE_PICKER = accessibility_id('TransportTypePickerSegementedControl')
DIRECTIONS_WAYPOINT_LIST = accessibility_id('RoutePlanningWaypointListViewTableView')
DIRECTIONS_ROUTE = accessibility_id('RoutePlanningCell')
DIRECTIONS_GO_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND (label ==[c] "Go" OR name CONTAINS[c] "GoButton")')
# Navigation, only available on real devices
NAVIGATION_TRAY = accessibility_id('NavTray')
NAVIGATION_END_ROUTE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label == "End Route"')
# Popups
POPUP_GETTING_THERE_SAFELY_OK = '//XCUIElementTypeAlert[@name="Getting There Safely"]//XCUIElementTypeButton[@name="OK"]'


def transport_type_button(transport_type: str) -> str:
    return accessibility_id(transport_type)
