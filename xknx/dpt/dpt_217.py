"""Implementation of the KNX 217 data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class Version(DPTComplexData):
    """
    Representation of a version information.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.42
    `magic_number`: int 0..31 - incremented for an incompatible change
    `version`: int 0..31 - incremented for new features
    `revision`: int 0..63 - incremented for minor changes
    """

    magic_number: int = field(metadata={"value_min": 0, "value_max": 31})
    version: int = field(metadata={"value_min": 0, "value_max": 31})
    revision: int = field(metadata={"value_min": 0, "value_max": 63})

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Version:
        """Init from a dictionary."""
        try:
            magic_number = int(data["magic_number"])
            version = int(data["version"])
            revision = int(data["revision"])
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for Version: {err}") from err
        return cls(magic_number=magic_number, version=version, revision=revision)

    def as_dict(self) -> dict[str, int]:
        """Create a JSON serializable dictionary."""
        return {
            "magic_number": self.magic_number,
            "version": self.version,
            "revision": self.revision,
        }

    def __str__(self) -> str:
        """Return the version as `magic_number.version.revision`."""
        return f"{self.magic_number}.{self.version}.{self.revision}"


class DPTVersion(DPTComplex[Version]):
    """
    Abstraction for KNX 2 octet Version (DPT 217.001).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.42: format U5U5U6 -
    Magic Number, Version Number, Revision Number. Used for software, hardware
    and data-interface versions, eg. `PID_VERSION` of an Interface Object.
    """

    data_type = Version
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 217
    dpt_sub_number = 1
    value_type = "version"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Version:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        value = raw[0] << 8 | raw[1]
        return Version(
            magic_number=value >> 11,
            version=value >> 6 & 0x1F,
            revision=value & 0x3F,
        )

    @classmethod
    def _to_knx(cls, value: Version) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        for name, maximum in (("magic_number", 31), ("version", 31), ("revision", 63)):
            number = getattr(value, name)
            if not 0 <= number <= maximum:
                raise ValueError(f"{name} out of range 0..{maximum}: {number}")
        encoded = value.magic_number << 11 | value.version << 6 | value.revision
        return DPTArray((encoded >> 8, encoded & 0xFF))
