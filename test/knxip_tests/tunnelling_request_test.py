"""Unit test for KNX/IP TunnellingRequest objects."""
import pytest
from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import CEMIFrame, CEMIMessageCode, KNXIPFrame, TunnellingRequest
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestKNXIPTunnelingRequest:
    """Test class for KNX/IP TunnellingRequest objects."""

    def test_connect_request(self):
        """Test parsing and streaming connection tunneling request KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 04 20 00 15 04 01 17 00 11 00 BC E0 00 00 48 08 01 00 81"
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        assert isinstance(knxipframe.body, TunnellingRequest)
        assert knxipframe.body.communication_channel_id == 1
        assert knxipframe.body.sequence_counter == 23
        assert isinstance(knxipframe.body.pdu, CEMIFrame)

        assert knxipframe.body.pdu.telegram == Telegram(
            destination_address=GroupAddress("9/0/8"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        cemi = CEMIFrame(xknx, code=CEMIMessageCode.L_DATA_REQ)
        cemi.telegram = Telegram(
            destination_address=GroupAddress("9/0/8"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        tunnelling_request = TunnellingRequest(
            xknx, communication_channel_id=1, sequence_counter=23, pdu=cemi
        )
        knxipframe2 = KNXIPFrame.init_from_body(tunnelling_request)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_header(self):
        """Test parsing and streaming wrong TunnellingRequest (wrong header length byte)."""
        raw = bytes((0x06, 0x10, 0x04, 0x20, 0x00, 0x15, 0x03))
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)

    def test_from_knx_wrong_header2(self):
        """Test parsing and streaming wrong TunnellingRequest (wrong header length)."""
        raw = bytes((0x06, 0x10, 0x04, 0x20, 0x00, 0x15, 0x04))
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
