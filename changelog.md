Changelog
=========

Upcoming version (unreleased)
-----------------------------


0.11.2 Add invert for climate on_off; fixed RGBW lights and stability improvements  2019-09-29
----------------------------------------------------------------------------------------------

## New Features

*  Sensor: add DPT 9.006 as pressure_2byte #223 (@michelde)
*  Climate: add new attribute on_off_invert #225 (@tombbo)

## Bugfixes

* Light: Fix for wrong structure of RGBW DPT 251.600 #231 (@dstrigl)
* Core: Correct handling of E_NO_MORE_CONNECTIONS within ConnectResponses #217 (@Julius2342)
* Core: Fix exceptions #234 (@elupus)
* Core: Avoid leaking ValueError exception on unknown APCI command #235 (@elupus)
* add tests for Climate on_off_invert (#233) @farmio
* merge HA plugin from upstream 0.97.2 (#224) @farmio 
* Small adjustments to the sensor documentation and example (#219) @biggestj 
* merge HA plugin from upstream @farmio


0.11.1 Bugfix release 2019-07-08
--------------------------------

* Optionally disable reading (GroupValueRead) for sensor and binary_sensor #216 @farmio


0.11.0 Added new sensor types and fixed a couple of bugs 2019-06-12
-------------------------------------------------------------------

### Features

* Auto detection of local ip: #184 (@farmio )
* Added new sensor types and fix existing: #189 (@farmio )
        - binary mapped to RemoteValueSwitch
        - angle DPT 5.003
        - percentU8DPT 5.004 (1 byte unscaled)
        - percentV8 DPT 6.001 (1 byte signed unscaled)
        - counter_pulses DPT 6.010
        - DPT 8.*** types (percentV16, delta_time_*, rotation_angle, 2byte_signed and DPT-8)
        - luminous_flux DPT 14.042
        - pressure DPT 14.058
        - string DPT 16.000
        - scene_number DPT 17.001
* Binary values are now exposable
* Add support for RGBW lights - DPT 251.600: #191 #206 (@phbaer )
* Bump PyYAML to latest version (5.1): #204 (@Julius2342 )
* Add DPT-8 support for Sensors and HA Sensors: #208 (@farmio )

### Breaking changes

* Scene: scene_number is now 1 indexed according to KNX standards
* Replaced group_address in BinarySensor with group_address_state (not for Home Assistant component)

### Bugfixes

* Fix pulse sensor type: #187 (@farmio )
* Fix climate device using setpoint_shift: #190 (@farmio )
* Read binary sensors on startup: #199 (@farmio )
* Updated YAML to use safe mode: #196 (@farmio )
* Update README.md #195 (thanks @amp-man)
* Code refactoring: #200 (@farmio )
* Fix #194, #193, #129, #116, #114
* Fix #183 and #148 through #190 (@farmio )


0.10.0 Bugfix release 2019-02-22
--------------------------------

* Connection config can now be configured in xknx.yml (#179 @farmio )
* (breaking change) Introduced target_temperature_state for climate devices (#175 @marvin-w )
* Introduce a configurable rate limit (#178 @marvin-w)
* updated HA plugin (#174 @marvin-w)
* Migrate documentation in main project (#168 @marvin-w)
* documentation updates (@farmio & @marvin-w)


0.9.4 - Release 2019-01-01
--------------------------

* updated hass plugin (@marvin-w #162)
* tunable white and color temperature for lights (@farmio #154)


0.9.3 - Release 2018-12-23
--------------------------

* updated requirements (added flake8-isort)
* some more unit tests
* Breaking Change:
  ClimateMode is now a member of Climate (the hass plugin
  needs this kind of dependency. Please note the updated xknx.yml)


0.9.2 - Release 2018-12-22
--------------------------

* Min and max values for Climate device
* Splitted up Climate in Climate and ClimateMode
* added __contains__ method for Devices class.
* fixed KeyError when action refers to a non existing device.


0.9.1 - Release 2018-10-28
--------------------------

* state_addresses of binary_sesor should return emty value if no
  state address is set.
* state_address for notification device


0.9.0 - Release 2018-09-23
--------------------------

* Updated requirements
* Feature: Added new DPTs for DPTEnthalpy, DPTPartsPerMillion, DPTVoltage. Thanks @magenbrot #146
* Breaking Change: Only read explicit state addresses #140
* Minor: Fixed some comments,  @magenbrot #145
* Minor: lowered loglevel from INFO to DEBUG for 'correct answer from KNX bus' @magenbrot #144
* Feature: Add fan device,  @itineric #139
* Bugfix: Tunnel: Use the bus address assigned by the server,  @M-o-a-T #141
* Bugfix: Adde:wd a check for windows because windows does not support add_signal  @pulse-mind #135
* Bugfix: correct testing if xknx exists within self  @FireFrei #131  
* Feature: Implement support to automatically reconnect KNX/IP tunnel,  @rnixx #125
* Feature: Adjusted to Home Assistant's changes to light colors @oliverblaha #128
* Feature: Scan multiple gateways @DrMurx #111
* Bugfix: Pylint errors @rnixx #132
* Typo: @itineric #124
* Feature: Add support for KNX DPT 20.105  @cian #122


0.8.5 -Release 2018-03-10
-------------------------

* Bugfix: fixed string representation of GroupAddress https://github.com/home-assistant/home-assistant/issues/13049


0.8.4 -Release 2018-03-04
--------------------------

* Bugfix: invert scaling value #114
* Minor: current_brightness and current_color are now properties
* Feature: Added DPT 5.010 DPTValue1Ucount @andreasnanko #109


0.8.3 - Release 2018-02-05
--------------------------

* Color support for HASS plugin
* Bugfixes (esp problem with unhashable exceptions)
* Refactoring: splitted up remote_value.py
* Better test coverage  


0.8.1 - Release 2018-02-03
--------------------------

* Basic support for colored lights
* Better unit test coverage


0.8.0 - Release 2018-01-27
---------------------------

* New example for MQTT forwarder (thanks @JohanElmis)
* Splitted up Address into GroupAddress and PhysicalAddress (thanks @encbladexp) 
* Time object was renamed to Datetime and does now support different broadcast types "time", "date" and "datetime" (thanks @Roemer)
* Many new DTP datapoints esp for physical values (thanks @Straeng and @JohanElmis)
* new asyncio `await` syntax
* new device "ExposeSensor" to read a local value from KNX bus or to expose a local value to KNX bus.
* Support for KNX-scenes
* better test coverage
* Fixed versions for dependencies (@encbladexp)

And many more smaller improvements :-)


0.7.7-0.7.18 - Release 2017-11-05
---------------------------------

* Many iterations and bugfixes to get climate support with setpoint shift working.
* Support for invert-position and invert-angle within cover.
* State updater may be switched of within home assistant plugin


0.7.6 - Release 2017-08-09
--------------------------

Introduced KNX HVAC/Climate support with operation modes (Frost protection, night, comfort).


0.7.0 - Released 2017-07-30
---------------------------

### More asyncio:

More intense usage of asyncio. All device operations and callback functions are now async. 

E.g. to switch on a light you have to do:

```python
await light.set_on()
```

See updated [examples](https://github.com/XKNX/xknx/tree/master/examples) for details.

### Renaming of several objects:

The naming of some device were changed in order to get the nomenclature closer to several other automation projects and to avoid confusion. The device objects were also moved into `xknx.devices`.

#### Climate

Renamed class `Thermostat` to `Climate` . Plase rename the section within configuration:

```yaml
groups:
    climate:
        Cellar.Thermostat: {group_address_temperature: '6/2/0'}
```

#### Cover

Renamed class `Shutter` to `Cover`. Plase rename the section within configuration:

```yaml
groups:
   cover:
        Livingroom.Shutter_1: {group_address_long: '1/4/1', group_address_short: '1/4/2', group_address_position_feedback: '1/4/3', group_address_position: '1/4/4', travel_time_down: 50, travel_time_up: 60 }
```

#### Binary Sensor

Renamed class `Switch` to `BinarySensor`. Plase rename the section within configuration:

```yaml
groups:
    binary_sensor:
        Kitchen.3Switch1:
            group_address: '5/0/0'
```

Sensors with `value_type=binary` are now integrated into the `BinarySensor` class:

```yaml
groups:
    binary_sensor:
        SleepingRoom.Motion.Sensor: {group_address: '6/0/0', device_class: 'motion'}
        ExtraRoom.Motion.Sensor: {group_address: '6/0/1', device_class: 'motion'}
```

The attribute `significant_bit` is now only possible within `binary_sensors`:

```yaml
groups:
    binary_sensor_motion_dection:
        Kitchen.Thermostat.Presence: {group_address: '3/0/2', device_class: 'motion', significant_bit: 2}
```

#### Switch

Renamed `Outlet` to `Switch` (Sorry for the confusion...). The configuration now looks like:

```yaml
groups:
    switch:
        Livingroom.Outlet_1: {group_address: '1/3/1'}
        Livingroom.Outlet_2: {group_address: '1/3/2'}
```


Within `Light` class i introduced an attribute `group_address_brightness_state`. The attribute `group_address_state` was renamed to `group_address_switch_state`. I also removed the attribute `group_address_dimm` (which did not have any implemented logic).


Version 0.6.2 - Released 2017-07-24
-----------------------------------

XKNX Tunnel now does hartbeat - and reopens connections which are no longer valid.


Version 0.6.0 - Released 2017-07-23
-----------------------------------

Using `asyncio` interface, XKNX has now to be stated and stopped asynchronously:

```python
import asyncio
from xknx import XKNX, Outlet

async def main():
    xknx = XKNX()
    await xknx.start()
    outlet = Outlet(xknx,
                    name='TestOutlet',
                    group_address='1/1/11')
    outlet.set_on()
    await asyncio.sleep(2)
    outlet.set_off()
    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

`sync_state` was renamed to `sync`:

````python
await sensor2.sync()
```


