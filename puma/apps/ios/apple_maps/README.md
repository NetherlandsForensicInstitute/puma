# Apple Maps - iOS

Apple Maps is the maps application built into iOS.
Apple Maps is part of iOS, so its version is the iOS version.

## Prerequisites
- An iOS device or simulator running iOS 26
- Apple Maps needs to know the location of the device to plan routes. On a simulator, set the location with
  `xcrun simctl location <udid> set <latitude>,<longitude>`, or with the route simulator (see below).

### Initialization is standard:

```python
from puma.apps.ios.apple_maps.apple_maps import AppleMaps, TransportType
phone = AppleMaps("C14C2402-9144-4BC2-9866-A1DB5AFAD376")
```

### Navigating the UI

You can search for places, and plan routes:

```python
phone.search_place("Eiffel Tower")
phone.search_place("coffee")    # opens the first search result
phone.get_directions("Eiffel Tower", TransportType.BIKE)
phone.start_navigation("Eiffel Tower", TransportType.CAR)
```

Note that turn-by-turn navigation (`start_navigation`) is not available on the iOS simulator, only on real devices.

### Simulating routes

Like for Google Maps on Android, the route simulator can be used to spoof the location of the device along a route:

```python
from geopy import Point

route_simulator = phone.get_route_simulator()
route_simulator.update_speed(50)
route_simulator.execute_route_with_points([Point(48.8606, 2.3376), Point(48.8584, 2.2945)])
```
