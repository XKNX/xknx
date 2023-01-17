"""Tests for the CEMIFrame object."""
import pytest

from xknx.cemi import CEMIFlags, CEMIFrame, CEMIMessageCode
from xknx.exceptions import ConversionError, UnsupportedCEMIMessage
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
    assert frame.flags == 0x0080
    assert frame.src_addr == IndividualAddress(1)
    assert frame.dst_addr == GroupAddress(1)
    assert frame.payload == GroupValueRead()
    assert frame.tpci == TDataGroup()
    assert frame.calculated_length() == 11
    assert frame.to_knx() == raw


def test_valid_tpci_control():
    """Test for valid tpci control."""
    raw = bytes((0x29, 0, 0, 0, 0, 0, 0, 0, 0, 0x80))
    frame = CEMIFrame.from_knx(raw)
    assert frame.code == CEMIMessageCode.L_DATA_IND
    assert frame.flags == 0
    assert frame.payload is None
    assert frame.src_addr == IndividualAddress(0)
    assert frame.dst_addr == IndividualAddress(0)
    assert frame.tpci == TConnect()
    assert frame.calculated_length() == 10
    assert frame.to_knx() == raw


@pytest.mark.parametrize(
    "raw,err_msg",
    [
        (
            get_data(0x29, 0, 0, 0, 0, 1, 0xFFC0, []),
            r".*Invalid length for control TPDU.*",
        ),
        (
            get_data(0x29, 0, 0, 0, 0, 1, 0x08C0, []),
            r".*TPCI not supported.*",
        ),
        (
            get_data(0x29, 0, 0, 0, 0, 1, 0x03C0, []),
            r".*APCI not supported*",
        ),
    ],
)
def test_invalid_tpci_apci(raw, err_msg):
    """Test for invalid APCIService."""
    with pytest.raises(UnsupportedCEMIMessage, match=err_msg):
        CEMIFrame.from_knx_data_link_layer(raw, code=CEMIMessageCode.L_DATA_IND)


def test_invalid_apdu_len():
    """Test for invalid apdu len."""
    with pytest.raises(UnsupportedCEMIMessage, match=r".*APDU LEN should be .*"):
        CEMIFrame.from_knx(get_data(0x29, 0, 0, 0, 0, 2, 0, []))


def test_invalid_payload():
    """Test for having wrong payload set."""
    frame = CEMIFrame(
        code=CEMIMessageCode.L_DATA_IND,
        flags=0,
        src_addr=IndividualAddress(0),
        dst_addr=IndividualAddress(0),
        tpci=TDataGroup(),
        payload=None,
    )

    with pytest.raises(TypeError):
        frame.calculated_length()

    with pytest.raises(ConversionError):
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
    with pytest.raises(UnsupportedCEMIMessage, match=r".*CEMI too small.*"):
        CEMIFrame.from_knx_data_link_layer(
            get_data(0x29, 0, 0, 0, 0, 2, 0, [])[:5],
            code=CEMIMessageCode.L_DATA_IND,
        )


def test_from_knx_group_address():
    """Test conversion for a cemi with a group address as destination."""
    frame = CEMIFrame.from_knx(get_data(0x29, 0, 0x80, 0, 0, 1, 0, []))
    assert frame.dst_addr == GroupAddress(0)


def test_from_knx_individual_address():
    """Test conversion for a cemi with a individual address as destination."""
    frame = CEMIFrame.from_knx(get_data(0x29, 0, 0x00, 0, 0, 1, 0, []))
    assert frame.dst_addr == IndividualAddress(0)


def test_telegram_group_address():
    """Test telegram conversion flags with a group address."""
    _telegram = Telegram(destination_address=GroupAddress(1))
    frame = CEMIFrame.init_from_telegram(_telegram)
    assert frame.flags & 0x0080 == CEMIFlags.DESTINATION_GROUP_ADDRESS
    assert frame.flags & 0x0C00 == CEMIFlags.PRIORITY_LOW
    # test CEMIFrame.telegram property
    assert frame.telegram == _telegram


def test_telegram_broadcast():
    """Test telegram conversion flags with a group address."""
    _telegram = Telegram(destination_address=GroupAddress(0))
    frame = CEMIFrame.init_from_telegram(_telegram)
    assert frame.flags & 0x0080 == CEMIFlags.DESTINATION_GROUP_ADDRESS
    assert frame.flags & 0x0C00 == CEMIFlags.PRIORITY_SYSTEM
    assert frame.tpci == TDataBroadcast()
    # test CEMIFrame.telegram property
    assert frame.telegram == _telegram


def test_telegram_individual_address():
    """Test telegram conversion flags with a individual address."""
    _telegram = Telegram(destination_address=IndividualAddress(0), tpci=TConnect())
    frame = CEMIFrame.init_from_telegram(_telegram)
    assert frame.flags & 0x0080 == CEMIFlags.DESTINATION_INDIVIDUAL_ADDRESS
    assert frame.flags & 0x0C00 == CEMIFlags.PRIORITY_SYSTEM
    assert frame.flags & 0x0200 == CEMIFlags.NO_ACK_REQUESTED
    # test CEMIFrame.telegram property
    assert frame.telegram == _telegram


def test_telegram_unsupported_address():
    """Test telegram conversion flags with an unsupported address."""
    with pytest.raises(TypeError):
        CEMIFrame.init_from_telegram(Telegram(destination_address=object()))
