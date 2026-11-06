# Apple Maps - iOS

Apple Maps is the maps application built into iOS, developed by Apple.
Puma supports part of the features of Apple Maps.
For detailed information on each method, see the method its PyDoc documentation.

Apple Maps is part of iOS, so its version is the iOS version.

## Prerequisites

- An iOS device or simulator running iOS 26, set up as described in [Setting up iOS](../../../../docs/setup-ios.md)
- Device language needs to be set to English
- Apple Maps needs to know the location of the device to plan routes. On a simulator, set the location
  with `xcrun simctl location <udid> set <latitude>,<longitude>`, or with the route simulator (see below).

## Initialization

Initialization is standard:

```python
from puma.apps.ios.apple_maps.apple_maps import AppleMaps, TransportType

phone = AppleMaps("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
```

On a real device, also pass the signing settings for WebDriverAgent as `desired_capabilities`, see
[Setting up iOS](../../../../docs/setup-ios.md).

## Searching and directions

You can search for places, and plan routes:

```python
phone.search_place("Eiffel Tower")
phone.search_place("coffee")    # opens the first search result
phone.get_directions("Eiffel Tower", TransportType.BIKE)
phone.start_navigation("Eiffel Tower", TransportType.CAR)
phone.end_navigation()
```

Note that turn-by-turn navigation (`start_navigation`) is not available on the iOS simulator, only on real devices.

## Traveling routes

Like for Google Maps on Android, Puma can travel a route: the location of the device is moved along the route, while
Apple Maps navigates to the destination. The route is planned with OpenStreetMap, by car, bike or on foot.

```python
phone.start_route("Louvre, Paris", "Eiffel Tower, Paris", speed=15, transport_type=TransportType.BIKE)
phone.driver.update_route_speed(25)                           # change the speed (km/h) on the way
phone.driver.wait_until_route_finished()                      # wait until the destination is reached
phone.stop_route()                                            # stop, end the navigation, reset the location
```

On a real device, Apple Maps starts turn-by-turn navigation. On a simulator, turn-by-turn navigation is not available,
so Apple Maps shows the directions while the device moves. On a real device, the simulated location stays active until
`stop_route()` is called, or the device is restarted.

### Spoofing the location directly

The driver can also travel your own points or a GPX file, or set a single location. A device travels one route at a
time: starting a second route raises an error until the first is stopped.

```python
from geopy import Point

phone.driver.start_route_with_points([Point(48.8606, 2.3376), Point(48.8584, 2.2945)], speed=50)
phone.driver.stop_route()
phone.driver.start_route_with_gpx('route.gpx', speed=15)
phone.driver.stop_route()
phone.driver.set_location(48.8584, 2.2945)
phone.driver.reset_location()
```
