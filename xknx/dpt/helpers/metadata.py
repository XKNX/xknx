"""
Shared value-range / resolution constants used as dataclass field ``metadata``.

Each constant describes a field's valid range (and step resolution where defined)
and is surfaced by ``DPTComplexData.get_dict_schema()``.
"""

from __future__ import annotations

from typing import Final

RANGE_UINT8: Final[dict[str, int]] = {"value_min": 0, "value_max": 255}
RANGE_UINT16: Final[dict[str, int]] = {"value_min": 0, "value_max": 65_535}
RANGE_INT32: Final[dict[str, int]] = {
    "value_min": -2_147_483_648,
    "value_max": 2_147_483_647,
}
# 1..7 higher is more intervals -> slower; 0 stop
RANGE_STEP_CODE: Final[dict[str, int]] = {"value_min": 0, "value_max": 7}
RANGE_FADE_TIME_S: Final[dict[str, float]] = {
    "value_min": 0.0,
    "value_max": 6553.5,
    "resolution": 0.1,
}
