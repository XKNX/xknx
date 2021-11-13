"""Unit test for KNX/IP gateway scanner."""
import asyncio
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from xknx import XKNX
from xknx.io import GatewayScanFilter, GatewayScanner, UDPClient
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.knxip import (
    HPAI,
    DIBDeviceInformation,
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    KNXIPFrame,
    SearchResponse,
)
from xknx.telegram import IndividualAddress


@pytest.mark.asyncio
class TestGatewayScanner:
    """Test class for xknx/io/GatewayScanner objects."""

    gateway_desc_interface = GatewayDescriptor(
        name="KNX-Interface",
        ip_addr="10.1.1.11",
        port=3761,
        local_interface="en1",
        local_ip="110.1.1.100",
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
        supports_routing=True,
        individual_address=IndividualAddress("1.1.0"),
    )
    gateway_desc_neither = GatewayDescriptor(
        name="AC/S 1.1.1 Application Control",
        ip_addr="10.1.1.15",
        port=3671,
        local_interface="en1",
        local_ip="192.168.42.50",
        supports_tunnelling=False,
        supports_routing=False,
    )

    fake_interfaces = ["lo0", "en0", "en1"]
    fake_ifaddresses = {
        "lo0": {
            2: [{"addr": "127.0.0.1", "netmask": "255.0.0.0", "peer": "127.0.0.1"}],
            30: [
                {
                    "addr": "::1",
                    "netmask": "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128",
                    "peer": "::1",
                    "flags": 0,
                },
                {
                    "addr": "fe80::1%lo0",
                    "netmask": "ffff:ffff:ffff:ffff::/64",
                    "flags": 0,
                },
            ],
        },
        "en0": {18: [{"addr": "FF:FF:00:00:00:00"}]},
        "en1": {
            18: [{"addr": "FF:FF:00:00:00:01"}],
            30: [
                {
                    "addr": "fe80::1234:1234:1234:1234%en1",
                    "netmask": "ffff:ffff:ffff:ffff::/64",
                    "flags": 1024,
                }
            ],
            2: [
                {
                    "addr": "10.1.1.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "10.1.1.255",
                }
            ],
        },
    }

    def test_gateway_scan_filter_match(self):
        """Test match function of gateway filter."""
        filter_default = GatewayScanFilter()
        filter_tunnel = GatewayScanFilter(tunnelling=True)
        filter_router = GatewayScanFilter(routing=True)
        filter_name = GatewayScanFilter(name="KNX-Router")
        filter_no_tunnel = GatewayScanFilter(tunnelling=False)
        filter_no_router = GatewayScanFilter(routing=False)
        filter_tunnel_and_router = GatewayScanFilter(tunnelling=True, routing=True)

        assert filter_default.match(self.gateway_desc_interface)
        assert filter_default.match(self.gateway_desc_router)
        assert filter_default.match(self.gateway_desc_both)
        assert not filter_default.match(self.gateway_desc_neither)

        assert filter_tunnel.match(self.gateway_desc_interface)
        assert not filter_tunnel.match(self.gateway_desc_router)
        assert filter_tunnel.match(self.gateway_desc_both)
        assert not filter_tunnel.match(self.gateway_desc_neither)

        assert not filter_router.match(self.gateway_desc_interface)
        assert filter_router.match(self.gateway_desc_router)
        assert filter_router.match(self.gateway_desc_both)
        assert not filter_router.match(self.gateway_desc_neither)

        assert not filter_name.match(self.gateway_desc_interface)
        assert filter_name.match(self.gateway_desc_router)
        assert not filter_name.match(self.gateway_desc_both)
        assert not filter_name.match(self.gateway_desc_neither)

        assert not filter_no_tunnel.match(self.gateway_desc_interface)
        assert filter_no_tunnel.match(self.gateway_desc_router)
        assert not filter_no_tunnel.match(self.gateway_desc_both)
        assert not filter_no_tunnel.match(self.gateway_desc_neither)

        assert filter_no_router.match(self.gateway_desc_interface)
        assert not filter_no_router.match(self.gateway_desc_router)
        assert not filter_no_router.match(self.gateway_desc_both)
        assert not filter_no_router.match(self.gateway_desc_neither)

        assert not filter_tunnel_and_router.match(self.gateway_desc_interface)
        assert not filter_tunnel_and_router.match(self.gateway_desc_router)
        assert filter_tunnel_and_router.match(self.gateway_desc_both)
        assert not filter_tunnel_and_router.match(self.gateway_desc_neither)

    def test_search_response_reception(self):
        """Test function of gateway scanner."""
        xknx = XKNX()
        gateway_scanner = GatewayScanner(xknx)
        test_search_response = fake_router_search_response(xknx)
        udp_client_mock = create_autospec(UDPClient)
        udp_client_mock.local_addr = ("192.168.42.50", 0)
        udp_client_mock.getsockname.return_value = ("192.168.42.50", 0)

        assert gateway_scanner.found_gateways == []
        gateway_scanner._response_rec_callback(
            test_search_response,
            udp_client_mock,
            interface="en1",
        )

        assert str(gateway_scanner.found_gateways[0]) == str(self.gateway_desc_both)
        assert len(gateway_scanner.found_gateways) == 1

        gateway_scanner._response_rec_callback(
            test_search_response,
            udp_client_mock,
            interface="eth1",
        )
        assert len(gateway_scanner.found_gateways) == 1

    @patch("xknx.io.gateway_scanner.netifaces", autospec=True)
    async def test_scan_timeout(self, netifaces_mock):
        """Test gateway scanner timeout."""
        xknx = XKNX()
        # No interface shall be found
        netifaces_mock.interfaces.return_value = []

        gateway_scanner = GatewayScanner(xknx)
        gateway_scanner._response_received_event.wait = MagicMock(
            side_effect=asyncio.TimeoutError()
        )
        timed_out_scan = await gateway_scanner.scan()
        # Unsuccessfull scan() returns None
        assert timed_out_scan == []

    @patch("xknx.io.gateway_scanner.netifaces", autospec=True)
    @patch("xknx.io.GatewayScanner._search_interface", autospec=True)
    async def test_send_search_requests(self, _search_interface_mock, netifaces_mock):
        """Test finding all valid interfaces to send search requests to. No requests are sent."""
        xknx = XKNX()

        netifaces_mock.interfaces.return_value = self.fake_interfaces
        netifaces_mock.ifaddresses = lambda interface: self.fake_ifaddresses[interface]
        netifaces_mock.AF_INET = 2

        async def async_none():
            return None

        _search_interface_mock.return_value = asyncio.ensure_future(async_none())

        gateway_scanner = GatewayScanner(xknx, timeout_in_seconds=0)

        test_scan = await gateway_scanner.scan()

        assert _search_interface_mock.call_count == 2
        expected_calls = [
            ((gateway_scanner, "lo0", "127.0.0.1"),),
            ((gateway_scanner, "en1", "10.1.1.2"),),
        ]
        assert _search_interface_mock.call_args_list == expected_calls
        assert test_scan == []


def fake_router_search_response(xknx: XKNX) -> KNXIPFrame:
    """Return the KNXIPFrame of a KNX/IP Router with a SearchResponse body."""
    frame_body = SearchResponse(xknx)
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
