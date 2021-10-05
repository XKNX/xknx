"""Implementation of Basic KNX datatypes."""
from __future__ import annotations

from abc import ABC, abstractmethod
from inspect import isabstract
from typing import Any, Iterator, Type, TypeVar, cast

from xknx.exceptions import ConversionError

T = TypeVar("T", bound=Type["DPTBase"])  # pylint: disable=invalid-name


class DPTBase(ABC):
    """
    Base class for KNX data point type transcoder.

    KNX communicates using Group-addresses, and every Group Object represents a data point of some type.
    To have a standardized interpretation of the data there are a number of Data Point types (DPT).
    The DPT's is written like: xx.yyy, for example 14.056 for a 4-octet float, with Power info in Watts.
    The Major number (xx) describes the data type (format and encoding) - while the the minor (YYY) number
    describes the measurement with value range and unit.

    More DTP's are added as new needs come up, but this a list of some of the commonly used ones:
    1.yyy  boolean, like switching, on/off, open/close, move up/down, step
    2.yyy  2 x boolean, e.g. switching + priority control
    3.yyy  boolean + 3-bit unsigned value, e.g. dimming up/down
    4.yyy  character (8-bit)
    5.yyy  8-bit unsigned value, like dim value (0..100%), blinds position (0..100%)
    6.yyy  8-bit signed (2's complement), e.g. +/- %
    7.yyy  2-byte unsigned value, i.e. pulse counter
    8.yyy  2-byte signed (2's complement), e.g. +/- %
    9.yyy  2-byte float, e.g. temperature
    10.yyy time (3 bytes)
    11.yyy date (3 bytes)
    12.yyy 4-byte unsigned value, i.e. pulse counter
    13.yyy 4-byte signed (2's complement), i.e. flow, energy
    14.yyy 4-byte float, IEEE 754, i.e. Electrical measurements: current, power
    15.yyy access control
    16.yyy string -> 14 characters (14 x 8-bit)
    17.yyy scene number
    18.yyy scene control
    19.yyy date / time
    20.yyy 8-bit enumeration, e.g. HVAC mode ('auto', 'comfort', 'standby', 'economy', 'protection')
    28.yyy UTF-8
    29.yyy V64, 64-bit signed value
    232.yyy RGB [0,0,0]...[255,255,255]

    """

    payload_length: int = cast(int, None)
    dpt_main_number: int | None = None
    dpt_sub_number: int | None = None
    value_type: str | None = None
    unit: str | None = None
    ha_device_class: str | None = None

    @classmethod
    @abstractmethod
    def from_knx(cls, raw: tuple[int, ...]) -> Any:
        """Parse/deserialize from KNX/IP raw data (big endian)."""

    @classmethod
    @abstractmethod
    def to_knx(cls, value: Any) -> bytes | tuple[int, ...]:
        """Serialize to KNX/IP raw data."""

    @classmethod
    def test_bytesarray(cls, raw: tuple[int, ...]) -> None:
        """Test if array of raw bytes has the correct length and values of correct type."""
        if cls.payload_length is None:
            raise NotImplementedError(f"payload_length has to be defined for: {cls}")
        if (
            not isinstance(raw, (tuple, list))
            or len(raw) != cls.payload_length
            or any(not isinstance(byte, int) for byte in raw)
            or any(byte < 0 for byte in raw)
            or any(byte > 255 for byte in raw)
        ):
            raise ConversionError("Invalid raw bytes", raw=raw)

    @classmethod
    def __recursive_subclasses__(cls: T) -> Iterator[T]:
        """Yield all subclasses and their subclasses."""
        for subclass in cls.__subclasses__():
            yield from subclass.__recursive_subclasses__()
            if not isabstract(subclass):
                yield subclass

    @classmethod
    def has_distinct_dpt_numbers(cls) -> bool:
        """Return True if dpt numbers are defined (not inherited)."""
        return "dpt_main_number" in cls.__dict__ and "dpt_sub_number" in cls.__dict__

    @classmethod
    def has_distinct_value_type(cls) -> bool:
        """Return True if value_type is defined (not inherited)."""
        return "value_type" in cls.__dict__

    @classmethod
    def transcoder_by_dpt(
        cls: T, dpt_main: int, dpt_sub: int | None = None
    ) -> T | None:
        """Return Class reference of DPTBase subclass with matching DPT number."""
        for dpt in cls.__recursive_subclasses__():
            if dpt.has_distinct_dpt_numbers():
                if dpt_main == dpt.dpt_main_number and dpt_sub == dpt.dpt_sub_number:
                    return dpt
        return None

    @classmethod
    def transcoder_by_value_type(cls: T, value_type: str) -> T | None:
        """Return Class reference of DPTBase subclass with matching value_type."""
        for dpt in cls.__recursive_subclasses__():
            if dpt.has_distinct_value_type():
                if value_type == dpt.value_type:
                    return dpt
        return None

    @classmethod
    def parse_transcoder(cls: T, value_type: int | str) -> T | None:
        """Return Class reference of DPTBase subclass from value_type or DPT number."""
        if isinstance(value_type, int):
            return cls.transcoder_by_dpt(value_type)
        if isinstance(value_type, str):
            string_type = value_type.strip()
            transcoder = cls.transcoder_by_value_type(string_type)
            if transcoder is None:
                # Try to parse the value_type if it is a string but not found by cls.transcoder_by_value_type()
                # for backwards compatibility (eg. "DPT-5") and strings representing numbers (eg. "7", "9.001")
                string_type = string_type.upper().strip(" DPT-")
                if string_type.isdigit():
                    transcoder = cls.transcoder_by_dpt(int(string_type))
                else:
                    try:
                        main, sub = map(int, string_type.split("."))
                        transcoder = cls.transcoder_by_dpt(dpt_main=main, dpt_sub=sub)
                    except (ValueError, IndexError):
                        pass
            return transcoder


class DPTNumeric(DPTBase):
    """Base class for KNX data point types decoding numeric values."""

    value_min: int | float
    value_max: int | float
    resolution: int | float

    @classmethod
    @abstractmethod
    def from_knx(cls, raw: tuple[int, ...]) -> int | float:
        """Parse/deserialize from KNX/IP raw data (big endian)."""

    @classmethod
    @abstractmethod
    def to_knx(cls, value: int | float) -> bytes | tuple[int, ...]:
        """Serialize to KNX/IP raw data."""


class DPTBinary:
    """The DPTBinary is a base class for all datatypes encoded directly into the last 6 bit of the APCI (mostly integer)."""

    # APCI (application layer control information)
    APCI_BITMASK = 0x3F
    APCI_MAX_VALUE = APCI_BITMASK

    def __init__(self, value: int | tuple[int]) -> None:
        """Initialize DPTBinary class."""
        if isinstance(value, tuple):
            value = value[0]
        if not isinstance(value, int):
            raise TypeError()
        if value > DPTBinary.APCI_BITMASK or value < 0:
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
