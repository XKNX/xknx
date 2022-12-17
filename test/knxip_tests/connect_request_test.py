"""Unit test for KNX/IP ConnectRequests."""
import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import HPAI, ConnectRequest, ConnectRequestType, KNXIPFrame


class TestKNXIPConnectRequest:
    """Test class for KNX/IP ConnectRequests."""

    def test_connect_request(self):
        """Test parsing and streaming connection request KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 02 05 00 1A 08 01 C0 A8 2A 01 84 95 08 01"
            "C0 A8 2A 01 CC A9 04 04 02 00"
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, ConnectRequest)
        assert knxipframe.body.request_type == ConnectRequestType.TUNNEL_CONNECTION
        assert knxipframe.body.control_endpoint == HPAI(
            ip_addr="192.168.42.1", port=33941
        )
        assert knxipframe.body.data_endpoint == HPAI(ip_addr="192.168.42.1", port=52393)

        connect_request = ConnectRequest(
            request_type=ConnectRequestType.TUNNEL_CONNECTION,
            control_endpoint=HPAI(ip_addr="192.168.42.1", port=33941),
            data_endpoint=HPAI(ip_addr="192.168.42.1", port=52393),
        )
        knxipframe2 = KNXIPFrame.init_from_body(connect_request)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_length_of_cri(self):
        """Test parsing and streaming wrong ConnectRequest."""
        raw = bytes.fromhex(
            "06 10 02 05 00 1A 08 01 C0 A8 2A 01 84 95 08 01"
            "C0 A8 2A 01 CC A9 02 04 02 00"
        )
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_from_knx_wrong_cri(self):
        """Test parsing and streaming wrong ConnectRequest."""
        raw = bytes.fromhex(
            "06 10 02 05 00 1A 08 01 C0 A8 2A 01 84 95 08 01"
            "C0 A8 2A 01 CC A9 04 04 02"
        )
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
