# Google Maps - Android

Google Maps is a consumer mapping and navigation application offered by Google.
Puma supports searching places, showing directions, navigating, and traveling a route by spoofing the location of the
device. For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded
in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.google.android.apps.maps).

### Prerequisites

- The application installed on your device
- Location services turned on, and Google Maps allowed to access the location of the device
- For traveling routes: Appium Settings (`io.appium.settings`, installed by Appium) allowed as mock location app. Appium
  allows it when it starts a session; if spoofing has no effect, select it in Developer options > Select mock location
  app

### Initialization

Initialization is standard:

```python
from puma.apps.android.google_maps.google_maps import GoogleMaps, TransportType

phone = GoogleMaps("emulator-5444")
```

### Searching places

You can search for a location with a text search:

```python
phone.search_place('eiffel tower')  # searches for the eiffel tower
phone.search_place('Laan van Ypenburg 6, The Hague')  # specific places give better results
phone.search_place('52°35\'05.6"N 5°22\'53.2"E')  # coordinates are also possible!
```

The text is simply inserted into the search box, and Puma will pick the first suggested result.

### Directions and navigation

```python
phone.get_directions('eiffel tower')  # shows the directions from the current location
phone.start_navigation('eiffel tower')  # starts navigating to the eiffel tower
phone.start_navigation('eiffel tower', transport_type=TransportType.BIKE)  # CAR or BIKE. CAR is the default
phone.start_navigation('eiffel tower', time_to_wait=20)  # wait up to 20 seconds for the route, instead of 10
phone.end_navigation()
```

### Traveling a route

Navigation starts from the location of the device, but since your (virtual) device isn't moving, nothing much
happens. Therefore Puma can spoof the location of the device along a route:

```python
# this will start driving from the NFI to the eiffel tower at 100 kmph
phone.start_route('laan van ypenburg 6', 'eiffel tower', 100)
phone.stop_route()  # stop, end the navigation, reset the location
# we can also travel by bike (default is CAR, just like when planning navigation)
phone.start_route('eiffel tower', 'laan van ypenburg 6', 40, transport_type=TransportType.BIKE)
```

This method call does several things:

1. look up the route using OpenStreetMap, and move the device to the start of the route
2. start the navigation in the Google Maps UI
3. move the device along the route at the given speed

Because the route for location spoofing comes from a different source than the route Google Maps will show in the UI,
your car might drive a different route than what Google Maps has planned. A device travels one route at a time:
starting a second route raises an error until the first is stopped.

⚠️ Make sure you're using specific addresses: if OpenStreetMap cannot find your start or end position, this method
raises an exception.

On a real device, `stop_route()` resets the location to the real location of the device. On an emulator this is not
possible: the device stays at the last spoofed location.

#### Changing speed

While your route is being traveled, you can change the speed through the driver to make the route more realistic:

```python
phone.driver.update_route_speed(50)  # 50 kmph
phone.driver.update_route_speed(0)  # make a stop
phone.driver.update_route_speed(100, variance_absolute=10)  # drive 100 kmph, + or - 10 kmph
phone.driver.update_route_speed(50, variance_relative=0.2)  # drive 50 kmph, + or - 20%
phone.driver.wait_until_route_finished()  # wait until the destination is reached
```

When using variance in the speed, the speed will constantly change within the defined margin, simulating 'real'
driving.

#### Spoofing the location directly

The driver can also travel your own points or a GPX file, or set a single location, in any app:

```python
from geopy import Point

phone.driver.start_route_with_points([Point(52.0, 4.3), Point(52.1, 4.3)], speed=50)
phone.driver.stop_route()
phone.driver.start_route_with_gpx('route.gpx', speed=15)
phone.driver.stop_route()
phone.driver.set_location(52.0, 4.3)
phone.driver.reset_location()
```
