"""Unit test for KNX/IP gateway scanner."""
import asyncio
from unittest.mock import patch

import pytest
from xknx import XKNX
from xknx.prog.management import NM_EXISTS, NM_OK, NetworkManagement
from xknx.telegram import IndividualAddress


@pytest.mark.asyncio
class TestProgrammingInterface:
    """Test class for xknx/io/GatewayScanner objects."""

    called = 0

    async def fake_devicedescriptor_read_response(self, *p):
        """Fake function for evicedescriptor_read_response."""
        if self.called == 1:
            return
        self.called += 1
        await asyncio.sleep(60.0)

    @patch("xknx.prog.device.ProgDevice.individualaddress_read_response", autospec=True)
    @patch("xknx.prog.device.ProgDevice.devicedescriptor_read_response", autospec=True)
    async def test_write_individual_address_success(
        self, mock_devicedescriptor_read_response, mock_individualaddress_read_response
    ):
        """Test IndividualAddress_Write with success."""
        xknx = XKNX()
        mock_devicedescriptor_read_response.side_effect = (
            self.fake_devicedescriptor_read_response
        )
        network_management = NetworkManagement(xknx)
        return_code = await network_management.individualaddress_write(
            IndividualAddress("1.2.1")
        )
        assert return_code == NM_OK

    @patch("xknx.prog.device.ProgDevice.devicedescriptor_read_response", autospec=True)
    async def test_write_individual_address_exists(
        self, mock_devicedescriptor_read_response
    ):
        """Test IndividualAddress_Write with existing device."""
        xknx = XKNX()
        network_management = NetworkManagement(xknx)
        return_code = await network_management.individualaddress_write(
            IndividualAddress("1.2.1")
        )
        assert return_code == NM_EXISTS
