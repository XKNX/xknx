---
layout: default
title: Devices
nav_order: 4
has_children: true
---

# [](#header-1)Devices

XKNX uses devices to separate different functionality in logical groups like lights, climate et al.
They are also needed in order to provide support for the home assistant plugin.

An instantiated device is automatically added to `xknx.devices`.

## [](#header-2)Common public interface for all Device classes

* `xknx` is the XKNX object.
* `name` is the name of the object.
* `device_updated_cb` List of awaitable callbacks for each update.
* `group_address*` Group address for a specific function. If a list is passed the first element is used for sending / reading,  the rest are passively updating state (listening group address).

* `has_group_address(group_address)` Test if device has given group address.
* `sync(wait_for_result)` Read states of device from KNX bus via GroupValueRead requests.
* `register_device_updated_cb(device_updated_cb)` Register device updated callback.
* `unregister_device_updated_cb(device_updated_cb)` Unregister device updated callback.
* `shutdown()` Remove callbacks and device form Devices vector.

## [](#header-2)Device classes

The following pages will give you an overview over the available devices within XKNX.