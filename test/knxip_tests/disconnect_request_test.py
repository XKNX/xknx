"""Unit test for KNX/IP DisconnectRequest objects."""

import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import HPAI, DisconnectRequest, KNXIPFrame


class TestKNXIPDisconnectRequest:
    """Test class for KNX/IP DisconnectRequest objects."""

    def test_disconnect_request(self) -> None:
        """Test parsing and streaming DisconnectRequest KNX/IP packet."""
        raw = bytes.fromhex("06 10 02 09 00 10 15 00 08 01 C0 A8 C8 0C C3 B4")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, DisconnectRequest)

        assert knxipframe.body.communication_channel_id == 21
        assert knxipframe.body.control_endpoint == HPAI(
            ip_addr="192.168.200.12", port=50100
        )

        disconnect_request = DisconnectRequest(
            communication_channel_id=21,
            control_endpoint=HPAI(ip_addr="192.168.200.12", port=50100),
        )
        knxipframe2 = KNXIPFrame.init_from_body(disconnect_request)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_length(self) -> None:
        """Test parsing and streaming wrong DisconnectRequest."""
        raw = bytes((0x06, 0x10, 0x02, 0x09, 0x00, 0x10))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
