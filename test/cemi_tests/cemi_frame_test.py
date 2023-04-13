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
from xknx.exceptions import ConversionError, CouldNotParseCEMI, UnsupportedCEMIMessage
from xknx.profile.const import ResourceKNXNETIPPropertyId, ResourceObjectType
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueRead
from xknx.telegram.tpci import TConnect, TDataBroadcast, TDataGroup


def get_data(code, adil, flags, src, dst, npdu_len, tpci_apci, payload):
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


def test_valid_command():
    """Test for valid frame parsing."""
    raw = get_data(0x29, 0, 0x0080, 1, 1, 1, 0, [])
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.L_DATA_IND
    assert isinstance(frame.data, CEMILData)
    assert frame.data.flags == 0x0080
    assert frame.data.hops == 0
    assert frame.data.src_addr == IndividualAddress(1)
    assert frame.data.dst_addr == GroupAddress(1)
    assert frame.data.payload == GroupValueRead()
    assert frame.data.tpci == TDataGroup()
    assert frame.calculated_length() == 11
    assert frame.to_knx() == raw


def test_valid_tpci_control():
    """Test for valid tpci control."""
    raw = bytes((0x29, 0, 0, 0, 0, 0, 0, 0, 0, 0x80))
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.L_DATA_IND
    assert isinstance(frame.data, CEMILData)
    assert frame.data.flags == 0
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
def test_invalid_tpci_apci(raw, err_msg):
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
            get_data(0x29, 0, 0, 0, 0, 1, 0x03C0, []),
            r".*APDU not supported*",
        ),
    ],
)
def test_unsupported_tpci_apci(raw, err_msg):
    """Test for invalid APCIService."""
    with pytest.raises(UnsupportedCEMIMessage, match=err_msg):
        CEMIFrame.from_knx(raw)


def test_invalid_apdu_len():
    """Test for invalid apdu len."""
    with pytest.raises(CouldNotParseCEMI, match=r".*APDU LEN should be .*"):
        CEMIFrame.from_knx(get_data(0x29, 0, 0, 0, 0, 2, 0, []))


def test_invalid_payload():
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


def test_missing_data():
    """Test for having no data set."""
    frame = CEMIFrame(
        code=CEMIMessageCode.L_DATA_IND,
        data=None,
    )

    with pytest.raises(UnsupportedCEMIMessage):
        frame.calculated_length()

    with pytest.raises(UnsupportedCEMIMessage):
        frame.to_knx()


def test_from_knx_with_not_handleable_cemi():
    """Test for having unhandlebale cemi set."""
    with pytest.raises(
        UnsupportedCEMIMessage, match=r".*CEMIMessageCode not implemented:.*"
    ):
        CEMIFrame.from_knx(get_data(0x30, 0, 0, 0, 0, 2, 0, []))


def test_from_knx_with_not_implemented_cemi():
    """Test for having not implemented CEMI set."""
    with pytest.raises(
        UnsupportedCEMIMessage, match=r".*Could not handle CEMIMessageCode:.*"
    ):
        CEMIFrame.from_knx(
            get_data(CEMIMessageCode.L_BUSMON_IND.value, 0, 0, 0, 0, 2, 0, [])
        )


def test_invalid_invalid_len():
    """Test for invalid cemi len."""
    with pytest.raises(CouldNotParseCEMI, match=r".*CEMI too small.*"):
        CEMIFrame.from_knx(get_data(0x29, 0, 0, 0, 0, 2, 0, [])[:5])


def test_from_knx_group_address():
    """Test conversion for a cemi with a group address as destination."""
    frame = CEMIFrame.from_knx(get_data(0x29, 0, 0x80, 0, 0, 1, 0, []))
    assert isinstance(frame.data, CEMILData)
    assert frame.data.dst_addr == GroupAddress(0)


def test_from_knx_individual_address():
    """Test conversion for a cemi with a individual address as destination."""
    frame = CEMIFrame.from_knx(get_data(0x29, 0, 0x00, 0, 0, 1, 0, []))
    assert isinstance(frame.data, CEMILData)
    assert frame.data.dst_addr == IndividualAddress(0)


def test_telegram_group_address():
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


def test_telegram_broadcast():
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


def test_telegram_individual_address():
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


def test_telegram_unsupported_address():
    """Test telegram conversion flags with an unsupported address."""
    with pytest.raises(TypeError):
        CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(Telegram(destination_address=object())),
        )


def get_prop(code, obj_id, obj_inst, prop_id, num, six, payload):
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


def test_valid_read_req():
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


def test_valid_read_con():
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


def test_valid_error_read_con():
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


def test_valid_write_req():
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


def test_valid_empty_write_con():
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


def test_valid_error_write_con():
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
def test_invalid_length(raw, err_msg):
    """Test for invalid frame parsing."""
    with pytest.raises(CouldNotParseCEMI, match=err_msg):
        CEMIFrame.from_knx(raw)


def test_invalid_resource_object():
    """Test for invalid frame parsing."""
    with pytest.raises(
        UnsupportedCEMIMessage, match=r".*CEMIMProp Object Type not supported:.*"
    ):
        CEMIFrame.from_knx(get_prop(0xFC, 0x1234, 1, 52, 1, 1, []))
