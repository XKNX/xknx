"""Helper class for KNX DPT unsigned int."""
import struct
from xknx.exceptions import ConversionError

from .helper import test_bytesarray


class DPTInteger(object):
    """Abstraction for KNX int."""

    # pylint: disable=too-many-arguments

    @classmethod
    def from_knx(cls, raw, octets=1, min_value=None, max_value=None, signed=False):
        """Parse/deserialize from KNX/IP raw data."""
        if max_value is None:
            max_value = cls._calc_max_value(octets, signed)
        if min_value is None:
            min_value = cls._calc_min_value(octets, signed)

        test_bytesarray(raw, octets)

        try:
            value = struct.unpack(cls._struct_format(octets, signed), bytes(raw))[0]
        except struct.error:
            raise ConversionError("Cant parse Integer", raw=raw)

        if not cls._test_boundaries(value, min_value, max_value):
            raise ConversionError("Integer extended max/min value", value=value, raw=raw)

        return value

    @classmethod
    def to_knx(cls, value, octets=1, min_value=None, max_value=None, signed=False):
        """Serialize to KNX/IP raw data."""
        if max_value is None:
            max_value = cls._calc_max_value(octets, signed)
        if min_value is None:
            min_value = cls._calc_min_value(octets, signed)
        if not isinstance(value, (int)):
            raise ConversionError("Cant serialize Integer", value=value)
        if not cls._test_boundaries(value, min_value, max_value):
            raise ConversionError("Cant serialize Integer", value=value)
        try:
            return tuple(struct.pack(cls._struct_format(octets, signed), value))
        except struct.error:
            raise ConversionError("Cant serialize Integer", value=value)

    @staticmethod
    def _struct_format(octets, signed):
        """Determine struct format for packing/unpacking bytes."""
        if octets == 4:
            return ">i" if signed else ">I"
        if octets == 2:
            return ">h" if signed else ">H"
        if octets == 1:
            return ">b" if signed else ">B"
        raise ConversionError("Cant handle number of octetx", octets=octets)

    @staticmethod
    def _calc_max_value(octets, signed):
        """Calculate the max value of integer."""
        return (256**octets)/2-1 if signed else 256**octets-1

    @staticmethod
    def _calc_min_value(octets, signed):
        """Calculate the min value of integer."""
        return -(256**octets)/2 if signed else 0

    @classmethod
    def _test_boundaries(cls, value, min_value, max_value):
        """Test if value is within defined range for this object."""
        return value >= min_value and \
            value <= max_value
