# Reminders - iOS

Reminders is the reminders application built into iOS.
Reminders is part of iOS, so its version is the iOS version.

## Prerequisites
- An iOS device or simulator running iOS 26

### Initialization is standard:

```python
from puma.apps.ios.reminders.reminders import Reminders
phone = Reminders("C14C2402-9144-4BC2-9866-A1DB5AFAD376")
```

### Navigating the UI

You can add, complete and delete reminders, and add and delete lists. Reminders are identified by their title, and are
added to the default list 'Reminders' unless another list is given:

```python
from datetime import datetime

phone.add_reminder("Buy milk")
phone.add_reminder("Dentist", notes="Bring insurance card", due=datetime(2026, 9, 28, 9, 30), due_time=True)
phone.get_reminders()                       # ['Buy milk', 'Dentist']
phone.get_reminder_details("Dentist")       # 'Dentist, Incomplete, 28/09/2026, 09:30'
phone.complete_reminder("Buy milk")
phone.delete_reminder("Dentist")

phone.add_list("Groceries")
phone.add_reminder("Apples", list_name="Groceries")
phone.delete_list("Groceries")
```

Flagging reminders is not supported: the flag option is not available on the simulator, where this app was developed.
