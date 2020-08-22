"""Constants for the KNX integration"""
from enum import Enum

DOMAIN = "xknx"


class ColorTempModes(Enum):
    """Color temperature modes for config validation."""

    absolute = "DPT-7.600"
    relative = "DPT-5.001"
