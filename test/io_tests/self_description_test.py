"""Unit test for KNX/IP Tunnelling Request/Response."""
import asyncio
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.io.self_description import DescriptionQuery, request_description
from xknx.io.transport.udp_transport import UDPTransport
from xknx.knxip import HPAI, DescriptionRequest, KNXIPFrame


class TestSelfDescription:
    """Test class for KNX/IP self description."""

    async def test_description_query(self, time_travel):
        """Test DescriptionQuery class."""
        xknx = XKNX()
        local_addr = ("127.0.0.1", 12345)
        remote_addr = ("127.0.0.2", 54321)
        transport_mocked = UDPTransport(
            xknx, local_addr=local_addr, remote_addr=remote_addr
        )
        transport_mocked.getsockname = Mock(return_value=local_addr)
        transport_mocked.send = Mock()

        description_request = KNXIPFrame.init_from_body(
            DescriptionRequest(control_endpoint=HPAI(*local_addr))
        )
        description_response_raw = bytes.fromhex(
            "06 10 02 04 00 48 36 01 02 00 10 00 00 00 00"
            "08 2d 40 83 4d e0 00 17 0c 00 0a b3 27 4a 32"
            "4b 4e 58 2f 49 50 2d 52 6f 75 74 65 72 00 00"
            "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
            "0c 02 02 02 03 02 04 02 05 02 07 01",
        )
        description_query = DescriptionQuery(
            xknx, transport=transport_mocked, local_hpai=HPAI(*local_addr)
        )
        task = asyncio.create_task(description_query.start())
        await time_travel(0)
        transport_mocked.send.assert_called_once_with(description_request)

        transport_mocked.data_received_callback(
            raw=description_response_raw, source=remote_addr
        )
        await task
        assert description_query.gateway_descriptor is not None
        assert description_query.gateway_descriptor.name == "KNX/IP-Router"

    async def test_request_description(self, time_travel):
        """Test request_description function."""
        xknx = XKNX()
        local_addr = ("127.0.0.1", 12345)
        remote_addr = ("127.0.0.2", 54321)

        with patch(
            "xknx.io.transport.UDPTransport.connect"
        ) as transport_connect_mock, patch(
            "xknx.io.transport.UDPTransport.getsockname", return_value=local_addr
        ) as transport_getsockname_mock, patch(
            "xknx.io.transport.UDPTransport.stop"
        ) as transport_stop_mock, patch(
            "xknx.io.self_description.DescriptionQuery.start"
        ) as description_query_start_mock:
            await request_description(xknx, remote_addr[0])
            transport_connect_mock.assert_called_once_with()
            transport_getsockname_mock.assert_called_once_with()
            transport_stop_mock.assert_called_once_with()
            description_query_start_mock.assert_called_once_with()
