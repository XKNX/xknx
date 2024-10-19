"""
Module for managing a remote humidity value.

DPT 9.007.
"""

from __future__ import annotations

from xknx.dpt import DPTHumidity

from .remote_value import RemoteValue


class RemoteValueHumidity(RemoteValue[float]):
    """Abstraction for remote value of KNX 9.007 (DPT_Value_Humidity)."""

    dpt_class = DPTHumidity
