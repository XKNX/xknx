"""Unit test for KNX/IP gateway scanner."""
import asyncio
from unittest.mock import Mock, create_autospec, patch

import pytest

from xknx import XKNX
from xknx.exceptions import XKNXException
from xknx.io import GatewayScanFilter, GatewayScanner
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.io.transport import UDPTransport
from xknx.knxip import (
    HPAI,
    DIBDeviceInformation,
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    KNXIPFrame,
    SearchRequest,
    SearchRequestExtended,
    SearchResponse,
)
from xknx.telegram import IndividualAddress


class TestGatewayScanner:
    """Test class for xknx/io/GatewayScanner objects."""

    gateway_desc_interface = GatewayDescriptor(
        name="KNX-Interface",
        ip_addr="10.1.1.11",
        port=3761,
        local_interface="en1",
        local_ip="10.1.1.100",
        supports_tunnelling=True,
        supports_routing=False,
    )
    gateway_desc_router = GatewayDescriptor(
        name="KNX-Router",
        ip_addr="10.1.1.12",
        port=3761,
        local_interface="en1",
        local_ip="10.1.1.100",
        supports_tunnelling=False,
        supports_routing=True,
    )
    gateway_desc_both = GatewayDescriptor(
        name="Gira KNX/IP-Router",
        ip_addr="192.168.42.10",
        port=3671,
        local_interface="en1",
        local_ip="192.168.42.50",
        supports_tunnelling=True,
        supports_tunnelling_tcp=True,
        supports_routing=True,
        individual_address=IndividualAddress("1.1.0"),
    )
    gateway_desc_both.tunnelling_requires_secure = False
    gateway_desc_neither = GatewayDescriptor(
        name="AC/S 1.1.1 Application Control",
        ip_addr="10.1.1.15",
        port=3671,
        local_interface="en1",
        local_ip="192.168.42.50",
        supports_tunnelling=False,
        supports_routing=False,
    )
    gateway_desc_secure_tunnel = GatewayDescriptor(
        name="KNX-Interface",
        ip_addr="10.1.1.11",
        port=3761,
        local_interface="en1",
        local_ip="10.1.1.111",
        supports_routing=False,
        supports_tunnelling=True,
        supports_tunnelling_tcp=True,
        supports_secure=True,
    )
    gateway_desc_secure_tunnel.tunnelling_requires_secure = True

    def test_gateway_scan_filter_match(self):
        """Test match function of gateway filter."""
        filter_default = GatewayScanFilter()
        filter_tunnel = GatewayScanFilter(tunnelling=True)
        filter_tcp_tunnel = GatewayScanFilter(tunnelling_tcp=True, secure=None)
        filter_secure_tunnel = GatewayScanFilter(tunnelling_tcp=True, secure=True)
        filter_router = GatewayScanFilter(routing=True)
        filter_name = GatewayScanFilter(name="KNX-Router")
        filter_no_tunnel = GatewayScanFilter(tunnelling=False)
        filter_no_router = GatewayScanFilter(routing=False)
        filter_tunnel_and_router = GatewayScanFilter(tunnelling=True, routing=True)

        assert filter_default.match(self.gateway_desc_interface)
        assert filter_default.match(self.gateway_desc_router)
        assert filter_default.match(self.gateway_desc_both)
        assert not filter_default.match(self.gateway_desc_neither)
        assert not filter_default.match(self.gateway_desc_secure_tunnel)

        assert filter_tunnel.match(self.gateway_desc_interface)
        assert not filter_tunnel.match(self.gateway_desc_router)
        assert filter_tunnel.match(self.gateway_desc_both)
        assert not filter_tunnel.match(self.gateway_desc_neither)
        assert not filter_tunnel.match(self.gateway_desc_secure_tunnel)

        assert not filter_tcp_tunnel.match(self.gateway_desc_interface)
        assert not filter_tcp_tunnel.match(self.gateway_desc_router)
        assert filter_tcp_tunnel.match(self.gateway_desc_both)
        assert not filter_tcp_tunnel.match(self.gateway_desc_neither)
        assert filter_tcp_tunnel.match(self.gateway_desc_secure_tunnel)

        assert not filter_secure_tunnel.match(self.gateway_desc_interface)
        assert not filter_secure_tunnel.match(self.gateway_desc_router)
        assert not filter_secure_tunnel.match(self.gateway_desc_both)
        assert not filter_secure_tunnel.match(self.gateway_desc_neither)
        assert filter_secure_tunnel.match(self.gateway_desc_secure_tunnel)

        assert not filter_router.match(self.gateway_desc_interface)
        assert filter_router.match(self.gateway_desc_router)
        assert filter_router.match(self.gateway_desc_both)
        assert not filter_router.match(self.gateway_desc_neither)
        assert not filter_router.match(self.gateway_desc_secure_tunnel)

        assert not filter_name.match(self.gateway_desc_interface)
        assert filter_name.match(self.gateway_desc_router)
        assert not filter_name.match(self.gateway_desc_both)
        assert not filter_name.match(self.gateway_desc_neither)
        assert not filter_name.match(self.gateway_desc_secure_tunnel)

        assert not filter_no_tunnel.match(self.gateway_desc_interface)
        assert filter_no_tunnel.match(self.gateway_desc_router)
        assert not filter_no_tunnel.match(self.gateway_desc_both)
        assert not filter_no_tunnel.match(self.gateway_desc_neither)
        assert not filter_no_tunnel.match(self.gateway_desc_secure_tunnel)

        assert filter_no_router.match(self.gateway_desc_interface)
        assert not filter_no_router.match(self.gateway_desc_router)
        assert not filter_no_router.match(self.gateway_desc_both)
        assert not filter_no_router.match(self.gateway_desc_neither)
        assert not filter_no_router.match(self.gateway_desc_secure_tunnel)

        assert not filter_tunnel_and_router.match(self.gateway_desc_interface)
        assert not filter_tunnel_and_router.match(self.gateway_desc_router)
        assert filter_tunnel_and_router.match(self.gateway_desc_both)
        assert not filter_tunnel_and_router.match(self.gateway_desc_neither)
        assert not filter_tunnel_and_router.match(self.gateway_desc_secure_tunnel)

    def test_search_response_reception(self):
        """Test function of gateway scanner."""
        xknx = XKNX()
        gateway_scanner = GatewayScanner(xknx)
        test_search_response = fake_router_search_response()
        udp_transport_mock = create_autospec(UDPTransport)
        udp_transport_mock.local_addr = ("192.168.42.50", 0)
        udp_transport_mock.getsockname.return_value = ("192.168.42.50", 0)

        assert not gateway_scanner.found_gateways
        gateway_scanner._response_rec_callback(
            test_search_response,
            HPAI("192.168.42.50", 0),
            udp_transport_mock,
            interface="en1",
        )
        assert len(gateway_scanner.found_gateways) == 1

        gateway_scanner._response_rec_callback(
            test_search_response,
            HPAI("192.168.42.230", 0),
            udp_transport_mock,
            interface="eth1",
        )
        assert len(gateway_scanner.found_gateways) == 1

        assert str(
            gateway_scanner.found_gateways[test_search_response.body.control_endpoint]
        ) == str(self.gateway_desc_both)

    @patch("xknx.io.gateway_scanner.UDPTransport.connect")
    @patch("xknx.io.gateway_scanner.UDPTransport.send")
    @patch(
        "xknx.io.gateway_scanner.UDPTransport.getsockname",
        return_value=("10.1.1.2", 56789),
    )
    async def test_scan_timeout(
        self,
        getsockname_mock,
        udp_transport_send_mock,
        udp_transport_connect_mock,
        time_travel,
    ):
        """Test gateway scanner timeout."""
        xknx = XKNX()
        gateway_scanner = GatewayScanner(xknx)
        timed_out_scan_task = asyncio.create_task(gateway_scanner.scan())
        await time_travel(gateway_scanner.timeout_in_seconds)
        # Unsuccessfull scan() returns empty list
        assert await timed_out_scan_task == []

    @patch("xknx.io.gateway_scanner.UDPTransport.connect")
    @patch("xknx.io.gateway_scanner.UDPTransport.send")
    async def test_async_scan_timeout(
        self,
        udp_transport_send_mock,
        udp_transport_connect_mock,
        time_travel,
    ):
        """Test gateway scanner timeout for async generator."""

        async def test():
            xknx = XKNX()
            async for gateway in GatewayScanner(xknx).async_scan():
                break
            else:
                return True
            return False

        # timeout
        with patch(
            "xknx.io.util.get_default_local_ip",
            return_value="10.1.1.2",
        ), patch(
            "xknx.io.gateway_scanner.UDPTransport.getsockname",
            return_value=("10.1.1.2", 56789),
        ):
            timed_out_scan_task = asyncio.create_task(test())
            await time_travel(3)
            assert await timed_out_scan_task
        # no matching interface found
        with patch(
            "xknx.io.util.get_default_local_ip",
            return_value=None,
        ):
            timed_out_scan_task = asyncio.create_task(test())
            await time_travel(3)
            with pytest.raises(XKNXException):
                await timed_out_scan_task

    @patch("xknx.io.gateway_scanner.UDPTransport.connect")
    @patch("xknx.io.gateway_scanner.UDPTransport.send")
    async def test_async_scan_exit(
        self,
        udp_transport_send_mock,
        udp_transport_connect_mock,
        time_travel,
    ):
        """Test gateway scanner timeout for async generator."""
        xknx = XKNX()
        test_search_response = fake_router_search_response()
        udp_transport_mock = Mock()
        udp_transport_mock.local_addr = ("10.1.1.2", 56789)

        gateway_scanner = GatewayScanner(xknx, local_ip="10.1.1.2")

        async def test():
            async for gateway in gateway_scanner.async_scan():
                return True
            return False

        with patch(
            "xknx.io.gateway_scanner.UDPTransport.getsockname",
            return_value=("10.1.1.2", 56789),
        ), patch(
            "xknx.io.gateway_scanner.UDPTransport.register_callback"
        ) as register_callback_mock:
            # , patch.object(
            #     gateway_scanner,
            #     "_scan",
            #     wraps=gateway_scanner._scan,
            # ) as _scan_mock:
            scan_task = asyncio.create_task(test())
            await time_travel(0)
            _fished_response_rec_callback = register_callback_mock.call_args.args[0]
            _fished_response_rec_callback(
                test_search_response,
                HPAI("192.168.42.50", 0),
                udp_transport_mock,
            )
            assert await scan_task
            await time_travel(0)  # for task cleanup

    @patch("xknx.io.gateway_scanner.UDPTransport.connect")
    @patch("xknx.io.gateway_scanner.UDPTransport.send")
    async def test_send_search_requests(
        self,
        udp_transport_send_mock,
        udp_transport_connect_mock,
    ):
        """Test if both search requests are sent per interface."""
        xknx = XKNX()
        gateway_scanner = GatewayScanner(xknx, timeout_in_seconds=0)
        with patch(
            "xknx.io.util.get_default_local_ip",
            return_value="10.1.1.2",
        ), patch(
            "xknx.io.util.get_local_interface_name",
            return_value="en_0123",
        ), patch(
            "xknx.io.gateway_scanner.UDPTransport.getsockname",
            return_value=("10.1.1.2", 56789),
        ):
            await gateway_scanner.scan()

        assert udp_transport_connect_mock.call_count == 1
        assert udp_transport_send_mock.call_count == 2
        frame_1 = udp_transport_send_mock.call_args_list[0].args[0]
        frame_2 = udp_transport_send_mock.call_args_list[1].args[0]
        assert isinstance(frame_1.body, SearchRequestExtended)
        assert isinstance(frame_2.body, SearchRequest)
        assert frame_1.body.discovery_endpoint == HPAI(ip_addr="10.1.1.2", port=56789)


def fake_router_search_response() -> KNXIPFrame:
    """Return the KNXIPFrame of a KNX/IP Router with a SearchResponse body."""
    frame_body = SearchResponse()
    frame_body.control_endpoint = HPAI(ip_addr="192.168.42.10", port=3671)

    device_information = DIBDeviceInformation()
    device_information.name = "Gira KNX/IP-Router"
    device_information.serial_number = "11:22:33:44:55:66"
    device_information.individual_address = IndividualAddress("1.1.0")
    device_information.mac_address = "01:02:03:04:05:06"

    svc_families = DIBSuppSVCFamilies()
    svc_families.families.append(
        DIBSuppSVCFamilies.Family(name=DIBServiceFamily.CORE, version=1)
    )
    svc_families.families.append(
        DIBSuppSVCFamilies.Family(name=DIBServiceFamily.DEVICE_MANAGEMENT, version=2)
    )
    svc_families.families.append(
        DIBSuppSVCFamilies.Family(name=DIBServiceFamily.TUNNELING, version=1)
    )
    svc_families.families.append(
        DIBSuppSVCFamilies.Family(name=DIBServiceFamily.ROUTING, version=1)
    )
    svc_families.families.append(
        DIBSuppSVCFamilies.Family(
            name=DIBServiceFamily.REMOTE_CONFIGURATION_DIAGNOSIS, version=1
        )
    )

    frame_body.dibs.append(device_information)
    frame_body.dibs.append(svc_families)

    return KNXIPFrame.init_from_body(frame_body)
