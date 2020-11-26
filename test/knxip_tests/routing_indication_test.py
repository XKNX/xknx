"""Unit test for KNX/IP RountingIndication objects."""
import asyncio
import time
import unittest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, DPTTemperature, DPTTime
from xknx.knxip import CEMIFrame, KNXIPFrame, KNXIPServiceType, RoutingIndication
from xknx.telegram import GroupAddress, PhysicalAddress, Telegram, TelegramType


class Test_KNXIP(unittest.TestCase):
    """Class for KNX/IP RoutingIndication test."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_from_knx(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet (payload=0xf0)."""
        raw = bytes.fromhex("0610053000122900BCD012020151020040F0")
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, RoutingIndication))
        self.assertTrue(isinstance(knxipframe.body.cemi, CEMIFrame))

        self.assertEqual(knxipframe.body.cemi.src_addr, PhysicalAddress("1.2.2"))
        self.assertEqual(knxipframe.body.cemi.dst_addr, GroupAddress(337))

        self.assertEqual(len(knxipframe.body.cemi.payload.value), 1)
        self.assertEqual(knxipframe.body.cemi.payload.value[0], 0xF0)

    def test_from_knx_to_knx(self):
        """Test parsing and streaming CEMIFrame KNX/IP."""
        raw = bytes.fromhex("0610053000122900BCD012020151020040F0")
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        knxipframe.normalize()

        self.assertEqual(knxipframe.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe.to_knx(), list(raw))

    def test_telegram_set(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet with DPTArray/DPTTime as payload."""
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe.body.cemi.src_addr = PhysicalAddress("1.2.2")

        telegram = Telegram(
            destination_address=GroupAddress(337),
            payload=DPTArray(DPTTime().to_knx(time.strptime("13:23:42", "%H:%M:%S"))),
        )

        knxipframe.body.cemi.telegram = telegram

        knxipframe.body.cemi.set_hops(5)
        knxipframe.normalize()

        raw = bytes.fromhex("0610053000142900BCD012020151040080 0d 17 2a")

        self.assertEqual(knxipframe.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe.to_knx(), list(raw))

    def test_telegram_get(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, group read."""
        raw = bytes.fromhex("0610053000122900BCD012020151020040F0")
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        telegram = knxipframe.body.cemi.telegram

        self.assertEqual(telegram.destination_address, GroupAddress(337))

        self.assertEqual(len(telegram.payload.value), 1)
        self.assertEqual(telegram.payload.value[0], 0xF0)

    #
    # End-tox-End tests:
    #
    #   - parsing KNX telegram and check the result
    #   - reassembling scond KNXIPFrame
    #   - comparing both
    #

    def test_EndTOEnd_group_write_binary_on(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, switch on light in my kitchen."""
        # Switch on Kitchen-L1
        raw = bytes.fromhex("0610053000112900BCD0FFF90149010081")
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.cemi.telegram
        self.assertEqual(telegram, Telegram(GroupAddress("329"), payload=DPTBinary(1)))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.cemi.src_addr = PhysicalAddress("15.15.249")
        knxipframe2.body.cemi.telegram = telegram
        knxipframe2.body.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_write_binary_off(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, switch off light in my kitchen."""
        # Switch off Kitchen-L1
        raw = bytes.fromhex("0610053000112900BCD0FFF90149010080")
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.cemi.telegram
        self.assertEqual(telegram, Telegram(GroupAddress("329"), payload=DPTBinary(0)))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.cemi.src_addr = PhysicalAddress("15.15.249")
        knxipframe2.body.cemi.telegram = telegram
        knxipframe2.body.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_write_1byte(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, dimm light in my kitchen."""
        # Dimm Kitchen L1 to 0x65
        raw = bytes.fromhex("0610053000122900BCD0FFF9014B02008065")
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.cemi.telegram
        self.assertEqual(
            telegram, Telegram(GroupAddress("331"), payload=DPTArray(0x65))
        )

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.cemi.src_addr = PhysicalAddress("15.15.249")
        knxipframe2.body.cemi.telegram = telegram
        knxipframe2.body.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_write_2bytes(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, setting value of thermostat."""
        # Incoming Temperature from thermostat
        raw = bytes.fromhex("0610053000132900BCD01402080103008007C1")
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.cemi.telegram
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress("2049"), payload=DPTArray(DPTTemperature().to_knx(19.85))
            ),
        )

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.cemi.src_addr = PhysicalAddress("1.4.2")
        knxipframe2.body.cemi.telegram = telegram
        knxipframe2.body.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_read(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, group read."""
        # State request
        raw = bytes.fromhex("0610053000112900BCD0FFF901B8010000")
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.cemi.telegram
        self.assertEqual(
            telegram, Telegram(GroupAddress("440"), TelegramType.GROUP_READ)
        )

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.cemi.src_addr = PhysicalAddress("15.15.249")
        knxipframe2.body.cemi.telegram = telegram
        knxipframe2.body.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_response(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, group response."""
        # Incoming state
        raw = bytes.fromhex("0610053000112900BCD013010188010041")
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.cemi.telegram
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress("392"), TelegramType.GROUP_RESPONSE, payload=DPTBinary(1)
            ),
        )

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.cemi.src_addr = PhysicalAddress("1.3.1")
        knxipframe2.body.cemi.telegram = telegram
        knxipframe2.body.cemi.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_maximum_apci(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, testing maximum APCI."""
        telegram = Telegram(
            destination_address=GroupAddress(337),
            payload=DPTBinary(DPTBinary.APCI_MAX_VALUE)
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        knxipframe.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe.body.cemi.src_addr = PhysicalAddress("1.3.1")
        knxipframe.body.cemi.telegram = telegram
        knxipframe.body.cemi.set_hops(5)
        knxipframe.normalize()

        raw = bytes.fromhex("0610053000112900BCD0130101510100BF")

        self.assertEqual(knxipframe.to_knx(), list(raw))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.from_knx(knxipframe.to_knx())
        self.assertEqual(knxipframe2.body.cemi.telegram, telegram)

    def test_from_knx_invalid_cemi(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet with unsupported CEMICode."""
        xknx = XKNX()
        ri = RoutingIndication(xknx)
        raw = bytes([43, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0])
        self.assertEqual(11, ri.from_knx(raw))
