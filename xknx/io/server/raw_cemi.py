"""
Raw cEMI frames as a KNXnet/IP tunnelling server passes them on.

A server forwards the frames of its clients unchanged, also those with services
xknx doesn't parse. So only the fields the server needs are read from the raw
octets - the message code, the control fields and the addresses - and a frame is
sent through an `Interface` as it was received.
"""

from __future__ import annotations

from typing import Final

from xknx.cemi import CEMIFrame, CEMIMessageCode
from xknx.cemi.cemi_frame import CEMIData, CEMIInfo
from xknx.exceptions import CouldNotParseCEMI
from xknx.telegram import GroupAddress, IndividualAddress

# control field 1: confirm flag, 0 = no error - KNX v01.04.02 - External Message
# Interface 03.06.03 - §4.1.5.3.4
_CONFIRM_ERROR: Final = 0x01
# control field 2: destination address type, 1 = group address - KNX v01.04.02 -
# External Message Interface 03.06.03 - §4.1.5.3.2
_GROUP_ADDRESS: Final = 0x80
# control field 1, control field 2, source, destination, length
_L_DATA_HEADER_LENGTH: Final = 7

_L_DATA_CODES: Final = frozenset(
    {
        CEMIMessageCode.L_DATA_REQ.value,
        CEMIMessageCode.L_DATA_CON.value,
        CEMIMessageCode.L_DATA_IND.value,
    }
)


class LDataFrame:
    """An L_Data.req, L_Data.con or L_Data.ind cEMI frame kept as raw octets."""

    __slots__ = ("_control", "raw")

    def __init__(self, raw: bytes) -> None:
        """Initialize LDataFrame. Raise CouldNotParseCEMI for anything else."""
        if len(raw) < 2 or raw[0] not in _L_DATA_CODES:
            raise CouldNotParseCEMI(f"No L_Data frame: {raw.hex()}")
        control = 2 + raw[1]
        if len(raw) < control + _L_DATA_HEADER_LENGTH:
            raise CouldNotParseCEMI(f"L_Data frame too short: {raw.hex()}")
        self.raw = raw
        # offset of control field 1
        self._control = control

    @classmethod
    def parse(cls, raw: bytes) -> LDataFrame | None:
        """Return the frame, or None when `raw` is no valid L_Data frame."""
        try:
            return cls(raw)
        except CouldNotParseCEMI:
            return None

    @property
    def code(self) -> CEMIMessageCode:
        """Return the message code."""
        return CEMIMessageCode(self.raw[0])

    @property
    def confirm_error(self) -> bool:
        """Return whether an L_Data.con reports that the frame couldn't be sent."""
        return bool(self.raw[self._control] & _CONFIRM_ERROR)

    @property
    def source(self) -> IndividualAddress:
        """Return the source address."""
        return IndividualAddress.from_knx(
            self.raw[self._control + 2 : self._control + 4]
        )

    @property
    def destination(self) -> GroupAddress | IndividualAddress:
        """Return the destination address."""
        raw_address = self.raw[self._control + 4 : self._control + 6]
        if self.raw[self._control + 1] & _GROUP_ADDRESS:
            return GroupAddress.from_knx(raw_address)
        return IndividualAddress.from_knx(raw_address)

    def with_code(
        self, code: CEMIMessageCode, confirm_error: bool = False
    ) -> LDataFrame:
        """Return the frame with another message code and the confirm flag set or cleared."""
        control_1 = self.raw[self._control] & ~_CONFIRM_ERROR
        if confirm_error:
            control_1 |= _CONFIRM_ERROR
        return LDataFrame(
            bytes((code.value,))
            + self.raw[1 : self._control]
            + bytes((control_1,))
            + self.raw[self._control + 1 :]
        )

    def with_source(self, source: IndividualAddress) -> LDataFrame:
        """Return the frame with another source address."""
        return LDataFrame(
            self.raw[: self._control + 2]
            + source.to_knx()
            + self.raw[self._control + 4 :]
        )

    def with_destination(self, destination: IndividualAddress) -> LDataFrame:
        """Return a point-to-point frame with another destination address."""
        return LDataFrame(
            self.raw[: self._control + 4]
            + destination.to_knx()
            + self.raw[self._control + 6 :]
        )

    @property
    def tpci(self) -> int | None:
        """Return the first octet of the TPDU, None when the frame has none."""
        offset = self._control + _L_DATA_HEADER_LENGTH
        return self.raw[offset] if len(self.raw) > offset else None

    def cemi_frame(self) -> CEMIFrame:
        """Return a CEMIFrame that an `Interface` sends as these octets."""
        info, remainder = CEMIInfo.from_knx(self.raw[1:])
        return CEMIFrame(code=self.code, info=info, data=_RawCEMIData(remainder))

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f'<LDataFrame code="{self.code.name}" raw="{self.raw.hex()}" />'


class _RawCEMIData(CEMIData):
    """The service information of a cEMI frame kept as raw octets."""

    def __init__(self, raw: bytes) -> None:
        """Initialize _RawCEMIData object."""
        self.raw = raw

    def calculated_length(self) -> int:
        """Get length of CEMI data."""
        return len(self.raw)

    def to_knx(self) -> bytes:
        """Serialize to CEMI raw data."""
        return self.raw

    @classmethod
    def from_knx(cls, raw: bytes) -> CEMIData:
        """Parse/deserialize from KNX/IP raw data."""
        return cls(raw)

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f'_RawCEMIData("{self.raw.hex()}")'
