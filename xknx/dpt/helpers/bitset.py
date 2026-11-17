"""Shared helpers for bit set DPTs whose fields are single bits (B8, B16, B24)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar, Self

from ..dpt import DPTComplexData


def _to_bit(name: str, value: Any) -> bool:
    """Validate a bit value; accepts bool and the ints 0 and 1."""
    if value not in (True, False):
        raise ValueError(f"Invalid value for `{name}`: {value!r}")
    return bool(value)


def bits_from_dict(data: Mapping[str, Any], bits: Mapping[str, int]) -> dict[str, bool]:
    """
    Read the fields named in `bits` from a dictionary.

    Only keys present in `data` are returned, so missing fields take their
    dataclass default. Every field is optional, so an unknown key (e.g. a
    misspelled one) raises ValueError instead of being silently ignored.
    """
    if not isinstance(data, Mapping):
        raise ValueError(f"Invalid data for bit set: {data!r}")
    unknown = data.keys() - bits.keys()
    if unknown:
        raise ValueError(
            f"Unknown keys for bit set: {sorted(map(str, unknown))}; "
            f"valid keys: {list(bits)}"
        )
    return {name: _to_bit(name, data[name]) for name in bits if name in data}


def bits_from_raw(raw: int, bits: Mapping[str, int]) -> dict[str, bool]:
    """Unpack the bits named in `bits` from an integer; other bits are ignored."""
    return {name: bool(raw >> bit & 1) for name, bit in bits.items()}


def bits_to_raw(value: object, bits: Mapping[str, int]) -> int:
    """Pack the attributes of `value` named in `bits` into an integer."""
    raw = 0
    for name, bit in bits.items():
        raw |= _to_bit(name, getattr(value, name)) << bit
    return raw


class _BitsetData(DPTComplexData):
    """
    Base for DPTs whose every field is a `bool` stored in a single bit.

    Subclasses map each dataclass field name to its bit number in `_bits`,
    in field order. Bits not listed are reserved: sent as 0 and ignored on receive.
    """

    __slots__ = ()

    _bits: ClassVar[Mapping[str, int]]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Init from a dictionary. Missing keys take the field default."""
        return cls(**bits_from_dict(data, cls._bits))

    def as_dict(self) -> dict[str, bool]:
        """Create a JSON serializable dictionary."""
        return {name: getattr(self, name) for name in self._bits}

    @classmethod
    def from_raw(cls, raw: int) -> Self:
        """Unpack from an integer."""
        return cls(**bits_from_raw(raw, cls._bits))

    def to_raw(self) -> int:
        """Pack into an integer."""
        return bits_to_raw(self, self._bits)
