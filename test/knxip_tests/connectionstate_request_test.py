"""Unit test for KNX/IP ConnectionStateRequests."""

import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import HPAI, ConnectionStateRequest, KNXIPFrame


class TestKNXIPConnectionStateRequest:
    """Test class for KNX/IP ConnectionStateRequests."""

    def test_connection_state_request(self) -> None:
        """Test parsing and streaming connection state request KNX/IP packet."""
        raw = bytes.fromhex("06 10 02 07 00 10 15 00 08 01 C0 A8 C8 0C C3 B4")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, ConnectionStateRequest)

        assert knxipframe.body.communication_channel_id == 21
        assert knxipframe.body.control_endpoint == HPAI(
            ip_addr="192.168.200.12", port=50100
        )

        connectionstate_request = ConnectionStateRequest(
            communication_channel_id=21,
            control_endpoint=HPAI(ip_addr="192.168.200.12", port=50100),
        )
        knxipframe2 = KNXIPFrame.init_from_body(connectionstate_request)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_info(self) -> None:
        """Test parsing and streaming wrong ConnectionStateRequest."""
        raw = bytes((0x06, 0x10, 0x02, 0x07, 0x00, 0x010))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
