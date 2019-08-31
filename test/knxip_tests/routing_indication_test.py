"""Unit test for KNX/IP RountingIndication objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, DPTTemperature, DPTTime
from xknx.knxip import CEMIFrame, KNXIPFrame, KNXIPServiceType
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
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x12, 0x29, 0x00,
                0xbc, 0xd0, 0x12, 0x02, 0x01, 0x51, 0x02, 0x00,
                0x40, 0xf0))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, CEMIFrame))

        self.assertEqual(knxipframe.body.src_addr, PhysicalAddress("1.2.2"))
        self.assertEqual(knxipframe.body.dst_addr, GroupAddress(337))

        self.assertEqual(len(knxipframe.body.payload.value), 1)
        self.assertEqual(knxipframe.body.payload.value[0], 0xf0)

    def test_from_knx_to_knx(self):
        """Test parsing and streaming CEMIFrame KNX/IP."""
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x12, 0x29, 0x00,
                0xbc, 0xd0, 0x12, 0x02, 0x01, 0x51, 0x02, 0x00,
                0x40, 0xf0))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        knxipframe.normalize()

        self.assertEqual(knxipframe.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe.to_knx(), list(raw))

    def test_telegram_set(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet with DPTArray/DPTTime as payload."""
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe.body.src_addr = PhysicalAddress("1.2.2")

        telegram = Telegram()
        telegram.group_address = GroupAddress(337)

        telegram.payload = DPTArray(DPTTime().to_knx(
            {'hours': 13, 'minutes': 23, 'seconds': 42}))

        knxipframe.body.telegram = telegram

        knxipframe.body.set_hops(5)
        knxipframe.normalize()

        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x14, 0x29, 0x00,
                0xbc, 0xd0, 0x12, 0x02, 0x01, 0x51, 0x04, 0x00,
                0x80, 13, 23, 42))

        self.assertEqual(knxipframe.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe.to_knx(), list(raw))

    def test_telegram_get(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, group read."""
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x12, 0x29, 0x00,
                0xbc, 0xd0, 0x12, 0x02, 0x01, 0x51, 0x02, 0x00,
                0x40, 0xf0))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)

        telegram = knxipframe.body.telegram

        self.assertEqual(telegram.group_address, GroupAddress(337))

        self.assertEqual(len(telegram.payload.value), 1)
        self.assertEqual(telegram.payload.value[0], 0xf0)

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
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0xff, 0xf9, 0x01, 0x49, 0x01, 0x00,
                0x81))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(GroupAddress("329"), payload=DPTBinary(1)))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = PhysicalAddress("15.15.249")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_write_binary_off(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, switch off light in my kitchen."""
        # Switch off Kitchen-L1
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0xff, 0xf9, 0x01, 0x49, 0x01, 0x00,
                0x80))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(GroupAddress("329"), payload=DPTBinary(0)))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = PhysicalAddress("15.15.249")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_write_1byte(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, dimm light in my kitchen."""
        # Dimm Kitchen L1 to 0x65
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x12, 0x29, 0x00,
                0xbc, 0xd0, 0xff, 0xf9, 0x01, 0x4b, 0x02, 0x00,
                0x80, 0x65))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(GroupAddress("331"), payload=DPTArray(0x65)))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = PhysicalAddress("15.15.249")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_write_2bytes(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, setting value of thermostat."""
        # Incoming Temperature from thermostat
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x13, 0x29, 0x00,
                0xbc, 0xd0, 0x14, 0x02, 0x08, 0x01, 0x03, 0x00,
                0x80, 0x07, 0xc1))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(GroupAddress("2049"),
                                  payload=DPTArray(
                                      DPTTemperature().to_knx(19.85))))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = PhysicalAddress("1.4.2")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_read(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, group read."""
        # State request
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0xff, 0xf9, 0x01, 0xb8, 0x01, 0x00,
                0x00))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(GroupAddress("440"), TelegramType.GROUP_READ))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = PhysicalAddress("15.15.249")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_response(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, group response."""
        # Incoming state
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0x13, 0x01, 0x01, 0x88, 0x01, 0x00,
                0x41))
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(GroupAddress("392"),
                                  TelegramType.GROUP_RESPONSE,
                                  payload=DPTBinary(1)))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = PhysicalAddress("1.3.1")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_maximum_apci(self):
        """Test parsing and streaming CEMIFrame KNX/IP packet, testing maximum APCI."""
        telegram = Telegram()
        telegram.group_address = GroupAddress(337)
        telegram.payload = DPTBinary(DPTBinary.APCI_MAX_VALUE)
        xknx = XKNX(loop=self.loop)
        knxipframe = KNXIPFrame(xknx)
        knxipframe.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe.body.src_addr = PhysicalAddress("1.3.1")
        knxipframe.body.telegram = telegram
        knxipframe.body.set_hops(5)
        knxipframe.normalize()

        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0x13, 0x01, 0x01, 0x51, 0x01, 0x00,
                0xbf))
        self.assertEqual(knxipframe.to_knx(), list(raw))

        knxipframe2 = KNXIPFrame(xknx)
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.from_knx(knxipframe.to_knx())
        self.assertEqual(knxipframe2.body.telegram, telegram)
