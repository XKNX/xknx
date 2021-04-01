"""Unit test for KNX/IP ConnectRequests."""
import pytest
from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import HPAI, ConnectRequest, ConnectRequestType, KNXIPFrame


class Test_KNXIP_ConnectRequest:
    """Test class for KNX/IP ConnectRequests."""

    def test_connect_request(self):
        """Test parsing and streaming connection request KNX/IP packet."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x05,
            0x00,
            0x1A,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0x84,
            0x95,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0xCC,
            0xA9,
            0x04,
            0x04,
            0x02,
            0x00,
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        assert isinstance(knxipframe.body, ConnectRequest)
        assert knxipframe.body.request_type == ConnectRequestType.TUNNEL_CONNECTION
        assert knxipframe.body.control_endpoint == HPAI(
            ip_addr="192.168.42.1", port=33941
        )
        assert knxipframe.body.data_endpoint == HPAI(ip_addr="192.168.42.1", port=52393)

        connect_request = ConnectRequest(
            xknx,
            request_type=ConnectRequestType.TUNNEL_CONNECTION,
            control_endpoint=HPAI(ip_addr="192.168.42.1", port=33941),
            data_endpoint=HPAI(ip_addr="192.168.42.1", port=52393),
        )
        knxipframe2 = KNXIPFrame.init_from_body(connect_request)

        assert knxipframe2.to_knx() == list(raw)

    def test_from_knx_wrong_length_of_cri(self):
        """Test parsing and streaming wrong ConnectRequest."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x05,
            0x00,
            0x1A,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0x84,
            0x95,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0xCC,
            0xA9,
            0x02,
            0x04,
            0x02,
            0x00,
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)

    def test_from_knx_wrong_cri(self):
        """Test parsing and streaming wrong ConnectRequest."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x05,
            0x00,
            0x1A,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0x84,
            0x95,
            0x08,
            0x01,
            0xC0,
            0xA8,
            0x2A,
            0x01,
            0xCC,
            0xA9,
            0x04,
            0x04,
            0x02,
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
