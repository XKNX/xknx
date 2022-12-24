"""Unit test for KNX/IP ConnectResponses."""
import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import HPAI, ConnectRequestType, ConnectResponse, ErrorCode, KNXIPFrame


class TestKNXIPConnectResponse:
    """Test class for KNX/IP ConnectResponses."""

    def test_connect_response(self):
        """Test parsing and streaming connection response KNX/IP packet."""
        raw = bytes.fromhex(
            "06 10 02 06 00 14 01 00 08 01 C0 A8 2A 0A 0E 57 04 04 11 FF"
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)
        assert isinstance(knxipframe.body, ConnectResponse)
        assert knxipframe.body.communication_channel == 1
        assert knxipframe.body.status_code == ErrorCode.E_NO_ERROR
        assert knxipframe.body.data_endpoint == HPAI(ip_addr="192.168.42.10", port=3671)
        assert knxipframe.body.request_type == ConnectRequestType.TUNNEL_CONNECTION
        assert knxipframe.body.identifier == 4607

        connect_response = ConnectResponse(
            communication_channel=1,
            status_code=ErrorCode.E_NO_ERROR,
            request_type=ConnectRequestType.TUNNEL_CONNECTION,
            data_endpoint=HPAI(ip_addr="192.168.42.10", port=3671),
            identifier=4607,
        )
        knxipframe2 = KNXIPFrame.init_from_body(connect_response)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_crd(self):
        """Test parsing and streaming wrong ConnectRequest (wrong CRD length byte)."""
        raw = bytes.fromhex(
            "06 10 02 06 00 14 01 00 08 01 C0 A8 2A 0A 0E 57 03 04 11 FF"
        )
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_from_knx_wrong_crd2(self):
        """Test parsing and streaming wrong ConnectRequest (wrong CRD length)."""
        raw = bytes.fromhex("06 10 02 06 00 14 01 00 08 01 C0 A8 2A 0A 0E 57 04 04")
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_connect_response_connection_error_gira(self):
        """
        Test parsing and streaming connection response KNX/IP packet with error e_no_more_connections.

        HPAI and CRD normal. This was received from Gira devices (2020).
        """
        raw = bytes.fromhex(
            "06 10 02 06 00 14 C0 24 08 01 0A 01 00 29 0E 57 04 04 00 00"
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)
        assert isinstance(knxipframe.body, ConnectResponse)
        assert knxipframe.body.status_code == ErrorCode.E_NO_MORE_CONNECTIONS
        assert knxipframe.body.communication_channel == 192

        connect_response = ConnectResponse(
            communication_channel=192,
            status_code=ErrorCode.E_NO_MORE_CONNECTIONS,
            request_type=ConnectRequestType.TUNNEL_CONNECTION,
            data_endpoint=HPAI(ip_addr="10.1.0.41", port=3671),
            identifier=0,
        )
        knxipframe2 = KNXIPFrame.init_from_body(connect_response)

        assert knxipframe2.to_knx() == raw

    def test_connect_response_connection_error_lox(self):
        """
        Test parsing and streaming connection response KNX/IP packet with error e_no_more_connections.

        HPAI given, CRD all zero. This was received from Loxone device (2020).
        """
        raw = bytes.fromhex(
            "06 10 02 06 00 14 00 24 08 01 C0 A8 01 01 0E 57 00 00 00 00"
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)
        assert isinstance(knxipframe.body, ConnectResponse)
        assert knxipframe.body.status_code == ErrorCode.E_NO_MORE_CONNECTIONS
        assert knxipframe.body.communication_channel == 0

        # no further tests: the current API can't (and shouldn't) create such odd packets

    def test_connect_response_connection_error_mdt(self):
        """
        Test parsing and streaming connection response KNX/IP packet with error e_no_more_connections.

        HPAI and CRD all zero. This was received from MDT device (2020).
        """
        raw = bytes.fromhex("06 10 02 06 00 08 00 24 00 00 00 00 00 00 00 00 00 00")
        knxipframe, _ = KNXIPFrame.from_knx(raw)
        assert isinstance(knxipframe.body, ConnectResponse)
        assert knxipframe.body.status_code == ErrorCode.E_NO_MORE_CONNECTIONS
        assert knxipframe.body.communication_channel == 0

        # no further tests: the current API can't (and shouldn't) create such odd packets
