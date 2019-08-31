"""Unit test for KNX/IP gateway scanner."""
import asyncio
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.io import GatewayScanFilter, GatewayScanner, UDPClient
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.knxip import (
    HPAI, DIBDeviceInformation, DIBServiceFamily, DIBSuppSVCFamilies,
    KNXIPFrame, KNXIPHeader, KNXIPServiceType, SearchResponse)
from xknx.telegram import PhysicalAddress


class TestGatewayScanner(unittest.TestCase):
    """Test class for xknx/io/GatewayScanner objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.gateway_desc_interface = GatewayDescriptor(
            name='KNX-Interface',
            ip_addr='10.1.1.11',
            port=3761,
            local_interface='en1',
            local_ip='110.1.1.100',
            supports_tunnelling=True,
            supports_routing=False)
        self.gateway_desc_router = GatewayDescriptor(
            name='KNX-Router',
            ip_addr='10.1.1.12',
            port=3761,
            local_interface='en1',
            local_ip='10.1.1.100',
            supports_tunnelling=False,
            supports_routing=True)
        self.gateway_desc_both = GatewayDescriptor(
            name="Gira KNX/IP-Router",
            ip_addr="192.168.42.10",
            port=3671,
            local_interface="en1",
            local_ip="192.168.42.50",
            supports_tunnelling=True,
            supports_routing=True)

        self.fake_interfaces = ['lo0', 'en0', 'en1']
        self.fake_ifaddresses = {
            'lo0': {2: [{'addr': '127.0.0.1', 'netmask': '255.0.0.0', 'peer': '127.0.0.1'}],
                    30: [{'addr': '::1', 'netmask': 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff/128', 'peer': '::1', 'flags': 0},
                         {'addr': 'fe80::1%lo0', 'netmask': 'ffff:ffff:ffff:ffff::/64', 'flags': 0}]},
            'en0': {18: [{'addr': 'FF:FF:00:00:00:00'}]},
            'en1': {18: [{'addr': 'FF:FF:00:00:00:01'}],
                    30: [{'addr': 'fe80::1234:1234:1234:1234%en1', 'netmask': 'ffff:ffff:ffff:ffff::/64', 'flags': 1024}],
                    2: [{'addr': '10.1.1.2', 'netmask': '255.255.255.0', 'broadcast': '10.1.1.255'}]}
        }

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_gateway_scan_filter_match(self):
        """Test match function of gateway filter."""
        # pylint: disable=too-many-locals
        filter_tunnel = GatewayScanFilter(tunnelling=True)
        filter_router = GatewayScanFilter(routing=True)
        filter_name = GatewayScanFilter(name="KNX-Router")
        filter_no_tunnel = GatewayScanFilter(tunnelling=False)

        self.assertTrue(filter_tunnel.match(self.gateway_desc_interface))
        self.assertFalse(filter_tunnel.match(self.gateway_desc_router))
        self.assertTrue(filter_tunnel.match(self.gateway_desc_both))

        self.assertFalse(filter_router.match(self.gateway_desc_interface))
        self.assertTrue(filter_router.match(self.gateway_desc_router))
        self.assertTrue(filter_router.match(self.gateway_desc_both))

        self.assertFalse(filter_name.match(self.gateway_desc_interface))
        self.assertTrue(filter_name.match(self.gateway_desc_router))
        self.assertFalse(filter_name.match(self.gateway_desc_both))

        self.assertFalse(filter_no_tunnel.match(self.gateway_desc_interface))
        self.assertTrue(filter_no_tunnel.match(self.gateway_desc_router))
        self.assertFalse(filter_no_tunnel.match(self.gateway_desc_both))

    def test_search_response_reception(self):
        """Test function of gateway scanner."""
        # pylint: disable=protected-access
        xknx = XKNX(loop=self.loop)
        gateway_scanner = GatewayScanner(xknx)
        test_search_response = fake_router_search_response(xknx)
        udp_client_mock = unittest.mock.create_autospec(UDPClient)
        udp_client_mock.local_addr = ("192.168.42.50", 0, "en1")
        udp_client_mock.getsockname.return_value = ("192.168.42.50", 0)

        self.assertEqual(gateway_scanner.found_gateways, [])
        gateway_scanner._response_rec_callback(test_search_response, udp_client_mock)
        self.assertEqual(str(gateway_scanner.found_gateways[0]),
                         str(self.gateway_desc_both))

    @patch('xknx.io.gateway_scanner.netifaces', autospec=True)
    def test_scan_timeout(self, netifaces_mock):
        """Test gateway scanner timeout."""
        # pylint: disable=protected-access
        xknx = XKNX(loop=self.loop)
        # No interface shall be found
        netifaces_mock.interfaces.return_value = []

        gateway_scanner = GatewayScanner(xknx, timeout_in_seconds=0)

        timed_out_scan = self.loop.run_until_complete(gateway_scanner.scan())

        # Timeout handle was cancelled (cancelled method requires Python 3.7)
        event_has_cancelled = getattr(gateway_scanner._timeout_handle, "cancelled", None)
        if callable(event_has_cancelled):
            self.assertTrue(gateway_scanner._timeout_handle.cancelled())
        self.assertTrue(gateway_scanner._response_received_or_timeout.is_set())
        # Unsuccessfull scan() returns None
        self.assertEqual(timed_out_scan, [])

    @patch('xknx.io.gateway_scanner.netifaces', autospec=True)
    @patch('xknx.io.GatewayScanner._search_interface', autospec=True)
    def test_send_search_requests(self, _search_interface_mock, netifaces_mock):
        """Test finding all valid interfaces to send search requests to. No requests are sent."""
        # pylint: disable=protected-access
        xknx = XKNX(loop=self.loop)

        netifaces_mock.interfaces.return_value = self.fake_interfaces
        netifaces_mock.ifaddresses = lambda interface: self.fake_ifaddresses[interface]
        netifaces_mock.AF_INET = 2

        async def async_none():
            return None
        _search_interface_mock.return_value = asyncio.ensure_future(async_none())

        gateway_scanner = GatewayScanner(xknx, timeout_in_seconds=0)

        test_scan = self.loop.run_until_complete(gateway_scanner.scan())

        self.assertEqual(_search_interface_mock.call_count, 2)
        expected_calls = [((gateway_scanner, 'lo0', '127.0.0.1'),),
                          ((gateway_scanner, 'en1', '10.1.1.2'),)]
        self.assertEqual(_search_interface_mock.call_args_list, expected_calls)
        self.assertEqual(test_scan, [])


def fake_router_search_response(xknx: XKNX) -> SearchResponse:
    """Return the SearchResponse of a KNX/IP Router."""
    _frame_header = KNXIPHeader(xknx)
    _frame_header.service_type_ident = KNXIPServiceType.SEARCH_RESPONSE
    _frame_body = SearchResponse(xknx)
    _frame_body.control_endpoint = HPAI(ip_addr="192.168.42.10", port=3671)

    _device_information = DIBDeviceInformation()
    _device_information.name = "Gira KNX/IP-Router"
    _device_information.serial_number = "11:22:33:44:55:66"
    _device_information.individual_address = PhysicalAddress("1.1.0")
    _device_information.mac_address = "01:02:03:04:05:06"

    _svc_families = DIBSuppSVCFamilies()
    _svc_families.families.append(
        DIBSuppSVCFamilies.Family(name=DIBServiceFamily.CORE,
                                  version=1))
    _svc_families.families.append(
        DIBSuppSVCFamilies.Family(name=DIBServiceFamily.DEVICE_MANAGEMENT,
                                  version=2))
    _svc_families.families.append(
        DIBSuppSVCFamilies.Family(name=DIBServiceFamily.TUNNELING,
                                  version=1))
    _svc_families.families.append(
        DIBSuppSVCFamilies.Family(name=DIBServiceFamily.ROUTING,
                                  version=1))
    _svc_families.families.append(
        DIBSuppSVCFamilies.Family(name=DIBServiceFamily.REMOTE_CONFIGURATION_DIAGNOSIS,
                                  version=1))

    _frame_body.dibs.append(_device_information)
    _frame_body.dibs.append(_svc_families)
    _frame_header.set_length(_frame_body)

    search_response = KNXIPFrame(xknx)
    search_response.init(KNXIPServiceType.SEARCH_RESPONSE)
    search_response.header = _frame_header
    search_response.body = _frame_body
    search_response.normalize()

    return search_response
