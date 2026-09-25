from datetime import datetime
from time import sleep

from puma.state_graph.locators import accessibility_id, ios_class_chain, ios_predicate
from puma.state_graph.puma_driver import PumaDriver, PumaClickException

# The iOS date picker in its calendar style, used by e.g. Calendar and Reminders
DATE_PICKER = '//XCUIElementTypeDatePicker'
DATE_PICKER_MONTH = ios_predicate('type == "XCUIElementTypeButton" AND name == "Month"')
DATE_PICKER_PREVIOUS_MONTH = accessibility_id('DatePicker.PreviousMonth')
DATE_PICKER_NEXT_MONTH = accessibility_id('DatePicker.NextMonth')
# The iOS time picker, with wheels for the hours and minutes (and AM/PM on devices using a 12-hour clock)
PICKER_WHEEL = '//XCUIElementTypePickerWheel'


def date_picker_day(date: datetime) -> str:
    """
    A day in the date picker. Other buttons in the app can have the same name (e.g. the week at the top of the day view
    in Calendar), so the day is looked up inside the date picker only.
    """
    name = f'{date.strftime("%A")}, {date.strftime("%B")} {date.day}'
    return ios_class_chain(f'**/XCUIElementTypeDatePicker/**/XCUIElementTypeButton[`name == "{name}" OR name == "Today, {name}"`]')


def select_date(driver: PumaDriver, date: datetime):
    """
    Selects a date in an open date picker: navigates to the month of the date, and taps the day.

    :param driver: The PumaDriver.
    :param date: The date to select.
    """
    target_month = datetime(date.year, date.month, 1)
    for _ in range(240):
        shown_month = datetime.strptime(driver.get_element(DATE_PICKER_MONTH).get_attribute('value'), '%B %Y')
        if shown_month == target_month:
            break
        driver.click(DATE_PICKER_NEXT_MONTH if shown_month < target_month else DATE_PICKER_PREVIOUS_MONTH)
        sleep(0.5)
    driver.click(date_picker_day(date))


def _set_wheel(wheel, value: int):
    """
    Sets a picker wheel of the time picker to a number. Depending on the device settings, the values of the wheel are
    shown with or without a leading zero (e.g. '09 o’clock' or '9 o’clock'), so both are tried.
    """
    for text in (f'{value:02d}', str(value)):
        wheel.send_keys(text)
        if wheel.get_attribute('value').startswith(text + ' '):
            return
    raise PumaClickException(f'Could not set picker wheel to {value}, its value is {wheel.get_attribute("value")}')


def select_time(driver: PumaDriver, time: datetime):
    """
    Selects a time in an open time picker.

    :param driver: The PumaDriver.
    :param time: The time to select. Only the hours and minutes are used.
    """
    wheels = driver.get_elements(PICKER_WHEEL)
    if len(wheels) == 3:
        _set_wheel(wheels[0], time.hour % 12 or 12)
        wheels[2].send_keys(time.strftime('%p'))
    else:
        _set_wheel(wheels[0], time.hour)
    _set_wheel(wheels[1], time.minute)
    sleep(0.5)
