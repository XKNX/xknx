import unittest

from xknx.knxip import KNXIPFrame, KNXIPServiceType
from xknx.knx import Address, DPTTime, DPTBinary, DPTArray, \
    DPTTemperature, Telegram, TelegramType

class Test_KNXIP(unittest.TestCase):
    # pylint: disable=too-many-public-methods,invalid-name

    def test_from_knx(self):

        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x12, 0x29, 0x00,
                0xbc, 0xd0, 0x12, 0x02, 0x01, 0x51, 0x02, 0x00,
                0x40, 0xf0))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        self.assertEqual(knxipframe.body.src_addr, Address("1.2.2"))
        self.assertEqual(knxipframe.body.dst_addr, Address(337))

        self.assertEqual(len(knxipframe.body.payload.value), 1)
        self.assertEqual(knxipframe.body.payload.value[0], 0xf0)

    def test_from_knx_to_knx(self):

        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x12, 0x29, 0x00,
                0xbc, 0xd0, 0x12, 0x02, 0x01, 0x51, 0x02, 0x00,
                0x40, 0xf0))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        knxipframe.normalize()

        self.assertEqual(knxipframe.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe.to_knx(), list(raw))

    def test_telegram_set(self):
        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe.body.src_addr = Address("1.2.2")

        telegram = Telegram()
        telegram.group_address = Address(337)

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

        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x12, 0x29, 0x00,
                0xbc, 0xd0, 0x12, 0x02, 0x01, 0x51, 0x02, 0x00,
                0x40, 0xf0))
        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        telegram = knxipframe.body.telegram

        self.assertEqual(telegram.group_address, Address(337))

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
        # Switch on Kitchen-L1
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0xff, 0xf9, 0x01, 0x49, 0x01, 0x00,
                0x81))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(Address("329"), payload=DPTBinary(1)))

        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = Address("15.15.249")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_write_binary_off(self):
        # Switch off Kitchen-L1
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0xff, 0xf9, 0x01, 0x49, 0x01, 0x00,
                0x80))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(Address("329"), payload=DPTBinary(0)))

        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = Address("15.15.249")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))


    def test_EndTOEnd_group_write_1byte(self):
        # Dimm Kitchen L1 to 0x65
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x12, 0x29, 0x00,
                0xbc, 0xd0, 0xff, 0xf9, 0x01, 0x4b, 0x02, 0x00,
                0x80, 0x65))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(Address("331"), payload=DPTArray(0x65)))

        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = Address("15.15.249")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_write_2bytes(self):
        # Incoming Temperature from thermostat
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x13, 0x29, 0x00,
                0xbc, 0xd0, 0x14, 0x02, 0x08, 0x01, 0x03, 0x00,
                0x80, 0x07, 0xc1))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(Address("2049"),
                                  payload=DPTArray(
                                      DPTTemperature().to_knx(19.85))))

        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = Address("1.4.2")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_read(self):
        # State request
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0xff, 0xf9, 0x01, 0xb8, 0x01, 0x00,
                0x00))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(Address("440"), TelegramType.GROUP_READ))

        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = Address("15.15.249")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_EndTOEnd_group_response(self):
        # Incoming state
        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0x13, 0x01, 0x01, 0x88, 0x01, 0x00,
                0x41))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)
        telegram = knxipframe.body.telegram
        self.assertEqual(telegram,
                         Telegram(Address("392"),
                                  TelegramType.GROUP_RESPONSE,
                                  payload=DPTBinary(1)))

        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.body.src_addr = Address("1.3.1")
        knxipframe2.body.telegram = telegram
        knxipframe2.body.set_hops(5)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.header.to_knx(), list(raw[0:6]))
        self.assertEqual(knxipframe2.body.to_knx(), list(raw[6:]))
        self.assertEqual(knxipframe2.to_knx(), list(raw))

    def test_maximum_apci(self):
        telegram = Telegram()
        telegram.group_address = Address(337)
        telegram.payload = DPTBinary(DPTBinary.APCI_MAX_VALUE)

        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe.body.src_addr = Address("1.3.1")
        knxipframe.body.telegram = telegram
        knxipframe.body.set_hops(5)
        knxipframe.normalize()

        raw = ((0x06, 0x10, 0x05, 0x30, 0x00, 0x11, 0x29, 0x00,
                0xbc, 0xd0, 0x13, 0x01, 0x01, 0x51, 0x01, 0x00,
                0xbf))
        self.assertEqual(knxipframe.to_knx(), list(raw))

        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe2.from_knx(knxipframe.to_knx())
        self.assertEqual(knxipframe2.body.telegram, telegram)


    def test_connect_request(self):

        raw = ((0x06, 0x10, 0x02, 0x05, 0x00, 0x1a, 0x08, 0x01,
                0xc0, 0xa8, 0x2a, 0x01, 0x84, 0x95, 0x08, 0x01,
                0xc0, 0xa8, 0x2a, 0x01, 0xcc, 0xa9, 0x04, 0x04,
                0x02, 0x00))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        print(knxipframe)
        self.assertTrue(False)

SUITE = unittest.TestLoader().loadTestsFromTestCase(Test_KNXIP)
unittest.TextTestRunner(verbosity=2).run(SUITE)
