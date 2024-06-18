"""
Module for managing an RGB remote value.

DPT 232.600.
"""

from __future__ import annotations

from xknx.dpt import DPTColorRGB, RGBColor

from .remote_value import RemoteValue


class RemoteValueColorRGB(RemoteValue[RGBColor]):
    """Abstraction for remote value of KNX DPT 232.600 (DPT_Color_RGB)."""

    dpt_class = DPTColorRGB
