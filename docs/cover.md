---
layout: default
title: Cover
parent: Devices
nav_order: 3
---

# [](#header-1)Covers and Shutters

## [](#header-2)Overview

Shutters are simple representations of blind/roller cover actuators. With XKNX you can move them up, down, to direct positions or stop them. Internally the class calculates the current position while traveling.

## [](#header-2)Interface

- `xknx` XKNX object.
- `name` name of the device.
- `group_address_long` KNX group address to move the cover to an end position. *DPT 1.001*
- `group_address_short` KNX group address to move the cover stepwise. *DPT 1.001*
- `group_address_stop` KNX group address to stop movement. *DPT 1.001*
- `group_address_position` KNX group address to move to relative position. *DPT 5.001*
- `group_address_position_state` KNX group address for retrieving the relative position. *DPT 5.001*
- `group_address_angle` KNX group address to tilt blinds to relative position. *DPT 5.001*
- `group_address_angle_state` KNX group address to retrieve angle of blinds. *DPT 5.001*
- `group_address_locked_state` KNX group address to retrieve if manual interaction with the cover is currently disabled. *DPT 1.001*
- `sync_state` defines if and how often the value should be actively read from the bus. If `False` no GroupValueRead telegrams will be sent to its group address. Defaults to `True`
- `travel_time_down` seconds to reach lower end position. Default: 22
- `travel_time_up` seconds to reach upper end position. Default: 22
- `invert_updown` invert up/down binary payload. Default: False
- `invert_position` invert position percentage from / to KNX bus. Default: False
- `invert_angle` invert angle from / to KNX bus. Default: False
- `device_updated_cb` awaitable callback for each update.

## [](#header-2)Example

```python
cover = Cover(
    xknx,
    'TestCover',
    group_address_long='1/2/1',
    group_address_short='1/2/2',
    group_address_position='1/2/3',
    group_address_position_state='1/2/4',
    group_address_angle='1/2/5',
    group_address_angle_state='1/2/6',
    group_address_locked_state='1/2/7',
    travel_time_down=50,
    travel_time_up=60,
    invert_position=False,
    invert_angle=False,
)

# Moving to up position
await cover.set_up()

# Moving to down position
await cover.set_down()

# Moving cover a step up
await cover.set_short_up()

# Moving cover a step down
await cover.set_short_down()

# Stopping cover
await cover.stop()

# Moving cover to absolute position
await cover.set_position(50)

# Tilting blinds to absolute position
await cover.set_angle(50)

# Requesting current state
# If requested position was not reached yet, XKNX will calculate the position
# out of last known position and defined traveling times
position = cover.current_position()
angle = cover.current_angle()

# Helper functions to see if cover is traveling or has reached final position
is_traveling = cover.is_traveling()
position_reached = cover.position_reached()

# Helper functions to see if cover is fully closed or fully open or moving
is_open = cover.is_open()
is_closed = cover.is_closed()
is_traveling = cover.is_traveling()
is_opening = cover.is_opening()
is_closing = cover.is_closing()
is_locked = cover.is_locked()

# Requesting state via KNX GroupValueRead
await cover.sync()
```
