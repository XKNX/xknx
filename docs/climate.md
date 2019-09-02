---
layout: default
---

# [](#header-1)HVAC/Climate controls

## [](#header-2)Overview

Climate are representations of KNX HVAC/Climate controls.

## [](#header-2)Example

```python
climate_setpoint_shift = Climate(
    xknx,
    'TestClimateSPS',
    group_address_temperature='1/2/2',
    group_address_target_temperature_state='1/2/5',
    group_address_setpoint_shift='1/2/3',
    group_address_setpoint_shift_state='1/2/4'
)

climate_target_temp = Climate(
    xknx,
    'TestClimateTT',
    group_address_temperature='2/2/2',
    group_address_target_temperature='2/2/3',
    group_address_target_temperature_state='2/2/4'
)
``` 

## [](#header-2)Configuration via **xknx.yaml**

Climate devices are usually configured via [`xknx.yaml`](/configuration):

```yaml
groups:
    climate:
        Children.Climate: {group_address_temperature: '1/7/2', group_address_setpoint_shift: '1/7/3', group_address_target_temperature_state: '1/7/4'}
        Office.Climate: {group_address_temperature: '1/7/5', group_address_operation_mode: '1/7/6'}
        Attic.Climate: {group_address_temperature: '1/7/7', group_address_operation_mode_protection: '1/7/8', group_address_operation_mode_night: '1/7/9', group_address_operation_mode_comfort: '1/7/10'}
```

## [](#header-2)Interface

* **group_address_temperature** KNX address of current room temperature
* **group_address_setpoint_shift** KNX address to set setpoint_shift (base temperature deviation).
* **group_address_setpoint_shift_state** KNX address to read current setpoint_shift.
* **group_address_target_temperature** KNX address for setting the target temperature if setpoint shift is not supported.
* **group_address_target_temperature_state** KNX address for reading the target temperature from the KNX bus. Used in for setpoint_shift calculations.


* **group_address_operation_mode** KNX address for operation mode.
* **group_address_operation_mode_state** KNX address for operation mode status.
* **group_address_operation_mode_protection** KNX address for switching on/off frost/heat protection mode.
* **group_address_operation_mode_night** KNX address for switching on/off night nmode.
* **group_address_operation_mode_comfort** KNX address for switching on/off comfort mode.
* **group_address_operation_mode** KNX address for controller status.
* **group_address_operation_mode_state** KNX address for controller status state.
* **group_address_operation_mode** KNX address for controller mode.
* **group_address_operation_mode_state** KNX address for controller mode status.

`group_address_operation_mode_protection` / `group_address_operation_mode_night` / `group_address_operation_mode_comfort` are not necessary if `group_address_operation_mode` was specified.


```python
climate_mode = ClimateMode(xknx,
                 'TestClimateMode',
                 group_address_operation_mode='',
                 group_address_operation_mode_state='',
                 group_address_operation_mode_protection=None,
                 group_address_operation_mode_night=None,
                 group_address_operation_mode_comfort=None,
                 group_address_controller_status=None,
                 group_address_controller_status_state=None,
                 group_address_controller_mode=None,
                 group_address_controller_mode_state=None,
                 operation_modes=None,
                 device_updated_cb=None)

climate = Climate(
        xknx,
        'TestClimate',
        group_address_temperature='',
        group_address_target_temperature='',
        group_address_target_temperature_state='',
        group_address_setpoint_shift='',
        group_address_setpoint_shift_state='',
        setpoint_shift_step=0.1,
        setpoint_shift_max=6,
        setpoint_shift_min=-6,
        group_address_on_off='',
        group_address_on_off_state='',
        on_off_invert=False,
        min_temp=18,
        max_temp=26,
        mode=climate_mode,
        device_updated_cb=None)

# Set target temperature to 23 degrees. Works with setpoint_shift too.
await climate.set_target_temperature(23)
# Set new setpoint shift value.
await climate.set_setpoint_shift(1)
# Reading climate device
await climate.sync()
print("Current temperature: ", climate.temperature)
```
