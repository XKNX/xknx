---
layout: default
title: Climate / HVAC
parent: Devices
nav_order: 2
---

# [](#header-1)HVAC/Climate controls

## [](#header-2)Overview

Climate are representations of KNX HVAC/Climate controls.

## [](#header-2)Interface

- `xknx` is the XKNX object.
- `name` is the name of the object.
- `group_address_temperature` KNX address of current room temperature. *DPT 9.001*
- `group_address_target_temperature` KNX address for setting the target temperature if setpoint shift is not supported. *DPT 9.001*
- `group_address_target_temperature_state` KNX address for reading the target temperature from the KNX bus. Used in for setpoint_shift calculations as base temperature. *DPT 9.001*
- `group_address_setpoint_shift` KNX address to set setpoint_shift (base temperature deviation). *DPT 6.010* or *DPT 9.002*
- `group_address_setpoint_shift_state` KNX address to read current setpoint_shift. *DPT 6.010* or *DPT 9.002*
- `setpoint_shift_mode` SetpointShiftMode Enum for setpoint_shift payload encoding. When `None` it is inferred from first incoming payload. Default: `None`
- `setpoint_shift_max` Maximum value for setpoint_shift.
- `setpoint_shift_min` Minimum value for setpoint_shift.
- `temperature_step` Set the multiplier for setpoint_shift calculations when DPT 6.010 is used.
- `group_address_on_off` KNX address for turning climate device on or off. *DPT 1*
- `group_address_on_off_state` KNX address for reading the on/off state. *DPT 1*
- `on_off_invert` Invert on/off. Default: `False`
- `group_address_active_state` KNX address for reading if the climate device is currently active. *DPT 1*
- `group_address_command_value_state` KNX address for reading the current command value / valve position in %. *DPT 5.001*
- `sync_state` defines if and how often the value should be actively read from the bus. If `False` no GroupValueRead telegrams will be sent to its group address. Defaults to `True`
- `max_temp` Maximum value for target temperature.
- `min_temp` Minimum value for target temperature.
- `mode` ClimateMode instance for this climate device
- `group_address_operation_mode` KNX address for operation mode. *DPT 20.102*
- `group_address_operation_mode_state` KNX address for operation mode status. *DPT 20.102*
- `group_address_operation_mode_protection` KNX address for switching on/off frost/heat protection mode. *DPT 1*
- `group_address_operation_mode_night` KNX address for switching on/off night nmode. *DPT 1*
- `group_address_operation_mode_comfort` KNX address for switching on/off comfort mode. *DPT 1*
- `group_address_operation_mode_standby` KNX address for switching on/off standby mode. *DPT 1*
- `group_address_controller_status` KNX address for controller status.
- `group_address_controller_status_state` KNX address for controller status state.
- `group_address_controller_mode` KNX address for controller mode. *DPT 20.105*
- `group_address_controller_mode_state` KNX address for controller mode status. *DPT 20.105*
- `group_address_heat_cool` KNX address for switching heating / cooling mode. *DPT 1*
- `group_address_heat_cool_state` KNX address for reading heating / cooling mode. *DPT 1*
- `operation_modes` Overrides the supported operation modes.
- `controller_modes` Overrides the supported controller modes.
- `device_updated_cb` awaitable callback for each update.

**Note:** `group_address_operation_mode_protection` / `group_address_operation_mode_night` / `group_address_operation_mode_comfort` / `group_address_operation_mode_standby` are not necessary if `group_address_operation_mode` was specified. When one of these is set `True`, the others will be set `False`. When one of these is set `Standby`, `Comfort`, `Frost_Protection` and `Night` will be set as supported. If `group_address_operation_mode_standby` is omitted, `Standby` is set when the other 3 are set to `False`.
If only a subset of operation modes shall be used a list of supported modes may be passed to `operation_modes`.

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
                 controller_modes=None,
                 device_updated_cb=None)

climate = Climate(
        xknx,
        'TestClimate',
        group_address_temperature='',
        group_address_target_temperature='',
        group_address_target_temperature_state='',
        group_address_setpoint_shift='',
        group_address_setpoint_shift_state='',
        temperature_step=0.1,
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
await climate.sync(wait_for_result=True)
print("Current temperature: ", climate.temperature)
# Shutdown the Climate and the underlying ClimateMode!
climate.shutdown()
```

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
