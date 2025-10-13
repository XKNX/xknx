"""Implementation of Basic KNX datatypes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from inspect import isabstract
import struct
from typing import Any, Generic, TypeVar, cast, final

from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.typing import DPTParsable, Self

from .payload import DPTArray, DPTBinary


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

    payload_type: type[DPTArray | DPTBinary]
    payload_length: int = cast(int, None)  # DPTArray: byte length; DPTBinary bit length
    dpt_main_number: int | None = None
    dpt_sub_number: int | None = None
    value_type: str | None = None
    unit: str | None = None
    ha_device_class: str | None = None

    @classmethod
    def dpt_number_str(cls) -> str:
        """Return DPT number string representation."""
        if cls.dpt_sub_number is not None:
            return f"{cls.dpt_main_number}.{cls.dpt_sub_number:03d}"
        return f"{cls.dpt_main_number or ''}"

    @classmethod
    def dpt_name(cls) -> str:
        """Return string representation of class name and DPT number."""
        if cls.dpt_main_number is not None:
            return f"{cls.__name__} ({cls.dpt_number_str()})"
        return f"{cls.__name__} (abstract)"  # concrete classes have dpt_main_number

    @classmethod
    @abstractmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Any:
        """
        Parse/deserialize from KNX/IP payload data.

        Raise `CouldNotParseTelegram` for wrong payload
        or `ConversionError` for unparsable value.
        """
        # raw = cls.validate_payload(payload)

    @classmethod
    def validate_payload(cls, payload: DPTArray | DPTBinary) -> tuple[int, ...]:
        """
        Test if payload has the correct length and type for given DPT.

        Return tuple of raw values.
        Raise CouldNotParseTelegram if payload type or length is invalid for DPT.
        """
        if cls.payload_type is DPTArray and isinstance(payload, DPTArray):
            if cls.payload_length == len(payload.value):
                return payload.value

            raise CouldNotParseTelegram(
                f"Invalid payload length for {cls.dpt_name()}",
                payload=payload,
                expected_length=cls.payload_length,
            )

        if cls.payload_type is DPTBinary and isinstance(payload, DPTBinary):
            if payload.value >= 2**cls.payload_length:
                # >= 0 is already checked by DPTBinary
                raise CouldNotParseTelegram(
                    f"Invalid payload bitlength for {cls.dpt_name()}",
                    payload=payload,
                    expected_length=cls.payload_length,
                )
            # wrap in tuple for consistent return signature
            return (payload.value,)

        raise CouldNotParseTelegram(
            f"Invalid payload type for {cls.dpt_name()}",
            payload=payload,
            expected_type=cls.payload_type.__name__,
        )

    @classmethod
    @abstractmethod
    def to_knx(cls, value: Any) -> DPTArray | DPTBinary:
        """
        Serialize to KNX/IP raw data.

        Raise `ConversionError` for unparsable value.
        """

    @classmethod
    def __recursive_subclasses__(cls: type[Self]) -> Iterator[type[Self]]:
        """Yield all subclasses and their subclasses."""
        for subclass in cls.__subclasses__():
            if not isabstract(subclass):
                yield subclass
            yield from subclass.__recursive_subclasses__()

    @classmethod
    def dpt_class_tree(cls: type[Self]) -> Iterator[type[Self]]:
        """Yield class, all subclasses and their subclasses that are not abstract."""
        if not isabstract(cls):
            yield cls
        yield from cls.__recursive_subclasses__()

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
        cls: type[Self], dpt_main: int, dpt_sub: int | None = None
    ) -> type[Self] | None:
        """Return Class reference of DPTBase subclass with matching DPT number."""
        for dpt in cls.dpt_class_tree():
            if dpt.has_distinct_dpt_numbers():
                if dpt_main == dpt.dpt_main_number and dpt_sub == dpt.dpt_sub_number:
                    return dpt
        return None

    @classmethod
    def transcoder_by_value_type(cls: type[Self], value_type: str) -> type[Self] | None:
        """Return Class reference of DPTBase subclass with matching value_type."""
        for dpt in cls.dpt_class_tree():
            if dpt.has_distinct_value_type():
                if value_type == dpt.value_type:
                    return dpt
        return None

    @classmethod
    def parse_transcoder(cls: type[Self], value_type: DPTParsable) -> type[Self] | None:
        """
        Return Class reference of DPTBase subclass from value_type or DPT number.

        `value_type` accepts
        - Integer: DPT main number
        - String: value_type or "." separated dpt main and sub numbers (eg. "9.001")
        - Mapping: "main" and "sub" keys with DPT main and sub numbers (in accordance to xknxproject data)
        """
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
        if isinstance(value_type, Mapping):
            try:
                main = int(value_type["main"])
                if (_sub := value_type.get("sub")) is not None:
                    _sub = int(_sub)
                else:
                    _sub = None
            except (KeyError, TypeError, ValueError):
                return None
            return cls.transcoder_by_dpt(dpt_main=main, dpt_sub=_sub)

    @classmethod
    def get_dpt(cls: type[Self], value_type: DPTParsable | type[DPTBase]) -> type[Self]:
        """
        Return DPT class from value.

        Raises ValueError if value_type can't be parsed to DPT class.
        """
        if isinstance(value_type, type):
            if issubclass(value_type, cls) and not isabstract(value_type):
                return value_type
        else:
            if transcoder := cls.parse_transcoder(value_type):
                return transcoder
        raise ValueError(
            f"Invalid value type for base class {cls.__name__}: {value_type}"
        )


class DPTNumeric(DPTBase):
    """Base class for KNX data point types decoding numeric values."""

    payload_type = DPTArray
    value_min: int | float
    value_max: int | float
    resolution: int | float

    @classmethod
    @abstractmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> int | float:
        """Parse/deserialize from KNX/IP payload data."""

    @classmethod
    @abstractmethod
    def to_knx(cls, value: int | float) -> DPTArray:
        """Serialize to KNX/IP raw data."""


class DPTStructIntMixin:
    """
    Mixin for DPT classes using struct to convert values.

    Base class shall be DPTNumeric.
    Resolution shall always be 1.
    """

    value_min: int | float
    value_max: int | float
    # https://docs.python.org/3/library/struct.html#format-characters
    _struct_format: str

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)  # type: ignore[attr-defined]

        try:
            return struct.unpack(cls._struct_format, bytes(raw))[0]  # type: ignore[no-any-return]
        except struct.error as err:
            raise ConversionError(f"Could not parse {cls.dpt_name()}", raw=raw) from err  # type: ignore[attr-defined]

    @classmethod
    def to_knx(cls, value: int | float) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not (cls.value_min <= knx_value <= cls.value_max):
                raise ValueError
            return DPTArray(struct.pack(cls._struct_format, knx_value))
        except (ValueError, struct.error) as err:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}",  # type: ignore[attr-defined]
                value=value,
            ) from err


class DPTEnumData(Enum):
    """
    Base class for KNX data point types decoding Enum values.

    Member values should be integers representing the raw KNX value.
    """

    @classmethod
    def parse(cls, value: Self | str | int) -> Self:
        """Parse from Enum instance, name or value. Raises ValueError if parsing fails."""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            try:
                # snake_cased name may be used as translation key or serializable value
                return cls[value.upper()]
            except KeyError:
                pass  # raise ValueError below
        if isinstance(value, int):
            try:
                return cls(value)
            except ValueError:
                pass  # raise ValueError below
        raise ValueError(f"Could not parse {cls.__name__} from {value}")


EnumDataT = TypeVar("EnumDataT", bound=DPTEnumData)


class DPTEnum(DPTBase, Generic[EnumDataT]):
    """Base class for KNX data point types decoding Enum values."""

    payload_type: type[DPTArray | DPTBinary] = DPTArray
    payload_length = 1

    data_type: type[EnumDataT]

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> EnumDataT:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        try:
            return cls.data_type(raw[0])
        except ValueError:
            raise ConversionError(
                f"Payload not supported for {cls.dpt_name()}", raw=raw
            ) from None

    @classmethod
    def to_knx(cls, value: EnumDataT | str | int) -> DPTArray | DPTBinary:
        """Serialize to KNX/IP raw data."""
        try:
            return cls._to_knx(cls.data_type.parse(value))
        except ValueError as err:
            raise ConversionError(
                f"Value not supported for {cls.data_type.__name__} in {cls.dpt_name()}",
                value=value,
                valid_values=cls.get_valid_values(),
            ) from err

    @classmethod
    @abstractmethod
    def _to_knx(cls, value: EnumDataT) -> DPTArray | DPTBinary:
        """Return the raw KNX value for an Enum member."""
        # At least one abstract method is needed for our parse_transcoder lookup to
        # ignore the DPTEnum base class and only find concrete base classes.
        # `return DPTArray(value.value)` can be used typesafely if the Enum values are integers.

    @classmethod
    def get_valid_values(cls) -> list[EnumDataT]:
        """Return list of valid values."""
        return list(cls.data_type)


@dataclass(slots=True)
class DPTComplexData(ABC):
    """Base class for KNX data point types decoding complex values."""

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Init from a dictionary."""

    @abstractmethod
    def as_dict(self) -> dict[str, Any]:
        """Create a JSON serializable dictionary."""


_ComplexDataT = TypeVar("_ComplexDataT", bound=DPTComplexData)


class DPTComplex(DPTBase, Generic[_ComplexDataT]):
    """Base class for KNX data point types decoding complex values."""

    data_type: type[_ComplexDataT]

    @classmethod
    @abstractmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> _ComplexDataT:
        """Parse/deserialize from KNX/IP payload data."""

    @final
    @classmethod
    def to_knx(cls, value: _ComplexDataT | Mapping[str, Any]) -> DPTArray | DPTBinary:
        """Serialize to KNX/IP raw data."""
        try:
            if isinstance(value, cls.data_type):
                return cls._to_knx(value)
            return cls._to_knx(cls.data_type.from_dict(value))  # type: ignore[arg-type]
        except (ValueError, TypeError, AttributeError, ConversionError) as err:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}: {err}", value=value
            ) from err

    @classmethod
    @abstractmethod
    def _to_knx(cls, value: _ComplexDataT) -> DPTArray | DPTBinary:
        """Serialize to KNX/IP raw data."""
