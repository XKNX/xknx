"""Unit test for KNX/IP ConnectionStateResponses."""

import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import ConnectionStateResponse, ErrorCode, KNXIPFrame


class TestKNXIPConnectionStateResponse:
    """Test class for KNX/IP ConnectionStateResponses."""

    def test_disconnect_response(self) -> None:
        """Test parsing and streaming connection state response KNX/IP packet."""
        raw = bytes((0x06, 0x10, 0x02, 0x08, 0x00, 0x08, 0x15, 0x21))
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, ConnectionStateResponse)

        assert knxipframe.body.communication_channel_id == 21
        assert knxipframe.body.status_code == ErrorCode.E_CONNECTION_ID

        connectionstate_response = ConnectionStateResponse(
            communication_channel_id=21,
            status_code=ErrorCode.E_CONNECTION_ID,
        )
        knxipframe2 = KNXIPFrame.init_from_body(connectionstate_response)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_header(self) -> None:
        """Test parsing and streaming wrong ConnectionStateResponse (wrong header length)."""
        raw = bytes((0x06, 0x10, 0x02, 0x08, 0x00, 0x08, 0x15))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
