"""Implementation of KNX DPT 234 language and region codes."""

from __future__ import annotations

from xknx.exceptions import ConversionError

from .dpt_16 import DPTString
from .payload import DPTArray, DPTBinary


def _is_code(value: str) -> bool:
    """Return True if value consists of exactly two ASCII letters."""
    return len(value) == 2 and value.isascii() and value.isalpha()


class DPTLanguageCodeAlpha2ASCII(DPTString):
    """
    Abstraction for KNX 2 Octet language code (ISO 639-1 alpha-2).

    The encoding is not case sensitive. Lower case is sent; received upper case
    is decoded to lower case.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.47.1.1
    DPT 234.001
    """

    payload_length = 2
    dpt_main_number = 234
    dpt_sub_number = 1
    value_type = "language_code_alpha2"

    _encoding = "ascii"
    _upper_case = False

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> str:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        value = bytes(raw).decode("latin_1")
        if not _is_code(value):
            raise ConversionError(f"Could not parse {cls.dpt_name()}", raw=raw)
        return value.upper() if cls._upper_case else value.lower()

    @classmethod
    def to_knx(cls, value: str) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not isinstance(value, str) or not _is_code(value):
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}: two ASCII letters expected",
                value=value,
            )
        code = value.upper() if cls._upper_case else value.lower()
        return DPTArray(code.encode(cls._encoding))


class DPTRegionCodeAlpha2ASCII(DPTLanguageCodeAlpha2ASCII):
    """
    Abstraction for KNX 2 Octet region code (ISO 3166-1 alpha-2).

    The encoding is not case sensitive. Upper case is sent (as in the spec
    examples); received lower case is decoded to upper case.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.47.2
    DPT 234.002
    """

    dpt_main_number = 234
    dpt_sub_number = 2
    value_type = "region_code_alpha2"

    _upper_case = True
