"""
Module for managing a remote date and time values.

DPT 10.001, 11.001 and 19.001
"""

from __future__ import annotations

from xknx.dpt import DPTDate, DPTDateTime, DPTTime
from xknx.dpt.dpt_10 import KNXTime
from xknx.dpt.dpt_11 import KNXDate
from xknx.dpt.dpt_19 import KNXDateTime

from .remote_value import RemoteValue


class RemoteValueTime(RemoteValue[KNXTime]):
    """Abstraction for remote value of KNX 3 octet time."""

    dpt_class = DPTTime


class RemoteValueDate(RemoteValue[KNXDate]):
    """Abstraction for remote value of KNX 3 octet date."""

    dpt_class = DPTDate


class RemoteValueDateTime(RemoteValue[KNXDateTime]):
    """Abstraction for remote value of KNX 8 octet datetime."""

    dpt_class = DPTDateTime
