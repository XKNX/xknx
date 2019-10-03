---
layout: default
---

# [](#header-1)Sensor - Monitor values of KNX

## [](#header-2)Overview

Sensors are monitoring temperature, air humidity, pressure etc. from KNX bus.

```python
    sensor = Sensor(
        xknx=xknx,
        name='DiningRoom.Temperature.Sensor',
        group_address_state='6/2/1',
        sync_state=True,
        value_type='temperature'
    )
    await sensor.sync()
    print(sensor)
```

* `xknx` is the XKNX object.
* `name` is the name of the object.
* `group_address_state` is the KNX group address of the sensor device.
* `sync_state` defines if the value should be actively read from the bus. If `False` no GroupValueRead telegrams will be sent to its group address. Defaults to `True`
* `value_type` controls how the value should be rendered in a human readable representation. The attribut may have may have the values `percent`, `temperature`, `illuminance`, `speed_ms` or `current`.


## [](#header-2)Configuration via **xknx.yaml**

Sensor objects are usually configured via [`xknx.yaml`](/configuration):

```yaml
    sensor:
        Heating.Valve1: {group_address_state: '2/0/0', value_type: 'percent'}
        Heating.Valve2: {group_address_state: '2/0/1', value_type: 'percent', sync_state: False}
        Kitchen.Temperature: {group_address_state: '2/0/2', value_type: 'temperature'}
        Some.Other.Value: {group_address_state: '2/0/3'}
```

## [](#header-2)Interface

```python
sensor = Sensor(
        xknx=xknx,
        name='DiningRoom.Temperature.Sensor',
        group_address_state='6/2/1')

await sensor.sync() # Syncs the state. Tries to read the corresponding value from the bus.

sensor.resolve_state() # Returns the value of in a human readable way

sensor.unit_of_measurement() # returns the unit of the value in a human readable way
```


