"""Implementation of KNX DPT 15 Access Data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary

ACCESS_CODE_MAX = 999_999
INDEX_MAX = 15

_FLAG_FIELDS = ("detection_error", "permission", "read_right_to_left", "encrypted")


@dataclass(slots=True)
class AccessData(DPTComplexData):
    """
    Representation of access data.

    `access_code`: int 0..999999 - the six digits D6..D1 of the access
        identification code; unused leading digits are 0
    `detection_error`: bool - reading of the access information code failed (E)
    `permission`: bool - access accepted by the controlling device (P)
    `read_right_to_left`: bool - read direction, eg. of a badge (D)
    `encrypted`: bool - access information is encrypted (C)
    `index`: int 0..15 - index of the access identification code
    """

    access_code: int = field(metadata={"value_min": 0, "value_max": ACCESS_CODE_MAX})
    detection_error: bool = False
    permission: bool = False
    read_right_to_left: bool = False
    encrypted: bool = False
    index: int = field(default=0, metadata={"value_min": 0, "value_max": INDEX_MAX})

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AccessData:
        """Init from a dictionary."""
        try:
            access_code = int(data["access_code"])
            index = int(data.get("index", 0))
            flags = {key: data.get(key, False) for key in _FLAG_FIELDS}
        except KeyError as err:
            raise ValueError(f"Missing required key: {err}") from err
        except (AttributeError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for AccessData: {err}") from err
        for key, flag in flags.items():
            if not isinstance(flag, bool):
                raise ValueError(f"Invalid value for AccessData value `{key}`: {flag}")
        return cls(access_code=access_code, index=index, **flags)

    def as_dict(self) -> dict[str, int | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "access_code": self.access_code,
            "detection_error": self.detection_error,
            "permission": self.permission,
            "read_right_to_left": self.read_right_to_left,
            "encrypted": self.encrypted,
            "index": self.index,
        }


class DPTAccessData(DPTComplex[AccessData]):
    """
    Abstraction for KNX 4 octet access data (DPT 15.000).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.16
    """

    data_type = AccessData
    payload_type = DPTArray
    payload_length = 4
    dpt_main_number = 15
    dpt_sub_number = 0
    value_type = "access_data"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> AccessData:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        # D6..D1 are one binary encoded digit per nibble, most significant first
        digits = bytes(raw[:3]).hex()
        if not digits.isdigit():
            raise ConversionError(f"Could not parse {cls.dpt_name()}", raw=raw)
        return AccessData(
            access_code=int(digits),
            detection_error=bool(raw[3] & 0x80),
            permission=bool(raw[3] & 0x40),
            read_right_to_left=bool(raw[3] & 0x20),
            encrypted=bool(raw[3] & 0x10),
            index=raw[3] & 0x0F,
        )

    @classmethod
    def _to_knx(cls, value: AccessData) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= value.access_code <= ACCESS_CODE_MAX:
            raise ValueError(
                f"Access code out of range 0..{ACCESS_CODE_MAX}: {value.access_code}"
            )
        if not 0 <= value.index <= INDEX_MAX:
            raise ValueError(f"Index out of range 0..{INDEX_MAX}: {value.index}")
        for key in _FLAG_FIELDS:
            if not isinstance(flag := getattr(value, key), bool):
                raise ValueError(f"Invalid value for `{key}`: {flag}")
        return DPTArray(
            (
                *bytes.fromhex(f"{value.access_code:06d}"),
                value.detection_error << 7
                | value.permission << 6
                | value.read_right_to_left << 5
                | value.encrypted << 4
                | value.index,
            )
        )
