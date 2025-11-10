# Google Maps - Android

Google Maps is a consumer mapping and navigation application offered by Google.
Puma has limited support for Google Maps, allow users to search and navigate to locations.
For detailed information on each method, see the method its PyDoc documentation.

The application can be downloaded
in [the Google PlayStore](https://play.google.com/store/apps/details?id=com.google.android.apps.maps).

## Deprecation

This class does not use `StateGraph` as its base class, and has therefore been deprecated since Puma 3.0.0. It can still
be used, but it will not be maintained. If you want to add functionality, please rewrite this class using `StateGraph`
as the abstract base class. Also see the [CONTRIBUTING.md](../../../../CONTRIBUTING.md).

### Prerequisites

- The application installed on your device

### Initialization

Initialization is standard:

```python
from puma.apps.android.google_maps import GoogleMapsActions

phone = GoogleMapsActions("emulator-5444")
```

### Searching places

You can search for a location with a text search:

```python
phone.search_place('eiffel tower')  # searches for the eiffel tower
phone.search_place('McDonalds')  # It doesn't need to be a specific place...
phone.search_place('Laan van Ypenburg 6, The Hague')  # but specific places give better results
phone.search_place('52°35\'05.6"N 5°22\'53.2"E')  # coordinates are also possible!
```

The text is simply inserted into the search box, and Puma will pick the first suggested result.

### Starting navigation

You can start navigation:

```python
phone.search_place('eiffel tower')  # Searches for the eiffel tower and will then click to start navigation
phone.search_place('eiffel tower', transport_type=TransportType.BIKE)  # you can pick CAR or BIKE. CAR is the default
phone.search_place('eiffel tower',
                   wait_time=20)  # Google maps takes some time to load the route. By default we wait for 10 seconds before timing out, but you can increase this
```

### Starting navigation + location spoofing

The previous command starts navigation, but since your (virtual) device isn't moving, nothing much happens. Therefore
Puma supports location spoofing, and our Google Maps utilizes this:

```python
# this will start driving from the NFI to the eiffel tower at 100 kmph 
phone.start_route('laan van ypenburg 6', 'eiffel tower', 100)
# we can also travel by bike (default is CAR, jsut like when planning navigation)
phone.start_route('eiffel tower', 'laan van ypenburg 6', 40, transport_type=TransportType.BIKE)
```

This method call does several things:

1. lookup the route using OpenStreetMap, loading the GPS points of this route for location spoofing
2. start the navigation in the Google Maps UI

Because the route for location spoofing comes from a different source than the route Google Maps will show in the UI,
your car might drive a different route than what Google Maps has planned.

⚠️ Make sure you're using specific addresses: if OSM cannot resolve your start or end position, this method will raise
an exception.

#### Changing speed

While your route is being traveled, you can change the speed to make the route more realistic

```python
phone.route_simulator.update_speed(50)  # 50 kmph
phone.route_simulator.update_speed(0)  # make a stop
phone.route_simulator.update_speed(100, variance_absolute=10)  # drive 100 kmph, + or - 10 kmph
phone.route_simulator.update_speed(50, variance_relative=0.2)  # drive 50 kmph, + or - 20%
```

When using variance in the peed, the speed will constantly change within the defined margin, simulating 'real' driving.