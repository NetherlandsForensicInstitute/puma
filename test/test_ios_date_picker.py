import unittest
from datetime import datetime
from unittest.mock import Mock

from puma.apps.ios.date_picker import _set_wheel, select_date, select_time, date_picker_day, DATE_PICKER_MONTH, \
    DATE_PICKER_NEXT_MONTH, DATE_PICKER_PREVIOUS_MONTH
from puma.state_graph.locators import Locator
from puma.state_graph.puma_driver import PumaClickException


class FakeWheel:
    """A picker wheel that only accepts values in the given format, like the iOS time picker."""

    def __init__(self, value: str, zero_padded: bool):
        self.value = value
        self.zero_padded = zero_padded

    def send_keys(self, text: str):
        if (len(text) == 2) == self.zero_padded or not text.isdigit() or int(text) >= 10:
            self.value = f'{text} o’clock'

    def get_attribute(self, name):
        return self.value


class TestTimePicker(unittest.TestCase):
    def test_wheel_with_leading_zero(self):
        wheel = FakeWheel('22 o’clock', zero_padded=True)
        _set_wheel(wheel, 9)
        self.assertEqual('09 o’clock', wheel.value)

    def test_wheel_without_leading_zero(self):
        wheel = FakeWheel('10 o’clock', zero_padded=False)
        _set_wheel(wheel, 9)
        self.assertEqual('9 o’clock', wheel.value)

    def test_wheel_that_cannot_be_set(self):
        wheel = Mock()
        wheel.get_attribute.return_value = '22 o’clock'
        with self.assertRaises(PumaClickException):
            _set_wheel(wheel, 9)

    def test_select_time_24_hour_clock(self):
        hours, minutes = FakeWheel('22 o’clock', True), FakeWheel('00 o’clock', True)
        driver = Mock()
        driver.get_elements.return_value = [hours, minutes]
        select_time(driver, datetime(2026, 1, 1, 9, 5))
        self.assertEqual(('09 o’clock', '05 o’clock'), (hours.value, minutes.value))

    def test_select_time_12_hour_clock(self):
        hours, minutes, am_pm = FakeWheel('1 o’clock', False), FakeWheel('00 o’clock', True), Mock()
        driver = Mock()
        driver.get_elements.return_value = [hours, minutes, am_pm]
        select_time(driver, datetime(2026, 1, 1, 21, 30))
        self.assertEqual(('9 o’clock', '30 o’clock'), (hours.value, minutes.value))
        am_pm.send_keys.assert_called_with('PM')


class TestDatePicker(unittest.TestCase):
    def _driver(self, shown_month: datetime):
        """A driver with a date picker showing the given month, that navigates when the month buttons are clicked."""
        state = {'month': shown_month}
        driver = Mock()

        def get_element(locator):
            element = Mock()
            element.get_attribute.return_value = state['month'].strftime('%B %Y')
            return element

        def click(locator):
            month = state['month']
            if locator == DATE_PICKER_NEXT_MONTH:
                state['month'] = datetime(month.year + month.month // 12, month.month % 12 + 1, 1)
            elif locator == DATE_PICKER_PREVIOUS_MONTH:
                state['month'] = datetime(month.year - (month.month == 1), (month.month - 2) % 12 + 1, 1)

        driver.get_element.side_effect = get_element
        driver.click.side_effect = click
        return driver, state

    def test_navigates_forward_and_selects_day(self):
        driver, state = self._driver(datetime(2026, 11, 1))
        select_date(driver, datetime(2027, 2, 14))
        self.assertEqual(datetime(2027, 2, 1), state['month'])
        driver.click.assert_called_with(date_picker_day(datetime(2027, 2, 14)))

    def test_navigates_backward(self):
        driver, state = self._driver(datetime(2026, 3, 1))
        select_date(driver, datetime(2025, 12, 31))
        self.assertEqual(datetime(2025, 12, 1), state['month'])

    def test_day_locator_is_scoped_to_date_picker(self):
        # the week in the Calendar day view has buttons with the same names, so the day must be inside the date picker
        locator = date_picker_day(datetime(2026, 9, 25))
        self.assertIsInstance(locator, Locator)
        self.assertIn('XCUIElementTypeDatePicker', locator)
        self.assertIn('Friday, September 25', locator)
        self.assertIn('Today, Friday, September 25', locator)


if __name__ == '__main__':
    unittest.main()
