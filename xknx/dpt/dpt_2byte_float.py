"""
Implementation of KNX 2 byte Float-values.

They correspond to the the following KDN DPT 9 class.
"""
from __future__ import annotations

from xknx.exceptions import ConversionError

from .dpt import DPTNumeric


class DPT2ByteFloat(DPTNumeric):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.***
    """

    dpt_main_number = 9
    dpt_sub_number: int | None = None
    value_type = "2byte_float"
    payload_length = 2

    value_min = -671088.64
    value_max = 670760.96
    resolution = 0.01

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> float:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        data = (raw[0] * 256) + raw[1]
        exponent = (data >> 11) & 0x0F
        significand = data & 0x7FF
        sign = data >> 15

        if sign == 1:
            significand = significand - 2048

        value = float(significand << exponent) / 100

        if not cls._test_boundaries(value):
            raise ConversionError(f"Could not parse {cls.__name__}", value=value)

        return value

    @classmethod
    def to_knx(cls, value: float) -> tuple[int, int]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = float(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError

            value = knx_value * 100
            exponent = 0
            while not -2048 <= value <= 2047:
                exponent += 1
                value /= 2

            mantisse = int(round(value)) & 0x7FF
            msb = exponent << 3 | mantisse >> 8
            if value < 0:
                msb |= 0x80

            return msb, mantisse & 0xFF
        except ValueError:
            raise ConversionError(f"Could not serialize {cls.__name__}", value=value)

    @classmethod
    def _test_boundaries(cls, value: float) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTTemperature(DPT2ByteFloat):
    """DPT 9.001 DPT_Value_Temp."""

    dpt_main_number = 9
    dpt_sub_number = 1
    value_type = "temperature"
    unit = "°C"
    ha_device_class = "temperature"

    value_min = -273
    value_max = 670760


class DPTTemperatureDifference2Byte(DPT2ByteFloat):
    """DPT 9.002 DPT_Value_Tempd."""

    dpt_main_number = 9
    dpt_sub_number = 2
    value_type = "temperature_difference_2byte"
    unit = "K"
    ha_device_class = "temperature"

    value_min = -670760
    value_max = 670760


class DPTTemperatureA(DPT2ByteFloat):
    """DPT 9.003 DPT_Value_Tempa."""

    dpt_main_number = 9
    dpt_sub_number = 3
    value_type = "temperature_a"
    unit = "K/h"

    value_min = -670760
    value_max = 670760


class DPTLux(DPT2ByteFloat):
    """DPT 9.004 DPT_Value_Lux."""

    dpt_main_number = 9
    dpt_sub_number = 4
    value_type = "illuminance"
    unit = "lx"
    ha_device_class = "illuminance"

    value_min = 0
    value_max = 670760


class DPTWsp(DPT2ByteFloat):
    """DPT 9.005 DPT_Value_Ws Speed (m/s)."""

    dpt_main_number = 9
    dpt_sub_number = 5
    value_type = "wind_speed_ms"
    unit = "m/s"
    ha_device_class = "wind_speed"

    value_min = 0
    value_max = 670760


class DPTPressure2Byte(DPT2ByteFloat):
    """DPT 9.006 DPT_Value_Pres (Pa)."""

    dpt_main_number = 9
    dpt_sub_number = 6
    value_type = "pressure_2byte"
    unit = "Pa"
    ha_device_class = "pressure"

    value_min = 0
    value_max = 670760


class DPTHumidity(DPT2ByteFloat):
    """DPT 9.007 DPT_Value_Humidity."""

    dpt_main_number = 9
    dpt_sub_number = 7
    value_type = "humidity"
    unit = "%"
    ha_device_class = "humidity"

    value_min = 0
    value_max = 670760


class DPTPartsPerMillion(DPT2ByteFloat):
    """DPT 9.008 DPT_Value_parts/million."""

    dpt_main_number = 9
    dpt_sub_number = 8
    value_type = "ppm"
    unit = "ppm"


class DPTAirFlow(DPT2ByteFloat):
    """DPT 9.009 DPT_Value_AirFlow."""

    dpt_main_number = 9
    dpt_sub_number = 9
    value_type = "air_flow"
    unit = "m³/h"


class DPTTime1(DPT2ByteFloat):
    """DPT 9.010 DPT_Value_Time1 (s)."""

    dpt_main_number = 9
    dpt_sub_number = 10
    value_type = "time_1"
    unit = "s"

    value_min = -670760
    value_max = 670760


class DPTTime2(DPT2ByteFloat):
    """DPT 9.011 DPT_Value_Time2 (ms)."""

    dpt_main_number = 9
    dpt_sub_number = 11
    value_type = "time_2"
    unit = "ms"

    value_min = -670760
    value_max = 670760


class DPTVoltage(DPT2ByteFloat):
    """DPT 9.020 DPT_Value_Voltage."""

    dpt_main_number = 9
    dpt_sub_number = 20
    value_type = "voltage"
    unit = "mV"
    ha_device_class = "voltage"


class DPTCurrent(DPT2ByteFloat):
    """DPT 9.021 DPT_Value_Curr (mA)."""

    dpt_main_number = 9
    dpt_sub_number = 21
    value_type = "curr"
    unit = "mA"
    ha_device_class = "current"


class DPTPowerDensity(DPT2ByteFloat):
    """DPT 9.022 DPT_PowerDensity (W/m²)."""

    dpt_main_number = 9
    dpt_sub_number = 22
    value_type = "power_density"
    unit = "W/m²"


class DPTKelvinPerPercent(DPT2ByteFloat):
    """DPT 9.023 DPT_KelvinPerPercent (K/%)."""

    dpt_main_number = 9
    dpt_sub_number = 23
    value_type = "kelvin_per_percent"
    unit = "K/%"


class DPTPower2Byte(DPT2ByteFloat):
    """DPT 9.024 DPT_Power (kW)."""

    dpt_main_number = 9
    dpt_sub_number = 24
    value_type = "power_2byte"
    unit = "kW"
    ha_device_class = "power"


class DPTVolumeFlow(DPT2ByteFloat):
    """DPT 9.025 DPT_Value_Volume_Flow (L/h)."""

    dpt_main_number = 9
    dpt_sub_number = 25
    value_type = "volume_flow"
    unit = "L/h"


class DPTRainAmount(DPT2ByteFloat):
    """DPT 9.026 DPT_Rain_Amount (L/m²)."""

    dpt_main_number = 9
    dpt_sub_number = 26
    value_type = "rain_amount"
    unit = "L/m²"

    value_min = -671088.64
    value_max = 670760.96


class DPTTemperatureF(DPT2ByteFloat):
    """DPT 9.027 DPT_Value_Temp_F."""

    dpt_main_number = 9
    dpt_sub_number = 27
    value_type = "temperature_f"
    unit = "°F"
    ha_device_class = "temperature"

    value_min = -459.6
    value_max = 670760


class DPTWspKmh(DPT2ByteFloat):
    """DPT 9.028 DPT_Value_Wsp_kmh Speed (km/h)."""

    dpt_main_number = 9
    dpt_sub_number = 28
    value_type = "wind_speed_kmh"
    unit = "km/h"
    ha_device_class = "wind_speed"

    value_min = 0
    value_max = 670760


class DPTAbsoluteHumidity(DPT2ByteFloat):
    """DPT 9.029 DPT_Value_Absolute_Humidity."""

    dpt_main_number = 9
    dpt_sub_number = 29
    value_type = "absolute_humidity"
    unit = "g/m³"

    value_min = 0


class DPTConcentrationUGM3(DPT2ByteFloat):
    """DPT 9.030 DPT_Value_Concentration_μgm3."""

    dpt_main_number = 9
    dpt_sub_number = 30
    value_type = "concentration_ugm3"
    unit = "μg/m³"

    value_min = 0


class DPTEnthalpy(DPT2ByteFloat):
    """DPT 9.? 2-byte float value (with unit)."""

    dpt_main_number = 9
    # this is here for backwards compatibility
    dpt_sub_number = 999
    value_type = "enthalpy"
    unit = "H"
