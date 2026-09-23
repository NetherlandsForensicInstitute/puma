from time import sleep

from puma.apps.ios.contacts import logger
from puma.apps.ios.contacts.xpaths import *
from puma.state_graph.action import action
from puma.state_graph.locators import to_by_value
from puma.state_graph.puma_driver import PumaDriver, PumaClickException, Platform, supported_version
from puma.state_graph.state import SimpleState, ContextualState, compose_clicks
from puma.state_graph.state_graph import StateGraph

CONTACTS_BUNDLE_ID = 'com.apple.MobileAddressBook'


def _find_contact(driver: PumaDriver, name: str):
    """
    Finds a contact in the contact list, scrolling down and then up if needed, as only the contacts on screen are
    present in the UI hierarchy.
    """
    cell = contact_cell(name)
    if driver.is_present(cell):
        return driver.get_element(cell)
    try:
        return driver.swipe_to_find_element(cell, max_swipes=10, swipe_down=True)
    except PumaClickException:
        return driver.swipe_to_find_element(cell, max_swipes=20, swipe_down=False)


def _close_new_contact(driver: PumaDriver):
    """
    Closes the new contact form, discarding any changes.
    """
    driver.click(CLOSE_BUTTON)
    sleep(1)
    if driver.is_present(DISCARD_CHANGES_BUTTON):
        driver.click(DISCARD_CHANGES_BUTTON)


class ContactState(SimpleState, ContextualState):
    """
    A state representing the details of a single contact.
    """

    def __init__(self, parent_state):
        super().__init__(xpaths=[CONTACT_NAVIGATION_BAR, CONTACT_NAME_HEADER, EDIT_BUTTON], parent_state=parent_state)

    def validate_context(self, driver: PumaDriver, name: str = None) -> bool:
        if not name:
            return True
        return driver.is_present(contact_header(name))

    @staticmethod
    def open_contact(driver: PumaDriver, name: str):
        _find_contact(driver, name).click()


@supported_version("26.2")
class Contacts(StateGraph):
    """
    A class representing the Contacts application on iOS.
    Contacts are identified by their full name, as shown in the contact list.
    """
    platform = Platform.IOS

    # States
    contact_list_state = SimpleState(xpaths=[CONTACTS_NAVIGATION_BAR, ADD_CONTACT_BUTTON], initial_state=True)
    new_contact_state = SimpleState(xpaths=[NEW_CONTACT_NAVIGATION_BAR, FIRST_NAME, DONE_BUTTON],
                                    parent_state=contact_list_state,
                                    parent_state_transition=_close_new_contact)
    # the parent transition is the default back action, which uses the back button in the navigation bar
    contact_state = ContactState(parent_state=contact_list_state)

    # Transitions
    contact_list_state.to(new_contact_state, compose_clicks([ADD_CONTACT_BUTTON], 'open_new_contact'))
    contact_list_state.to(contact_state, contact_state.open_contact)

    def __init__(self, device_udid: str, **kwargs):
        """
        Initializes Contacts with a device UDID.

        :param device_udid: The unique device identifier of the iOS device or simulator.
        :param kwargs: Optional arguments passed to the StateGraph, such as appium_server or desired_capabilities.
        """
        StateGraph.__init__(self, device_udid, CONTACTS_BUNDLE_ID, **kwargs)

    @action(new_contact_state, end_state=contact_state)
    def add_contact(self, first_name: str, last_name: str = None, phone_number: str = None, email: str = None,
                    company: str = None):
        """
        Adds a new contact.

        :param first_name: The first name of the contact.
        :param last_name: Optional. The last name of the contact.
        :param phone_number: Optional. The (mobile) phone number of the contact.
        :param email: Optional. The email address of the contact.
        :param company: Optional. The company of the contact.
        """
        self.driver.get_element(FIRST_NAME).send_keys(first_name)
        if last_name:
            self.driver.get_element(LAST_NAME).send_keys(last_name)
        if company:
            self.driver.get_element(COMPANY).send_keys(company)
        if phone_number:
            self.driver.click(ADD_PHONE)
            self.driver.get_element(PHONE_FIELD).send_keys(phone_number)
        if email:
            self.driver.click(ADD_EMAIL)
            self.driver.get_element(EMAIL_FIELD).send_keys(email)
        self.driver.click(DONE_BUTTON)
        sleep(1)

    @action(contact_state)
    def get_contact_details(self, name: str) -> list[str]:
        """
        Returns the details shown for a contact, such as phone numbers and email addresses.

        :param name: The full name of the contact.
        :return: The details of the contact, e.g. ['mobile, +31 6 12 34 56 78', 'home, alice@example.com']
        """
        return [element.get_attribute('label') for element in
                self.driver.driver.find_elements(*to_by_value(CONTACT_DETAILS))]

    @action(contact_state, end_state=contact_list_state)
    def delete_contact(self, name: str):
        """
        Deletes a contact.

        :param name: The full name of the contact.
        """
        self.driver.click(EDIT_BUTTON)
        sleep(1)
        # The delete button is at the bottom of the edit form. Make sure it is on screen before tapping it, otherwise
        # the tap can be lost on real devices.
        for _ in range(5):
            if self.driver.get_element(DELETE_CONTACT).get_attribute('visible') == 'true':
                break
            self.driver._scroll_down()
        self.driver.click(DELETE_CONTACT)
        sleep(1)
        self.driver.click_alert_button(CONFIRM_DELETE_CONTACT_LABEL)
        sleep(1)
        logger.info(f'Deleted contact {name}')
