"""Unit test for KNX/IP ConnectRequests."""
import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import (
    HPAI,
    ConnectRequest,
    ConnectRequestInformation,
    ConnectRequestType,
    KNXIPFrame,
    TunnellingLayer,
)
from xknx.telegram import IndividualAddress


class TestKNXIPConnectRequest:
    """Test class for KNX/IP ConnectRequests."""

    def test_tunnel_connect_request(self):
        """Test parsing and streaming connection request KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 02 05 00 1A 08 01 C0 A8 2A 01 84 95 08 01"
            "C0 A8 2A 01 CC A9 04 04 02 00"
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, ConnectRequest)
        assert knxipframe.body.control_endpoint == HPAI(
            ip_addr="192.168.42.1", port=33941
        )
        assert knxipframe.body.data_endpoint == HPAI(ip_addr="192.168.42.1", port=52393)
        assert (
            knxipframe.body.cri.connection_type is ConnectRequestType.TUNNEL_CONNECTION
        )
        assert knxipframe.body.cri.knx_layer is TunnellingLayer.DATA_LINK_LAYER
        assert knxipframe.body.cri.individual_address is None

        cri = ConnectRequestInformation(
            connection_type=ConnectRequestType.TUNNEL_CONNECTION,
            knx_layer=TunnellingLayer.DATA_LINK_LAYER,
            individual_address=None,
        )
        connect_request = ConnectRequest(
            control_endpoint=HPAI(ip_addr="192.168.42.1", port=33941),
            data_endpoint=HPAI(ip_addr="192.168.42.1", port=52393),
            cri=cri,
        )
        knxipframe2 = KNXIPFrame.init_from_body(connect_request)

        assert knxipframe2.to_knx() == raw

    def test_mgmt_connect_request(self):
        """Test parsing and streaming connection request KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 02 05 00 18 08 01 C0 A8 2A 01 84 95 08 01 C0 A8 2A 01 CC A9 02 03"
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, ConnectRequest)
        assert knxipframe.body.control_endpoint == HPAI(
            ip_addr="192.168.42.1", port=33941
        )
        assert knxipframe.body.data_endpoint == HPAI(ip_addr="192.168.42.1", port=52393)
        assert (
            knxipframe.body.cri.connection_type
            is ConnectRequestType.DEVICE_MGMT_CONNECTION
        )
        assert knxipframe.body.cri.individual_address is None

        cri = ConnectRequestInformation(
            connection_type=ConnectRequestType.DEVICE_MGMT_CONNECTION,
            individual_address=None,
        )
        connect_request = ConnectRequest(
            control_endpoint=HPAI(ip_addr="192.168.42.1", port=33941),
            data_endpoint=HPAI(ip_addr="192.168.42.1", port=52393),
            cri=cri,
        )
        knxipframe2 = KNXIPFrame.init_from_body(connect_request)

        assert knxipframe2.to_knx() == raw

    def test_connect_request_extended_cri(self):
        """Test parsing and streaming connection request KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 02 05 00 1C 08 01 C0 A8 2A 01 84 95 08 01"
            "C0 A8 2A 01 CC A9 06 04 02 00 01 02"
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, ConnectRequest)
        assert knxipframe.body.control_endpoint == HPAI(
            ip_addr="192.168.42.1", port=33941
        )
        assert knxipframe.body.data_endpoint == HPAI(ip_addr="192.168.42.1", port=52393)
        assert (
            knxipframe.body.cri.connection_type is ConnectRequestType.TUNNEL_CONNECTION
        )
        assert knxipframe.body.cri.knx_layer is TunnellingLayer.DATA_LINK_LAYER
        assert knxipframe.body.cri.individual_address == IndividualAddress("0.1.2")

        cri = ConnectRequestInformation(
            connection_type=ConnectRequestType.TUNNEL_CONNECTION,
            knx_layer=TunnellingLayer.DATA_LINK_LAYER,
            individual_address=IndividualAddress("0.1.2"),
        )
        connect_request = ConnectRequest(
            control_endpoint=HPAI(ip_addr="192.168.42.1", port=33941),
            data_endpoint=HPAI(ip_addr="192.168.42.1", port=52393),
            cri=cri,
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

    def test_from_knx_wrong_length_of_cri2(self):
        """Test parsing and streaming wrong ConnectRequest."""
        raw = bytes.fromhex(
            "06 10 02 05 00 18 08 01 C0 A8 2A 01 84 95 08 01 C0 A8 2A 01 CC A9 03 03"
        )
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_from_knx_wrong_length_of_cri3(self):
        """Test parsing and streaming wrong ConnectRequest."""
        raw = bytes.fromhex(
            "06 10 02 05 00 18 08 01 C0 A8 2A 01 84 95 08 01 C0 A8 2A 01 CC A9 01 03"
        )
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_from_knx_wrong_length_of_cri4(self):
        """Test parsing and streaming wrong ConnectRequest."""
        raw = bytes.fromhex(
            "06 10 02 05 00 19 08 01 C0 A8 2A 01 84 95 08 01 C0 A8 2A 01 CC A9 03 03 01"
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
