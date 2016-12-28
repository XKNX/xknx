import unittest

from xknx import Telegram, Address, DPT_Time

class Test_KNXIP(unittest.TestCase):

    def test_from_knx(self):

        raw = ((0x06,0x10,0x05,0x30,0x00,0x12,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x02,0x00,0x40,0xf0))

        telegram = Telegram()
        telegram.read(raw)

        self.assertEqual( telegram.sender ,  Address("1.2.2") )
        self.assertEqual(telegram.group_address, Address(337))

        self.assertEqual(len(telegram.payload),2)
        self.assertEqual(telegram.payload[0],0x40)
        self.assertEqual(telegram.payload[1],0xf0)

    def test_from_knx_to_knx(self):

        raw = ((0x06,0x10,0x05,0x30,0x00,0x12,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x02,0x00,0x40,0xf0))

        telegram = Telegram()
        telegram.read(raw)

        self.assertEqual( telegram.str(), bytes(raw))

    def test_building_telegram(self):
        telegram = Telegram()
        telegram.sender = Address("1.2.2")
        telegram.group_address= Address(337)

        telegram.payload.append(0x80)
        test_payload = DPT_Time().to_knx(
                    {'hours': 13, 'minutes': 23, 'seconds': 42})
        for byte in test_payload:
            telegram.payload.append(byte)

        raw = ((0x06,0x10,0x05,0x30,0x00,0x14,0x29,0x00,0xbc,0xd0,0x12,0x02,0x01,0x51,0x04,0x00,0x80,13,23,42))

        self.assertEqual( telegram.str(), bytes(raw))

suite = unittest.TestLoader().loadTestsFromTestCase(Test_KNXIP)
unittest.TextTestRunner(verbosity=2).run(suite)
