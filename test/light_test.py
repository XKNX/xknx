import unittest
from unittest.mock import Mock
import asyncio
from xknx import XKNX, Light
from xknx.knx import Address, Telegram, TelegramType, DPTBinary, DPTArray

class TestLight(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    #
    # TEST SUPPORT DIMMING
    #
    def test_supports_dimm_yes(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4',
                      group_address_brightness='1/6/6')
        self.assertTrue(light.supports_dimming)

    def test_supports_dimm_no(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4')
        self.assertFalse(light.supports_dimming)


    #
    # SYNC
    #
    def test_sync(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.loop.run_until_complete(asyncio.Task(light.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 2)

        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(Address('1/2/3'), TelegramType.GROUP_READ))

        telegram2 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram2,
                         Telegram(Address('1/2/5'), TelegramType.GROUP_READ))

    #
    # SYNC WITH STATE ADDRESS
    #
    def test_sync_state_address(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_switch_state='1/2/6',
                      group_address_brightness='1/2/8',
                      group_address_brightness_state='1/2/9')
        self.loop.run_until_complete(asyncio.Task(light.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 2)

        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(Address('1/2/6'), TelegramType.GROUP_READ))
        telegram2 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram2,
                         Telegram(Address('1/2/9'), TelegramType.GROUP_READ))

    #
    # TEST SET ON
    #
    def test_set_on(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        light.set_on()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/3'), payload=DPTBinary(1)))

    #
    # TEST SET OFF
    #
    def test_set_off(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        light.set_off()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/3'), payload=DPTBinary(0)))

    #
    # TEST SET BRIGHTNESS
    #
    def test_set_brightness(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        light.set_brightness(23)
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/5'), payload=DPTArray(23)))


    #
    # TEST PROCESS
    #
    def test_process_switch(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.assertEqual(light.state, False)

        telegram = Telegram(Address('1/2/3'), payload=DPTBinary(1))
        light.process(telegram)
        self.assertEqual(light.state, True)

        telegram = Telegram(Address('1/2/3'), payload=DPTBinary(0))
        light.process(telegram)
        self.assertEqual(light.state, False)


    def test_process_switch_callback(self):
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')

        after_update_callback = Mock()
        light.register_device_updated_cb(after_update_callback)

        telegram = Telegram(Address('1/2/3'), payload=DPTBinary(1))
        light.process(telegram)

        after_update_callback.assert_called_with(light)


    def test_process_dimm(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.assertEqual(light.brightness, 0)

        telegram = Telegram(Address('1/2/5'), payload=DPTArray(23))
        light.process(telegram)
        self.assertEqual(light.brightness, 23)


    #
    # TEST DO
    #
    def test_do(self):
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        light.do("on")
        self.assertTrue(light.state)
        light.do("brightness:80")
        self.assertEqual(light.brightness, 80)
        light.do("off")
        self.assertFalse(light.state)


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestLight)
unittest.TextTestRunner(verbosity=2).run(SUITE)
