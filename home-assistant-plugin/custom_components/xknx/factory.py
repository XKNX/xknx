"""Factory function to initialize KNX devices from config."""
from homeassistant.const import CONF_ADDRESS, CONF_NAME, CONF_TYPE
from homeassistant.helpers.typing import ConfigType
from xknx import XKNX
from xknx.devices import Climate as XknxClimate
from xknx.devices import ClimateMode as XknxClimateMode
from xknx.devices import Cover as XknxCover
from xknx.devices import Device as XknxDevice
from xknx.devices import Light as XknxLight
from xknx.devices import Notification as XknxNotification
from xknx.devices import Scene as XknxScene
from xknx.devices import Sensor as XknxSensor
from xknx.devices import Switch as XknxSwitch

from .const import ColorTempModes, DeviceTypes
from .schema import (
    ClimateSchema,
    CoverSchema,
    LightSchema,
    SceneSchema,
    SensorSchema,
    SwitchSchema,
)


def create_knx_device(
    device_type: DeviceTypes, knx_module: XKNX, config: ConfigType
) -> XknxDevice:
    """Factory for creating KNX devices."""
    if device_type is DeviceTypes.light:
        return __create_light(knx_module, config)

    if device_type is DeviceTypes.cover:
        return __create_cover(knx_module, config)

    if device_type is DeviceTypes.climate:
        return __create_climate(knx_module, config)

    if device_type is DeviceTypes.climate_mode:
        return __create_climate_mode(knx_module, config)

    if device_type is DeviceTypes.switch:
        return __create_switch(knx_module, config)

    if device_type is DeviceTypes.sensor:
        return __create_sensor(knx_module, config)

    if device_type is DeviceTypes.notify:
        return __create_notify(knx_module, config)

    if device_type is DeviceTypes.scene:
        return __create_scene(knx_module, config)


def __create_cover(knx_module: XKNX, config: ConfigType) -> XknxCover:
    """Creates a KNX Cover device to be used within XKNX."""
    return XknxCover(
        knx_module,
        name=config[CONF_NAME],
        group_address_long=config.get(CoverSchema.CONF_MOVE_LONG_ADDRESS),
        group_address_short=config.get(CoverSchema.CONF_MOVE_SHORT_ADDRESS),
        group_address_stop=config.get(CoverSchema.CONF_STOP_ADDRESS),
        group_address_position_state=config.get(
            CoverSchema.CONF_POSITION_STATE_ADDRESS
        ),
        group_address_angle=config.get(CoverSchema.CONF_ANGLE_ADDRESS),
        group_address_angle_state=config.get(CoverSchema.CONF_ANGLE_STATE_ADDRESS),
        group_address_position=config.get(CoverSchema.CONF_POSITION_ADDRESS),
        travel_time_down=config[CoverSchema.CONF_TRAVELLING_TIME_DOWN],
        travel_time_up=config[CoverSchema.CONF_TRAVELLING_TIME_UP],
        invert_position=config[CoverSchema.CONF_INVERT_POSITION],
        invert_angle=config[CoverSchema.CONF_INVERT_ANGLE],
    )


def __create_light(knx_module: XKNX, config: ConfigType) -> XknxLight:
    """Creates a KNX Light device to be used within XKNX."""
    group_address_tunable_white = None
    group_address_tunable_white_state = None
    group_address_color_temp = None
    group_address_color_temp_state = None
    if config[LightSchema.CONF_COLOR_TEMP_MODE] == ColorTempModes.absolute:
        group_address_color_temp = config.get(LightSchema.CONF_COLOR_TEMP_ADDRESS)
        group_address_color_temp_state = config.get(
            LightSchema.CONF_COLOR_TEMP_STATE_ADDRESS
        )
    elif config[LightSchema.CONF_COLOR_TEMP_MODE] == ColorTempModes.relative:
        group_address_tunable_white = config.get(LightSchema.CONF_COLOR_TEMP_ADDRESS)
        group_address_tunable_white_state = config.get(
            LightSchema.CONF_COLOR_TEMP_STATE_ADDRESS
        )

    return XknxLight(
        knx_module,
        name=config[CONF_NAME],
        group_address_switch=config[CONF_ADDRESS],
        group_address_switch_state=config.get(LightSchema.CONF_STATE_ADDRESS),
        group_address_brightness=config.get(LightSchema.CONF_BRIGHTNESS_ADDRESS),
        group_address_brightness_state=config.get(
            LightSchema.CONF_BRIGHTNESS_STATE_ADDRESS
        ),
        group_address_color=config.get(LightSchema.CONF_COLOR_ADDRESS),
        group_address_color_state=config.get(LightSchema.CONF_COLOR_STATE_ADDRESS),
        group_address_rgbw=config.get(LightSchema.CONF_RGBW_ADDRESS),
        group_address_rgbw_state=config.get(LightSchema.CONF_RGBW_STATE_ADDRESS),
        group_address_tunable_white=group_address_tunable_white,
        group_address_tunable_white_state=group_address_tunable_white_state,
        group_address_color_temperature=group_address_color_temp,
        group_address_color_temperature_state=group_address_color_temp_state,
        min_kelvin=config[LightSchema.CONF_MIN_KELVIN],
        max_kelvin=config[LightSchema.CONF_MAX_KELVIN],
    )


def __create_climate(knx_module: XKNX, config: ConfigType) -> XknxClimate:
    """Creates a KNX Climate device to be used within XKNX."""
    return XknxClimate(
        knx_module,
        name=config[CONF_NAME],
        group_address_temperature=config[ClimateSchema.CONF_TEMPERATURE_ADDRESS],
        group_address_target_temperature=config.get(
            ClimateSchema.CONF_TARGET_TEMPERATURE_ADDRESS
        ),
        group_address_target_temperature_state=config[
            ClimateSchema.CONF_TARGET_TEMPERATURE_STATE_ADDRESS
        ],
        group_address_setpoint_shift=config.get(
            ClimateSchema.CONF_SETPOINT_SHIFT_ADDRESS
        ),
        group_address_setpoint_shift_state=config.get(
            ClimateSchema.CONF_SETPOINT_SHIFT_STATE_ADDRESS
        ),
        setpoint_shift_mode=config[ClimateSchema.CONF_SETPOINT_SHIFT_MODE],
        setpoint_shift_max=config[ClimateSchema.CONF_SETPOINT_SHIFT_MAX],
        setpoint_shift_min=config[ClimateSchema.CONF_SETPOINT_SHIFT_MIN],
        temperature_step=config[ClimateSchema.CONF_TEMPERATURE_STEP],
        group_address_on_off=config.get(ClimateSchema.CONF_ON_OFF_ADDRESS),
        group_address_on_off_state=config.get(ClimateSchema.CONF_ON_OFF_STATE_ADDRESS),
        min_temp=config.get(ClimateSchema.CONF_MIN_TEMP),
        max_temp=config.get(ClimateSchema.CONF_MAX_TEMP),
        on_off_invert=config[ClimateSchema.CONF_ON_OFF_INVERT],
    )


def __create_climate_mode(knx_module: XKNX, config: ConfigType) -> XknxClimateMode:
    """Creates a KNX Climate Mode device to be used within XKNX."""
    return XknxClimateMode(
        knx_module,
        name=f"{config[CONF_NAME]} Mode",
        group_address_operation_mode=config.get(
            ClimateSchema.CONF_OPERATION_MODE_ADDRESS
        ),
        group_address_operation_mode_state=config.get(
            ClimateSchema.CONF_OPERATION_MODE_STATE_ADDRESS
        ),
        group_address_controller_status=config.get(
            ClimateSchema.CONF_CONTROLLER_STATUS_ADDRESS
        ),
        group_address_controller_status_state=config.get(
            ClimateSchema.CONF_CONTROLLER_STATUS_STATE_ADDRESS
        ),
        group_address_controller_mode=config.get(
            ClimateSchema.CONF_CONTROLLER_MODE_ADDRESS
        ),
        group_address_controller_mode_state=config.get(
            ClimateSchema.CONF_CONTROLLER_MODE_STATE_ADDRESS
        ),
        group_address_operation_mode_protection=config.get(
            ClimateSchema.CONF_OPERATION_MODE_FROST_PROTECTION_ADDRESS
        ),
        group_address_operation_mode_night=config.get(
            ClimateSchema.CONF_OPERATION_MODE_NIGHT_ADDRESS
        ),
        group_address_operation_mode_comfort=config.get(
            ClimateSchema.CONF_OPERATION_MODE_COMFORT_ADDRESS
        ),
        group_address_operation_mode_standby=config.get(
            ClimateSchema.CONF_OPERATION_MODE_STANDBY_ADDRESS
        ),
        group_address_heat_cool=config.get(ClimateSchema.CONF_HEAT_COOL_ADDRESS),
        group_address_heat_cool_state=config.get(
            ClimateSchema.CONF_HEAT_COOL_STATE_ADDRESS
        ),
        operation_modes=config.get(ClimateSchema.CONF_OPERATION_MODES),
    )


def __create_switch(knx_module: XKNX, config: ConfigType) -> XknxSwitch:
    """Creates a KNX switch to be used within XKNX."""
    return XknxSwitch(
        knx_module,
        name=config[CONF_NAME],
        group_address=config[CONF_ADDRESS],
        group_address_state=config.get(SwitchSchema.CONF_STATE_ADDRESS),
    )


def __create_sensor(knx_module: XKNX, config: ConfigType) -> XknxSensor:
    """Creates a KNX sensor to be used within XKNX."""
    return XknxSensor(
        knx_module,
        name=config[CONF_NAME],
        group_address_state=config[SensorSchema.CONF_STATE_ADDRESS],
        sync_state=config[SensorSchema.CONF_SYNC_STATE],
        value_type=config[CONF_TYPE],
    )


def __create_notify(knx_module: XKNX, config: ConfigType) -> XknxNotification:
    """Creates a KNX notification to be used within XKNX."""
    return XknxNotification(
        knx_module, name=config[CONF_NAME], group_address=config[CONF_ADDRESS],
    )


def __create_scene(knx_module: XKNX, config: ConfigType) -> XknxScene:
    """Creates a KNX scene to be used within XKNX."""
    return XknxScene(
        knx_module,
        name=config[CONF_NAME],
        group_address=config[CONF_ADDRESS],
        scene_number=config[SceneSchema.CONF_SCENE_NUMBER],
    )
