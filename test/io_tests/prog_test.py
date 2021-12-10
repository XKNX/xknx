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
from xknx.telegram import (
    IndividualAddress,
    Priority,
    Telegram,
    TelegramDirection,
    TPDUType,
)
from xknx.telegram.apci import (
    IndividualAddressResponse,
)
from xknx.prog.management import NM_EXISTS, NM_OK, NM_TIME_OUT, NetworkManagement


@pytest.mark.asyncio
class TestProgrammingInterface:
    """Test class for xknx/io/GatewayScanner objects."""

    called = 0
    async def fake_DeviceDescriptor_Read_Response(self, *p):
        if self.called == 1:
            return
        self.called+=1
        await asyncio.sleep(60.)

    @patch("xknx.prog.device.A_Device.IndividualAddress_Read_Response", autospec=True)
    @patch("xknx.prog.device.A_Device.DeviceDescriptor_Read_Response", autospec=True)
    async def test_write_individual_address_success(self, mock_DeviceDescriptor_Read_Response, mock_IndividualAddress_Read_Response):
        """Test finding all valid interfaces to send search requests to. No requests are sent."""
        xknx = XKNX()
        mock_DeviceDescriptor_Read_Response.side_effect = self.fake_DeviceDescriptor_Read_Response
        network_management = NetworkManagement(xknx)
        return_code = await network_management.IndividualAddress_Write(
            IndividualAddress("1.2.1")
            )
        assert return_code == NM_OK

    @patch("xknx.prog.device.A_Device.DeviceDescriptor_Read_Response", autospec=True)
    async def test_write_individual_address_exists(self, mock_DeviceDescriptor_Read_Response):
        """Test finding all valid interfaces to send search requests to. No requests are sent."""
        xknx = XKNX()
        network_management = NetworkManagement(xknx)
        return_code = await network_management.IndividualAddress_Write(
            IndividualAddress("1.2.1")
            )
        assert return_code == NM_EXISTS

