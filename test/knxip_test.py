import unittest

from xknx import KNXIPFrame, Address, DPT_Time, Telegram

class Test_KNXIP(unittest.TestCase):

    def test_from_knx(self):

        raw = ((0x06,0x10,0x05,0x30,0x00,0x12,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x02,0x00,0x40,0xf0))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        self.assertEqual( knxipframe.sender ,  Address("1.2.2") )
        self.assertEqual(knxipframe.group_address, Address(337))

        self.assertEqual(len(knxipframe.payload),2)
        self.assertEqual(knxipframe.payload[0],0x40)
        self.assertEqual(knxipframe.payload[1],0xf0)

    def test_from_knx_to_knx(self):

        raw = ((0x06,0x10,0x05,0x30,0x00,0x12,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x02,0x00,0x40,0xf0))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        self.assertEqual( knxipframe.to_knx(), list(raw))

    def test_telegram_set(self):
        knxipframe = KNXIPFrame()
        knxipframe.sender = Address("1.2.2")

        telegram = Telegram()
        telegram.group_address= Address(337)

        telegram.payload.append(0x80)
        test_payload = DPT_Time().to_knx(
                    {'hours': 13, 'minutes': 23, 'seconds': 42})
        for byte in test_payload:
            telegram.payload.append(byte)

        knxipframe.telegram = telegram

        raw = ((0x06,0x10,0x05,0x30,0x00,0x14,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x04,0x00,0x80,13,23,42))

        self.assertEqual( knxipframe.to_knx(), list(raw))

    def test_telegram_get(self):

        raw = ((0x06,0x10,0x05,0x30,0x00,0x12,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x02,0x00,0x40,0xf0))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        telegram = knxipframe.telegram

        self.assertEqual(telegram.group_address, Address(337))

        self.assertEqual(len(telegram.payload),2)
        self.assertEqual(telegram.payload[0],0x40)
        self.assertEqual(telegram.payload[1],0xf0)

        print(telegram)

suite = unittest.TestLoader().loadTestsFromTestCase(Test_KNXIP)
unittest.TextTestRunner(verbosity=2).run(suite)
