"""Unit test for Light objects."""
import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import Light
from xknx.knx import DPTArray, DPTBinary, GroupAddress, Telegram, TelegramType
from xknx.exceptions import CouldNotParseTelegram


class TestLight(unittest.TestCase):
    """Class for testing Light objects."""

    # pylint: disable=too-many-public-methods

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # TEST SUPPORT DIMMING
    #
    def test_supports_dimm_yes(self):
        """Test supports_dimm attribute with a light with dimmer."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4',
                      group_address_brightness='1/6/6')
        self.assertTrue(light.supports_dimming)

    def test_supports_dimm_no(self):
        """Test supports_dimm attribute with a Light without dimmer."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4')
        self.assertFalse(light.supports_dimming)

    #
    # TEST SUPPORT COLOR
    #
    def test_supports_color_true(self):
        """Test supports_color true."""
        xknx = XKNX(loop=self.loop)
        light = Light(
            xknx,
            'Diningroom.Light_1',
            group_address_switch='1/6/4',
            group_address_color='1/6/5')
        self.assertTrue(light.supports_color)

    def test_supports_color_false(self):
        """Test supports_color false."""
        xknx = XKNX(loop=self.loop)
        light = Light(
            xknx,
            'Diningroom.Light_1',
            group_address_switch='1/6/4')
        self.assertFalse(light.supports_color)

    #
    # SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus. Testing with a Light without dimm functionality."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5',
                      group_address_color='1/2/6')
        self.loop.run_until_complete(asyncio.Task(light.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 3)

        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))

        telegram2 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram2,
                         Telegram(GroupAddress('1/2/6'), TelegramType.GROUP_READ))

        telegram3 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram3,
                         Telegram(GroupAddress('1/2/5'), TelegramType.GROUP_READ))

    #
    # SYNC WITH STATE ADDRESS
    #
    def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus. Testing with a Light with dimm functionality."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_switch_state='1/2/4',
                      group_address_brightness='1/2/5',
                      group_address_brightness_state='1/2/6',
                      group_address_color='1/2/7',
                      group_address_color_state='1/2/8')
        self.loop.run_until_complete(asyncio.Task(light.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 3)

        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))
        telegram2 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram2,
                         Telegram(GroupAddress('1/2/8'), TelegramType.GROUP_READ))
        telegram3 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram3,
                         Telegram(GroupAddress('1/2/6'), TelegramType.GROUP_READ))

    #
    # TEST SET ON
    #
    def test_set_on(self):
        """Test switching on a Light."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.loop.run_until_complete(asyncio.Task(light.set_on()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTBinary(1)))

    #
    # TEST SET OFF
    #
    def test_set_off(self):
        """Test switching off a Light."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.loop.run_until_complete(asyncio.Task(light.set_off()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTBinary(0)))

    #
    # TEST SET BRIGHTNESS
    #
    def test_set_brightness(self):
        """Test setting the brightness of a Light."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.loop.run_until_complete(asyncio.Task(light.set_brightness(23)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/5'), payload=DPTArray(23)))

    def test_set_brightness_not_dimmable(self):
        """Test setting the brightness of a non dimmable Light."""
        # pylint: disable=invalid-name
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3')
        with patch('logging.Logger.warning') as mock_warn:
            self.loop.run_until_complete(asyncio.Task(light.set_brightness(23)))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with('Dimming not supported for device %s', 'TestLight')

    #
    # TEST SET COLOR
    #
    def test_set_color(self):
        """Test setting the color of a Light."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color='1/2/5')
        self.loop.run_until_complete(asyncio.Task(light.set_color((23, 24, 25))))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24, 25))))
        self.assertEqual(light.current_color(), (23, 24, 25))

    def test_set_color_not_possible(self):
        """Test setting the color of a non light without color."""
        # pylint: disable=invalid-name
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3')
        with patch('logging.Logger.warning') as mock_warn:
            self.loop.run_until_complete(asyncio.Task(light.set_color((23, 24, 25))))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with('Colors not supported for device %s', 'TestLight')

    #
    # TEST PROCESS
    #
    def test_process_switch(self):
        """Test process / reading telegrams from telegram queue. Test if switch position is processed correctly."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.assertEqual(light.state, False)

        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTBinary(1))
        self.loop.run_until_complete(asyncio.Task(light.process(telegram)))
        self.assertEqual(light.state, True)

        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTBinary(0))
        self.loop.run_until_complete(asyncio.Task(light.process(telegram)))
        self.assertEqual(light.state, False)

    def test_process_switch_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is called."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)

        light.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTBinary(1))
        self.loop.run_until_complete(asyncio.Task(light.process(telegram)))

        after_update_callback.assert_called_with(light)

    def test_process_dimm(self):
        """Test process / reading telegrams from telegram queue. Test if brightness is processed."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.assertEqual(light.brightness, 0)

        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray(23))
        self.loop.run_until_complete(asyncio.Task(light.process(telegram)))
        self.assertEqual(light.brightness, 23)

    def test_process_dimm_wrong_payload(self):
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTBinary(1))
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(asyncio.Task(light.process(telegram)))

    def test_process_dimm_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        # pylint: disable=invalid-name
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24)))
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(asyncio.Task(light.process(telegram)))

    def test_process_color(self):
        """Test process / reading telegrams from telegram queue. Test if color is processed."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color='1/2/5')
        self.assertEqual(light.current_color(), None)
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24, 25)))
        self.loop.run_until_complete(asyncio.Task(light.process(telegram)))
        self.assertEqual(light.current_color(), (23, 24, 25))

    #
    # TEST DO
    #
    def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.loop.run_until_complete(asyncio.Task(light.do("on")))
        self.assertTrue(light.state)
        self.loop.run_until_complete(asyncio.Task(light.do("brightness:80")))
        self.assertEqual(light.brightness, 80)
        self.loop.run_until_complete(asyncio.Task(light.do("off")))
        self.assertFalse(light.state)

    def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX(loop=self.loop)
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        with patch('logging.Logger.warning') as mock_warn:
            self.loop.run_until_complete(asyncio.Task(light.do("execute")))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with('Could not understand action %s for device %s', 'execute', 'TestLight')

    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX(config='xknx.yaml', loop=self.loop)
        light = Light(
            xknx,
            'Office.Light_1',
            group_address_switch='1/7/1',
            group_address_switch_state='1/7/2',
            group_address_brightness='1/7/3',
            group_address_brightness_state='1/7/4',
            group_address_color='1/7/5',
            group_address_color_state='1/7/6')
        self.assertTrue(light.has_group_address(GroupAddress('1/7/1')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/2')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/3')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/4')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/5')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/6')))
        self.assertFalse(light.has_group_address(GroupAddress('1/7/7')))
