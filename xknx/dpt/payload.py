"""Implementation of KNX raw payload abstractions."""
from __future__ import annotations

from xknx.exceptions import ConversionError


class DPTBinary:
    """The DPTBinary is a base class for all datatypes encoded directly into the last 6 bit of the APCI/data octet."""

    APCI_BITMASK = 0x3F  # APCI uses first 2 bits

    def __init__(self, value: int | tuple[int]) -> None:
        """Initialize DPTBinary class."""
        if isinstance(value, tuple):
            value = value[0]
        if not isinstance(value, int):
            raise TypeError()
        if not 0 <= value <= DPTBinary.APCI_BITMASK:
            raise ConversionError("Could not init DPTBinary", value=str(value))

        self.value = value

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        if isinstance(other, DPTBinary):
            return self.value == other.value
        return False

    def __repr__(self) -> str:
        """Return object representation."""
        return f"DPTBinary({hex(self.value)})"

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<DPTBinary value="{self.value}" />'


class DPTArray:
    """The DPTArray is a base class for all datatypes appended to the KNX telegram."""

    def __init__(self, value: int | bytes | tuple[int, ...] | list[int]) -> None:
        """Initialize DPTArray class."""
        self.value: tuple[int, ...]
        if isinstance(value, int):
            self.value = (value,)
        elif isinstance(value, (list, bytes)):
            self.value = tuple(value)
        elif isinstance(value, tuple):
            self.value = value
        else:
            raise TypeError()

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        if isinstance(other, DPTArray):
            return self.value == other.value
        return False

    def __repr__(self) -> str:
        """Return object representation."""
        return f"DPTArray(({', '.join(hex(b) for b in self.value)}))"

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<DPTArray value="[{",".join(hex(b) for b in self.value)}]" />'
