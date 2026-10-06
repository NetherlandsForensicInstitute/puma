from time import sleep

from puma.apps.ios.contacts import logger
from puma.apps.ios.contacts.locators import *
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
    driver.click(NEW_CONTACT_CLOSE_BUTTON)
    sleep(1)
    if driver.is_present(NEW_CONTACT_DISCARD_CHANGES_BUTTON):
        driver.click(NEW_CONTACT_DISCARD_CHANGES_BUTTON)


class ContactState(SimpleState, ContextualState):
    """
    A state representing the details of a single contact.
    """

    def __init__(self, parent_state):
        super().__init__(xpaths=[CONTACT_NAVIGATION_BAR, CONTACT_NAME_HEADER, CONTACT_EDIT_BUTTON],
                         parent_state=parent_state)

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
    contact_list_state = SimpleState(xpaths=[CONTACT_LIST_NAVIGATION_BAR, CONTACT_LIST_ADD_BUTTON], initial_state=True)
    new_contact_state = SimpleState(xpaths=[NEW_CONTACT_NAVIGATION_BAR, NEW_CONTACT_FIRST_NAME,
                                            NEW_CONTACT_DONE_BUTTON],
                                    parent_state=contact_list_state,
                                    parent_state_transition=_close_new_contact)
    # the parent transition is the default back action, which uses the back button in the navigation bar
    contact_state = ContactState(parent_state=contact_list_state)

    # Transitions
    contact_list_state.to(new_contact_state, compose_clicks([CONTACT_LIST_ADD_BUTTON], 'open_new_contact'))
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
        self.gtl_logger.info(f'Entering first name "{first_name}"')
        self.driver.get_element(NEW_CONTACT_FIRST_NAME).send_keys(first_name)
        if last_name:
            self.gtl_logger.info(f'Entering last name "{last_name}"')
            self.driver.get_element(NEW_CONTACT_LAST_NAME).send_keys(last_name)
        if company:
            self.gtl_logger.info(f'Entering company "{company}"')
            self.driver.get_element(NEW_CONTACT_COMPANY).send_keys(company)
        if phone_number:
            self.gtl_logger.info(f'Adding phone number "{phone_number}"')
            self.driver.click(NEW_CONTACT_ADD_PHONE)
            self.driver.get_element(NEW_CONTACT_PHONE_FIELD).send_keys(phone_number)
        if email:
            self.gtl_logger.info(f'Adding email address "{email}"')
            self.driver.click(NEW_CONTACT_ADD_EMAIL)
            self.driver.get_element(NEW_CONTACT_EMAIL_FIELD).send_keys(email)
        self.gtl_logger.info('Pressing done button')
        self.driver.click(NEW_CONTACT_DONE_BUTTON)
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
        self.gtl_logger.info('Pressing edit button')
        self.driver.click(CONTACT_EDIT_BUTTON)
        sleep(1)
        # The delete button is at the bottom of the edit form. Make sure it is on screen before tapping it, otherwise
        # the tap can be lost on real devices.
        for _ in range(5):
            if self.driver.get_element(CONTACT_DELETE_BUTTON).get_attribute('visible') == 'true':
                break
            self.gtl_logger.info('Scrolling down to the delete button')
            self.driver._scroll_down()
        self.gtl_logger.info('Pressing delete contact button')
        self.driver.click(CONTACT_DELETE_BUTTON)
        sleep(1)
        self.gtl_logger.info('Confirming deletion')
        self.driver.click_alert_button(CONTACT_CONFIRM_DELETE_LABEL)
        sleep(1)
        logger.info(f'Deleted contact {name}')
