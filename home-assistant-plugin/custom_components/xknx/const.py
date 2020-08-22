"""Constants for the KNX integration"""
from enum import Enum

DOMAIN = "xknx"


class ColorTempModes(Enum):
    """Color temperature modes for config validation."""

    absolute = "DPT-7.600"
    relative = "DPT-5.001"


class DeviceTypes(Enum):
    """KNX device types"""

    cover = "cover"
    light = "light"
    binary_sensor = "binary_sensor"
    climate = "climate"
    switch = "switch"
    notify = "notify"
    scene = "scene"
    sensor = "sensor"
