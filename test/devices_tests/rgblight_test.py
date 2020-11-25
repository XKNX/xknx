"""Unit test for Light objects."""
import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import RGBLight
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram, TelegramType


class TestRGBLight(unittest.TestCase):
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
    def test_supports_dimm_no(self):
        """Test supports_dimm attribute with a light with dimmer."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.assertFalse(light.supports_brightness)

    #
    # TEST SUPPORT COLOR
    #
    def test_supports_color_true(self):
        """Test supports_color true."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
        )
        self.assertTrue(light.supports_color)

    def test_supports_color_false(self):
        """Test supports_color false."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
        )
        self.assertFalse(light.supports_color)

    #
    # TEST SUPPORT COLOR RGBW
    #
    def test_supports_rgbw_true(self):
        """Test supports_rgbw true."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.assertTrue(light.supports_rgbw)

    def test_supports_rgbw_false(self):
        """Test supports_color false."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
        )
        self.assertFalse(light.supports_rgbw)

    #
    # TEST SUPPORT TUNABLE WHITE
    #
    def test_supports_tw_no(self):
        """Test supports_tw attribute with a Light without tunable white function."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.assertFalse(light.supports_tunable_white)

    #
    # TEST SUPPORT COLOR TEMPERATURE
    #
    def test_supports_color_temp_false(self):
        """Test supports_color_temp attribute with a light with color temperature function."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.assertFalse(light.supports_color_temperature)

    #
    # SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus. Testing with a Light without dimm functionality."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.loop.run_until_complete(light.sync())

        self.assertEqual(xknx.telegrams.qsize(), 8)

        telegrams = [xknx.telegrams.get_nowait() for _ in range(8)]

        test_telegrams = [
            Telegram(GroupAddress("1/1/2"), TelegramType.GROUP_READ),
            Telegram(GroupAddress("1/1/4"), TelegramType.GROUP_READ),
            Telegram(GroupAddress("1/1/6"), TelegramType.GROUP_READ),
            Telegram(GroupAddress("1/1/8"), TelegramType.GROUP_READ),
            Telegram(GroupAddress("1/1/10"), TelegramType.GROUP_READ),
            Telegram(GroupAddress("1/1/12"), TelegramType.GROUP_READ),
            Telegram(GroupAddress("1/1/14"), TelegramType.GROUP_READ),
            Telegram(GroupAddress("1/1/16"), TelegramType.GROUP_READ),
        ]

        self.assertEqual(len(set(telegrams)), 8)
        self.assertEqual(set(telegrams), set(test_telegrams))

    #
    # TEST SET ON
    #
    def test_set_on(self):
        """Test switching on a Light."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.loop.run_until_complete(light.set_on())
        self.assertEqual(xknx.telegrams.qsize(), 4)

        telegrams = [xknx.telegrams.get_nowait() for _ in range(4)]

        test_telegrams = [
            Telegram(GroupAddress("1/1/1"), payload=DPTBinary(True)),
            Telegram(GroupAddress("1/1/5"), payload=DPTBinary(True)),
            Telegram(GroupAddress("1/1/9"), payload=DPTBinary(True)),
            Telegram(GroupAddress("1/1/13"), payload=DPTBinary(True)),
        ]
        self.assertEqual(len(set(telegrams)), 4)
        self.assertEqual(set(telegrams), set(test_telegrams))

    #
    # TEST SET OFF
    #
    def test_set_off(self):
        """Test switching off a Light."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.loop.run_until_complete(light.set_off())
        self.assertEqual(xknx.telegrams.qsize(), 4)

        telegrams = [xknx.telegrams.get_nowait() for _ in range(4)]

        test_telegrams = [
            Telegram(GroupAddress("1/1/1"), payload=DPTBinary(False)),
            Telegram(GroupAddress("1/1/5"), payload=DPTBinary(False)),
            Telegram(GroupAddress("1/1/9"), payload=DPTBinary(False)),
            Telegram(GroupAddress("1/1/13"), payload=DPTBinary(False)),
        ]
        self.assertEqual(len(set(telegrams)), 4)
        self.assertEqual(set(telegrams), set(test_telegrams))

    #
    # TEST SET COLOR
    #
    def test_set_color(self):
        """Test setting the color of a Light."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
        )
        self.loop.run_until_complete(light.set_color([23, 24, 25]))
        self.assertEqual(xknx.telegrams.qsize(), 3)
        telegrams = [xknx.telegrams.get_nowait() for _ in range(3)]

        test_telegrams = [
            Telegram(GroupAddress("1/1/3"), payload=DPTArray(23)),
            Telegram(GroupAddress("1/1/7"), payload=DPTArray(24)),
            Telegram(GroupAddress("1/1/11"), payload=DPTArray(25)),
        ]

        self.assertEqual(len(set(telegrams)), 3)
        self.assertEqual(set(telegrams), set(test_telegrams))

        self.loop.run_until_complete(
            xknx.devices.process(Telegram(GroupAddress("1/1/4"), payload=DPTArray(23)))
        )
        self.loop.run_until_complete(
            xknx.devices.process(Telegram(GroupAddress("1/1/8"), payload=DPTArray(24)))
        )
        self.loop.run_until_complete(
            xknx.devices.process(Telegram(GroupAddress("1/1/12"), payload=DPTArray(25)))
        )
        self.assertEqual(light.current_color, ([23, 24, 25], None))

    def test_set_color_not_possible(self):
        """Test setting the color of a non light without color."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
        )
        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(light.set_color((23, 24, 25)))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with(
                "Colors not supported for device %s", "TestLight"
            )

    #
    # TEST SET COLOR AS RGBW
    #
    def test_set_color_rgbw(self):
        """Test setting RGBW value of a Light."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.loop.run_until_complete(light.set_color([23, 24, 25], white=26))
        self.assertEqual(xknx.telegrams.qsize(), 4)
        telegrams = [xknx.telegrams.get_nowait() for _ in range(4)]

        test_telegrams = [
            Telegram(GroupAddress("1/1/3"), payload=DPTArray(23)),
            Telegram(GroupAddress("1/1/7"), payload=DPTArray(24)),
            Telegram(GroupAddress("1/1/11"), payload=DPTArray(25)),
            Telegram(GroupAddress("1/1/15"), payload=DPTArray(26)),
        ]

        self.assertEqual(len(set(telegrams)), 4)
        self.assertEqual(set(telegrams), set(test_telegrams))

        self.loop.run_until_complete(
            xknx.devices.process(Telegram(GroupAddress("1/1/4"), payload=DPTArray(23)))
        )
        self.loop.run_until_complete(
            xknx.devices.process(Telegram(GroupAddress("1/1/8"), payload=DPTArray(24)))
        )
        self.loop.run_until_complete(
            xknx.devices.process(Telegram(GroupAddress("1/1/12"), payload=DPTArray(25)))
        )
        self.loop.run_until_complete(
            xknx.devices.process(Telegram(GroupAddress("1/1/16"), payload=DPTArray(26)))
        )
        self.assertEqual(light.current_color, ([23, 24, 25], 26))

    def test_set_color_rgbw_not_possible(self):
        """Test setting RGBW value of a non light without color."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
        )
        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(light.set_color((23, 24, 25), 26))

            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with(
                "RGBW not supported for device %s", "TestLight"
            )

    #
    # TEST PROCESS
    #
    def test_process_switch(self):
        """Test process / reading telegrams from telegram queue. Test if switch position is processed correctly."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
        )
        self.assertEqual(light.state, False)

        telegram = Telegram(GroupAddress("1/1/2"), payload=DPTBinary(True))
        self.loop.run_until_complete(light.process(telegram))
        self.assertEqual(light.state, True)

        telegram = Telegram(GroupAddress("1/1/2"), payload=DPTBinary(False))
        self.loop.run_until_complete(light.process(telegram))
        self.assertEqual(light.state, False)

    def test_process_switch_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is called."""
        # pylint: disable=no-self-use
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
        )

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)

        light.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(GroupAddress("1/1/2"), payload=DPTBinary(True))
        self.loop.run_until_complete(light.process(telegram))

        after_update_callback.assert_called_with(light)

    def test_process_color(self):
        """Test process / reading telegrams from telegram queue. Test if color is processed."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
        )
        self.assertEqual(light.current_color, (None, None))

        telegrams = [
            Telegram(GroupAddress("1/1/4"), payload=DPTArray(42)),
            Telegram(GroupAddress("1/1/8"), payload=DPTArray(43)),
            Telegram(GroupAddress("1/1/12"), payload=DPTArray(44)),
        ]

        for telegram in telegrams:
            self.loop.run_until_complete(light.process(telegram))
        self.assertEqual(light.current_color, ([42, 43, 44], None))

    def test_process_color_rgbw(self):
        """Test process / reading telegrams from telegram queue. Test if RGBW is processed."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.assertEqual(light.current_color, (None, None))
        telegram = Telegram(GroupAddress("1/1/16"), payload=DPTArray(42))
        self.loop.run_until_complete(light.process(telegram))
        self.assertEqual(light.current_color, (None, 42))

    #
    # TEST DO
    #
    def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.loop.run_until_complete(light.do("on"))
        for _ in range(4):
            self.loop.run_until_complete(
                xknx.devices.process(xknx.telegrams.get_nowait())
            )
        self.assertTrue(light.state)

        self.loop.run_until_complete(light.do("off"))
        for _ in range(4):
            self.loop.run_until_complete(
                xknx.devices.process(xknx.telegrams.get_nowait())
            )
        self.assertFalse(light.state)

    def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "TestLight",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        with patch("logging.Logger.warning") as mock_warn:
            # brightness is not supported
            self.loop.run_until_complete(light.do("brightness:80"))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with(
                "Could not understand action %s for device %s",
                "brightness:80",
                "TestLight",
            )

    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        light = RGBLight(
            xknx,
            "Diningroom.Light_1",
            group_address_switch_red="1/1/1",
            group_address_switch_state_red="1/1/2",
            group_address_brightness_red="1/1/3",
            group_address_brightness_state_red="1/1/4",
            group_address_switch_green="1/1/5",
            group_address_switch_state_green="1/1/6",
            group_address_brightness_green="1/1/7",
            group_address_brightness_state_green="1/1/8",
            group_address_switch_blue="1/1/9",
            group_address_switch_state_blue="1/1/10",
            group_address_brightness_blue="1/1/11",
            group_address_brightness_state_blue="1/1/12",
            group_address_switch_white="1/1/13",
            group_address_switch_state_white="1/1/14",
            group_address_brightness_white="1/1/15",
            group_address_brightness_state_white="1/1/16",
        )
        self.assertTrue(light.has_group_address(GroupAddress("1/1/1")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/2")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/3")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/4")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/5")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/6")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/7")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/8")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/9")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/10")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/11")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/12")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/13")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/14")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/15")))
        self.assertTrue(light.has_group_address(GroupAddress("1/1/16")))

        self.assertFalse(light.has_group_address(GroupAddress("1/1/23")))
