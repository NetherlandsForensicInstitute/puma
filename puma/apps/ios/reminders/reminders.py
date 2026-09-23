from datetime import datetime
from time import sleep

from puma.apps.ios.date_picker import select_date, select_time
from puma.apps.ios.reminders import logger
from puma.apps.ios.reminders.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.popup_handler import PopUpHandler, known_ios_popups
from puma.state_graph.puma_driver import PumaDriver, Platform, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

REMINDERS_BUNDLE_ID = 'com.apple.reminders'
DEFAULT_LIST = 'Reminders'


def _set_switch(driver: PumaDriver, switch: str, on: bool):
    if (driver.get_element(switch).get_attribute('value') == '1') != on:
        driver.click(switch)
        sleep(1)


def _handle_notifications_intro(driver: PumaDriver):
    """
    The first time a due date is set, Reminders explains its notifications, followed by the system notification
    permission request.
    """
    if driver.is_present(POPUP_NOTIFICATIONS_INTRO_TEXT):
        driver.gtl_logger.info('Dismissing explanation of notifications')
        driver.click(POPUP_CONTINUE_BUTTON)
        sleep(2)
        for handler in known_ios_popups:
            if handler.is_popup_window(driver):
                handler.dismiss_popup(driver)
                sleep(1)


def _swipe_left(driver: PumaDriver, element: str):
    """
    Swipes a row in a list to the left, which reveals the delete button.
    """
    rect = driver.get_element(element).rect
    y = rect['y'] + rect['height'] / 2
    driver.execute_script('mobile: dragFromToForDuration', {
        'fromX': rect['x'] + rect['width'] - 20, 'fromY': y, 'toX': rect['x'] + 60, 'toY': y, 'duration': 0.2})
    sleep(1)


def _close_new_list(driver: PumaDriver):
    driver.click(NEW_LIST_CANCEL_BUTTON)
    sleep(1)


class ListState(SimpleState, ContextualState):
    """
    A state representing a list of reminders.
    """

    def __init__(self, parent_state):
        # the parent transition is the default back action, which uses the back button in the navigation bar
        super().__init__(xpaths=[LIST_NEW_REMINDER_BUTTON, LIST_MORE_BUTTON], invalid_xpaths=[LISTS_ADD_LIST_BUTTON],
                         parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, list_name: str = None) -> bool:
        # actions pass the default list when no list is given, so no list name means any list is fine
        if not list_name:
            return True
        return driver.is_present(list_title(list_name))

    @staticmethod
    def open_list(driver: PumaDriver, list_name: str = DEFAULT_LIST):
        driver.click(list_cell(list_name))
        sleep(1)


@supported_version("26.2")
class Reminders(StateGraph):
    """
    A class representing the Reminders application on iOS.
    Lists and reminders are identified by their name and title. Reminders are added to the default list 'Reminders',
    unless another list is given.
    """
    platform = Platform.IOS

    # States
    lists_state = SimpleState(xpaths=[LISTS_NAVIGATION_BAR, LISTS_ADD_LIST_BUTTON], initial_state=True)
    new_list_state = SimpleState(xpaths=[NEW_LIST_NAVIGATION_BAR, NEW_LIST_NAME_FIELD],
                                 parent_state=lists_state,
                                 parent_state_transition=_close_new_list)
    list_state = ListState(parent_state=lists_state)

    # Transitions
    lists_state.to(new_list_state, compose_clicks([LISTS_ADD_LIST_BUTTON], 'open_new_list'))
    lists_state.to(list_state, list_state.open_list)

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Reminders with a device UDID.

        :param device_udid: The unique device identifier of the iOS device or simulator.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, REMINDERS_BUNDLE_ID, **kwargs)
        self.add_popup_handlers(PopUpHandler([POPUP_WELCOME_TEXT], [POPUP_CONTINUE_BUTTON]),
                                PopUpHandler([POPUP_ICLOUD_SYNC_TEXT], [POPUP_NOT_NOW_BUTTON]),
                                PopUpHandler([POPUP_NOTIFICATIONS_INTRO_TEXT], [POPUP_CONTINUE_BUTTON]))

    @action(new_list_state, end_state=list_state)
    def add_list(self, name: str):
        """
        Adds a list of reminders. The new list is opened afterwards.

        :param name: The name of the list.
        """
        self.driver.send_keys(NEW_LIST_NAME_FIELD, name)
        self.driver.click(LIST_DONE_BUTTON)
        sleep(1)

    @action(lists_state)
    def delete_list(self, name: str):
        """
        Deletes a list, including all its reminders.

        :param name: The name of the list.
        """
        self.gtl_logger.info(f'Swiping list "{name}" to the left to reveal the delete button')
        _swipe_left(self.driver, list_cell(name))
        self.gtl_logger.info('Pressing delete button')
        self.driver.click(LIST_SWIPE_DELETE_BUTTON)
        sleep(1)
        # deleting a list has to be confirmed
        buttons = self.driver.alert_buttons()
        if LISTS_DELETE_LABEL in buttons:
            self.gtl_logger.info('Confirming deletion')
            self.driver.click_alert_button(LISTS_DELETE_LABEL)
            sleep(1)
        logger.info(f'Deleted list {name}')

    @action(list_state)
    def add_reminder(self, title: str, list_name: str = DEFAULT_LIST, notes: str = None, due: datetime = None,
                     due_time: bool = False):
        """
        Adds a reminder to a list.

        :param title: The title of the reminder.
        :param list_name: Optional. The list to add the reminder to, the default list 'Reminders' if not given.
        :param notes: Optional. Notes for the reminder.
        :param due: Optional. The date the reminder is due.
        :param due_time: Whether the time of the due date is used. If False, the reminder is due on the date only.
        """
        self.gtl_logger.info('Pressing new reminder button')
        self.driver.click(LIST_NEW_REMINDER_BUTTON)
        sleep(1)
        self.gtl_logger.info(f'Entering title "{title}"')
        self.driver.driver.switch_to.active_element.send_keys(title)
        if notes or due:
            self.gtl_logger.info('Opening the details of the reminder')
            self.driver.click(LIST_EDIT_DETAILS_BUTTON)
            sleep(1.5)
            if notes:
                self.driver.send_keys(DETAILS_NOTES_FIELD, notes)
            if due:
                self.gtl_logger.info(f'Setting the due date to {due.date()}')
                _set_switch(self.driver, DETAILS_DATE_SWITCH, True)
                _handle_notifications_intro(self.driver)
                select_date(self.driver, due)
                if due_time:
                    self.gtl_logger.info(f'Setting the due time to {due.time()}')
                    _set_switch(self.driver, DETAILS_TIME_SWITCH, True)
                    select_time(self.driver, due)
            self.gtl_logger.info('Closing the details')
            self.driver.click(LIST_DONE_BUTTON)
            sleep(1)
        # stop editing the new reminder
        if self.driver.is_present(LIST_DONE_BUTTON):
            self.gtl_logger.info('Pressing done button')
            self.driver.click(LIST_DONE_BUTTON)
            sleep(1)

    @action(list_state)
    def get_reminders(self, list_name: str = DEFAULT_LIST) -> list[str]:
        """
        Returns the titles of the reminders in a list that have not been completed.

        :param list_name: Optional. The list, the default list 'Reminders' if not given.
        :return: The titles of the reminders.
        """
        if not self.driver.is_present(LIST_REMINDER_TITLES):
            return []
        return [element.get_attribute('value') for element in self.driver.get_elements(LIST_REMINDER_TITLES)]

    @action(list_state)
    def get_reminder_details(self, title: str, list_name: str = DEFAULT_LIST) -> str:
        """
        Returns the details of a reminder as shown in the list: its title, status and due date.

        :param title: The title of the reminder.
        :param list_name: Optional. The list of the reminder, the default list 'Reminders' if not given.
        :return: The details, e.g. 'Buy milk, Incomplete, Tomorrow, 10:00'
        """
        return self.driver.get_element(reminder_row(title)).get_attribute('label')

    @action(list_state)
    def complete_reminder(self, title: str, list_name: str = DEFAULT_LIST):
        """
        Marks a reminder as completed. Completed reminders are hidden from the list after a few seconds.

        :param title: The title of the reminder.
        :param list_name: Optional. The list of the reminder, the default list 'Reminders' if not given.
        """
        self.gtl_logger.info(f'Pressing the circle of reminder "{title}"')
        self.driver.click(reminder_circle(title))
        # completed reminders disappear from the list after a few seconds
        sleep(4)

    @action(list_state)
    def delete_reminder(self, title: str, list_name: str = DEFAULT_LIST):
        """
        Deletes a reminder, by swiping it to the left.

        :param title: The title of the reminder.
        :param list_name: Optional. The list of the reminder, the default list 'Reminders' if not given.
        """
        self.gtl_logger.info(f'Swiping reminder "{title}" to the left to reveal the delete button')
        _swipe_left(self.driver, reminder_row(title))
        self.gtl_logger.info('Pressing delete button')
        self.driver.click(LIST_SWIPE_DELETE_BUTTON)
        sleep(1)
        logger.info(f'Deleted reminder {title}')
