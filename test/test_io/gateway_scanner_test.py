"""Unit test for KNX/IP gateway scanner."""
import asyncio
import unittest

from xknx import XKNX
from xknx.io import GatewayScanFilter, GatewayScanner, UDPClient
from xknx.io.gateway_scanner import GatewayDescriptor
from xknx.knx import PhysicalAddress
from xknx.knxip import (
    HPAI, DIBDeviceInformation, DIBServiceFamily, DIBSuppSVCFamilies,
    KNXIPFrame, KNXIPHeader, KNXIPServiceType, SearchResponse)


class TestGatewayScanner(unittest.TestCase):
    """Test class for xknx/io/GatewayScanner objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_gateway_scan_filter_match(self):
        """Test match function of gateway filter."""
        # pylint: disable=too-many-locals
        gateway_1 = GatewayDescriptor(name='KNX-Interface',
                                      ip_addr='10.1.1.11',
                                      port=3761,
                                      local_interface='en1',
                                      local_ip='110.1.1.100',
                                      supports_tunnelling=True,
                                      supports_routing=False)
        gateway_2 = GatewayDescriptor(name='KNX-Router',
                                      ip_addr='10.1.1.12',
                                      port=3761,
                                      local_interface='en1',
                                      local_ip='10.1.1.100',
                                      supports_tunnelling=False,
                                      supports_routing=True)
        filter_tunnel = GatewayScanFilter(tunnelling=True)
        filter_router = GatewayScanFilter(routing=True)
        filter_name = GatewayScanFilter(name="KNX-Router")
        filter_no_tunnel = GatewayScanFilter(tunnelling=False)

        self.assertTrue(filter_tunnel.match(gateway_1))
        self.assertFalse(filter_tunnel.match(gateway_2))
        self.assertFalse(filter_router.match(gateway_1))
        self.assertTrue(filter_router.match(gateway_2))
        self.assertFalse(filter_name.match(gateway_1))
        self.assertTrue(filter_name.match(gateway_2))
        self.assertFalse(filter_no_tunnel.match(gateway_1))
        self.assertTrue(filter_no_tunnel.match(gateway_2))

    def test_search_response_reception(self):
        """Test function of gateway scanner."""
        # pylint: disable=protected-access
        xknx = XKNX(loop=self.loop)
        gateway_scanner = GatewayScanner(xknx)
        search_response = fake_router_search_response(xknx)
        udp_client = unittest.mock.create_autospec(UDPClient)
        udp_client.local_addr = ("192.168.42.50", 0, "en1")
        udp_client.getsockname.return_value = ("192.168.42.50", 0)
        router_gw_descriptor = GatewayDescriptor(name="Gira KNX/IP-Router",
                                                 ip_addr="192.168.42.10",
                                                 port=3671,
                                                 local_interface="en1",
                                                 local_ip="192.168.42.50",
                                                 supports_tunnelling=True,
                                                 supports_routing=True)

        self.assertEqual(gateway_scanner.found_gateways, [])
        gateway_scanner._response_rec_callback(search_response, udp_client)
        self.assertEqual(str(gateway_scanner.found_gateways[0]),
                         str(router_gw_descriptor))


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
