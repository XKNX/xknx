"""
Module for encoding and decoding KNX datatypes.

* KNX Values like Int, Float, String, Time
* Derived KNX Values like Scaling, Temperature
"""
# flake8: noqa
from .dpt import DPTArray, DPTBase, DPTBinary, DPTComparator, DPTWeekday
from .dpt_1byte_signed import (
    DPTPercentV8, DPTSignedRelativeValue, DPTValue1Count)
from .dpt_1byte_uint import (
    DPTPercentU8, DPTSceneNumber, DPTTariff, DPTValue1Ucount)
from .dpt_2byte_float import (
    DPT2ByteFloat, DPTEnthalpy, DPTHumidity, DPTLux, DPTPartsPerMillion,
    DPTPressure2Byte, DPTTemperature, DPTVoltage, DPTWsp, DPTCurrent)
from .dpt_2byte_signed import (
    DPT2ByteSigned, DPTDeltaTimeHrs, DPTDeltaTimeMin, DPTDeltaTimeMsec,
    DPTDeltaTimeSec, DPTPercentV16, DPTRotationAngle, DPTValue2Count)
from .dpt_2byte_uint import (
    DPT2ByteUnsigned, DPT2Ucount, DPTBrightness, DPTColorTemperature,
    DPTUElCurrentmA)
from .dpt_4byte_float import (
    DPT4ByteFloat, DPTElectricCurrent, DPTElectricPotential, DPTEnergy,
    DPTFrequency, DPTHeatFlowRate, DPTLuminousFlux, DPTPhaseAngleDeg,
    DPTPhaseAngleRad, DPTPower, DPTPowerFactor, DPTPressure, DPTSpeed,
    DPTCommonTemperature, DPTAbsoluteTemperature, DPTValueTime)

from .dpt_4byte_int import (
    DPT4ByteSigned, DPT4ByteUnsigned, DPTActiveEnergy, DPTApparantEnergy, 
    DPTReactiveEnergy, DPTActiveEnergykWh, DPTApparantEnergykVAh, DPTReactiveEnergykVARh)
from .dpt_date import DPTDate
from .dpt_datetime import DPTDateTime
from .dpt_hvac_contr_mode import DPTHVACContrMode
from .dpt_hvac_mode import DPTControllerStatus, DPTHVACMode, HVACOperationMode
from .dpt_scaling import DPTAngle, DPTScaling
from .dpt_string import DPTString
from .dpt_time import DPTTime

# ----------------------------------------------------------------------------
# Remarks to input and output of to_knx() and from_knx():
#
#   - Input to to_knx() and output from from_knx() of class DPT and its derived classes:
#    +------------------------------------ +                                      +---------------------+
#    | one value ot type:                  |                                      |   array of bytes    |
#    | - scalar value (int, float)         |     ------->  to_knx()  ------>      |   (1 .. N bytes)    |
#    | - dictionary (e.g. for date, time)  |     <------  from_knx() -------      |                     |
#    | - string (text, DPT-16.000)         |                                      |                     |
#    +-------------------------------------+                                      +---------------------+
#
#  - Input to to_knx() and output from from_knx() of classes derived from RemoteValue:
#
#    +------------------------------------ +
#    | one value ot type:                  |                                      +---------------------+
#    | - scalar value (int, float)         |   ---in-->  to_knx()   ---out--->    |      DPTArray,      |
#    | - booleans (True, False, UP,        |   <--out--  from_knx() <----in---    |       DPTBinary,    |
#    |   DOWN, INCREASE, ...)              |                                      |       DPTControl    |
#    | - dictionary (e.g. date, time, ...) |                                      +---------------------+
#    | - list (e.g. color)                 |
#    +-------------------------------------+
