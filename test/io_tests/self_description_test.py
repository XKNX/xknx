"""Unit test for KNX/IP Tunnelling Request/Response."""

import asyncio
from unittest.mock import Mock, patch

from xknx.io.self_description import DescriptionQuery, request_description
from xknx.io.transport.udp_transport import UDPTransport
from xknx.knxip import HPAI, DescriptionRequest, KNXIPFrame, SearchRequestExtended
from xknx.telegram import IndividualAddress

from ..conftest import EventLoopClockAdvancer


class TestSelfDescription:
    """Test class for KNX/IP self description."""

    # Core v1 device MDT KNX IP Router SCN-IP100.02
    description_response_v1_raw = bytes.fromhex(
        "06 10 02 04 00 46 36 01 02 00 20 00 00 00 00"
        "83 47 7f 01 24 e0 00 17 0c cc 1b e0 80 04 c4"
        "4d 44 54 20 4b 4e 58 20 49 50 20 52 6f 75 74"
        "65 72 00 00 00 00 00 00 00 00 00 00 00 00 00"
        "0a 02 02 01 03 01 04 01 05 01"
    )
    # Core v2 responses from a KNX IP Router 752 secure
    description_response_raw = bytes.fromhex(
        "06 10 02 04 00 4e 36 01 02 00 50 00 00 00 00"
        "c5 01 04 d5 9d e0 00 17 0d 00 24 6d 02 94 c4"
        "4b 4e 58 20 49 50 20 52 6f 75 74 65 72 20 37"
        "35 32 20 73 65 63 75 72 65 00 00 00 00 00 00"
        "0a 02 02 02 03 02 04 02 05 02 08 08 00 00 00"
        "37 09 1a"
    )
    search_response_extended_raw = bytes.fromhex(
        "06 10 02 0c 00 84 08 01 0a 01 01 5f 0e 57 36"
        "01 02 00 50 00 00 00 00 c5 01 04 d5 9d e0 00"
        "17 0d 00 24 6d 02 94 c4 4b 4e 58 20 49 50 20"
        "52 6f 75 74 65 72 20 37 35 32 20 73 65 63 75"
        "72 65 00 00 00 00 00 00 0c 02 02 02 03 02 04"
        "02 05 02 09 01 08 06 03 01 04 01 05 01 24 07"
        "00 37 50 01 ff fd 50 02 ff fd 50 03 ff fd 50"
        "04 ff fd 50 05 ff fd 50 06 ff fd 50 07 ff fd"
        "50 08 ff fd 08 08 00 00 00 37 09 1a"
    )

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    @patch("xknx.io.transport.udp_transport.UDPTransport.getsockname")
    async def test_description_query(
        self,
        mock_transport_getsockname: Mock,
        mock_transport_send: Mock,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test DescriptionQuery class."""
        local_addr = ("127.0.0.1", 12345)
        remote_addr = ("127.0.0.2", 54321)
        transport_mocked = UDPTransport(local_addr=local_addr, remote_addr=remote_addr)
        mock_transport_getsockname.return_value = local_addr

        description_request = KNXIPFrame.init_from_body(
            DescriptionRequest(control_endpoint=HPAI(*local_addr))
        )

        description_query = DescriptionQuery(
            transport=transport_mocked, local_hpai=HPAI(*local_addr)
        )
        task = asyncio.create_task(description_query.start())
        await time_travel(0)
        mock_transport_send.assert_called_once_with(description_request)
        transport_mocked.data_received_callback(
            raw=self.description_response_raw, source=remote_addr
        )
        await task
        assert description_query.gateway_descriptor is not None
        assert description_query.gateway_descriptor.name == "KNX IP Router 752 secure"

    async def test_request_description_v1(
        self,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test request_description function with Core v1 device."""
        local_addr = ("127.0.0.1", 12345)
        remote_addr = ("127.0.0.2", 54321)

        with (
            patch(
                "xknx.io.self_description.UDPTransport.connect"
            ) as transport_connect_mock,
            patch(
                "xknx.io.self_description.UDPTransport.getsockname",
                return_value=local_addr,
            ),
            patch("xknx.io.self_description.UDPTransport.send") as transport_send_mock,
            patch("xknx.io.self_description.UDPTransport.stop") as transport_stop_mock,
            patch(
                "xknx.io.self_description.DescriptionQuery", wraps=DescriptionQuery
            ) as description_query_mock,
        ):
            task = asyncio.create_task(request_description(remote_addr[0]))
            await time_travel(0)
            transport_connect_mock.assert_called_once_with()
            assert transport_send_mock.call_count == 1
            assert isinstance(
                transport_send_mock.call_args[0][0].body, DescriptionRequest
            )
            _transport = description_query_mock.call_args.kwargs["transport"]
            _transport.data_received_callback(
                self.description_response_v1_raw, remote_addr
            )
            gateway = await task
            transport_stop_mock.assert_called_once()
            assert transport_send_mock.call_count == 1

            assert gateway.core_version == 1
            assert gateway.name == "MDT KNX IP Router"
            assert gateway.tunnelling_requires_secure is None
            assert gateway.individual_address == IndividualAddress("2.0.0")

    async def test_request_description_extended(
        self,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test request_description function with Core v2 device."""
        local_addr = ("127.0.0.1", 12345)
        remote_addr = ("127.0.0.2", 54321)

        with (
            patch(
                "xknx.io.self_description.UDPTransport.connect"
            ) as transport_connect_mock,
            patch(
                "xknx.io.self_description.UDPTransport.getsockname",
                return_value=local_addr,
            ),
            patch("xknx.io.self_description.UDPTransport.send") as transport_send_mock,
            patch("xknx.io.self_description.UDPTransport.stop") as transport_stop_mock,
            patch(
                "xknx.io.self_description.DescriptionQuery", wraps=DescriptionQuery
            ) as description_query_mock,
        ):
            task = asyncio.create_task(request_description(remote_addr[0]))
            await time_travel(0)
            transport_connect_mock.assert_called_once_with()
            assert transport_send_mock.call_count == 1
            assert isinstance(
                transport_send_mock.call_args[0][0].body, DescriptionRequest
            )

            _transport = description_query_mock.call_args.kwargs["transport"]
            _transport.data_received_callback(
                self.description_response_raw, remote_addr
            )
            await time_travel(0)
            assert transport_send_mock.call_count == 2
            assert isinstance(
                transport_send_mock.call_args[0][0].body, SearchRequestExtended
            )

            _transport = description_query_mock.call_args.kwargs["transport"]
            _transport.data_received_callback(
                self.search_response_extended_raw, remote_addr
            )

            gateway = await task
            transport_stop_mock.assert_called_once()
            assert transport_send_mock.call_count == 2

            assert gateway.core_version == 2
            assert gateway.name == "KNX IP Router 752 secure"
            assert gateway.tunnelling_requires_secure is True
            assert gateway.individual_address == IndividualAddress("5.0.0")
