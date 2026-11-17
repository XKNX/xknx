"""Implementation of KNX v02.02.01 - Datapoint Types 03.07.02 - §3.24 DPT_VarString_8859_1."""

from __future__ import annotations

from xknx.cemi.const import MAX_NPDU_LENGTH
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .dpt import DPTBase
from .payload import DPTArray, DPTBinary


class DPTVariableLatin1(DPTBase):
    """
    Abstraction for a KNX variable length ISO 8859-1 string.

    DPT 24.001

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.24: "The length is not fixed, but
    variable; the string shall be terminated by a single character NULL (00h). No length
    information shall be transmitted in the APDU."

    `payload_length` is the longest payload a group telegram can carry: an L_Data_Extended
    frame's NPDU holds at most `MAX_NPDU_LENGTH` octets, one of which is the APCI octet of
    the A_GroupValue_Write/_Response-PDU. The terminating NULL counts towards it.
    """

    payload_type = DPTArray
    payload_length = MAX_NPDU_LENGTH - 1
    dpt_main_number = 24
    dpt_sub_number = 1
    value_type = "variable_latin_1"
    unit = None

    _encoding = "latin_1"

    @classmethod
    def validate_payload(cls, payload: DPTArray | DPTBinary) -> tuple[int, ...]:
        """Test if payload is an array of 1 to `payload_length` octets."""
        if not isinstance(payload, DPTArray):
            raise CouldNotParseTelegram(
                f"Invalid payload type for {cls.dpt_name()}", payload=payload
            )
        if not 0 < len(payload.value) <= cls.payload_length:
            raise CouldNotParseTelegram(
                f"Invalid payload length for {cls.dpt_name()}",
                payload=payload,
                max_length=cls.payload_length,
            )
        return payload.value

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> str:
        """Parse/deserialize from KNX/IP raw data."""
        raw = bytes(cls.validate_payload(payload))
        # A string without the terminating NULL is read up to the end of the payload.
        return raw.split(b"\x00", 1)[0].decode(cls._encoding, errors="replace")

    @classmethod
    def to_knx(cls, value: str) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        knx_value = str(value)
        if "\x00" in knx_value:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}: NULL inside the string",
                value=value,
            )
        # replace invalid characters with question marks
        raw_bytes = knx_value.encode(cls._encoding, errors="replace") + b"\x00"
        if len(raw_bytes) > cls.payload_length:
            raise ConversionError(
                f"Could not serialize {cls.dpt_name()}: longer than "
                f"{cls.payload_length} octets",
                value=value,
            )
        return DPTArray(raw_bytes)
