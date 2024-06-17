"""
Module for managing an xyY-color remote value.

DPT 242.600.
"""

from __future__ import annotations

from xknx.dpt import DPTColorXYY, XYYColor

from .remote_value import RemoteValue


class RemoteValueColorXYY(RemoteValue[XYYColor]):
    """Abstraction for remote value of KNX DPT 242.600 (DPT_Colour_xyY)."""

    dpt_class = DPTColorXYY
