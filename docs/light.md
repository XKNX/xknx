---
layout: default
title: Lights / Dimmer
parent: Devices
nav_order: 5
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
- `group_address_hue` KNX group address to set the current hue. *DPT 5.003*
- `group_address_hue_state` KNX group address for the current hue. *DPT 5.003*
- `group_address_saturation` KNX group address to set the current saturation. *DPT 5.001*
- `group_address_saturation_state` KNX group address for the current saturation. *DPT 5.001*
- `group_address_xyy_color`: KNX group address to set the xyY color. *DPT 242.600*
- `group_address_xyy_color_state`: KNX group address for the current xyY color. *DPT 242.600*
- `group_address_tunable_white` KNX group address to set relative color temperature. *DPT 5.001*
- `group_address_tunable_white_state` KNX group address for the current relative color temperature. *DPT 5.001*
- `group_address_color_temperature` KNX group address to set absolute color temperature. *DPT 7.600 or 9*
- `group_address_color_temperature_state` KNX group address for the current absolute color temperature. *DPT 7.600 or 9*

- `group_address_switch_red` KNX group address to switch the red component. *DPT 1.001*
- `group_address_switch_red_state` KNX group address for the state of the red component. *DPT 1.001*
- `group_address_brightness_red` KNX group address to set the brightness of the red component. *DPT 5.001*
- `group_address_brightness_red_state` KNX group address for the current brightness of the red component. *DPT 5.001*
- `group_address_switch_green` KNX group address to switch the green component. *DPT 1.001*
- `group_address_switch_green_state` KNX group address for the state of the green component. *DPT 1.001*
- `group_address_brightness_green` KNX group address to set the brightness of the green component. *DPT 5.001*
- `group_address_brightness_green_state` KNX group address for the current brightness of the green component. *DPT 5.001*
- `group_address_switch_blue` KNX group address to switch the blue component. *DPT 1.001*
- `group_address_switch_blue_state` KNX group address for the state of the blue component. *DPT 1.001*
- `group_address_brightness_blue` KNX group address to set the brightness of the blue component. *DPT 5.001*
- `group_address_brightness_blue_state` KNX group address for the current brightness of the blue component. *DPT 5.001*
- `group_address_switch_white` KNX group address to switch the white component. *DPT 1.001*
- `group_address_switch_white_state` KNX group address for the state of the white component. *DPT 1.001*
- `group_address_brightness_white` KNX group address to set the brightness of the white component. *DPT 5.001*
- `group_address_brightness_white_state` KNX group address for the current brightness of the white component. *DPT 5.001*
- `color_temperature_type` defines if DPT 7.600 or 9 is used for absolute color temperature. Default is `ColorTemperatureType.UINT_2_BYTE` (7.600)
- `sync_state` defines if and how often the value should be actively read from the bus. If `False` no GroupValueRead telegrams will be sent to its group address. Defaults to `True`
- `min_kelvin` lowest possible color temperature in Kelvin. Default: 2700
- `max_kelvin` highest possible color temperature in Kelvin. Default: 6000
- `device_updated_cb` awaitable callback for each update.

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

# Update current state via KNX GroupValueRead
await light.sync(wait_for_result=True)

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
```

## [](#header-2)Example: RGBW light with individual group addresses for red, green, blue and white

```python
light = Light(xknx,
              name='TestRGBWLight',
              group_address_switch_red="1/1/1",
              group_address_switch_red_state="1/1/2",
              group_address_brightness_red="1/1/3",
              group_address_brightness_red_state="1/1/4",
              group_address_switch_green="1/1/5",
              group_address_switch_green_state="1/1/6",
              group_address_brightness_green="1/1/7",
              group_address_brightness_green_state="1/1/8",
              group_address_switch_blue="1/1/9",
              group_address_switch_blue_state="1/1/10",
              group_address_brightness_blue="1/1/11",
              group_address_brightness_blue_state="1/1/12",
              group_address_switch_white="1/1/13",
              group_address_switch_white_state="1/1/14",
              group_address_brightness_white="1/1/15",
              group_address_brightness_white_state="1/1/16")

# Switching light on
await light.set_on()

# Switching light off
await light.set_off()

# Set color
await light.set_color((20, 70,200))

# Set rgbw color
await light.set_color((20,70,200), 30)

# Accessing state
print(light.state)
print(light.supports_brightness)
print(light.supports_color)
print(light.supports_rgbw)
print(light.current_color)
print(light.supports_tunable_white)
print(light.supports_color_temperature)

# Requesting current state via KNX GroupValueRead for all _state addresses
await light.sync()

```

## [](#header-2)Example: HSV-color light

```python
light = Light(
    xknx,
    "Hue and saturation",
    group_address_switch="1/1/1",
    group_address_switch_state='1/2/1',
    group_address_brightness='1/1/2',
    group_address_brightness_state='1/2/2',
    group_address_hue="1/1/3",
    group_address_hue_state="1/2/3",
    group_address_saturation="1/1/4",
    group_address_saturation_state="1/2/4",
)
print(light.supports_brightness)
print(light.supports_hs_color)

await light.set_hs_color((25,40))
```
