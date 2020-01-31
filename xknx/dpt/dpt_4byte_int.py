"""
Implementation of Basic KNX 4-Byte Signed and Unsigned Values.

They correspond the following KNX DPTs:
    12.yyy 4-byte/octet unsigned value, i.e. pulse counter
    13.yyy 4-byte/octet signed (2's complement), i.e. flow, energy
"""

import struct

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPT4ByteUnsigned(DPTBase):
    """
    Abstraction for KNX 4 Byte "32-bit unsigned".

    DPT 12.***
    """

    value_min = 0
    value_max = 4294967295
    unit = ""
    resolution = 1
    payload_length = 4

    _struct_format = ">I"

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 4)

        try:
            return struct.unpack(cls._struct_format, bytes(raw))[0]
        except struct.error:
            raise ConversionError("Cant parse %s" % cls.__name__, raw=raw)

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            return tuple(struct.pack(cls._struct_format, knx_value))
        except (ValueError, struct.error):
            raise ConversionError("Cant serialize %s" % cls.__name__, value=value)

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPT4ByteSigned(DPT4ByteUnsigned):
    """
    Abstraction for KNX 4 Byte "32-bit signed".

    DPT 13.***
    """

    value_min = -2147483648
    value_max = 2147483647
    unit = ""
    resolution = 1

    _struct_format = ">i"

class DPTActiveEnergy(DPT4ByteSigned):
    """DPT 13.010 DPT_ActiveEnergy."""

    value_min = -2147483648
    value_max = 2147483647
    unit = "Wh"
    resolution = 1

class DPTApparantEnergy(DPT4ByteSigned):
    """DPT 13.011 DPT_ApparantEnergy."""

    value_min = -2147483648
    value_max = 2147483647
    unit = "VAh"
    resolution = 1

class DPTReactiveEnergy(DPT4ByteSigned):
    """DPT 13.012 DPT_ReactiveEnergy."""

    value_min = -2147483648
    value_max = 2147483647
    unit = "VARh"
    resolution = 1

class DPTActiveEnergykWh(DPT4ByteSigned):
    """DPT 13.013 DPT_ActiveEnergy_kWh."""

    value_min = -2147483648
    value_max = 2147483647
    unit = "kWh"
    resolution = 1


class DPTApparantEnergykVAh(DPT4ByteSigned):
    """DPT 13.014 DPT_ApparantEnergy_kVAh."""

    value_min = -2147483648
    value_max = 2147483647
    unit = "kVAh"
    resolution = 1

class DPTReactiveEnergykVARh(DPT4ByteSigned):
    """DPT 13.015 DPT_ReactiveEnergy_kVARh."""

    value_min = -2147483648
    value_max = 2147483647
    unit = "kVARh"
    resolution = 1

