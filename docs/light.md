---
layout: default
---

# [](#header-1)Light & Dimmer

## [](#header-2)Overview

The Light object is either a representation of a binary or a dimm actor. 

## [](#header-2)Example

```python
light = Light(xknx,
              name='TestLight',
              group_address_switch='1/2/3',
              group_address_brightness='1/2/5')
xknx.devices.add(light)

# Accessing light
await xknx.devices['TestLight'].set_on()
await xknx.devices['TestLight'].set_brightness(23)
``` 

## [](#header-2)Configuration via **xknx.yaml**

Outlets are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:
    light:

        # Lights with dimming
        Kitchen.Light_1:     {group_address_switch: '1/6/1', group_address_brightness: '1/6/3'}
        Diningroom.Light_1:  {group_address_switch: '1/6/4', group_address_brightness: '1/6/6'}

        # Light without dimming
        Living-Room.Light_1: {group_address_switch: '1/6/7'}

        # Light with extra addresses for states:
        Office.Light_1:  {group_address_switch: '1/7/4', group_address_switch_state: '1/7/5', group_address_brightness: '1/7/6', group_address_brightness_state: '1/7/7'}
```


## [](#header-2)Interface


```python
light = Light(xknx,
              name='TestLight',
              group_address_switch='1/2/3',
              group_address_switch_state='1/2/4',
              group_address_brightness='1/2/5',
              group_address_brightness_state='1/2/6')

# Switching light on
await light.set_on()

# Switching light off
await light.set_off()

# Set brightness
await light.set_brightness(23)

# Accessing light via 'do'
await light.do('on')
await light.do('off')
await light.do('brightness:80')

# Accessing state
print(light.state)
print(light.supports_dimming)
print(light.brightness)


# Requesting current state via KNX GROUP WRITE
await light.sync()
```


