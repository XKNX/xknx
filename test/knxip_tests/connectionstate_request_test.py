"""Unit test for KNX/IP ConnectionStateRequests."""
import pytest
from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import HPAI, ConnectionStateRequest, KNXIPFrame


class TestKNXIPConnectionStateRequest:
    """Test class for KNX/IP ConnectionStateRequests."""

    def test_connection_state_request(self):
        """Test parsing and streaming connection state request KNX/IP packet."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x07,
            0x00,
            0x10,
            0x15,
            0x00,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0xC8,
            0x0C,
            0xC3,
            0xB4,
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        assert isinstance(knxipframe.body, ConnectionStateRequest)

        assert knxipframe.body.communication_channel_id == 21
        assert knxipframe.body.control_endpoint == HPAI(
            ip_addr="192.168.200.12", port=50100
        )

        connectionstate_request = ConnectionStateRequest(
            xknx,
            communication_channel_id=21,
            control_endpoint=HPAI(ip_addr="192.168.200.12", port=50100),
        )
        knxipframe2 = KNXIPFrame.init_from_body(connectionstate_request)

        assert knxipframe2.to_knx() == list(raw)

    def test_from_knx_wrong_info(self):
        """Test parsing and streaming wrong ConnectionStateRequest."""
        raw = (0x06, 0x10, 0x02, 0x07, 0x00, 0x010)
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
