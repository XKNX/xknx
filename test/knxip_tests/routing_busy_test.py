"""Unit test for KNX/IP RoutingBusy objects."""

import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import KNXIPFrame, RoutingBusy


class TestKNXIPRoutingBusy:
    """Test class for KNX/IP RoutingBusy objects."""

    def test_routing_busy(self) -> None:
        """Test parsing and streaming RoutingBusy KNX/IP packet."""
        raw = bytes(
            (0x06, 0x10, 0x05, 0x32, 0x00, 0x0C, 0x06, 0x00, 0x00, 0x64, 0x00, 0x00)
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, RoutingBusy)
        assert knxipframe.body.device_state == 0
        assert knxipframe.body.wait_time == 100
        assert knxipframe.body.control_field == 0

        routing_busy = RoutingBusy(wait_time=100)
        knxipframe2 = KNXIPFrame.init_from_body(routing_busy)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_busy_information(self) -> None:
        """Test parsing and streaming wrong RoutingBusy (wrong length byte)."""
        raw = bytes(
            (0x06, 0x10, 0x05, 0x32, 0x00, 0x0C, 0x08, 0x00, 0x00, 0x64, 0x00, 0x00)
        )
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_from_knx_wrong_busy_information2(self) -> None:
        """Test parsing and streaming wrong RoutingBusy (wrong length)."""
        raw = bytes((0x06, 0x10, 0x05, 0x32, 0x00, 0x0C, 0x06, 0x00, 0x00, 0x64, 0x00))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
