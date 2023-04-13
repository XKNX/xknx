"""Unit test for KNX/IP RountingIndication objects."""
import time

from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.dpt import DPTTime
from xknx.knxip import KNXIPFrame, RoutingIndication
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestKNXIPRountingIndication:
    """Class for KNX/IP RoutingIndication test."""

    def test_from_knx(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet (payload=0xf0)."""
        raw = bytes.fromhex("06 10 05 30 00 12 29 00 bc d0 12 02 01 51 02 00 40 f0")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, RoutingIndication)
        assert isinstance(knxipframe.body.raw_cemi, bytes)
        assert len(knxipframe.body.raw_cemi) == 12

    def test_from_knx_to_knx(self):
        """Test parsing and streaming CEMIFrame KNX/IP."""
        raw = bytes.fromhex("06 10 05 30 00 12 29 00 bc d0 12 02 01 51 02 00 40 f0")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert knxipframe.header.to_knx() == raw[:6]
        assert knxipframe.body.to_knx() == raw[6:]
        assert knxipframe.to_knx() == raw

    def test_telegram_set(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet with DPTArray/DPTTime as payload."""
        telegram = Telegram(
            destination_address=GroupAddress(337),
            payload=GroupValueWrite(
                DPTTime().to_knx(time.strptime("13:23:42", "%H:%M:%S"))
            ),
        )
        cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(
                telegram,
                src_addr=IndividualAddress("1.2.2"),
            ),
        )
        assert isinstance(cemi.data, CEMILData)
        cemi.data.hops = 5
        routing_indication = RoutingIndication(raw_cemi=cemi.to_knx())
        knxipframe = KNXIPFrame.init_from_body(routing_indication)

        raw = bytes.fromhex(
            "06 10 05 30 00 14 29 00 bc d0 12 02 01 51 04 00 80 0d 17 2a"
        )

        assert knxipframe.header.to_knx() == raw[:6]
        assert knxipframe.body.to_knx() == raw[6:]
        assert knxipframe.to_knx() == raw

    def test_end_to_end_routing_indication(self):
        """Test parsing and streaming RoutingIndication KNX/IP packet."""
        # Switch off Kitchen-L1
        raw = bytes.fromhex("06 10 05 30 00 11 29 00 bc d0 ff f9 01 49 01 00 80")
        knxipframe, _ = KNXIPFrame.from_knx(raw)
        raw_cemi = knxipframe.body.raw_cemi

        routing_indication = RoutingIndication(raw_cemi=raw_cemi)
        knxipframe2 = KNXIPFrame.init_from_body(routing_indication)

        assert knxipframe2.header.to_knx() == raw[:6]
        assert knxipframe2.body.to_knx() == raw[6:]
        assert knxipframe2.to_knx() == raw

    def test_from_knx_invalid_cemi(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet with unsupported CEMICode."""
        routing_indication = RoutingIndication()
        raw = bytes([43, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0])
        assert routing_indication.from_knx(raw) == 11
