"""Unit test for KNX/IP RoutingLostMessage objects."""

import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import KNXIPFrame, RoutingLostMessage


class TestKNXIPRoutingLostMessage:
    """Test class for KNX/IP RoutingLostMessage objects."""

    def test_routing_lost_message(self) -> None:
        """Test parsing and streaming RoutingLostMessage KNX/IP packet."""
        raw = bytes((0x06, 0x10, 0x05, 0x31, 0x00, 0x0A, 0x04, 0x00, 0x00, 0x05))
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, RoutingLostMessage)
        assert knxipframe.body.device_state == 0
        assert knxipframe.body.lost_messages == 5

        routing_lost_message = RoutingLostMessage(lost_messages=5)
        knxipframe2 = KNXIPFrame.init_from_body(routing_lost_message)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_lost_message_information(self) -> None:
        """Test parsing and streaming wrong RoutingLostMessage (wrong length byte)."""
        raw = bytes((0x06, 0x10, 0x05, 0x31, 0x00, 0x0A, 0x06, 0x00, 0x00, 0x05))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_from_knx_wrong_lost_message_information2(self) -> None:
        """Test parsing and streaming wrong RoutingLostMessage (wrong length)."""
        raw = bytes((0x06, 0x10, 0x05, 0x31, 0x00, 0x0A, 0x04, 0x00, 0x00))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
