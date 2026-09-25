from puma.state_graph.locators import accessibility_id, ios_predicate

# Home
SEARCH_FIELD = accessibility_id('MapsSearchTextField')
PROFILE_BUTTON = accessibility_id('userProfileButton')
SEARCH_SUGGESTION = ios_predicate('type == "XCUIElementTypeCell" AND name == "Maps.PlaceTableViewCell"')
# Search results, shown when searching for a category (e.g. 'coffee') instead of a single place
FIRST_SEARCH_RESULT = '(//XCUIElementTypeTable[@name="ResultsViewTable"]//XCUIElementTypeButton[@name="SearchCell"])[1]'
# Cards
CLOSE_CARD_BUTTON = accessibility_id('CardButtonTypeClose')
# Place
DIRECTIONS_BUTTON = accessibility_id('ActionRowItemTypeDirections')
# Directions
TRANSPORT_TYPE_PICKER = accessibility_id('TransportTypePickerSegementedControl')
WAYPOINT_LIST = accessibility_id('RoutePlanningWaypointListViewTableView')
ROUTE = accessibility_id('RoutePlanningCell')
GO_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND (label ==[c] "Go" OR name CONTAINS[c] "GoButton")')
# Navigation, only available on real devices
NAVIGATION_TRAY = accessibility_id('NavTray')
END_ROUTE_BUTTON = ios_predicate('type == "XCUIElementTypeButton" AND label == "End Route"')
# Popups
GETTING_THERE_SAFELY_ALERT = '//XCUIElementTypeAlert[@name="Getting There Safely"]'
GETTING_THERE_SAFELY_OK = '//XCUIElementTypeAlert[@name="Getting There Safely"]//XCUIElementTypeButton[@name="OK"]'


def transport_type_button(transport_type: str) -> str:
    return accessibility_id(transport_type)
