---
layout: default
---

# [](#header-1)HVAC/Climate controls

## [](#header-2)Overview

Climate are representations of KNX HVAC/Climate controls.

## [](#header-2)Example

```python
climate = Climate(
    xknx,
    'TestClimate',
    group_address_temperature='1/2/2',
    group_address_setpoint='1/2/3',
    group_address_operation_mode='1/2/4')

# Setting basis setpoint to 23 degrees.
await climate.set_setpoint(23)))
# Reading climate device
await climate.sync()
print("Current temperature: ", climate.temperature)
``` 

## [](#header-2)Configuration via **xknx.yaml**

Switches are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:
    climate:
        Children.Climate: {group_address_temperature: '1/7/2', group_address_setpoint: '1/7/3', group_address_target_temperature: '1/7/4'}
        Office.Climate: {group_address_temperature: '1/7/5', group_address_operation_mode: '1/7/6'}
        Attic.Climate: {group_address_temperature: '1/7/7', group_address_operation_mode_protection: '1/7/8', group_address_operation_mode_night: '1/7/9', group_address_operation_mode_comfort: '1/7/10'}
```

* **group_address_temperature** KNX address of current room temperature
* **group_address_setpoint** KNX address of basis setpoint.
* **group_address_target_temperature** KNX address for reading the target temperature from KNX bus.
* **group_address_operation_mode** KNX address for operation mode.

* **group_address_operation_mode_protection** KNX address for switching on/off frost/heat protection mode.
* **group_address_operation_mode_night** KNX address for switching on/off night nmode.
* **group_address_operation_mode_comfort** KNX address for switching on/off comfort mode.

`group_address_operation_mode_protection` / `group_address_operation_mode_night` / `group_address_operation_mode_comfort` are not necessary if `group_address_operation_mode` was specified.
