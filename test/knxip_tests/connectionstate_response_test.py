"""Unit test for KNX/IP ConnectionStateResponses."""
import pytest
from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import ConnectionStateResponse, ErrorCode, KNXIPFrame


class Test_KNXIP_ConnStateResp:
    """Test class for KNX/IP ConnectionStateResponses."""

    def test_disconnect_response(self):
        """Test parsing and streaming connection state response KNX/IP packet."""
        raw = (0x06, 0x10, 0x02, 0x08, 0x00, 0x08, 0x15, 0x21)
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        assert isinstance(knxipframe.body, ConnectionStateResponse)

        assert knxipframe.body.communication_channel_id == 21
        assert knxipframe.body.status_code == ErrorCode.E_CONNECTION_ID

        connectionstate_response = ConnectionStateResponse(
            xknx, communication_channel_id=21, status_code=ErrorCode.E_CONNECTION_ID
        )
        knxipframe2 = KNXIPFrame.init_from_body(connectionstate_response)

        assert knxipframe2.to_knx() == list(raw)

    def test_from_knx_wrong_header(self):
        """Test parsing and streaming wrong ConnectionStateResponse (wrong header length)."""
        raw = (0x06, 0x10, 0x02, 0x08, 0x00, 0x08, 0x15)
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
