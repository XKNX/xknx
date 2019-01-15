---
layout: default
---

# [](#header-1)Covers and Shutters

## [](#header-2)Overview

Shutters are simple representations of blind/roller cover actuators. With XKNX you can move them up, down, to direct positions or stop them. Internally the class provides a calculation which calculates the current position while traveling.

## [](#header-2)Example

```python
cover = Cover(xknx,
              'TestCover',
              group_address_long='1/2/1',
              group_address_short='1/2/2',
              group_address_position='1/2/3',
              group_address_position_feedback='1/2/4',
              travel_time_down=50,
              travel_time_up=60)

xknx.devices.add(cover)

# Accessing cover
await xknx.devices['TestShutter'].set_up()
```

## [](#header-2)Configuration via **xknx.yaml**

Covers are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:
    cover:
        Livingroom.Shutter_1: {group_address_long: '1/4/1', group_address_short: '1/4/2', group_address_position_feedback: '1/4/3', group_address_position: '1/4/4', travel_time_down: 50, travel_time_up: 60 }
```


## [](#header-2)Interface


```python
cover = Cover(xknx,
              'TestCover',
              group_address_long='1/2/1',
              group_address_short='1/2/2',
              group_address_position='1/2/3',
              group_address_position_feedback='1/2/4',
              travel_time_down=50,
              travel_time_up=60)

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

# Requesting current state
# If requested position was not reached yet, XKNX will calculate the position
# out of last known position and defined traveling times
position = cover.current_position()

# Helper functions to see if cover is traveling or has reached final position
is_traveling = cover.is_traveling()
position_reached = cover.position_reached()

# Helper functions to see if cover is fully closed or fully open
is_open = cover.is_open()
is_closed = cover.is_closed()

# Accessing cover via 'do'
await cover.do('up')
await cover.do('short_up')
await cover.do('down')
await cover.do('short_down')

# Requesting state via KNX GROUP WRITE
await cover.sync()
```


