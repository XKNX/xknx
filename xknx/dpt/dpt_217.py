"""Implementation of the KNX 217 data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class KNXVersion(DPTComplexData):
    """
    Representation of a version information.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.42
    `magic_number`: int 0..31 - incremented for an incompatible change
    `version_number`: int 0..31 - incremented for new features
    `revision_number`: int 0..63 - incremented for minor changes

    Invalid, void or undefined version information is encoded as
    31.31.63 (`KNXVersion.invalid()`, see `is_invalid`). It is decoded and
    encoded like any other value.
    """

    magic_number: int = field(metadata={"value_min": 0, "value_max": 31})
    version_number: int = field(metadata={"value_min": 0, "value_max": 31})
    revision_number: int = field(metadata={"value_min": 0, "value_max": 63})

    @classmethod
    def invalid(cls) -> KNXVersion:
        """Return the encoding of invalid version information (31.31.63)."""
        return cls(magic_number=31, version_number=31, revision_number=63)

    @property
    def is_invalid(self) -> bool:
        """Return whether this is the encoding of invalid version information."""
        return self == KNXVersion.invalid()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> KNXVersion:
        """Init from a dictionary."""
        try:
            magic_number = int(data["magic_number"])
            version_number = int(data["version_number"])
            revision_number = int(data["revision_number"])
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for KNXVersion: {err}") from err
        return cls(
            magic_number=magic_number,
            version_number=version_number,
            revision_number=revision_number,
        )

    def as_dict(self) -> dict[str, int]:
        """Create a JSON serializable dictionary."""
        return {
            "magic_number": self.magic_number,
            "version_number": self.version_number,
            "revision_number": self.revision_number,
        }

    def __str__(self) -> str:
        """
        Return the version as `magic_number.version_number.revision_number`.

        This is the M.V.R notation of the spec. A user interface normally
        doesn't show the magic number, see KNX v02.02.01 - Datapoint Types
        03.07.02 - §3.42.
        """
        return f"{self.magic_number}.{self.version_number}.{self.revision_number}"


class DPTVersion(DPTComplex[KNXVersion]):
    """
    Abstraction for KNX 2 octet Version (DPT 217.001).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.42: format U5U5U6 -
    Magic Number, Version Number, Revision Number. Used for software, hardware
    and data-interface versions, e.g. `PID_VERSION` of an Interface Object.

    KNX v01.04.01 - Standardized Identifier Tables 03.07.03 - §3.2 lists
    `PID_VERSION` as `PDT_VERSION (U6U6U6)`, but §4.1 of the same document
    defines `PDT_VERSION` as DPT_Version `U5U5U6` in 2 octets. Only 5 + 5 + 6
    bits fit in 2 octets, so this is the encoding used here.
    """

    data_type = KNXVersion
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 217
    dpt_sub_number = 1
    value_type = "version"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> KNXVersion:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        value = raw[0] << 8 | raw[1]
        return KNXVersion(
            magic_number=value >> 11,
            version_number=value >> 6 & 0x1F,
            revision_number=value & 0x3F,
        )

    @classmethod
    def _to_knx(cls, value: KNXVersion) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        for name, maximum in (
            ("magic_number", 31),
            ("version_number", 31),
            ("revision_number", 63),
        ):
            number = getattr(value, name)
            if not 0 <= number <= maximum:
                raise ValueError(f"{name} out of range 0..{maximum}: {number}")
        encoded = (
            value.magic_number << 11 | value.version_number << 6 | value.revision_number
        )
        return DPTArray((encoded >> 8, encoded & 0xFF))
