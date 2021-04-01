"""Unit test for KNX/IP TunnellingRequest objects."""
import pytest
from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import CEMIFrame, CEMIMessageCode, KNXIPFrame, TunnellingRequest
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class Test_KNXIP_TunnelingReq:
    """Test class for KNX/IP TunnellingRequest objects."""

    def test_connect_request(self):
        """Test parsing and streaming connection tunneling request KNX/IP packet."""
        raw = (
            0x06,
            0x10,
            0x04,
            0x20,
            0x00,
            0x15,
            0x04,
            0x01,
            0x17,
            0x00,
            0x11,
            0x00,
            0xBC,
            0xE0,
            0x00,
            0x00,
            0x48,
            0x08,
            0x01,
            0x00,
            0x81,
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        assert isinstance(knxipframe.body, TunnellingRequest)
        assert knxipframe.body.communication_channel_id == 1
        assert knxipframe.body.sequence_counter == 23
        assert isinstance(knxipframe.body.cemi, CEMIFrame)

        assert knxipframe.body.cemi.telegram == Telegram(
            destination_address=GroupAddress("9/0/8"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        cemi = CEMIFrame(xknx, code=CEMIMessageCode.L_DATA_REQ)
        cemi.telegram = Telegram(
            destination_address=GroupAddress("9/0/8"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        tunnelling_request = TunnellingRequest(
            xknx, communication_channel_id=1, sequence_counter=23, cemi=cemi
        )
        knxipframe2 = KNXIPFrame.init_from_body(tunnelling_request)

        assert knxipframe2.to_knx() == list(raw)

    def test_from_knx_wrong_header(self):
        """Test parsing and streaming wrong TunnellingRequest (wrong header length byte)."""
        raw = (0x06, 0x10, 0x04, 0x20, 0x00, 0x15, 0x03)
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)

    def test_from_knx_wrong_header2(self):
        """Test parsing and streaming wrong TunnellingRequest (wrong header length)."""
        raw = (0x06, 0x10, 0x04, 0x20, 0x00, 0x15, 0x04)
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
