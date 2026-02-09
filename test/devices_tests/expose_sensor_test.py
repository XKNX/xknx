"""Unit test for Sensor objects."""

from unittest.mock import AsyncMock, Mock, call

from xknx import XKNX
from xknx.core import XknxConnectionState
from xknx.devices import ExposeSensor
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

from ..conftest import EventLoopClockAdvancer


class TestExposeSensor:
    """Test class for Sensor objects."""

    #
    # STR FUNCTIONS
    #
    async def test_str_binary(self) -> None:
        """Test resolve state with binary sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="binary"
        )
        expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(value=DPTBinary(1)),
            )
        )

        assert expose_sensor.resolve_state() is True
        assert expose_sensor.unit_of_measurement() is None

    async def test_str_percent(self) -> None:
        """Test resolve state with percent sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="percent"
        )

        expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x40,))),
            )
        )

        assert expose_sensor.resolve_state() == 25
        assert expose_sensor.unit_of_measurement() == "%"

    async def test_str_temperature(self) -> None:
        """Test resolve state with temperature sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )

        expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
            )
        )

        assert expose_sensor.resolve_state() == 21.0
        assert expose_sensor.unit_of_measurement() == "°C"

    #
    # TEST SET
    #
    async def test_set_binary(self) -> None:
        """Test set with binary sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="binary"
        )
        await expose_sensor.set(False)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    async def test_set_percent(self) -> None:
        """Test set with percent sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="percent"
        )
        await expose_sensor.set(75)
        assert xknx.telegrams.qsize() == 1

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0xBF,))),
        )

    async def test_set_temperature(self) -> None:
        """Test set with temperature sensor."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )
        await expose_sensor.set(21.0)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
        )

    #
    # TEST PROCESS (GROUP READ)
    #
    async def test_process_binary(self) -> None:
        """Test reading binary expose sensor from bus."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", value_type="binary", group_address="1/2/3"
        )
        expose_sensor.sensor_value.value = True

        telegram = Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        expose_sensor.process(telegram)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTBinary(True)),
        )

    async def test_process_percent(self) -> None:
        """Test reading percent expose sensor from bus."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", value_type="percent", group_address="1/2/3"
        )

        expose_sensor.process(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray((0x40,))),
            )
        )

        telegram = Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        expose_sensor.process(telegram)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0x40,))),
        )

    async def test_process_temperature(self) -> None:
        """Test reading temperature expose sensor from bus."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", value_type="temperature", group_address="1/2/3"
        )
        expose_sensor.sensor_value.value = 21.0

        telegram = Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        expose_sensor.process(telegram)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0x0C, 0x1A))),
        )

    async def test_process_no_respond_to_read(self) -> None:
        """Test expose sensor with respond_to_read set to False."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx,
            "TestSensor",
            value_type="temperature",
            group_address="1/2/3",
            respond_to_read=False,
        )
        expose_sensor.sensor_value.value = 21.0

        telegram = Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        expose_sensor.process(telegram)
        assert xknx.telegrams.qsize() == 0

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self) -> None:
        """Test expose sensor has group address."""
        xknx = XKNX()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", value_type="temperature", group_address="1/2/3"
        )
        assert expose_sensor.has_group_address(GroupAddress("1/2/3"))
        assert not expose_sensor.has_group_address(GroupAddress("1/2/4"))

    #
    # PROCESS CALLBACK
    #
    async def test_process_callback(self) -> None:
        """Test setting value. Test if callback is called."""

        xknx = XKNX()
        after_update_callback = Mock()
        expose_sensor = ExposeSensor(
            xknx, "TestSensor", group_address="1/2/3", value_type="temperature"
        )
        expose_sensor.register_device_updated_cb(after_update_callback)
        xknx.devices.async_add(expose_sensor)

        await expose_sensor.set(21.0)
        xknx.devices.process(xknx.telegrams.get_nowait())
        after_update_callback.assert_called_with(expose_sensor)

    #
    # TEST COOLDOWN
    #
    async def test_cooldown(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test cooldown."""
        xknx = XKNX()
        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        xknx.cemi_handler = AsyncMock()
        await xknx.telegram_queue.start()

        expose_sensor_cd = ExposeSensor(
            xknx,
            "TestSensor",
            group_address="1/2/3",
            value_type="temperature",
            cooldown=10,
        )
        xknx.devices.async_add(expose_sensor_cd)
        expose_sensor_no_cd = ExposeSensor(
            xknx,
            "TestSensor",
            group_address="1/2/4",
            value_type="temperature",
        )
        xknx.devices.async_add(expose_sensor_no_cd)

        await expose_sensor_cd.set(21.0)
        await expose_sensor_no_cd.set(21.0)
        await time_travel(0)
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/3"),
                    payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
                )
            ),
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/4"),
                    payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
                )
            ),
        ]
        xknx.cemi_handler.send_telegram.reset_mock()

        # don't send telegram with same payload twice if cooldown is active
        await expose_sensor_cd.set(21.0)
        await expose_sensor_no_cd.set(21.0)
        await time_travel(0)
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/4"),
                    payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
                )
            ),
        ]

        xknx.cemi_handler.send_telegram.reset_mock()

        await time_travel(10)
        assert xknx.telegrams.qsize() == 0
        xknx.cemi_handler.send_telegram.assert_not_called()

        # different payload after cooldown
        await expose_sensor_cd.set(10.0)
        await expose_sensor_no_cd.set(10.0)
        await time_travel(0)
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/3"),
                    payload=GroupValueWrite(DPTArray((0x03, 0xE8))),
                )
            ),
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/4"),
                    payload=GroupValueWrite(DPTArray((0x03, 0xE8))),
                )
            ),
        ]
        xknx.cemi_handler.send_telegram.reset_mock()
        # different payload in cooldown (payload of 3.111 equals 3.11)
        await expose_sensor_cd.set(3.111)
        await expose_sensor_no_cd.set(3.111)
        await time_travel(0)
        assert expose_sensor_cd._cooldown_task.done() is False
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/4"),
                    payload=GroupValueWrite(DPTArray((0x01, 0x37))),
                )
            ),
        ]
        xknx.cemi_handler.send_telegram.reset_mock()
        assert expose_sensor_cd.sensor_value.value == 10
        await time_travel(10)
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/3"),
                    payload=GroupValueWrite(DPTArray((0x01, 0x37))),
                )
            ),
        ]
        xknx.cemi_handler.send_telegram.reset_mock()
        assert expose_sensor_cd.resolve_state() == 3.11
        await time_travel(10)
        assert expose_sensor_cd._cooldown_task.done()  # done after no change
        xknx.cemi_handler.send_telegram.assert_not_called()

        # reading unsent value
        await expose_sensor_cd.set(10)
        #   first send new value
        await time_travel(0)
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/3"),
                    payload=GroupValueWrite(DPTArray((0x03, 0xE8))),
                )
            ),
        ]
        xknx.cemi_handler.send_telegram.reset_mock()
        #   in cooldown with a new value - receiving a read request
        await expose_sensor_cd.set(21)
        expose_sensor_cd.process(
            Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        )
        await time_travel(0)
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/3"),
                    payload=GroupValueResponse(DPTArray((0x0C, 0x1A))),
                )
            ),
        ]
        xknx.cemi_handler.send_telegram.reset_mock()
        #   after cooldown - new value not sent again (already in GroupValueResponse)
        await time_travel(10)
        xknx.cemi_handler.send_telegram.assert_not_called()

        # no connection blocks cooldown to avoid queueing unsent telegrams
        await expose_sensor_cd.set(20)
        await time_travel(1)
        xknx.cemi_handler.send_telegram.assert_called_once()
        xknx.cemi_handler.send_telegram.reset_mock()
        await expose_sensor_cd.set(30)
        await time_travel(5)
        xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        await time_travel(5)
        await time_travel(10)
        xknx.cemi_handler.send_telegram.assert_not_called()
        assert not expose_sensor_cd._cooldown_task.done()
        await expose_sensor_cd.set(40)
        await time_travel(1)
        await expose_sensor_cd.set(50)
        await time_travel(1)
        await expose_sensor_cd.set(10)
        await time_travel(1)
        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        await time_travel(0)
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(
                Telegram(
                    destination_address=GroupAddress("1/2/3"),
                    payload=GroupValueWrite(DPTArray((0x03, 0xE8))),
                )
            ),
        ]

        await xknx.stop()

    async def test_cooldown_read_request(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test cooldown for read requests."""
        xknx = XKNX()
        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        xknx.cemi_handler = AsyncMock()
        await xknx.telegram_queue.start()

        expose_sensor_cd = ExposeSensor(
            xknx,
            "TestSensor",
            group_address="1/2/3",
            value_type="temperature",
            cooldown=10,
        )
        xknx.devices.async_add(expose_sensor_cd)
        expose_sensor_no_cd = ExposeSensor(
            xknx,
            "TestSensor",
            group_address="1/2/4",
            value_type="temperature",
        )
        xknx.devices.async_add(expose_sensor_no_cd)
        # reading during cooldown sends immediately, response starts cooldown
        await expose_sensor_cd.set(15)
        await time_travel(0)  # 0 after GroupValueWrite
        assert expose_sensor_cd._cooldown_task.done() is False
        xknx.cemi_handler.send_telegram.assert_called_once()
        xknx.cemi_handler.send_telegram.reset_mock()
        await time_travel(5)  # 5 after GroupValueWrite
        #   in cooldown - read request
        expose_sensor_cd.process(
            Telegram(GroupAddress("1/2/3"), payload=GroupValueRead())
        )
        await time_travel(0)  # 5 after GroupValueWrite (0 after GroupValueResponse)
        xknx.cemi_handler.send_telegram.assert_called_once()
        xknx.cemi_handler.send_telegram.reset_mock()
        assert expose_sensor_cd._cooldown_task.done() is False
        await time_travel(7)  # 12 after GroupValueWrite, 7 after GroupValueResponse
        assert expose_sensor_cd._cooldown_task.done() is False
        await time_travel(3)  # 15 after GroupValueWrite, 10 after GroupValueResponse
        assert expose_sensor_cd._cooldown_task.done() is True

        await xknx.stop()

    async def test_set_same_payload(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test expose sensor with similar payloads in cooldown."""
        xknx = XKNX()
        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        expose_sensor = ExposeSensor(
            xknx,
            "TestSensor",
            group_address="1/2/3",
            value_type="temperature",
            cooldown=10,
        )

        telegram_21_degree = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0C, 0x1A))),
        )

        await expose_sensor.set(21.000123, skip_unchanged=True)  # 21.0 when decoded
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == telegram_21_degree

        expose_sensor.process(telegram)
        assert expose_sensor.resolve_state() == 21.0

        # in cooldown, similar payload, no telegram sent
        assert expose_sensor._cooldown_task.done() is False
        await expose_sensor.set(21.000567, skip_unchanged=True)  # 21.0 when decoded
        await time_travel(10)
        assert xknx.telegrams.empty()

        # outside cooldown, similar payload, no telegram sent
        await time_travel(10)
        assert expose_sensor._cooldown_task.done() is True
        await expose_sensor.set(21.00089, skip_unchanged=True)
        assert xknx.telegrams.empty()

        # no cooldown for non-sent telegram, new payload, telegram sent immediately
        assert expose_sensor._cooldown_task.done() is True
        await expose_sensor.set(22.0, skip_unchanged=True)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram.payload.value == DPTArray((0x0C, 0x4C))
        expose_sensor.process(telegram)

        # in cooldown getting new payload and then previous payload again - shall skip sending
        assert expose_sensor._cooldown_task.done() is False
        await expose_sensor.set(21.0, skip_unchanged=True)
        await expose_sensor.set(22.0, skip_unchanged=True)
        await time_travel(10)
        assert xknx.telegrams.empty()

    async def test_periodic_send(
        self,
        xknx_no_interface: XKNX,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test periodic send of expose sensor."""
        xknx = xknx_no_interface
        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        xknx.cemi_handler = AsyncMock()
        expose_sensor = ExposeSensor(
            xknx,
            "TestSensor",
            group_address="1/2/3",
            value_type="switch",
            cooldown=2,
            periodic_send=10,
        )
        xknx.devices.async_add(expose_sensor)
        await xknx.start()

        test_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(True)),
        )

        # uninitialized doesn't send anything
        await time_travel(10)
        xknx.cemi_handler.send_telegram.assert_not_called()

        # set a value - send immediately
        await expose_sensor.set(True)
        await time_travel(0)
        xknx.cemi_handler.send_telegram.assert_called_once_with(test_telegram)
        xknx.cemi_handler.send_telegram.reset_mock()

        # no resend before periodic time
        await time_travel(9)
        xknx.cemi_handler.send_telegram.assert_not_called()

        # resend after periodic time
        await time_travel(1)
        xknx.cemi_handler.send_telegram.assert_called_once_with(test_telegram)
        xknx.cemi_handler.send_telegram.reset_mock()

        # incoming update doesn't reset periodic timer
        await time_travel(7)
        expose_sensor.process(
            Telegram(
                direction=TelegramDirection.INCOMING,
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(True)),
            )
        )
        await time_travel(2)
        xknx.cemi_handler.send_telegram.assert_not_called()
        await time_travel(1)
        xknx.cemi_handler.send_telegram.assert_called_once_with(test_telegram)
        xknx.cemi_handler.send_telegram.reset_mock()

        # outgoing cooldown telegram resets periodic timer
        await time_travel(7)
        await expose_sensor.set(False)
        await expose_sensor.set(True)  # within cooldown
        await time_travel(0)
        xknx.cemi_handler.send_telegram.assert_called_once()  # with False, second is in cooldown
        xknx.cemi_handler.send_telegram.reset_mock()
        await time_travel(2)
        xknx.cemi_handler.send_telegram.assert_called_once_with(test_telegram)
        xknx.cemi_handler.send_telegram.reset_mock()
        #    after cooldown, periodic timer reset - wait full periodic time
        await time_travel(9)
        xknx.cemi_handler.send_telegram.assert_not_called()
        await time_travel(1)
        xknx.cemi_handler.send_telegram.assert_called_once_with(test_telegram)
        xknx.cemi_handler.send_telegram.reset_mock()
        #    periodic telegram triggers cooldown
        await expose_sensor.set(False)
        await time_travel(0)
        xknx.cemi_handler.send_telegram.assert_not_called()
        xknx.cemi_handler.send_telegram.reset_mock()
        await time_travel(2)
        xknx.cemi_handler.send_telegram.assert_called_once_with(
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(False)),
            )
        )
        xknx.cemi_handler.send_telegram.reset_mock()
        # don't try to send without connection
        xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        await time_travel(10)
        xknx.cemi_handler.send_telegram.assert_not_called()

        await xknx.stop()
