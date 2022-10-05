"""Test Secure Group."""
import asyncio
from unittest.mock import patch

from xknx.io.const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT, XKNX_SERIAL_NUMBER
from xknx.io.ip_secure import SecureGroup
from xknx.knxip import HPAI, KNXIPFrame, SecureWrapper, TimerNotify

ONE_HOUR_MS = 60 * 60 * 1000


@patch("xknx.io.transport.udp_transport.UDPTransport.connect")
@patch("xknx.io.transport.udp_transport.UDPTransport.send")
class TestSecureGroup:
    """Test class for xknx/io/SecureGroup objects."""

    mock_addr = ("127.0.0.1", 12345)
    mock_backbone_key = bytes.fromhex(
        "0a a2 27 b4 fd 7a 32 31 9b a9 96 0a c0 36 ce 0e"
        "5c 45 07 b5 ae 55 16 1f 10 78 b1 dc fb 3c b6 31"
    )

    def assert_timer_notify(
        self,
        knxipframe,
        timer_value=None,
        serial_number=None,
        message_tag=None,
        mac=None,
    ) -> bytes:
        """Assert that knxipframe is a TimerNotify."""
        assert isinstance(knxipframe.body, TimerNotify)
        if timer_value is not None:
            assert knxipframe.body.timer_value == timer_value
        if serial_number is not None:
            assert knxipframe.body.serial_number == serial_number
        if message_tag is not None:
            assert knxipframe.body.message_tag == message_tag
        if mac is not None:
            assert knxipframe.body.message_authentication_code == mac
        return knxipframe.body.message_tag

    async def test_no_synchronize(
        self,
        mock_super_send,
        mock_super_connect,
        time_travel,
    ):
        """Test synchronisazion not answered."""
        secure_group = SecureGroup(
            local_addr=self.mock_addr,
            remote_addr=(DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            backbone_key=self.mock_backbone_key,
            latency_ms=1000,
        )
        connect_task = asyncio.create_task(secure_group.connect())
        await time_travel(0)
        mock_super_connect.assert_called_once()
        self.assert_timer_notify(
            mock_super_send.call_args[0][0],
            serial_number=XKNX_SERIAL_NUMBER,
        )
        mock_super_send.reset_mock()
        # synchronize timed out
        await time_travel(
            secure_group.secure_timer.max_delay_time_follower_update_notify
            + 2 * secure_group.secure_timer.latency_tolerance_ms / 1000
        )
        assert connect_task.done()
        # we are timekeeper so we send TimerNotify after time_keeper_periodic
        assert secure_group.secure_timer.timekeeper
        await time_travel(
            secure_group.secure_timer.min_delay_time_keeper_periodic_notify - 0.01
        )
        mock_super_send.assert_not_called()
        await time_travel(
            secure_group.secure_timer.sync_latency_tolerance_ms / 1000 * 3 + 0.02
        )
        self.assert_timer_notify(
            mock_super_send.call_args[0][0],
            serial_number=XKNX_SERIAL_NUMBER,
        )
        secure_group.stop()
        assert secure_group.secure_timer._notify_timer_handle is None

    async def test_synchronize(
        self,
        mock_super_send,
        mock_super_connect,
        time_travel,
    ):
        """Test synchronisazion."""
        secure_group = SecureGroup(
            local_addr=self.mock_addr,
            remote_addr=(DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            backbone_key=self.mock_backbone_key,
            latency_ms=1000,
        )
        connect_task = asyncio.create_task(secure_group.connect())
        await time_travel(0)
        mock_super_connect.assert_called_once()
        _message_tag = self.assert_timer_notify(
            mock_super_send.call_args[0][0],
            serial_number=XKNX_SERIAL_NUMBER,
        )
        mock_super_send.reset_mock()
        # incoming
        timer_update = KNXIPFrame.init_from_body(
            TimerNotify(
                timer_value=ONE_HOUR_MS,
                serial_number=XKNX_SERIAL_NUMBER,
                message_tag=_message_tag,
            )
        )
        secure_group.handle_knxipframe(timer_update, HPAI(*self.mock_addr))
        await time_travel(0)
        assert secure_group.secure_timer.current_timer_value() == ONE_HOUR_MS
        assert connect_task.done()
        # nothing sent until time_follower_periodic
        assert not secure_group.secure_timer.timekeeper
        await time_travel(
            secure_group.secure_timer.min_delay_time_follower_periodic_notify - 0.01
        )
        mock_super_send.assert_not_called()
        await time_travel(
            secure_group.secure_timer.sync_latency_tolerance_ms / 1000 * 10 + 0.02
        )
        self.assert_timer_notify(
            mock_super_send.call_args[0][0],
            serial_number=XKNX_SERIAL_NUMBER,
        )
        mock_super_send.reset_mock()
        secure_group.stop()
        assert secure_group.secure_timer._notify_timer_handle is None

    @patch("xknx.io.ip_secure.SecureSequenceTimer._notify_timer_expired")
    @patch("xknx.io.ip_secure.SecureSequenceTimer._monotonic_ms")
    async def test_received_timer_notify(
        self,
        mock_monotonic_ms,
        _mock_notify_timer_expired,  # we don't want to actually send here
        mock_super_send,
        mock_super_connect,
        time_travel,
    ):
        """Test handling of received TimerNotify frames."""
        mock_monotonic_ms.return_value = 0
        secure_group = SecureGroup(
            local_addr=self.mock_addr,
            remote_addr=(DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            backbone_key=self.mock_backbone_key,
            latency_ms=1000,
        )
        secure_timer = secure_group.secure_timer

        with patch.object(
            secure_timer, "reschedule", wraps=secure_timer.reschedule
        ) as mock_reschedule:
            # E1
            timer_newer = KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=ONE_HOUR_MS,
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                )
            )
            secure_group.handle_knxipframe(timer_newer, HPAI(*self.mock_addr))
            mock_reschedule.assert_called_once()
            assert ONE_HOUR_MS == secure_timer.current_timer_value()
            assert not secure_timer.timekeeper
            assert not secure_timer.sched_update
            mock_reschedule.reset_mock()
            # E2
            timer_exact = KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=ONE_HOUR_MS,
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                )
            )
            secure_group.handle_knxipframe(timer_exact, HPAI(*self.mock_addr))
            mock_reschedule.assert_called_once()
            assert ONE_HOUR_MS == secure_timer.current_timer_value()
            assert not secure_timer.timekeeper
            assert not secure_timer.sched_update
            mock_reschedule.reset_mock()

            timer_valid = KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=ONE_HOUR_MS
                    - secure_timer.sync_latency_tolerance_ms
                    + 1,
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                )
            )
            secure_group.handle_knxipframe(timer_valid, HPAI(*self.mock_addr))
            mock_reschedule.assert_called_once()
            assert ONE_HOUR_MS == secure_timer.current_timer_value()
            assert not secure_timer.timekeeper
            assert not secure_timer.sched_update
            mock_reschedule.reset_mock()
            # E3
            timer_tolerable_1 = KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=ONE_HOUR_MS - secure_timer.sync_latency_tolerance_ms,
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                )
            )
            secure_group.handle_knxipframe(timer_tolerable_1, HPAI(*self.mock_addr))
            mock_reschedule.assert_not_called()

            timer_tolerable_2 = KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=ONE_HOUR_MS - secure_timer.latency_tolerance_ms + 1,
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                )
            )
            secure_group.handle_knxipframe(timer_tolerable_2, HPAI(*self.mock_addr))
            mock_reschedule.assert_not_called()
            # E4
            timer_invalid = KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=ONE_HOUR_MS - secure_timer.latency_tolerance_ms,
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                )
            )
            secure_group.handle_knxipframe(timer_invalid, HPAI(*self.mock_addr))
            mock_reschedule.assert_called_once_with(
                update=(bytes.fromhex("12 34"), bytes.fromhex("00 fa 12 34 56 78"))
            )
            assert not secure_timer.timekeeper
            assert secure_timer.sched_update
            mock_reschedule.reset_mock()
            # E4 from sched_update
            secure_group.handle_knxipframe(timer_invalid, HPAI(*self.mock_addr))
            mock_reschedule.assert_not_called()

    @patch("xknx.io.ip_secure.SecureSequenceTimer._notify_timer_expired")
    @patch("xknx.io.ip_secure.SecureSequenceTimer._monotonic_ms")
    @patch("xknx.io.transport.udp_transport.UDPTransport.handle_knxipframe")
    async def test_received_secure_wrapper(
        self,
        mock_super_handle_knxipframe,
        mock_monotonic_ms,
        _mock_notify_timer_expired,  # we don't want to actually send here
        mock_super_send,
        mock_super_connect,
        time_travel,
    ):
        """Test handling of received TimerNotify frames."""
        mock_monotonic_ms.return_value = 0
        secure_group = SecureGroup(
            local_addr=self.mock_addr,
            remote_addr=(DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            backbone_key=self.mock_backbone_key,
            latency_ms=1000,
        )
        secure_timer = secure_group.secure_timer
        secure_timer.timer_authenticated = True

        with patch.object(
            secure_timer, "reschedule", wraps=secure_timer.reschedule
        ) as mock_reschedule, patch.object(
            secure_group, "decrypt_frame"
        ) as mock_decrypt:
            mock_decrypt.return_value = True  # we are only interested in timer value
            # E5
            wrapper_newer = KNXIPFrame.init_from_body(
                SecureWrapper(
                    sequence_information=ONE_HOUR_MS.to_bytes(6, "big"),
                )
            )

            secure_group.handle_knxipframe(wrapper_newer, HPAI(*self.mock_addr))
            mock_super_handle_knxipframe.assert_called_once()
            mock_super_handle_knxipframe.reset_mock()
            mock_reschedule.assert_called_once()
            assert ONE_HOUR_MS == secure_timer.current_timer_value()
            assert not secure_timer.sched_update
            mock_reschedule.reset_mock()
            # E6
            wrapper_exact = KNXIPFrame.init_from_body(
                SecureWrapper(sequence_information=ONE_HOUR_MS.to_bytes(6, "big"))
            )

            secure_group.handle_knxipframe(wrapper_exact, HPAI(*self.mock_addr))
            mock_super_handle_knxipframe.assert_called_once()
            mock_super_handle_knxipframe.reset_mock()
            mock_reschedule.assert_called_once()
            assert ONE_HOUR_MS == secure_timer.current_timer_value()
            assert not secure_timer.timekeeper
            assert not secure_timer.sched_update
            mock_reschedule.reset_mock()

            wrapper_valid = KNXIPFrame.init_from_body(
                SecureWrapper(
                    sequence_information=(
                        ONE_HOUR_MS - secure_timer.sync_latency_tolerance_ms + 1
                    ).to_bytes(6, "big")
                )
            )

            secure_group.handle_knxipframe(wrapper_valid, HPAI(*self.mock_addr))
            mock_super_handle_knxipframe.assert_called_once()
            mock_super_handle_knxipframe.reset_mock()
            mock_reschedule.assert_called_once()
            assert ONE_HOUR_MS == secure_timer.current_timer_value()
            assert not secure_timer.timekeeper
            assert not secure_timer.sched_update
            mock_reschedule.reset_mock()
            # E7
            wrapper_tolerable_1 = KNXIPFrame.init_from_body(
                SecureWrapper(
                    sequence_information=(
                        ONE_HOUR_MS - secure_timer.sync_latency_tolerance_ms
                    ).to_bytes(6, "big"),
                )
            )

            secure_group.handle_knxipframe(wrapper_tolerable_1, HPAI(*self.mock_addr))
            mock_super_handle_knxipframe.assert_called_once()
            mock_super_handle_knxipframe.reset_mock()
            mock_reschedule.assert_not_called()

            wrapper_tolerable_2 = KNXIPFrame.init_from_body(
                SecureWrapper(
                    sequence_information=(
                        ONE_HOUR_MS - secure_timer.latency_tolerance_ms + 1
                    ).to_bytes(6, "big"),
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                )
            )

            secure_group.handle_knxipframe(wrapper_tolerable_2, HPAI(*self.mock_addr))
            mock_super_handle_knxipframe.assert_called_once()
            mock_super_handle_knxipframe.reset_mock()
            mock_reschedule.assert_not_called()
            # E8
            wrapper_invalid = KNXIPFrame.init_from_body(
                SecureWrapper(
                    sequence_information=(
                        ONE_HOUR_MS - secure_timer.latency_tolerance_ms
                    ).to_bytes(6, "big"),
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                )
            )

            secure_group.handle_knxipframe(wrapper_invalid, HPAI(*self.mock_addr))
            mock_reschedule.assert_called_once_with(
                update=(bytes.fromhex("12 34"), bytes.fromhex("00 fa 12 34 56 78"))
            )
            assert not secure_timer.timekeeper
            assert secure_timer.sched_update
            mock_reschedule.reset_mock()
            # E8 from sched_update
            secure_group.handle_knxipframe(wrapper_invalid, HPAI(*self.mock_addr))
            mock_super_handle_knxipframe.assert_not_called()
            mock_reschedule.assert_not_called()
