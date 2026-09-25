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
phone = AppleMaps("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
```

### Navigating the UI

You can search for places, and plan routes:

```python
phone.search_place("Eiffel Tower")
phone.search_place("coffee")    # opens the first search result
phone.get_directions("Eiffel Tower", TransportType.BIKE)
phone.start_navigation("Eiffel Tower", TransportType.CAR)
phone.end_navigation()
```

Note that turn-by-turn navigation (`start_navigation`) is not available on the iOS simulator, only on real devices.

### Traveling routes

Like for Google Maps on Android, Puma can travel a route: the location of the device is moved along the route, while
Apple Maps navigates to the destination. The route is planned with OpenStreetMap, by car, bike or on foot.

```python
phone.start_route("Louvre, Paris", "Eiffel Tower, Paris", speed=15, transport_type=TransportType.BIKE)
phone.get_route_simulator().update_speed(25)                  # change the speed (km/h) on the way
phone.get_route_simulator().wait_until_route_finished()       # wait until the destination is reached
phone.stop_route()                                            # stop, end the navigation, reset the location
```

On a real device, Apple Maps starts turn-by-turn navigation. On a simulator, turn-by-turn navigation is not available,
so Apple Maps shows the directions while the device moves. On a real device, the simulated location stays active until
`stop_route()` is called, or the device is restarted.

The route simulator can also be used directly, to travel along your own points or a GPX file:

```python
from geopy import Point

route_simulator = phone.get_route_simulator()
route_simulator.update_speed(50)
route_simulator.execute_route_with_points([Point(48.8606, 2.3376), Point(48.8584, 2.2945)])
```
