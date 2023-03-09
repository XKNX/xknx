"""
Module for serialization and deserialization of KNX/IP CEMI Frame.

cEMI stands for Common External Message Interface

A CEMI frame is the container to transport a KNX/IP Telegram to/from the KNX bus.

Documentation within:

    Application Note 117/08 v02
    KNX IP Communication Medium
    File: AN117 v02.01 KNX IP Communication Medium DV.pdf
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from xknx.exceptions import ConversionError, CouldNotParseCEMI, UnsupportedCEMIMessage
from xknx.profile.const import ResourceObjectType, ResourcePropertyId
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import APCI
from xknx.telegram.tpci import TPCI, TDataBroadcast

from .const import CEMIErrorCode, CEMIFlags, CEMIMessageCode


class CEMIInfo:
    """
    Raw helper class for all CEMI additional info.

    As specified within KNX Chapter 3.6.3/4.1.4.3 "Additional information".
    """

    def __init__(self, raw: bytes = bytes(0)):
        """Initialize CEMILInfo object."""
        self.raw = raw

    def calculated_length(self) -> int:
        """Get length of CEMI info."""
        return 1 + len(self.raw)

    @staticmethod
    def from_knx(raw: bytes) -> tuple[CEMIInfo, bytes]:
        """Parse/deserialize from CEMI raw data."""
        length = raw[0]
        return CEMIInfo(raw[1 : length + 1]), raw[length + 1 :]

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return bytes((len(self.raw),)) + self.raw

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f'CEMIInfo("{self.raw.hex()}")'

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__


class CEMIData(ABC):
    """Base class for all CEMI data."""

    @abstractmethod
    def calculated_length(self) -> int:
        """Get length of CEMI data."""

    @abstractmethod
    def to_knx(self) -> bytes:
        """Serialize to CEMI raw data."""

    @classmethod
    @abstractmethod
    def from_knx(cls, raw: bytes) -> CEMIData:
        """Parse/deserialize from KNX/IP raw data."""

    @abstractmethod
    def __repr__(self) -> str:
        """Return object as readable string."""

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__


class CEMILData(CEMIData):
    """Representation of CEMI Link Layer Data."""

    def __init__(
        self,
        *,
        flags: int,
        src_addr: IndividualAddress,
        dst_addr: GroupAddress | IndividualAddress,
        tpci: TPCI,
        payload: APCI | None,
    ):
        """Initialize CEMILData object."""
        self.flags = flags
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.tpci = tpci
        self.payload = payload

    @property
    def hops(self) -> int:
        """Return hops."""
        return (self.flags & 0x0070) >> 4

    @hops.setter
    def hops(self, val: int) -> None:
        """Set hops."""
        # Resetting hops
        self.flags &= 0xFFFF ^ 0x0070
        # Setting new hops
        self.flags |= val << 4

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        if not self.tpci.control and self.payload is not None:
            return 8 + self.payload.calculated_length()
        if self.tpci.control and self.payload is None:
            return 8
        raise TypeError("Data TPDU must have a payload; control TPDU must not.")

    @staticmethod
    def init_from_telegram(
        telegram: Telegram,
        src_addr: IndividualAddress | None = None,
    ) -> CEMILData:
        """Return CEMILData from a Telegram."""
        flags = (
            CEMIFlags.FRAME_TYPE_STANDARD
            | CEMIFlags.DO_NOT_REPEAT
            | CEMIFlags.BROADCAST
            | CEMIFlags.NO_ACK_REQUESTED
            | CEMIFlags.CONFIRM_NO_ERROR
            | CEMIFlags.HOP_COUNT_1ST
        )
        if isinstance(telegram.destination_address, GroupAddress):
            flags |= CEMIFlags.DESTINATION_GROUP_ADDRESS
            if isinstance(telegram.tpci, TDataBroadcast):
                flags |= CEMIFlags.PRIORITY_SYSTEM
            else:
                flags |= CEMIFlags.PRIORITY_LOW
        elif isinstance(telegram.destination_address, IndividualAddress):
            flags |= (
                CEMIFlags.DESTINATION_INDIVIDUAL_ADDRESS | CEMIFlags.PRIORITY_SYSTEM
            )
        else:
            raise TypeError()

        return CEMILData(
            flags=flags,
            src_addr=src_addr or telegram.source_address,
            dst_addr=telegram.destination_address,
            tpci=telegram.tpci,
            payload=telegram.payload,
        )

    def telegram(self) -> Telegram:
        """Return Telegram from a CEMILData."""

        return Telegram(
            destination_address=self.dst_addr,
            payload=self.payload,
            source_address=self.src_addr,
            tpci=self.tpci,
        )

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.tpci.control:
            tpdu = self.tpci.to_knx().to_bytes(1, "big")
            npdu_len = 0
        else:
            if not isinstance(self.payload, APCI):
                raise ConversionError(
                    f"Invalid payload set for data TPDU: {type(self.payload)}"
                )
            tpdu = self.payload.to_knx()
            tpdu[0] |= self.tpci.to_knx()
            npdu_len = self.payload.calculated_length()

        return (
            self.flags.to_bytes(2, "big")
            + self.src_addr.to_knx()
            + self.dst_addr.to_knx()
            + npdu_len.to_bytes(1, "big")
            + tpdu
        )

    @classmethod
    def from_knx(cls, raw: bytes) -> CEMILData:
        """Parse L_DATA_IND, CEMIMessageCode.L_DATA_REQ, CEMIMessageCode.L_DATA_CON."""
        if len(raw) < 8:
            raise CouldNotParseCEMI(
                f"CEMI too small. Length: {len(raw)}; CEMI: {raw.hex()}"
            )

        # Control field 1 and Control field 2 - first 2 octets
        flags = int.from_bytes(raw[0:2], "big")

        src_addr = IndividualAddress.from_knx(raw[2:4])

        _dst_is_group_address = bool(flags & CEMIFlags.DESTINATION_GROUP_ADDRESS)
        dst_addr: GroupAddress | IndividualAddress = (
            GroupAddress.from_knx(raw[4:6])
            if _dst_is_group_address
            else IndividualAddress.from_knx(raw[4:6])
        )

        _npdu_len = raw[6]
        _tpdu = raw[7:]
        _apdu = bytes([_tpdu[0] & 0b11]) + _tpdu[1:]  # clear TPCI bits
        if len(_apdu) != (_npdu_len + 1):  # TCPI octet not included in NPDU length
            raise CouldNotParseCEMI(
                f"APDU LEN should be {_npdu_len} but is {len(_apdu) - 1} "
                f"from {src_addr} in CEMI: {raw.hex()}"
            )

        # TPCI (transport layer control information)
        # - with control bit set -> 8 bit; no APDU
        # - no control bit set (data) -> First 6 bit
        # APCI (application layer control information) -> Last  10 bit of TPCI/APCI
        try:
            tpci = TPCI.resolve(
                raw_tpci=_tpdu[0],
                dst_is_group_address=_dst_is_group_address,
                dst_is_zero=not dst_addr.raw,
            )
        except ConversionError as err:
            raise UnsupportedCEMIMessage(
                f"TPCI not supported: {_tpdu[0]:#10b} "
                f"from {src_addr} in CEMI: {raw.hex()}"
            ) from err

        if tpci.control:
            if _npdu_len:
                raise CouldNotParseCEMI(
                    f"Invalid length for control TPDU {tpci}: {_npdu_len}"
                    f" from {src_addr} in CEMI: {raw.hex()}"
                )
            return cls(
                flags=flags,
                src_addr=src_addr,
                dst_addr=dst_addr,
                tpci=tpci,
                payload=None,
            )

        try:
            payload = APCI.from_knx(_apdu)
        except ConversionError as err:
            raise UnsupportedCEMIMessage(
                f"APDU not supported from {src_addr} "
                f"from {src_addr} in CEMI: {raw.hex()}"
            ) from err

        return cls(
            flags=flags,
            src_addr=src_addr,
            dst_addr=dst_addr,
            tpci=tpci,
            payload=payload,
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "CEMILData("
            f'src_addr="{self.src_addr.__repr__()}" '
            f'dst_addr="{self.dst_addr.__repr__()}" '
            f'flags="{self.flags:16b}" '
            f'tpci="{self.tpci}" '
            f'payload="{self.payload}")'
        )


class CEMIMPropInfo:
    """Representation of CEMI Device Management Property."""

    LENGTH = 6

    def __init__(
        self,
        *,
        object_type: ResourceObjectType,
        object_instance: int = 1,
        property_id: ResourcePropertyId | int,
        number_of_elements: int = 1,
        start_index: int = 1,
    ):
        """Initialize CEMIMProp object."""
        self.object_type = object_type
        self.object_instance = object_instance
        self.property_id = (
            property_id.value
            if isinstance(property_id, ResourcePropertyId)
            else property_id
        )
        self.number_of_elements = number_of_elements
        self.start_index = start_index

    def calculated_length(self) -> int:
        """Get length of CEMI data."""
        return CEMIMPropInfo.LENGTH

    @staticmethod
    def from_knx(raw: bytes) -> CEMIMPropInfo:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != CEMIMPropInfo.LENGTH:
            raise CouldNotParseCEMI(
                f"Invalid CEMI length: {len(raw)}; CEMI: {raw.hex()}"
            )

        try:
            object_type = ResourceObjectType(int.from_bytes(raw[0:2], "big"))
        except ValueError:
            raise UnsupportedCEMIMessage(
                f"CEMIMProp Object Type not supported: {raw[0:2].hex()} in CEMI: {raw.hex()}"
            )

        return CEMIMPropInfo(
            object_type=object_type,
            object_instance=raw[2],
            property_id=raw[3],
            number_of_elements=(raw[4] >> 4),
            start_index=(int.from_bytes(raw[4:6], "big") % 0x1000),
        )

    def to_knx(self) -> bytes:
        """Serialize to CEMI raw data."""
        return (
            self.object_type.value.to_bytes(2, "big")
            + self.object_instance.to_bytes(1, "big")
            + self.property_id.to_bytes(1, "big")
            + ((self.number_of_elements << 12) + self.start_index).to_bytes(2, "big")
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            f'object_type="{self.object_type.value}" '
            f'object_instance="{self.object_instance}" '
            f'property_id="{self.property_id}" '
            f'number_of_elements="{self.number_of_elements}" '
            f'start_index="{self.start_index}" '
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__


class CEMIMPropReadRequest(CEMIData):
    """Representation of CEMI Device Management Property Read Request."""

    def __init__(self, *, property_info: CEMIMPropInfo):
        """Initialize CEMIMPropReadRequest object."""
        self.property_info = property_info

    def calculated_length(self) -> int:
        """Get length of CEMI data."""
        return self.property_info.calculated_length()

    def to_knx(self) -> bytes:
        """Serialize to CEMI raw data."""
        return self.property_info.to_knx()

    @classmethod
    def from_knx(cls, raw: bytes) -> CEMIData:
        """Parse/deserialize from KNX/IP raw data."""
        return cls(property_info=CEMIMPropInfo.from_knx(raw))

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f"CEMIMPropReadRequest({self.property_info})"


class CEMIMPropReadResponse(CEMIData):
    """Representation of CEMI Device Management Property Read Response."""

    def __init__(
        self,
        *,
        property_info: CEMIMPropInfo,
        data: bytes,
    ):
        """Initialize CEMIMPropReadResponse object."""
        self.property_info = property_info
        self.data = data

    @property
    def error_code(self) -> CEMIErrorCode | None:
        """Return an optional CEMI error code."""
        if self.property_info.number_of_elements == 0:
            return CEMIErrorCode(self.data[0])

        return None

    def calculated_length(self) -> int:
        """Get length of CEMI data."""
        return CEMIMPropInfo.LENGTH + len(self.data)

    def to_knx(self) -> bytes:
        """Serialize to CEMI raw data."""
        return self.property_info.to_knx() + self.data

    @classmethod
    def from_knx(cls, raw: bytes) -> CEMIData:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) <= CEMIMPropInfo.LENGTH:
            raise CouldNotParseCEMI(
                f"CEMI Property Read Response too small. Length: {len(raw)}; CEMI: {raw.hex()}"
            )

        property_info = CEMIMPropInfo.from_knx(raw[0 : CEMIMPropInfo.LENGTH])

        # Did we get an error?
        if property_info.number_of_elements == 0 and len(raw) != 7:
            raise CouldNotParseCEMI(
                f"Invalid CEMI error response length: {len(raw)}; CEMI: {raw.hex()}"
            )

        return cls(property_info=property_info, data=raw[CEMIMPropInfo.LENGTH :])

    def __repr__(self) -> str:
        """Return object as readable string."""
        _data = (
            f'data="{self.data.hex()}" '
            if self.property_info.number_of_elements != 0
            else ""
        )
        return (
            f"CEMIMPropReadResponse("
            f"{self.property_info}"
            f'error_code="{self.error_code}" '
            f"{_data})"
        )


class CEMIMPropWriteRequest(CEMIData):
    """Representation of CEMI Device Management Property Write Request."""

    def __init__(
        self,
        *,
        property_info: CEMIMPropInfo,
        data: bytes,
    ):
        """Initialize CEMIMPropWriteRequest object."""
        self.property_info = property_info
        self.data = data

    def calculated_length(self) -> int:
        """Get length of CEMI data."""
        return CEMIMPropInfo.LENGTH + len(self.data)

    def to_knx(self) -> bytes:
        """Serialize to CEMI raw data."""
        return self.property_info.to_knx() + self.data

    @classmethod
    def from_knx(cls, raw: bytes) -> CEMIData:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) <= CEMIMPropInfo.LENGTH:
            raise CouldNotParseCEMI(
                f"CEMI Property Write Request too small. Length: {len(raw)}; CEMI: {raw.hex()}"
            )

        property_info = CEMIMPropInfo.from_knx(raw[0 : CEMIMPropInfo.LENGTH])

        return cls(property_info=property_info, data=raw[CEMIMPropInfo.LENGTH :])

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            f"CEMIMPropWriteRequest("
            f"{self.property_info}"
            f'data="{self.data.hex()}" )'
        )


class CEMIMPropWriteResponse(CEMIData):
    """Representation of CEMI Device Management Property Write Response."""

    def __init__(
        self,
        *,
        property_info: CEMIMPropInfo,
        error_code: CEMIErrorCode | None = None,
    ):
        """Initialize CEMIMPropWriteResponse object."""
        self.property_info = property_info
        self._error_code = error_code

    def calculated_length(self) -> int:
        """Get length of CEMI data."""
        return CEMIMPropInfo.LENGTH + (1 if self._error_code else 0)

    def to_knx(self) -> bytes:
        """Serialize to CEMI raw data."""
        if self._error_code:
            return self.property_info.to_knx() + self._error_code.value.to_bytes(
                1, "big"
            )

        return self.property_info.to_knx()

    @property
    def error_code(self) -> CEMIErrorCode | None:
        """Return an optional CEMI error code."""
        return self._error_code

    @classmethod
    def from_knx(cls, raw: bytes) -> CEMIData:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < CEMIMPropInfo.LENGTH:
            raise CouldNotParseCEMI(
                f"CEMI Property Write Response too small. Length: {len(raw)}; CEMI: {raw.hex()}"
            )

        property_info = CEMIMPropInfo.from_knx(raw[0 : CEMIMPropInfo.LENGTH])

        # Did we get an error?
        if property_info.number_of_elements == 0:
            if len(raw) != 7:
                raise CouldNotParseCEMI(
                    f"Invalid CEMI error response length: {len(raw)}; CEMI: {raw.hex()}"
                )
            return cls(
                property_info=property_info,
                error_code=CEMIErrorCode(raw[CEMIMPropInfo.LENGTH]),
            )

        if len(raw) != CEMIMPropInfo.LENGTH:
            raise CouldNotParseCEMI(
                f"Invalid CEMI response length: {len(raw)}; CEMI: {raw.hex()}"
            )

        return cls(property_info=property_info)

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            f"CEMIMPropWriteResponse("
            f"{self.property_info}"
            f'error_code="{self.error_code}" )'
        )


class CEMIFrame:
    """Representation of a CEMI Frame."""

    def __init__(
        self,
        *,
        code: CEMIMessageCode,
        info: CEMIInfo | None = None,
        data: CEMIData | None,
    ):
        """Initialize CEMIFrame object."""
        self.code = code
        self.info = info or CEMIInfo()
        self.data = data

    @staticmethod
    def _has_info(code: CEMIMessageCode) -> bool:
        return code not in (
            CEMIMessageCode.M_PROP_READ_REQ,
            CEMIMessageCode.M_PROP_READ_CON,
            CEMIMessageCode.M_PROP_WRITE_REQ,
            CEMIMessageCode.M_PROP_WRITE_CON,
            CEMIMessageCode.M_PROP_INFO_IND,
            CEMIMessageCode.M_FUNC_PROP_COMMAND_REQ,
            CEMIMessageCode.M_FUNC_PROP_STATE_READ_REQ,
            CEMIMessageCode.M_FUNC_PROP_COMMAND_CON,
            CEMIMessageCode.M_FUNC_PROP_STATE_READ_CON,
            CEMIMessageCode.M_RESET_REQ,
            CEMIMessageCode.M_RESET_IND,
        )

    @staticmethod
    def _has_data(code: CEMIMessageCode) -> bool:
        return code not in (
            CEMIMessageCode.M_RESET_REQ,
            CEMIMessageCode.M_RESET_IND,
        )

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        length = 1

        if self._has_info(self.code):
            length += self.info.calculated_length()

        if self._has_data(self.code):
            if self.data is None:
                raise UnsupportedCEMIMessage(
                    f"CEMI data required for code: {self.code}"
                )
            length += self.data.calculated_length()

        return length

    @staticmethod
    def from_knx(raw: bytes) -> CEMIFrame:
        """Parse/deserialize from KNX/IP raw data."""
        try:
            code = CEMIMessageCode(raw[0])
        except ValueError:
            raise UnsupportedCEMIMessage(
                f"CEMIMessageCode not implemented: {raw[0]} in CEMI: {raw.hex()}"
            )

        if code in (
            CEMIMessageCode.L_DATA_IND,
            CEMIMessageCode.L_DATA_REQ,
            CEMIMessageCode.L_DATA_CON,
        ):
            info, remainder = CEMIInfo.from_knx(raw[1:])
            return CEMIFrame(
                code=code,
                info=info,
                data=CEMILData.from_knx(remainder),
            )
        if code == CEMIMessageCode.M_PROP_READ_REQ:
            return CEMIFrame(code=code, data=CEMIMPropReadRequest.from_knx(raw[1:]))
        if code == CEMIMessageCode.M_PROP_READ_CON:
            return CEMIFrame(code=code, data=CEMIMPropReadResponse.from_knx(raw[1:]))
        if code == CEMIMessageCode.M_PROP_WRITE_REQ:
            return CEMIFrame(code=code, data=CEMIMPropWriteRequest.from_knx(raw[1:]))
        if code == CEMIMessageCode.M_PROP_WRITE_CON:
            return CEMIFrame(code=code, data=CEMIMPropWriteResponse.from_knx(raw[1:]))

        raise UnsupportedCEMIMessage(
            f"Could not handle CEMIMessageCode: {code} / {raw[0]} in CEMI: {raw.hex()}"
        )

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        raw = bytes((self.code.value,))

        if self._has_info(self.code):
            raw += self.info.to_knx()

        if self._has_data(self.code):
            if self.data is None:
                raise UnsupportedCEMIMessage(
                    f"CEMI data required for code: {self.code}"
                )
            raw += self.data.to_knx()

        return raw

    def __repr__(self) -> str:
        """Return object as readable string."""
        _info = f'info="{self.info.__repr__()}" ' if self._has_info(self.code) else ""
        _data = f'data="{self.data.__repr__()}" ' if self._has_data(self.code) else ""

        return f'<CEMIFrame code="{self.code.name}" {_info}{_data}/>'

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
