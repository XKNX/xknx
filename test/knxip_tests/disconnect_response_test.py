"""Unit test for KNX/IP DisconnectResponse objects."""
import pytest

from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import (
    DisconnectResponse, ErrorCode, KNXIPFrame, KNXIPServiceType)

from xknx._test import Testcase

class Test_KNXIP_DisconnectResp(Testcase):
    """Test class for KNX/IP DisconnectResponse objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    @pytest.mark.anyio
    async def test_disconnect_response(self):
        """Test parsing and streaming DisconnectResponse KNX/IP packet."""
        raw = ((0x06, 0x10, 0x02, 0x0A, 0x00, 0x08, 0x15, 0x25))
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, DisconnectResponse))

        self.assertEqual(
            knxipframe.body.communication_channel_id, 21)
        self.assertEqual(
            knxipframe.body.status_code, ErrorCode.E_NO_MORE_UNIQUE_CONNECTIONS)

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.DISCONNECT_RESPONSE)
        knxipframe2.body.communication_channel_id = 21
        knxipframe2.body.status_code = ErrorCode.E_NO_MORE_UNIQUE_CONNECTIONS
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))

    @pytest.mark.anyio
    async def test_from_knx_wrong_length(self):
        """Test parsing and streaming wrong DisconnectResponse."""
        raw = ((0x06, 0x10, 0x02, 0x0A, 0x00, 0x08, 0x15))
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with self.assertRaises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
