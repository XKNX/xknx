"""Unit test for Light objects."""
from unittest.mock import Mock, patch
import pytest

from xknx import XKNX
from xknx.devices import Light
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram, TelegramType

from xknx._test import Testcase

class TestLight(Testcase):
    """Class for testing Light objects."""

    # pylint: disable=too-many-public-methods

    #
    # TEST SUPPORT DIMMING
    #
    @pytest.mark.anyio
    async def test_supports_dimm_yes(self):
        """Test supports_dimm attribute with a light with dimmer."""
        xknx = XKNX()
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4',
                      group_address_brightness='1/6/6')
        self.assertTrue(light.supports_brightness)

    @pytest.mark.anyio
    async def test_supports_dimm_no(self):
        """Test supports_dimm attribute with a Light without dimmer."""
        xknx = XKNX()
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4')
        self.assertFalse(light.supports_brightness)

    #
    # TEST SUPPORT COLOR
    #
    @pytest.mark.anyio
    async def test_supports_color_true(self):
        """Test supports_color true."""
        xknx = XKNX()
        light = Light(
            xknx,
            'Diningroom.Light_1',
            group_address_switch='1/6/4',
            group_address_color='1/6/5')
        self.assertTrue(light.supports_color)

    @pytest.mark.anyio
    async def test_supports_color_false(self):
        """Test supports_color false."""
        xknx = XKNX()
        light = Light(
            xknx,
            'Diningroom.Light_1',
            group_address_switch='1/6/4')
        self.assertFalse(light.supports_color)

    #
    # TEST SUPPORT COLOR RGBW
    #
    @pytest.mark.anyio
    async def test_supports_rgbw_true(self):
        """Test supports_rgbw true."""
        xknx = XKNX()
        light = Light(
            xknx,
            'Diningroom.Light_1',
            group_address_switch='1/6/4',
            group_address_rgbw='1/6/5',
            group_address_color='1/6/6')
        self.assertTrue(light.supports_rgbw)

    @pytest.mark.anyio
    async def test_supports_rgbw_false(self):
        """Test supports_color false."""
        xknx = XKNX()
        light = Light(
            xknx,
            'Diningroom.Light_1',
            group_address_switch='1/6/4',
            group_address_color='1/6/6')
        self.assertFalse(light.supports_rgbw)

    #
    # TEST SUPPORT TUNABLE WHITE
    #
    @pytest.mark.anyio
    async def test_supports_tw_yes(self):
        """Test supports_tw attribute with a light with tunable white function."""
        xknx = XKNX()
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4',
                      group_address_tunable_white='1/6/6')
        self.assertTrue(light.supports_tunable_white)

    @pytest.mark.anyio
    async def test_supports_tw_no(self):
        """Test supports_tw attribute with a Light without tunable white function."""
        xknx = XKNX()
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4')
        self.assertFalse(light.supports_tunable_white)

    #
    # TEST SUPPORT COLOR TEMPERATURE
    #
    @pytest.mark.anyio
    async def test_supports_color_temp_true(self):
        """Test supports_color_temp attribute with a light with color temperature function."""
        xknx = XKNX()
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4',
                      group_address_color_temperature='1/6/6')
        self.assertTrue(light.supports_color_temperature)

    @pytest.mark.anyio
    async def test_supports_color_temp_false(self):
        """Test supports_color_temp attribute with a Light without color temperature function."""
        xknx = XKNX()
        light = Light(xknx,
                      'Diningroom.Light_1',
                      group_address_switch='1/6/4')
        self.assertFalse(light.supports_color_temperature)

    #
    # SYNC
    #
    @pytest.mark.anyio
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus. Testing with a Light without dimm functionality."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch_state='1/2/3',
                      group_address_brightness_state='1/2/5',
                      group_address_color_state='1/2/6',
                      group_address_tunable_white_state='1/2/7',
                      group_address_color_temperature_state='1/2/8',
                      group_address_rgbw_state='1/2/9')
        await light.sync(False)

        self.assertEqual(xknx.telegrams_out.qsize(), 6)

        telegram1 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))

        telegram2 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram2,
                         Telegram(GroupAddress('1/2/6'), TelegramType.GROUP_READ))

        telegram6 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram6,
                         Telegram(GroupAddress('1/2/9'), TelegramType.GROUP_READ))

        telegram3 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram3,
                         Telegram(GroupAddress('1/2/5'), TelegramType.GROUP_READ))

        telegram4 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram4,
                         Telegram(GroupAddress('1/2/7'), TelegramType.GROUP_READ))

        telegram5 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram5,
                         Telegram(GroupAddress('1/2/8'), TelegramType.GROUP_READ))

    #
    # SYNC WITH STATE ADDRESS
    #
    @pytest.mark.anyio
    async def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus. Testing with a Light with dimm functionality."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_switch_state='1/2/4',
                      group_address_brightness='1/2/5',
                      group_address_brightness_state='1/2/6',
                      group_address_color='1/2/7',
                      group_address_color_state='1/2/8',
                      group_address_tunable_white='1/2/9',
                      group_address_tunable_white_state='1/2/10',
                      group_address_color_temperature='1/2/11',
                      group_address_color_temperature_state='1/2/12',
                      group_address_rgbw='1/2/13',
                      group_address_rgbw_state='1/2/14')
        await light.sync(False)

        self.assertEqual(xknx.telegrams_out.qsize(), 6)

        telegram1 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))
        telegram2 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram2,
                         Telegram(GroupAddress('1/2/8'), TelegramType.GROUP_READ))
        telegram6 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram6,
                         Telegram(GroupAddress('1/2/14'), TelegramType.GROUP_READ))
        telegram3 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram3,
                         Telegram(GroupAddress('1/2/6'), TelegramType.GROUP_READ))
        telegram4 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram4,
                         Telegram(GroupAddress('1/2/10'), TelegramType.GROUP_READ))
        telegram5 = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram5,
                         Telegram(GroupAddress('1/2/12'), TelegramType.GROUP_READ))

    #
    # TEST SET ON
    #
    @pytest.mark.anyio
    async def test_set_on(self):
        """Test switching on a Light."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        await light.set_on()
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTBinary(1)))

    #
    # TEST SET OFF
    #
    @pytest.mark.anyio
    async def test_set_off(self):
        """Test switching off a Light."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        await light.set_off()
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTBinary(0)))

    #
    # TEST SET BRIGHTNESS
    #
    @pytest.mark.anyio
    async def test_set_brightness(self):
        """Test setting the brightness of a Light."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        await light.set_brightness(23)
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/5'), payload=DPTArray(23)))

    @pytest.mark.anyio
    async def test_set_brightness_not_dimmable(self):
        """Test setting the brightness of a non dimmable Light."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3')
        with patch('logging.Logger.warning') as mock_warn:
            await light.set_brightness(23)
            self.assertEqual(xknx.telegrams_out.qsize(), 0)
            mock_warn.assert_called_with('Dimming not supported for device %s', 'TestLight')

    #
    # TEST SET COLOR
    #
    @pytest.mark.anyio
    async def test_set_color(self):
        """Test setting the color of a Light."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color='1/2/5')
        await light.set_color((23, 24, 25))
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24, 25))))
        self.assertEqual(light.current_color, ((23, 24, 25), None))

    @pytest.mark.anyio
    async def test_set_color_not_possible(self):
        """Test setting the color of a non light without color."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3')
        with patch('logging.Logger.warning') as mock_warn:
            await light.set_color((23, 24, 25))
            self.assertEqual(xknx.telegrams_out.qsize(), 0)
            mock_warn.assert_called_with('Colors not supported for device %s', 'TestLight')

    #
    # TEST SET COLOR AS RGBW
    #
    @pytest.mark.anyio
    async def test_set_color_rgbw(self):
        """Test setting RGBW value of a Light."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color='1/2/4',
                      group_address_rgbw='1/2/5')
        await light.set_color((23, 24, 25), 26)
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24, 25, 26, 0, 15))))
        self.assertEqual(light.current_color, ([23, 24, 25], 26))

    @pytest.mark.anyio
    async def test_set_color_rgbw_not_possible(self):
        """Test setting RGBW value of a non light without color."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color='1/2/4')
        with patch('logging.Logger.warning') as mock_warn:
            await light.set_color((23, 24, 25), 26)
            self.assertEqual(xknx.telegrams_out.qsize(), 0)
            mock_warn.assert_called_with('RGBW not supported for device %s', 'TestLight')

    #
    # TEST SET TUNABLE WHITE
    #
    @pytest.mark.anyio
    async def test_set_tw(self):
        """Test setting the tunable white value of a Light."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_tunable_white='1/2/5')
        await light.set_tunable_white(23)
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/5'), payload=DPTArray(23)))

    @pytest.mark.anyio
    async def test_set_tw_unsupported(self):
        """Test setting the tunable white value of a non tw Light."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3')
        with patch('logging.Logger.warning') as mock_warn:
            await light.set_tunable_white(23)
            self.assertEqual(xknx.telegrams_out.qsize(), 0)
            mock_warn.assert_called_with('Tunable white not supported for device %s', 'TestLight')

    #
    # TEST SET COLOR TEMPERATURE
    #
    @pytest.mark.anyio
    async def test_set_color_temp(self):
        """Test setting the color temperature value of a Light."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color_temperature='1/2/5')
        await light.set_color_temperature(4000)
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/5'), payload=DPTArray((0x0F, 0xA0, ))))

    @pytest.mark.anyio
    async def test_set_color_temp_unsupported(self):
        """Test setting the color temperature value of an unsupported Light."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3')
        with patch('logging.Logger.warning') as mock_warn:
            await light.set_color_temperature(4000)
            self.assertEqual(xknx.telegrams_out.qsize(), 0)
            mock_warn.assert_called_with('Absolute Color Temperature not supported for device %s', 'TestLight')

    #
    # TEST PROCESS
    #
    @pytest.mark.anyio
    async def test_process_switch(self):
        """Test process / reading telegrams from telegram queue. Test if switch position is processed correctly."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.assertEqual(light.state, False)

        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTBinary(1))
        await light.process(telegram)
        self.assertEqual(light.state, True)

        telegram = Telegram(GroupAddress('1/2/3'), payload=DPTBinary(0))
        await light.process(telegram)
        self.assertEqual(light.state, False)

    @pytest.mark.anyio
    async def test_process_switch_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is called."""
        # pylint: disable=no-self-use
        xknx = XKNX()
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
        await light.process(telegram)

        after_update_callback.assert_called_with(light)

    @pytest.mark.anyio
    async def test_process_dimm(self):
        """Test process / reading telegrams from telegram queue. Test if brightness is processed."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        self.assertEqual(light.current_brightness, None)

        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray(23))
        await light.process(telegram)
        self.assertEqual(light.current_brightness, 23)

    @pytest.mark.anyio
    async def test_process_dimm_wrong_payload(self):
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTBinary(1))
        with self.assertRaises(CouldNotParseTelegram):
            await light.process(telegram)

    @pytest.mark.anyio
    async def test_process_dimm_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24)))
        with self.assertRaises(CouldNotParseTelegram):
            await light.process(telegram)

    @pytest.mark.anyio
    async def test_process_color(self):
        """Test process / reading telegrams from telegram queue. Test if color is processed."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color='1/2/5')
        self.assertEqual(light.current_color, (None, None))
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24, 25)))
        await light.process(telegram)
        self.assertEqual(light.current_color, ((23, 24, 25), None))

    @pytest.mark.anyio
    async def test_process_color_rgbw(self):
        """Test process / reading telegrams from telegram queue. Test if RGBW is processed."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color='1/2/4',
                      group_address_rgbw='1/2/5')
        self.assertEqual(light.current_color, (None, None))
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24, 25, 26, 0, 15)))
        await light.process(telegram)
        self.assertEqual(light.current_color, ([23, 24, 25], 26))

    @pytest.mark.anyio
    async def test_process_tunable_white(self):
        """Test process / reading telegrams from telegram queue. Test if tunable white is processed."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_tunable_white='1/2/5')
        self.assertEqual(light.current_tunable_white, None)

        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray(23))
        await light.process(telegram)
        self.assertEqual(light.current_tunable_white, 23)

    @pytest.mark.anyio
    async def test_process_tunable_white_wrong_payload(self):
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_tunable_white='1/2/5')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTBinary(1))
        with self.assertRaises(CouldNotParseTelegram):
            await light.process(telegram)

    @pytest.mark.anyio
    async def test_process_tunable_white_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_tunable_white='1/2/5')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray((23, 24)))
        with self.assertRaises(CouldNotParseTelegram):
            await light.process(telegram)

    @pytest.mark.anyio
    async def test_process_color_temperature(self):
        """Test process / reading telegrams from telegram queue. Test if color temperature is processed."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color_temperature='1/2/5')
        self.assertEqual(light.current_color_temperature, None)

        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray((0x0F, 0xA0, )))
        await light.process(telegram)
        self.assertEqual(light.current_color_temperature, 4000)

    @pytest.mark.anyio
    async def test_process_color_temperature_wrong_payload(self):
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color_temperature='1/2/5')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTBinary(1))
        with self.assertRaises(CouldNotParseTelegram):
            await light.process(telegram)

    @pytest.mark.anyio
    async def test_process_color_temperature_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_color_temperature='1/2/5')
        telegram = Telegram(GroupAddress('1/2/5'), payload=DPTArray((23)))
        with self.assertRaises(CouldNotParseTelegram):
            await light.process(telegram)

    #
    # TEST DO
    #
    @pytest.mark.anyio
    async def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5',
                      group_address_tunable_white='1/2/9',
                      group_address_color_temperature='1/2/11')
        await light.do("on")
        self.assertTrue(light.state)
        await light.do("brightness:80")
        self.assertEqual(light.current_brightness, 80)
        await light.do("tunable_white:80")
        self.assertEqual(light.current_tunable_white, 80)
        await light.do("color_temperature:3750")
        self.assertEqual(light.current_color_temperature, 3750)
        await light.do("off")
        self.assertFalse(light.state)

    @pytest.mark.anyio
    async def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        light = Light(xknx,
                      name="TestLight",
                      group_address_switch='1/2/3',
                      group_address_brightness='1/2/5')
        with patch('logging.Logger.warning') as mock_warn:
            await light.do("execute")
            self.assertEqual(xknx.telegrams_out.qsize(), 0)
            mock_warn.assert_called_with('Could not understand action %s for device %s', 'execute', 'TestLight')

    @pytest.mark.anyio
    async def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        light = Light(
            xknx,
            'Office.Light_1',
            group_address_switch='1/7/1',
            group_address_switch_state='1/7/2',
            group_address_brightness='1/7/3',
            group_address_brightness_state='1/7/4',
            group_address_color='1/7/5',
            group_address_color_state='1/7/6',
            group_address_tunable_white='1/7/7',
            group_address_tunable_white_state='1/7/8',
            group_address_color_temperature='1/7/9',
            group_address_color_temperature_state='1/7/10',
            group_address_rgbw='1/7/11',
            group_address_rgbw_state='1/7/12',)
        self.assertTrue(light.has_group_address(GroupAddress('1/7/1')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/2')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/3')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/4')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/5')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/6')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/7')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/8')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/9')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/10')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/11')))
        self.assertTrue(light.has_group_address(GroupAddress('1/7/12')))
        self.assertFalse(light.has_group_address(GroupAddress('1/7/13')))
