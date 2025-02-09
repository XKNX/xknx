"""Unit test for KNX/IP DisconnectResponse objects."""

import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import DisconnectResponse, ErrorCode, KNXIPFrame


class TestKNXIPDisconnectResponse:
    """Test class for KNX/IP DisconnectResponse objects."""

    def test_disconnect_response(self) -> None:
        """Test parsing and streaming DisconnectResponse KNX/IP packet."""
        raw = bytes((0x06, 0x10, 0x02, 0x0A, 0x00, 0x08, 0x15, 0x25))
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, DisconnectResponse)

        assert knxipframe.body.communication_channel_id == 21
        assert knxipframe.body.status_code == ErrorCode.E_NO_MORE_UNIQUE_CONNECTIONS

        disconnect_response = DisconnectResponse(
            communication_channel_id=21,
            status_code=ErrorCode.E_NO_MORE_UNIQUE_CONNECTIONS,
        )
        knxipframe2 = KNXIPFrame.init_from_body(disconnect_response)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_length(self) -> None:
        """Test parsing and streaming wrong DisconnectResponse."""
        raw = bytes((0x06, 0x10, 0x02, 0x0A, 0x00, 0x08, 0x15))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
