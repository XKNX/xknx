import unittest
from unittest.mock import Mock

from xknx import XKNX, Light, Address, Telegram, TelegramType, DPTBinary, \
    DPTArray

class TestLight(unittest.TestCase):

    #
    # SYNC STATE
    #
    def test_sync_state(self):

        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_dimm='1/2/4',
                      group_address_dimm_feedback='1/2/5')
        light.sync_state()

        self.assertEqual(xknx.telegrams.qsize(), 2)

        telegram1 = xknx.telegrams.get()
        self.assertEqual(telegram1,
                         Telegram(Address('1/2/3'), TelegramType.GROUP_READ))

        telegram2 = xknx.telegrams.get()
        self.assertEqual(telegram2,
                         Telegram(Address('1/2/5'), TelegramType.GROUP_READ))


    #
    # TEST SET ON
    #
    def test_set_on(self):
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_dimm='1/2/4',
                      group_address_dimm_feedback='1/2/5')
        light.set_on()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/3'), payload=DPTBinary(1)))

    #
    # TEST SET OFF
    #
    def test_set_off(self):
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_dimm='1/2/4',
                      group_address_dimm_feedback='1/2/5')
        light.set_off()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/3'), payload=DPTBinary(0)))

    #
    # TEST SET BRIGHTNESS
    #
    def test_set_brightness(self):
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_dimm='1/2/4',
                      group_address_dimm_feedback='1/2/5')
        light.set_brightness(23)
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/5'), payload=DPTArray(23)))


    #
    # TEST PROCESS
    #
    def test_process_switch(self):
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_dimm='1/2/4',
                      group_address_dimm_feedback='1/2/5')
        self.assertEqual(light.state, False)

        telegram = Telegram(Address('1/2/3'), payload=DPTBinary(1))
        light.process(telegram)
        self.assertEqual(light.state, True)

        telegram = Telegram(Address('1/2/3'), payload=DPTBinary(0))
        light.process(telegram)
        self.assertEqual(light.state, False)


    def test_process_switch_callback(self):
        # pylint: disable=no-self-use
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_dimm='1/2/4',
                      group_address_dimm_feedback='1/2/5')

        after_update_callback = Mock()
        light.after_update_callback = after_update_callback

        telegram = Telegram(Address('1/2/3'), payload=DPTBinary(1))
        light.process(telegram)

        after_update_callback.assert_called_with(light)


    def test_process_dimm(self):
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_dimm='1/2/4',
                      group_address_dimm_feedback='1/2/5')
        self.assertEqual(light.brightness, 0)

        telegram = Telegram(Address('1/2/5'), payload=DPTArray(23))
        light.process(telegram)
        self.assertEqual(light.brightness, 23)


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestLight)
unittest.TextTestRunner(verbosity=2).run(SUITE)
