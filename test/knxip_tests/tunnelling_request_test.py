"""Unit test for KNX/IP TunnellingRequest objects."""
import pytest

from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.dpt import DPTBinary
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import KNXIPFrame, TunnellingRequest
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestKNXIPTunnellingRequest:
    """Test class for KNX/IP TunnellingRequest objects."""

    def test_connect_request(self):
        """Test parsing and streaming connection tunneling request KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 04 20 00 15 04 01 17 00 11 00 BC E0 00 00 48 08 01 00 81"
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, TunnellingRequest)
        assert knxipframe.body.communication_channel_id == 1
        assert knxipframe.body.sequence_counter == 23
        assert isinstance(knxipframe.body.raw_cemi, bytes)

        incoming_cemi = CEMIFrame.from_knx(knxipframe.body.raw_cemi)
        assert incoming_cemi.data.telegram() == Telegram(
            destination_address=GroupAddress("9/0/8"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        outgoing_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_REQ,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=GroupAddress("9/0/8"),
                    payload=GroupValueWrite(DPTBinary(1)),
                ),
            ),
        )
        tunnelling_request = TunnellingRequest(
            communication_channel_id=1,
            sequence_counter=23,
            raw_cemi=outgoing_cemi.to_knx(),
        )
        knxipframe2 = KNXIPFrame.init_from_body(tunnelling_request)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_header(self):
        """Test parsing and streaming wrong TunnellingRequest (wrong header length byte)."""
        raw = bytes((0x06, 0x10, 0x04, 0x20, 0x00, 0x15, 0x03))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_from_knx_wrong_header2(self):
        """Test parsing and streaming wrong TunnellingRequest (wrong header length)."""
        raw = bytes((0x06, 0x10, 0x04, 0x20, 0x00, 0x15, 0x04))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
