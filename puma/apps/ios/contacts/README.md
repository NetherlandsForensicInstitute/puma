# Contacts - iOS

Contacts is the address book application built into iOS.
Contacts is part of iOS, so its version is the iOS version.

## Prerequisites
- An iOS device or simulator running iOS 26

### Initialization is standard:

```python
from puma.apps.ios.contacts.contacts import Contacts
phone = Contacts("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
```

### Navigating the UI

You can add, view and delete contacts. Contacts are identified by their full name, as shown in the contact list:

```python
phone.add_contact("Bob", "Puma", phone_number="+31687654321", email="bob@example.com", company="NFI")
phone.get_contact_details("Bob Puma")   # ['mobile, +31 6 87 65 43 21', 'home, bob@example.com']
phone.delete_contact("Bob Puma")
```
