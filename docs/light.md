---
layout: default
title: Lights / Dimmer
parent: Devices
nav_order: 4
---

# [](#header-1)Light & Dimmer

## [](#header-2)Overview

The Light object is either a representation of a binary or dimm actor, LED-controller or DALI-gateway.

## [](#header-2)Interface

- `xknx` XKNX object.
- `name` name of the device.
- `group_address_switch` KNX group address to switch the light. *DPT 1.001*
- `group_address_switch_state` KNX group address for the state of the light. *DPT 1.001*
- `group_address_brightness` KNX group address to set the brightness. *DPT 5.001*
- `group_address_brightness_state` KNX group address for the current brightness state. *DPT 5.001*
- `group_address_color` KNX group address to set the RGB color. *DPT 232.600*
- `group_address_color_state` KNX group address for the current RGB color. *DPT 232.600*
- `group_address_rgbw` KNX group address to set the RGBW color. *DPT 251.600*
- `group_address_rgbw_state` KNX group address for the current RGBW color. *DPT 251.600*
- `group_address_tunable_white` KNX group address to set relative color temperature. *DPT 5.001*
- `group_address_tunable_white_state` KNX group address for the current relative color temperature. *DPT 5.001*
- `group_address_color_temperature` KNX group address to set absolute color temperature. *DPT 7.600*
- `group_address_color_temperature_state` KNX group address for the current absolute color temperature. *DPT 7.600*
- `min_kelvin` lowest possible color temperature in Kelvin. Default: 2700
- `max_kelvin` hightest possible color temperature in Kelvin. Default: 6000
- `device_updated_cb` awaitable callback for each update.
- `icon` for the light (see [icon documentation](https://www.home-assistant.io/docs/configuration/customizing-devices/#icon) for details).

## [](#header-2)Example

```python
light = Light(xknx,
              name='TestLight',
              group_address_switch='1/2/3',
              group_address_switch_state='1/2/4',
              group_address_brightness='1/2/5',
              group_address_brightness_state='1/2/6',
              group_address_color='1/2/7',
              group_address_color_state='1/2/8',
              group_address_rgbw='1/2/13',
              group_address_rgbw_state='1/2/14',
              group_address_tunable_white='1/2/9',
              group_address_tunable_white_state='1/2/10',
              group_address_color_temperature='1/2/11',
              group_address_color_temperature_state='1/2/12')

# Switching light on
await light.set_on()

# Switching light off
await light.set_off()

# Set brightness
await light.set_brightness(23)

# Set color
await light.set_color((20, 70,200))

# Set rgbw color
await light.set_color((20,70,200), 30)

# Set relative color temperature (percent)
await set_tunable_white(25)

# Set absolute color temperature (Kelvin)
await set_color_temperature(3300)

# Accessing light via 'do'
await light.do('on')
await light.do('off')
await light.do('brightness:80')
await light.do('tunable_white:75')
await light.do('color_temperature:5000')

# Accessing state
print(light.state)
print(light.supports_brightness)
print(light.current_brightness)
print(light.supports_color)
print(light.current_color)
print(light.supports_rgbw)
print(light.supports_tunable_white)
print(light.current_tunable_white)
print(light.supports_color_temperature)
print(light.current_color_temperature)

# Requesting current state via KNX GROUP WRITE
await light.sync()
```

## [](#header-2)Configuration via **xknx.yaml**

Lights are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:
    light:

        # Lights with dimming
        Kitchen.Light_1:     {group_address_switch: '1/6/1', group_address_brightness: '1/6/3'}
        Diningroom.Light_1:  {group_address_switch: '1/6/4', group_address_brightness: '1/6/6', icon: "mdi:ceiling-light" }

        # Light without dimming
        Living-Room.Light_1: {group_address_switch: '1/6/7'}

        # Light with extra addresses for states:
        Office.Light_1:  {group_address_switch: '1/7/4', group_address_switch_state: '1/7/5', group_address_brightness: '1/7/6', group_address_brightness_state: '1/7/7'}

        # Light with color temperature in Kelvin
        Living-Room.Light_CT:  {group_address_switch: '1/6/11', group_address_switch_state: '1/6/10', group_address_brightness: '1/6/12', group_address_brightness_state: '1/6/13', group_address_color_temperature: '1/6/14',  group_address_color_temperature_state: '1/6/15'}

        # Light with color temperature in percent
        Living-Room.Light_TW:  {group_address_switch: '1/6/21', group_address_switch_state: '1/6/20', group_address_brightness: '1/6/22', group_address_brightness_state: '1/6/23', group_address_tunable_white: '1/6/24',  group_address_tunable_white_state: '1/6/25'}

```

