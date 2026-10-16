# Calendar - iOS

Calendar is the calendar application built into iOS, developed by Apple.
Puma supports part of the features of Calendar.
For detailed information on each method, see the method its PyDoc documentation.

Calendar is part of iOS, so its version is the iOS version.

## Prerequisites

- An iOS device or simulator running iOS 26, set up as described in [Setting up iOS](../../../../docs/setup-ios.md)
- Device language needs to be set to English

## Initialization

Initialization is standard:

```python
from puma.apps.ios.calendar.calendar import Calendar

phone = Calendar("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
```

On a real device, also pass the signing settings for WebDriverAgent as `desired_capabilities`, see
[Setting up iOS](../../../../docs/setup-ios.md).

## Managing events

You can add, view and delete events in the default calendar. Events are identified by their title:

```python
from datetime import datetime

phone.add_event("Meeting", datetime(2026, 10, 12, 14, 0), datetime(2026, 10, 12, 16, 0), location="NFI The Hague")
phone.add_event("Day off", datetime(2026, 10, 13), all_day=True)
phone.get_event_details("Meeting")   # ['Meeting', 'NFI The Hague', 'Monday, 12 Oct 2026', '14:00 – 16:00']
phone.delete_event("Meeting")
```

The location is used as text; it is not looked up in Apple Maps.

### All-day events

Events are found using the search in Calendar, which does not find all-day events. For all-day events, pass the date of
the event:

```python
phone.get_event_details("Day off", date=datetime(2026, 10, 13))
phone.delete_event("Day off", date=datetime(2026, 10, 13))
```
