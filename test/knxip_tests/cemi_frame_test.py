"""Tests for the CEMIFrame object"""

from unittest.mock import MagicMock

from pytest import fixture, raises

from xknx.dpt import DPTBinary
from xknx.exceptions import CouldNotParseKNXIP, UnsupportedCEMIMessage
from xknx.knxip.cemi_frame import CEMIFrame
from xknx.knxip.knxip_enum import APCICommand, CEMIMessageCode
from xknx.telegram import PhysicalAddress


def get_data(code, adil, flags, src, dst, mpdu_len, tpci_apci, payload):
    return [
        code,
        adil,  # adil
        (flags >> 8) & 255,  # flags
        flags & 255,  # flags
        (src >> 8) & 255,  # src
        src & 255,  # src
        (dst >> 8) & 255,  # dst
        dst & 255,  # dst
        mpdu_len,  # mpdu_len
        (tpci_apci >> 8) & 255,  # tpci_apci
        tpci_apci & 255,  # tpci_apci
        *payload,  # payload
    ]


@fixture(name="frame")
def fixture_frame():
    """Fixture to get a simple mocked frame"""
    xknx = MagicMock()
    return CEMIFrame(xknx)


def test_valid_command(frame):
    """Test for valid frame parsing"""
    packet_len = frame.from_knx(get_data(0x29, 0, 0, 0, 0, 1, 0, []))
    assert frame.code == CEMIMessageCode.L_DATA_IND
    assert frame.cmd == APCICommand.GROUP_READ
    assert frame.flags == 0
    assert frame.mpdu_len == 1
    assert frame.payload == DPTBinary(0)
    assert frame.src_addr == PhysicalAddress(0)
    assert frame.dst_addr == PhysicalAddress(0)
    assert packet_len == 11


def test_invalid_tpci_apci(frame):
    """Test for invalid APCICommand"""
    with raises(UnsupportedCEMIMessage, match=r".*APCI not supported: .*"):
        frame.from_knx_data_link_layer(get_data(0x29, 0, 0, 0, 0, 1, 0xFFC0, []))


def test_invalid_apdu_len(frame):
    """Test for invalid apdu len"""
    with raises(CouldNotParseKNXIP, match=r".*APDU LEN should be .*"):
        frame.from_knx(get_data(0x29, 0, 0, 0, 0, 2, 0, []))


def test_invalid_invalid_len(frame):
    """Test for invalid cemi len"""
    with raises(UnsupportedCEMIMessage, match=r".*CEMI too small.*"):
        frame.from_knx_data_link_layer(get_data(0x29, 0, 0, 0, 0, 2, 0, [])[:5])
