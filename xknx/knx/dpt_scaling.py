
""" Implementation of Basic KNX DPT_Scaling (Percent) Values """

from .dpt import DPTBase, ConversionError

class DPTScaling(DPTBase):
    """
    Abstraction for KNX 1 Octet DPT_Scaling ()
    DPT 5.001
    """

    value_min = 0
    value_max = 100
    unit = ""
    resolution = 1

    @classmethod
    def from_knx(cls, raw):
        """Convert a 1 byte KNX Value to a scaling / percentage value"""
        cls.test_bytesarray(raw, 1)

        value = round((raw[0]/256)*100)

        if not cls.test_boundaries(value):
            raise ConversionError(value)

        return value

    @classmethod
    def to_knx(cls, value):
        """Convert a scaling / percentage value to a 1 byte KNX value"""

        if not isinstance(value, (int, float)):
            raise ConversionError(value)

        if not cls.test_boundaries(value):
            raise ConversionError(value)

        knx_value = round(value/100*255.4)

        return (knx_value,)

    @classmethod
    def test_boundaries(cls, value):
        return value >= cls.value_min and \
               value <= cls.value_max
