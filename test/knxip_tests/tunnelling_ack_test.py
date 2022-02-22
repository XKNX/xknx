"""Unit test for KNX/IP TunnellingAck objects."""
import pytest

from xknx import XKNX
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import ErrorCode, KNXIPFrame, TunnellingAck


class TestKNXIPTunnelingAck:
    """Test class for KNX/IP TunnellingAck objects."""

    def test_connect_request(self):
        """Test parsing and streaming tunneling ACK KNX/IP packet."""
        raw = bytes((0x06, 0x10, 0x04, 0x21, 0x00, 0x0A, 0x04, 0x2A, 0x17, 0x00))
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        assert isinstance(knxipframe.body, TunnellingAck)
        assert knxipframe.body.communication_channel_id == 42
        assert knxipframe.body.sequence_counter == 23
        assert knxipframe.body.status_code == ErrorCode.E_NO_ERROR

        tunnelling_ack = TunnellingAck(
            xknx, communication_channel_id=42, sequence_counter=23
        )
        knxipframe2 = KNXIPFrame.init_from_body(tunnelling_ack)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_ack_information(self):
        """Test parsing and streaming wrong TunnellingAck (wrong length byte)."""
        raw = bytes((0x06, 0x10, 0x04, 0x21, 0x00, 0x0A, 0x03, 0x2A, 0x17, 0x00))
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)

    def test_from_knx_wrong_ack_information2(self):
        """Test parsing and streaming wrong TunnellingAck (wrong length)."""
        raw = bytes((0x06, 0x10, 0x04, 0x21, 0x00, 0x0A, 0x04, 0x2A, 0x17))
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        with pytest.raises(CouldNotParseKNXIP):
            knxipframe.from_knx(raw)
