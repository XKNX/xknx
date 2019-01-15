---
layout: default
---

# [](#header-1)Sensor - Monitor values of KNX

## [](#header-2)Overview

Sensors are monitoring temperature, air humidity, pressure etc. from KNX bus.

```python
    sensor = Sensor(
        xknx=xknx,
        name='DiningRoom.Temperatur.Sensor',
        group_address='6/2/1',
        value_type='float',
        device_class='temperature')
    await sensor2.sync()
    print(sensor2)
```

* `xknx` is the XKNX object.
* `name` is the name of the object.
* `group_address` is the KNX group address of the sensor device.
* `value_type` controls how the value should be rendered in a human readable representation. The attribut may have may have the values `percent`, `temperature`, `illuminance`, `speed_ms` or `current`.
* `device_class` may be used to store the type of sensor, e.g. "motion" for motion detectors.


## [](#header-2)Configuration via **xknx.yaml**

Sensor objects are usually configured via [`xknx.yaml`](/configuration):

```yaml
    sensor:
        Heating.Valve1: {group_address: '2/0/0', value_type: 'percent'}
        Heating.Valve2: {group_address: '2/0/1', value_type: 'percent'}
	Kitchen.Temperature: {group_address: '2/0/2', value_type: 'temperature'}
        Some.Other.Value: {group_address: '2/0/3'}
```

## [](#header-2)Interface

```python
sensor = Sensor(
        xknx=xknx,
        name='DiningRoom.Temperatur.Sensor',
        group_address='6/2/1')

await sensor.sync() # Syncs the state. Tries to read the corresponding value from the bus.

sensor.resolve_state() # Returns the value of in a human readable way

sensor.unit_of_measurement() # returns the unit of the value in a human readable way
```


