from datetime import datetime, timedelta

from puma.apps.ios.calendar import logger
from puma.apps.ios.calendar.locators import *
from puma.apps.ios.date_picker import select_date, select_time, DATE_PICKER_MONTH, DATE_PICKER_WHEEL
from puma.state_graph.action import action
from puma.state_graph.puma_driver import PumaDriver, Platform, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

CALENDAR_BUNDLE_ID = 'com.apple.mobilecal'


class CalendarError(Exception):
    """
    Raised when Calendar refuses an action, e.g. saving an event that ends before it starts.
    """
    pass


def _close_new_event(driver: PumaDriver):
    """
    Closes the new event form, discarding any changes.
    """
    driver.click(NEW_EVENT_CANCEL_BUTTON)
    # when the form has changes, Calendar first asks to discard them
    driver.wait_until(lambda: _discard_changes_shown(driver) or not driver.is_present(NEW_EVENT_NAVIGATION_BAR),
                      timeout=5)
    if _discard_changes_shown(driver):
        driver.click_alert_button(NEW_EVENT_DISCARD_CHANGES_LABEL)
    driver.wait_until_not_present(NEW_EVENT_NAVIGATION_BAR)


def _discard_changes_shown(driver: PumaDriver) -> bool:
    return NEW_EVENT_DISCARD_CHANGES_LABEL in driver.alert_buttons()


def _show_date(driver: PumaDriver, date: datetime):
    """
    Shows a date in the day view, using the calshow URL scheme of Calendar. The date is given as the number of seconds
    since 1 January 2001. Noon is used, so time zone differences do not change the date.
    """
    noon = datetime(date.year, date.month, date.day, 12)
    seconds = int(noon.timestamp() - datetime(2001, 1, 1).timestamp())
    driver.execute_script('mobile: deepLink', {'url': f'calshow:{seconds}', 'bundleId': CALENDAR_BUNDLE_ID})


def _open_event(driver: PumaDriver, title: str, date: datetime = None):
    """
    Opens the details of an event. When the date of the event is given, the event is opened from the day view of that
    date. Otherwise, the event is searched for by its title. Note that the search in Calendar does not find all-day
    events: for those, the date is required.
    """
    if date:
        _show_date(driver, date)
        event = day_view_event(title)
    else:
        driver.click(DAY_VIEW_SEARCH_BUTTON)
        driver.send_keys(SEARCH_FIELD, title)
        event = search_result(title)
    driver.wait_until_present(event)
    driver.click(event)
    driver.wait_until_present(EVENT_DELETE_BUTTON)


def _close_search_if_open(driver: PumaDriver):
    # the search results are not updated after changes, so the search is closed instead of reused
    if driver.is_present(SEARCH_CLOSE_BUTTON):
        driver.click(SEARCH_CLOSE_BUTTON)
        driver.wait_until_not_present(SEARCH_CLOSE_BUTTON)


def _close_event(driver: PumaDriver):
    """
    Goes back from the details of an event to the day view. When the event was opened from the search results, the
    search is closed as well.
    """
    driver.back()
    driver.wait_until_not_present(EVENT_NAVIGATION_BAR)
    _close_search_if_open(driver)


def _close_picker(driver: PumaDriver, cell: str):
    """
    Closes the date or time picker of the start or end cell, if it is still open, by tapping the label ('Starts' or
    'Ends') on the left of the cell. While a picker is open, the buttons in the cell are not always present.
    """
    if not (driver.is_present(DATE_PICKER_MONTH) or driver.is_present(DATE_PICKER_WHEEL)):
        # the picker already closed, tapping the cell would open it again
        return
    driver.click(cell + NEW_EVENT_CELL_LABEL)
    # the picker of the end cell looks the same as the one of the start cell, so wait until this one is gone
    driver.wait_until_not_present(DATE_PICKER_MONTH, DATE_PICKER_WHEEL)


def _set_date(driver: PumaDriver, cell: str, date: datetime):
    """
    Sets the date of the start or end of an event.
    """
    driver.click(cell + NEW_EVENT_DATE_BUTTON)
    select_date(driver, date)
    _close_picker(driver, cell)


def _set_time(driver: PumaDriver, cell: str, time: datetime):
    """
    Sets the time of the start or end of an event.
    """
    driver.click(cell + NEW_EVENT_TIME_BUTTON)
    select_time(driver, time)
    _close_picker(driver, cell)


class EventState(SimpleState, ContextualState):
    """
    A state representing the details of an event.
    """

    def __init__(self, parent_state):
        super().__init__(xpaths=[EVENT_NAVIGATION_BAR, EVENT_TITLE_CELL, EVENT_DELETE_BUTTON],
                         parent_state=parent_state,
                         parent_state_transition=_close_event)

    def validate_context(self, driver: PumaDriver, title: str = None) -> bool:
        if not title:
            return True
        return driver.is_present(event_title(title))


@supported_version("26.2")
class Calendar(StateGraph):
    """
    A class representing the Calendar application on iOS.
    Events are identified by their title, and optionally their date. When multiple events have the same title, the first
    one is used. Note that the search in Calendar does not find all-day events: pass the date for those.
    """
    platform = Platform.IOS

    # States
    day_view_state = SimpleState(xpaths=[DAY_VIEW_NAVIGATION_BAR, DAY_VIEW_ADD_BUTTON, DAY_VIEW_SEARCH_BUTTON],
                                 initial_state=True)
    new_event_state = SimpleState(xpaths=[NEW_EVENT_NAVIGATION_BAR, NEW_EVENT_EVENT_REMINDER_CONTROL],
                                  parent_state=day_view_state,
                                  parent_state_transition=_close_new_event)
    search_state = SimpleState(xpaths=[SEARCH_FIELD, SEARCH_CLOSE_BUTTON],
                               parent_state=day_view_state,
                               parent_state_transition=compose_clicks([SEARCH_CLOSE_BUTTON], 'close_search'))
    event_state = EventState(parent_state=day_view_state)

    # Transitions
    day_view_state.to(new_event_state, compose_clicks([DAY_VIEW_ADD_BUTTON], 'open_new_event'))
    day_view_state.to(search_state, compose_clicks([DAY_VIEW_SEARCH_BUTTON], 'open_search'))
    day_view_state.to(event_state, _open_event)

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Calendar with a device UDID.

        :param device_udid: The unique device identifier of the iOS device or simulator.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, CALENDAR_BUNDLE_ID, **kwargs)

    @action(new_event_state, end_state=day_view_state)
    def add_event(self, title: str, start: datetime, end: datetime = None, location: str = None,
                  all_day: bool = False):
        """
        Adds an event to the default calendar.

        :param title: The title of the event.
        :param start: The start of the event. For all-day events, only the date is used.
        :param end: Optional. The end of the event. Defaults to one hour after the start, or the same day for all-day
        events.
        :param location: Optional. The location of the event. The text is used as-is, it is not looked up in Apple Maps.
        :param all_day: Whether the event lasts all day.
        """
        if self.driver.get_element(NEW_EVENT_EVENT_SEGMENT).get_attribute('value') != '1':
            self.gtl_logger.info('Switching the form from reminder to event')
            self.driver.click(NEW_EVENT_EVENT_SEGMENT)
        self.driver.send_keys(NEW_EVENT_TITLE_FIELD, title)
        if location:
            self.gtl_logger.info(f'Entering location "{location}"')
            self.driver.click(NEW_EVENT_LOCATION_FIELD)
            self.driver.send_keys(NEW_EVENT_LOCATION_SEARCH_FIELD, location)
            self.driver.wait_until_present(location_text(location))
            self.driver.click(location_text(location))
            self.driver.wait_until_not_present(NEW_EVENT_LOCATION_SEARCH_FIELD)
        # the form remembers the all-day setting of the previous event, so set it rather than toggle it
        if (self.driver.get_element(NEW_EVENT_ALL_DAY_SWITCH).get_attribute('value') == '1') != all_day:
            self.gtl_logger.info(f'Turning all-day {"on" if all_day else "off"}')
            self.driver.click(NEW_EVENT_ALL_DAY_SWITCH)
            # all-day events have no time, so the time buttons disappear or appear
            start_time = NEW_EVENT_START_CELL + NEW_EVENT_TIME_BUTTON
            if all_day:
                self.driver.wait_until_not_present(start_time)
            else:
                self.driver.wait_until_present(start_time)
        # The form remembers the dates of the previous event, and refuses to save when the start is after the end.
        # Therefore the end is always set explicitly.
        if end is None:
            end = start if all_day else start + timedelta(hours=1)
        self.gtl_logger.info(f'Setting the start to {start}')
        _set_date(self.driver, NEW_EVENT_START_CELL, start)
        if not all_day:
            _set_time(self.driver, NEW_EVENT_START_CELL, start)
        self.gtl_logger.info(f'Setting the end to {end}')
        _set_date(self.driver, NEW_EVENT_END_CELL, end)
        if not all_day:
            _set_time(self.driver, NEW_EVENT_END_CELL, end)
        self.gtl_logger.info('Pressing save button')
        self.driver.click(NEW_EVENT_SAVE_BUTTON)
        # the form closes, or Calendar shows why it cannot save the event
        self.driver.wait_until(
            lambda: self.driver.alert_buttons() or not self.driver.is_present(NEW_EVENT_NAVIGATION_BAR), timeout=5)
        if self.driver.alert_buttons():
            # Calendar refused to save the event, e.g. because the end is before the start
            message = self.driver.driver.switch_to.alert.text
            self.gtl_logger.warning(f'Calendar refused to save the event: {message}')
            self.driver.click_alert_button(self.driver.alert_buttons()[0])
            _close_new_event(self.driver)
            raise CalendarError(f'Calendar could not save the event "{title}": {message}')

    @action(event_state)
    def get_event_details(self, title: str, date: datetime = None) -> list[str]:
        """
        Returns the details of an event as shown in the app: the title, the location (if any), the date and the time.

        :param title: The title of the event.
        :param date: Optional. The date of the event. Required for all-day events, as these are not found by searching.
        :return: The details of the event, e.g. ['Meeting', 'Eiffel Tower', 'Wednesday, 23 Sep 2026', '10:30 – 11:30']
        """
        details = []
        for element in self.driver.get_elements(EVENT_TITLE_CELL_TEXTS):
            text = element.get_attribute('label') or element.get_attribute('value')
            if text and text not in details:
                details.append(text)
        return details

    @action(event_state, end_state=day_view_state)
    def delete_event(self, title: str, date: datetime = None):
        """
        Deletes an event.

        :param title: The title of the event.
        :param date: Optional. The date of the event. Required for all-day events, as these are not found by searching.
        """
        self.gtl_logger.info('Pressing delete button')
        self.driver.click(EVENT_DELETE_BUTTON)
        self.driver.wait_until(lambda: EVENT_DELETE_LABEL in self.driver.alert_buttons(), timeout=5)
        self.gtl_logger.info('Confirming deletion')
        self.driver.click_alert_button(EVENT_DELETE_LABEL)
        self.driver.wait_until_not_present(EVENT_NAVIGATION_BAR)
        _close_search_if_open(self.driver)
        logger.info(f'Deleted event {title}')
