# Reminders - iOS

Reminders is the reminders application built into iOS, developed by Apple.
Puma supports part of the features of Reminders.
For detailed information on each method, see the method its PyDoc documentation.

Reminders is part of iOS, so its version is the iOS version.

## Prerequisites

- An iOS device or simulator running iOS 26, set up as described in [Setting up iOS](../../../../docs/setup-ios.md)
- Device language needs to be set to English

## Initialization

Initialization is standard:

```python
from puma.apps.ios.reminders.reminders import Reminders

phone = Reminders("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
```

On a real device, also pass the signing settings for WebDriverAgent as `desired_capabilities`, see
[Setting up iOS](../../../../docs/setup-ios.md).

## Managing reminders

You can add, view, complete and delete reminders. Reminders are identified by their title, and are added to the default
list 'Reminders' unless another list is given:

```python
from datetime import datetime

phone.add_reminder("Buy milk")
phone.add_reminder("Dentist", notes="Bring insurance card", due=datetime(2026, 9, 28, 9, 30), due_time=True)
phone.get_reminders()                       # ['Buy milk', 'Dentist']
phone.get_reminder_details("Dentist")       # 'Dentist, Incomplete, 28/09/2026, 09:30'
phone.complete_reminder("Buy milk")
phone.delete_reminder("Dentist")
```

Flagging reminders is not supported: the flag option is not available on the simulator, where this app was developed.

## Managing lists

```python
phone.add_list("Groceries")
phone.add_reminder("Apples", list_name="Groceries")
phone.get_reminders(list_name="Groceries")  # ['Apples']
phone.delete_list("Groceries")
```
