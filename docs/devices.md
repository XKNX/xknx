---
layout: default
title: Devices
nav_order: 4
has_children: true
---

# [](#header-1)Devices

XKNX uses devices to separate different functionality in logical groups like lights, climate et al.
They are also needed in order to provide support for the home assistant plugin.

An instantiated device can be added to `xknx.devices` to receive telegrams and start background tasks by calling `xknx.devices.async_add(device)`. It can be removed by calling `xknx.devices.async_remove(device)`.

## [](#header-2)Common public interface for all Device classes

* `xknx` is the XKNX object.
* `name` is the name of the object. It is optional and used for logging and string representations only - devices are never looked up by name. When omitted it defaults to the class name of the device - `ExposeSensor` appends its value type.
  It can be changed at any time; the new name is passed down to the devices `RemoteValue` instances, so log messages and exceptions use it too.

  ```python
  light = Light(xknx, group_address_switch="1/2/3")
  light.name  # "Light"
  light.name = "light.kitchen_ceiling"
  ```
* `device_updated_cb` List of callbacks for each update.
* `group_address*` Group address for a specific function. If a list is passed the first element is used for sending / reading,  the rest are passively updating state (listening group address).

* `group_addresses()` Returns a set of all configured group addresses of this Device.
* `has_group_address(group_address)` Test if device has given group address.
* `sync(wait_for_result)` Read states of device from KNX bus via GroupValueRead requests.
* `register_device_updated_cb(device_updated_cb)` Register device updated callback.
* `unregister_device_updated_cb(device_updated_cb)` Unregister device updated callback.

## [](#header-2)Example

```python
>>> light_s = Light(
...     xknx,
...     name="light with state address",
...     group_address_switch="0/2/2",
...     group_address_switch_state="0/3/3",
...     )
>>> light_s.switch.group_address # this is used to send payloads to the bus
GroupAddress("0/2/2")
>>> light_s.switch.group_address_state # group_address_*_state is used to send GroupValueRead requests to (from `sync()` or StateUpdater)
GroupAddress("0/3/3")
>>> light_s.switch.passive_group_addresses # none configured
[]
>>>
>>> light_p = Light(
...     xknx,
...     name="light with state and passive addresses",
...     group_address_switch=["1/2/2", "4/2/10", "4/2/20"],
...     group_address_switch_state=["1/3/3", "4/3/10", "4/3/20"],
...     )
>>> light_p.switch.group_address # this is used to send payloads to the bus
GroupAddress("1/2/2")
>>> light_p.switch.group_address_state # group_address_*_state is used for reading state from the bus
GroupAddress("1/3/3")
>>> light_p.switch.passive_group_addresses # these are only listening
[GroupAddress("4/2/10"), GroupAddress("4/2/20"), GroupAddress("4/3/10"), GroupAddress("4/3/20")]
```

## [](#header-2)Addresses

`GroupAddress` classes are initialized with strings or integers in the format “1/2/3” for 3-level GA-structure, “1/2” for 2-level GA-structure or “1” for free GA-structure.

`InternalGroupAddress` classes are initialized by prepending "i", "i-" or "i_" to any string. These can be used to connect xknx devices without sending telegrams to the KNX/IP interface.

Addresses passed to devices as arguments are initialized by `xknx.telegram.address.parse_device_group_address()` to create the according address class.

```python
>>> s = Switch(xknx,
...     name="Switch",
...     group_address=["1/2/3", "1/2/100", "i-🤖⚡️"],
...     )
>>> s.switch.group_address
GroupAddress("1/2/3")
>>> s.switch.passive_group_addresses
[GroupAddress("1/2/100"), InternalGroupAddress("i-🤖⚡️")]
```

## [](#header-2)Device classes

The following pages will give you an overview over the available devices within XKNX.
