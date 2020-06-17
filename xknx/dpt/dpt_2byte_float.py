"""
Implementation of KNX 2 byte Float-values.

They correspond to the the following KDN DPT 9 class.
"""

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPT2ByteFloat(DPTBase):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.***
    """

    value_min = -671088.64
    value_max = 670760.96
    unit = ""
    resolution = 1
    payload_length = 2

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 2)
        data = (raw[0] * 256) + raw[1]
        exponent = (data >> 11) & 0x0f
        significand = data & 0x7ff
        sign = data >> 15

        if sign == 1:
            significand = significand - 2048

        value = float(significand << exponent) / 100

        if not cls._test_boundaries(value):
            raise ConversionError("Cant parse %s" % cls.__name__, value=value)

        return value

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        def calc_exponent(float_value, sign):
            """Return float exponent."""
            exponent = 0
            significand = abs(int(float_value * 100))

            while significand < -2048 or significand > 2048:
                exponent += 1
                significand >>= 1

            if sign:
                significand ^= 0x7ff  # invert
                significand += 1     # and add 1

            return exponent, significand

        try:
            knx_value = float(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError

            sign = 1 if knx_value < 0 else 0
            exponent, significand = calc_exponent(knx_value, sign)

            return (sign << 7) | (exponent << 3) | (significand >> 8), \
                significand & 0xff
        except ValueError:
            raise ConversionError("Cant serialize %s" % cls.__name__, value=value)

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTTemperature(DPT2ByteFloat):
    """DPT 9.001 DPT_Value_Temp."""

    value_min = -273
    value_max = 670760
    unit = "°C"
    ha_device_class = "temperature"
    resolution = 1


class DPTTemperatureDifference2Byte(DPT2ByteFloat):
    """DPT 9.002 DPT_Value_Tempd."""

    value_min = -670760
    value_max = 670760
    unit = "K"
    ha_device_class = "temperature"
    resolution = 1


class DPTTemperatureA(DPT2ByteFloat):
    """DPT 9.003 DPT_Value_Tempa."""

    value_min = -670760
    value_max = 670760
    unit = "K/h"
    resolution = 1


class DPTLux(DPT2ByteFloat):
    """DPT 9.004 DPT_Value_Lux."""

    value_min = 0
    value_max = 670760
    unit = "lx"
    ha_device_class = "illuminance"
    resolution = 1


class DPTWsp(DPT2ByteFloat):
    """DPT 9.005 DPT_Value_Ws Speed (m/s)."""

    value_min = 0
    value_max = 670760
    unit = "m/s"
    resolution = 1


class DPTPressure2Byte(DPT2ByteFloat):
    """DPT 9.006 DPT_Value_Pres (Pa)."""

    value_min = 0
    value_max = 670760
    unit = "Pa"
    ha_device_class = "pressure"
    resolution = 1


class DPTHumidity(DPT2ByteFloat):
    """DPT 9.007 DPT_Value_Humidity."""

    value_min = 0
    value_max = 670760
    unit = "%"
    ha_device_class = "humidity"
    resolution = 1


class DPTPartsPerMillion(DPT2ByteFloat):
    """DPT 9.008 DPT_Value_parts/million."""

    unit = "ppm"


class DPTTime1(DPT2ByteFloat):
    """DPT 9.010 DPT_Value_Time1 (s)."""

    value_min = -670760
    value_max = 670760
    unit = "s"
    resolution = 1


class DPTTime2(DPT2ByteFloat):
    """DPT 9.011 DPT_Value_Time2 (ms)."""

    value_min = -670760
    value_max = 670760
    unit = "ms"
    resolution = 1


class DPTVoltage(DPT2ByteFloat):
    """DPT 9.020 DPT_Value_Voltage."""

    unit = "mV"


class DPTCurrent(DPT2ByteFloat):
    """DPT 9.021 DPT_Value_Curr (mA)."""

    unit = "mA"


class DPTPowerDensity(DPT2ByteFloat):
    """DPT 9.022 DPT_PowerDensity (W/m²)."""

    unit = "W/m²"


class DPTKelvinPerPercent(DPT2ByteFloat):
    """DPT 9.023 DPT_KelvinPerPercent (K/%)."""

    unit = "K/%"


class DPTPower2Byte(DPT2ByteFloat):
    """DPT 9.024 DPT_Power (kW)."""

    unit = "kW"
    ha_device_class = "power"


class DPTVolumeFlow(DPT2ByteFloat):
    """DPT 9.025 DPT_Value_Volume_Flow (l/h)."""

    unit = "l/h"


class DPTRainAmount(DPT2ByteFloat):
    """DPT 9.026 DPT_Rain_Amount (l/m²)."""

    value_min = -671088.64
    value_max = 670760.96
    unit = "l/m²"


class DPTTemperatureF(DPT2ByteFloat):
    """DPT 9.027 DPT_Value_Temp_F."""

    value_min = -459.6
    value_max = 670760
    unit = "°F"
    ha_device_class = "temperature"
    resolution = 1


class DPTWspKmh(DPT2ByteFloat):
    """DPT 9.028 DPT_Value_Wsp_kmh Speed (km/h)."""

    value_min = 0
    value_max = 670760
    unit = "km/h"
    resolution = 1


class DPTEnthalpy(DPT2ByteFloat):
    """DPT 9.* 2-byte float value (with unit)."""

    unit = "H"
