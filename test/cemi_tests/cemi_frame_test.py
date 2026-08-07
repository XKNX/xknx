"""Tests for the CEMIFrame object."""

import pytest

from xknx.cemi import (
    CEMIFlags,
    CEMIFrame,
    CEMILData,
    CEMIMessageCode,
    CEMIMPropReadRequest,
    CEMIMPropReadResponse,
    CEMIMPropWriteRequest,
    CEMIMPropWriteResponse,
)
from xknx.cemi.const import CEMIErrorCode
from xknx.dpt import DPTArray
from xknx.exceptions import ConversionError, CouldNotParseCEMI, UnsupportedCEMIMessage
from xknx.profile.const import ResourceKNXNETIPPropertyId, ResourceObjectType
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite
from xknx.telegram.tpci import TConnect, TDataBroadcast, TDataGroup


def get_data(
    code: int,
    adil: int,
    flags: int,
    src: int,
    dst: int,
    npdu_len: int,
    tpci_apci: int,
    payload: list[int],
) -> bytes:
    """Encode to cemi data raw bytes."""
    return bytes(
        [
            code,
            adil,  # adil
            (flags >> 8) & 255,  # flags
            flags & 255,  # flags
            (src >> 8) & 255,  # src
            src & 255,  # src
            (dst >> 8) & 255,  # dst
            dst & 255,  # dst
            npdu_len,  # npdu_len
            (tpci_apci >> 8) & 255,  # tpci_apci
            tpci_apci & 255,  # tpci_apci
            *payload,  # payload
        ]
    )


def test_valid_command() -> None:
    """Test for valid frame parsing."""
    raw = get_data(0x29, 0, 0x8080, 1, 1, 1, 0, [])
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.L_DATA_IND
    assert isinstance(frame.data, CEMILData)
    assert frame.data.flags == 0x8080
    assert frame.data.hops == 0
    assert frame.data.src_addr == IndividualAddress(1)
    assert frame.data.dst_addr == GroupAddress(1)
    assert frame.data.payload == GroupValueRead()
    assert frame.data.tpci == TDataGroup()
    assert frame.calculated_length() == 11
    assert frame.to_knx() == raw


def test_valid_tpci_control() -> None:
    """Test for valid tpci control."""
    raw = bytes((0x29, 0, 0x80, 0, 0, 0, 0, 0, 0, 0x80))
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.L_DATA_IND
    assert isinstance(frame.data, CEMILData)
    assert frame.data.flags == 0x8000
    assert frame.data.hops == 0
    assert frame.data.payload is None
    assert frame.data.src_addr == IndividualAddress(0)
    assert frame.data.dst_addr == IndividualAddress(0)
    assert frame.data.tpci == TConnect()
    assert frame.calculated_length() == 10
    assert frame.to_knx() == raw


@pytest.mark.parametrize(
    "raw,err_msg",
    [
        (
            get_data(0x29, 0, 0, 0, 0, 1, 0xFFC0, []),
            r".*Invalid length for control TPDU.*",
        ),
    ],
)
def test_invalid_tpci_apci(raw: bytes, err_msg: str) -> None:
    """Test for invalid APCIService."""
    with pytest.raises(CouldNotParseCEMI, match=err_msg):
        CEMIFrame.from_knx(raw)


@pytest.mark.parametrize(
    "raw,err_msg",
    [
        (
            get_data(0x29, 0, 0, 0, 0, 1, 0x08C0, []),
            r".*TPCI not supported.*",
        ),
        (
            # reserved gap between A_FilterTable_Write and A_RouterMemory_Read
            get_data(0x29, 0, 0, 0, 0, 1, 0x03C4, []),
            r"APDU not supported*",
        ),
        (
            # A_RouterStatus_Read - legacy BCU coupler service, deliberately
            # unimplemented; must be rejected cleanly, not crash the receive
            # path with an uncaught NotImplementedError.
            get_data(0x29, 0, 0, 0, 0, 1, 0x03CD, []),
            r"APDU not supported*",
        ),
        (
            # A_RouterStatus_Response
            get_data(0x29, 0, 0, 0, 0, 1, 0x03CE, []),
            r"APDU not supported*",
        ),
        (
            # A_RouterStatus_Write
            get_data(0x29, 0, 0, 0, 0, 1, 0x03CF, []),
            r"APDU not supported*",
        ),
    ],
)
def test_unsupported_tpci_apci(raw: bytes, err_msg: str) -> None:
    """Test for invalid APCIService."""
    with pytest.raises(UnsupportedCEMIMessage, match=err_msg):
        CEMIFrame.from_knx(raw)


def test_truncated_secure_apdu() -> None:
    """
    Test a real captured frame with a truncated secured APDU is rejected cleanly.

    L_Data.con, src 1.1.253, dst 1/1/78, carrying an A_SecureData APDU
    (APCI 0x3F1) with no secure ASDU - observed on a real bus. Parsing this
    used to leak a bare IndexError out of SecureAPDU.from_knx and crash the
    receive path. It must now be rejected as CouldNotParseCEMI - a recognized
    service with a malformed payload is a parse error, not an unsupported one.
    """
    raw = bytes.fromhex("2e00bcf011fd094e0103f1")
    with pytest.raises(CouldNotParseCEMI, match=r"APDU invalid"):
        CEMIFrame.from_knx(raw)


def test_invalid_secure_apdu_keeps_cause_in_message() -> None:
    """
    Test the CEMI parse error repeats the underlying APDU error message.

    L_Data.ind carrying an A_SecureData APDU (APCI 0x3F1) whose SCF names the
    reserved S-A-Service 0b100. `CouldNotParseCEMI` is logged as a plain string,
    so the message must carry the cause; without it the log only says "APDU
    invalid" and the actual defect of the frame is lost.
    """
    raw = bytes.fromhex(
        "290030e010fc00001803f194003f1414e8e5000a46492919b3498640a7655948919e"
    )
    with pytest.raises(CouldNotParseCEMI) as err_info:
        CEMIFrame.from_knx(raw)

    message = str(err_info.value)
    assert "APDU invalid" in message
    assert "Error parsing APCI 0b1111110001" in message  # APCI layer
    assert "4 is not a valid SecurityALService" in message  # root cause
    assert "from 1.0.252 to 0/0/0" in message  # CEMI layer context


def test_invalid_apdu_len() -> None:
    """Test for invalid apdu len."""
    with pytest.raises(CouldNotParseCEMI, match=r".*APDU LEN should be .*"):
        CEMIFrame.from_knx(get_data(0x29, 0, 0, 0, 0, 2, 0, []))


def test_invalid_payload() -> None:
    """Test for having wrong payload set."""
    frame = CEMIFrame(
        code=CEMIMessageCode.L_DATA_IND,
        data=CEMILData(
            flags=0,
            src_addr=IndividualAddress(0),
            dst_addr=IndividualAddress(0),
            tpci=TDataGroup(),
            payload=None,
        ),
    )

    with pytest.raises(TypeError):
        frame.calculated_length()

    with pytest.raises(ConversionError):
        frame.to_knx()


def test_missing_data() -> None:
    """Test for having no data set."""
    frame = CEMIFrame(
        code=CEMIMessageCode.L_DATA_IND,
        data=None,
    )

    with pytest.raises(UnsupportedCEMIMessage):
        frame.calculated_length()

    with pytest.raises(UnsupportedCEMIMessage):
        frame.to_knx()


def test_from_knx_with_not_handleable_cemi() -> None:
    """Test for having unhandlebale cemi set."""
    with pytest.raises(
        UnsupportedCEMIMessage, match=r".*CEMIMessageCode not implemented:.*"
    ):
        CEMIFrame.from_knx(get_data(0x30, 0, 0, 0, 0, 2, 0, []))


def test_from_knx_with_not_implemented_cemi() -> None:
    """Test for having not implemented CEMI set."""
    with pytest.raises(
        UnsupportedCEMIMessage, match=r".*Could not handle CEMIMessageCode:.*"
    ):
        CEMIFrame.from_knx(
            get_data(CEMIMessageCode.L_BUSMON_IND.value, 0, 0, 0, 0, 2, 0, [])
        )


def test_invalid_invalid_len() -> None:
    """Test for invalid cemi len."""
    with pytest.raises(CouldNotParseCEMI, match=r".*CEMI too small.*"):
        CEMIFrame.from_knx(get_data(0x29, 0, 0, 0, 0, 2, 0, [])[:5])


def test_from_knx_group_address() -> None:
    """Test conversion for a cemi with a group address as destination."""
    frame = CEMIFrame.from_knx(get_data(0x29, 0, 0x80, 0, 0, 1, 0, []))
    assert isinstance(frame.data, CEMILData)
    assert frame.data.dst_addr == GroupAddress(0)


def test_from_knx_individual_address() -> None:
    """Test conversion for a cemi with a individual address as destination."""
    frame = CEMIFrame.from_knx(get_data(0x29, 0, 0x00, 0, 0, 1, 0, []))
    assert isinstance(frame.data, CEMILData)
    assert frame.data.dst_addr == IndividualAddress(0)


def test_telegram_group_address() -> None:
    """Test telegram conversion flags with a group address."""
    _telegram = Telegram(destination_address=GroupAddress(1))
    frame = CEMIFrame(
        code=CEMIMessageCode.L_DATA_IND,
        data=CEMILData.init_from_telegram(_telegram),
    )
    assert isinstance(frame.data, CEMILData)
    assert frame.data.flags & 0x0080 == CEMIFlags.DESTINATION_GROUP_ADDRESS
    assert frame.data.flags & 0x0C00 == CEMIFlags.PRIORITY_LOW
    # test CEMIFrame.telegram property
    assert frame.data.telegram() == _telegram


def test_telegram_broadcast() -> None:
    """Test telegram conversion flags with a group address."""
    _telegram = Telegram(destination_address=GroupAddress(0))
    frame = CEMIFrame(
        code=CEMIMessageCode.L_DATA_IND,
        data=CEMILData.init_from_telegram(_telegram),
    )
    assert isinstance(frame.data, CEMILData)
    assert frame.data.flags & 0x0080 == CEMIFlags.DESTINATION_GROUP_ADDRESS
    assert frame.data.flags & 0x0C00 == CEMIFlags.PRIORITY_SYSTEM
    assert frame.data.tpci == TDataBroadcast()
    # test CEMIFrame.telegram property
    assert frame.data.telegram() == _telegram


def test_telegram_individual_address() -> None:
    """Test telegram conversion flags with a individual address."""
    _telegram = Telegram(destination_address=IndividualAddress(0), tpci=TConnect())
    frame = CEMIFrame(
        code=CEMIMessageCode.L_DATA_IND,
        data=CEMILData.init_from_telegram(_telegram),
    )
    assert isinstance(frame.data, CEMILData)
    assert frame.data.flags & 0x0080 == CEMIFlags.DESTINATION_INDIVIDUAL_ADDRESS
    assert frame.data.flags & 0x0C00 == CEMIFlags.PRIORITY_SYSTEM
    assert frame.data.flags & 0x0200 == CEMIFlags.NO_ACK_REQUESTED
    # test CEMIFrame.telegram property
    assert frame.data.telegram() == _telegram


def test_telegram_unsupported_address() -> None:
    """Test telegram conversion flags with an unsupported address."""
    with pytest.raises(TypeError):
        CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(Telegram(destination_address=object())),
        )


def _cemi_l_data_from_payload(payload: GroupValueWrite) -> bytes:
    """Serialize a group write telegram to raw CEMI L_Data bytes."""
    return CEMILData.init_from_telegram(
        Telegram(destination_address=GroupAddress(1), payload=payload),
        src_addr=IndividualAddress(1),
    ).to_knx()


@pytest.mark.parametrize(
    "apdu_payload_length,expected_npdu_len,expected_frame_type",
    [
        (1, 2, CEMIFlags.FRAME_TYPE_STANDARD),
        # 15 octets after the TPCI octet is the maximum of a standard frame
        (14, 15, CEMIFlags.FRAME_TYPE_STANDARD),
        (15, 16, CEMIFlags.FRAME_TYPE_EXTENDED),
        (253, 254, CEMIFlags.FRAME_TYPE_EXTENDED),
    ],
)
def test_frame_type_from_npdu_length(
    apdu_payload_length: int, expected_npdu_len: int, expected_frame_type: int
) -> None:
    """Test Frame Type flag is derived from the NPDU length."""
    raw = _cemi_l_data_from_payload(
        GroupValueWrite(DPTArray(bytes(apdu_payload_length)))
    )
    assert raw[6] == expected_npdu_len
    assert (raw[0] << 8) & CEMIFlags.FRAME_TYPE_STANDARD == expected_frame_type


def test_frame_type_overrides_flags() -> None:
    """Test Frame Type flag of `flags` is overridden by the payload length."""
    long_payload = GroupValueWrite(DPTArray(bytes(15)))
    short_payload = GroupValueWrite(DPTArray(bytes(1)))
    cemi_data = CEMILData(
        # standard frame flag set although the payload requires an extended frame
        flags=CEMIFlags.FRAME_TYPE_STANDARD | CEMIFlags.DESTINATION_GROUP_ADDRESS,
        src_addr=IndividualAddress(1),
        dst_addr=GroupAddress(1),
        tpci=TDataGroup(),
        payload=long_payload,
    )
    assert not cemi_data.to_knx()[0] & 0x80
    # `flags` is not modified by serialization
    assert cemi_data.flags & CEMIFlags.FRAME_TYPE_STANDARD

    cemi_data.flags = CEMIFlags.DESTINATION_GROUP_ADDRESS  # extended frame flag
    cemi_data.payload = short_payload
    assert cemi_data.to_knx()[0] & 0x80


def test_npdu_length_exceeded() -> None:
    """Test APDU too long for a single frame."""
    with pytest.raises(ConversionError, match=r".*APDU too long for a single frame.*"):
        _cemi_l_data_from_payload(GroupValueWrite(DPTArray(bytes(254))))


def test_extended_frame_format_not_supported() -> None:
    """Test parsing of LTE-HEE and reserved Extended Frame Formats."""
    raw = get_data(
        0x29,
        0,
        CEMIFlags.FRAME_TYPE_EXTENDED
        | CEMIFlags.DESTINATION_GROUP_ADDRESS
        | CEMIFlags.LTE_FRAME_FORMAT,
        1,
        1,
        1,
        0,
        [],
    )
    with pytest.raises(
        UnsupportedCEMIMessage, match=r".*Extended Frame Format not supported.*"
    ):
        CEMIFrame.from_knx(raw)


def test_frame_type_not_validated_when_parsing() -> None:
    """Test tolerance towards the Frame Type flag when parsing - 3/6/3 §4.1.5.2.3."""
    # standard frame flag with a 17 octet NPDU; eg. AN158 v07 Annex A example
    raw = get_data(0x29, 0, 0x8080, 1, 1, 17, 0x0080, list(range(16)))
    frame = CEMIFrame.from_knx(raw)
    assert isinstance(frame.data, CEMILData)
    assert frame.data.payload == GroupValueWrite(DPTArray(bytes(range(16))))
    # serializing it again corrects the Frame Type flag
    assert not frame.to_knx()[2] & 0x80


def get_prop(
    code: int,
    obj_id: int,
    obj_inst: int,
    prop_id: int,
    num: int,
    six: int,
    payload: list[int],
) -> bytes:
    """Encode to cemi prop raw bytes."""
    return bytes(
        [
            code,
            (obj_id >> 8) & 255,  # Interface Object Type
            obj_id & 255,  # Interface Object Type
            obj_inst & 255,  # Object instance
            prop_id & 255,  # Property ID
            (num << 4) | (six >> 8),  # Number of Elements (4bit) Start index (hsb 4bit)
            six & 255,  # Start index (lsb 8bit)
            *payload,  # payload
        ]
    )


def test_valid_read_req() -> None:
    """Test for valid frame parsing."""
    raw = get_prop(0xFC, 0x000B, 1, 52, 1, 1, [])
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.M_PROP_READ_REQ
    assert isinstance(frame.data, CEMIMPropReadRequest)
    assert (
        frame.data.property_info.object_type
        == ResourceObjectType.OBJECT_KNXNETIP_PARAMETER
    )
    assert frame.data.property_info.object_instance == 1
    assert (
        frame.data.property_info.property_id
        == ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS
    )
    assert frame.data.property_info.number_of_elements == 1
    assert frame.data.property_info.start_index == 1
    assert frame.calculated_length() == 7
    assert frame.to_knx() == raw
    with pytest.raises(AttributeError):
        frame.data.telegram()


def test_valid_read_con() -> None:
    """Test for valid frame parsing."""
    raw = get_prop(0xFB, 0x000B, 1, 52, 1, 1, [0x12, 0x03])
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.M_PROP_READ_CON
    assert isinstance(frame.data, CEMIMPropReadResponse)
    assert (
        frame.data.property_info.object_type
        == ResourceObjectType.OBJECT_KNXNETIP_PARAMETER
    )
    assert frame.data.property_info.object_instance == 1
    assert (
        frame.data.property_info.property_id
        == ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS
    )
    assert frame.data.property_info.number_of_elements == 1
    assert frame.data.property_info.start_index == 1
    assert frame.data.error_code is None
    assert IndividualAddress.from_knx(frame.data.data) == IndividualAddress("1.2.3")
    assert frame.calculated_length() == 9
    assert frame.to_knx() == raw


def test_valid_error_read_con() -> None:
    """Test for valid frame parsing."""
    raw = get_prop(0xFB, 0x000B, 1, 52, 0, 1, [0x07])
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.M_PROP_READ_CON
    assert isinstance(frame.data, CEMIMPropReadResponse)
    assert (
        frame.data.property_info.object_type
        == ResourceObjectType.OBJECT_KNXNETIP_PARAMETER
    )
    assert frame.data.property_info.object_instance == 1
    assert (
        frame.data.property_info.property_id
        == ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS
    )
    assert frame.data.property_info.number_of_elements == 0
    assert frame.data.property_info.start_index == 1
    assert frame.data.error_code == CEMIErrorCode.CEMI_ERROR_VOID_DP
    assert frame.calculated_length() == 8
    assert frame.to_knx() == raw


def test_valid_write_req() -> None:
    """Test for valid frame parsing."""
    raw = get_prop(0xF6, 0x000B, 1, 52, 1, 1, [0x12, 0x03])
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.M_PROP_WRITE_REQ
    assert isinstance(frame.data, CEMIMPropWriteRequest)
    assert (
        frame.data.property_info.object_type
        == ResourceObjectType.OBJECT_KNXNETIP_PARAMETER
    )
    assert frame.data.property_info.object_instance == 1
    assert (
        frame.data.property_info.property_id
        == ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS
    )
    assert frame.data.property_info.number_of_elements == 1
    assert frame.data.property_info.start_index == 1
    assert IndividualAddress.from_knx(frame.data.data) == IndividualAddress("1.2.3")
    assert frame.calculated_length() == 9
    assert frame.to_knx() == raw


def test_valid_empty_write_con() -> None:
    """Test for valid frame parsing."""
    raw = get_prop(0xF5, 0x000B, 1, 52, 1, 1, [])
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.M_PROP_WRITE_CON
    assert isinstance(frame.data, CEMIMPropWriteResponse)
    assert (
        frame.data.property_info.object_type
        == ResourceObjectType.OBJECT_KNXNETIP_PARAMETER
    )
    assert frame.data.property_info.object_instance == 1
    assert (
        frame.data.property_info.property_id
        == ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS
    )
    assert frame.data.property_info.number_of_elements == 1
    assert frame.data.property_info.start_index == 1
    assert frame.data.error_code is None
    assert frame.calculated_length() == 7
    assert frame.to_knx() == raw


def test_valid_error_write_con() -> None:
    """Test for valid frame parsing."""
    raw = get_prop(0xF5, 0x000B, 1, 52, 0, 1, [0x07])
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.M_PROP_WRITE_CON
    assert isinstance(frame.data, CEMIMPropWriteResponse)
    assert (
        frame.data.property_info.object_type
        == ResourceObjectType.OBJECT_KNXNETIP_PARAMETER
    )
    assert frame.data.property_info.object_instance == 1
    assert (
        frame.data.property_info.property_id
        == ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS
    )
    assert frame.data.property_info.number_of_elements == 0
    assert frame.data.property_info.start_index == 1
    assert frame.data.error_code == CEMIErrorCode.CEMI_ERROR_VOID_DP
    assert frame.calculated_length() == 8
    assert frame.to_knx() == raw


@pytest.mark.parametrize(
    "raw,err_msg",
    [
        (
            get_prop(0xFC, 0x000B, 1, 52, 1, 1, [])[:5],
            r".*Invalid CEMI length:*",
        ),
        (
            get_prop(0xFB, 0x000B, 1, 52, 1, 1, [])[:5],
            r".*CEMI Property Read Response too small.*",
        ),
        (
            get_prop(0xFB, 0x000B, 1, 52, 0, 1, [0x07, 0x00]),
            r".*Invalid CEMI error response length:.*",
        ),
        (
            get_prop(0xF6, 0x000B, 1, 52, 1, 1, [])[:5],
            r".*CEMI Property Write Request too small.*",
        ),
        (
            get_prop(0xF5, 0x000B, 1, 52, 1, 1, [])[:5],
            r".*CEMI Property Write Response too small.*",
        ),
        (
            get_prop(0xF5, 0x000B, 1, 52, 0, 1, [0x07, 0x00]),
            r".*Invalid CEMI error response length:.*",
        ),
        (
            get_prop(0xF5, 0x000B, 1, 52, 1, 1, [0x07]),
            r".*Invalid CEMI response length:.*",
        ),
    ],
)
def test_invalid_length(raw: bytes, err_msg: str) -> None:
    """Test for invalid frame parsing."""
    with pytest.raises(CouldNotParseCEMI, match=err_msg):
        CEMIFrame.from_knx(raw)


def test_invalid_resource_object() -> None:
    """Test for invalid frame parsing."""
    with pytest.raises(
        UnsupportedCEMIMessage, match=r".*CEMIMProp Object Type not supported:.*"
    ):
        CEMIFrame.from_knx(get_prop(0xFC, 0x1234, 1, 52, 1, 1, []))
