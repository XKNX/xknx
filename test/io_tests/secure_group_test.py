"""Test Secure Group."""
import asyncio
from unittest.mock import Mock, patch

from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.io.const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT, XKNX_SERIAL_NUMBER
from xknx.io.ip_secure import SecureGroup
from xknx.knxip import HPAI, KNXIPFrame, RoutingIndication, SecureWrapper, TimerNotify
from xknx.telegram import GroupAddress, Telegram, apci

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
        secure_timer = secure_group.secure_timer
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
            secure_timer.max_delay_time_follower_update_notify
            + 2 * secure_timer.latency_tolerance_ms / 1000
        )
        assert connect_task.done()
        # we are timekeeper so we send TimerNotify after time_keeper_periodic
        assert secure_timer.timekeeper
        assert not secure_timer.sched_update
        await time_travel(secure_timer.min_delay_time_keeper_periodic_notify - 0.01)
        mock_super_send.assert_not_called()
        await time_travel(secure_timer.sync_latency_tolerance_ms / 1000 * 3 + 0.02)
        self.assert_timer_notify(
            mock_super_send.call_args[0][0],
            serial_number=XKNX_SERIAL_NUMBER,
        )
        mock_super_send.reset_mock()
        # test response to invalid timer as timekeeper
        timer_invalid = KNXIPFrame.init_from_body(
            TimerNotify(
                timer_value=0,
                serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                message_tag=bytes.fromhex("12 34"),
                message_authentication_code=bytes.fromhex(
                    "3195051bb981941d57e6c5b55355f341"
                ),
            )
        )
        secure_group.handle_knxipframe(timer_invalid, HPAI(*self.mock_addr))
        assert secure_timer.timekeeper
        assert secure_timer.sched_update
        await time_travel(secure_timer.min_delay_time_keeper_update_notify - 0.01)
        mock_super_send.assert_not_called()
        await time_travel(secure_timer.sync_latency_tolerance_ms / 1000 * 1 + 0.02)
        self.assert_timer_notify(
            mock_super_send.call_args[0][0],
            message_tag=bytes.fromhex("12 34"),
            serial_number=bytes.fromhex("00 fa 12 34 56 78"),
        )
        # stop
        secure_group.stop()
        assert secure_timer._notify_timer_handle is None

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
        secure_timer = secure_group.secure_timer
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
        with patch("xknx.io.ip_secure.SecureSequenceTimer.verify_timer_notify_mac"):
            # TimerNotify MAC is random so we don't verify it in tests
            secure_group.handle_knxipframe(timer_update, HPAI(*self.mock_addr))
        await time_travel(0)
        _leeway_for_ci = 50  # ms
        assert (
            ONE_HOUR_MS
            <= secure_timer.current_timer_value()
            <= ONE_HOUR_MS + _leeway_for_ci
        )
        assert connect_task.done()
        # nothing sent until time_follower_periodic
        assert not secure_timer.timekeeper
        await time_travel(secure_timer.min_delay_time_follower_periodic_notify - 0.01)
        mock_super_send.assert_not_called()
        await time_travel(secure_timer.sync_latency_tolerance_ms / 1000 * 10 + 0.02)
        self.assert_timer_notify(
            mock_super_send.call_args[0][0],
            serial_number=XKNX_SERIAL_NUMBER,
        )
        mock_super_send.reset_mock()
        secure_group.stop()
        assert secure_timer._notify_timer_handle is None

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
            # TimerNotify with invalid MAC shall be discarded
            timer_invalid_mac = KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=ONE_HOUR_MS,
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                )
            )
            secure_group.handle_knxipframe(timer_invalid_mac, HPAI(*self.mock_addr))
            mock_reschedule.assert_not_called()
            # E1
            timer_newer = KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=ONE_HOUR_MS,
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                    message_authentication_code=bytes.fromhex(
                        "d2fad5657a5788a36cdd8a3ef84c90ab"
                    ),
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
                    message_authentication_code=bytes.fromhex(
                        "d2fad5657a5788a36cdd8a3ef84c90ab"
                    ),
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
                    message_authentication_code=bytes.fromhex(
                        "7572b70b4f986d7ae68891a00c0d46d3"
                    ),
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
                    message_authentication_code=bytes.fromhex(
                        "3d70cc44607ad9b4a4425de95101a54c"
                    ),
                )
            )
            secure_group.handle_knxipframe(timer_tolerable_1, HPAI(*self.mock_addr))
            mock_reschedule.assert_not_called()

            timer_tolerable_2 = KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=ONE_HOUR_MS - secure_timer.latency_tolerance_ms + 1,
                    serial_number=bytes.fromhex("00 fa 12 34 56 78"),
                    message_tag=bytes.fromhex("12 34"),
                    message_authentication_code=bytes.fromhex(
                        "66b8b2e52196bcce3dce2da7e0dc50ec"
                    ),
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
                    message_authentication_code=bytes.fromhex(
                        "873d9a5a25b8508446bbd5ff1bb4b465"
                    ),
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

    @patch("xknx.io.ip_secure.SecureSequenceTimer._notify_timer_expired")
    @patch("xknx.io.ip_secure.SecureSequenceTimer._monotonic_ms")
    @patch("xknx.io.transport.udp_transport.UDPTransport.handle_knxipframe")
    async def test_send_secure_wrapper(
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

        raw_test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=GroupAddress("1/2/3"),
                    payload=apci.GroupValueRead(),
                )
            ),
        ).to_knx()

        with patch.object(
            secure_timer, "reschedule", wraps=secure_timer.reschedule
        ) as mock_reschedule:
            assert not secure_timer.sched_update
            secure_group.send(
                KNXIPFrame.init_from_body(RoutingIndication(raw_cemi=raw_test_cemi))
            )
            mock_reschedule.assert_called_once()
            mock_reschedule.reset_mock()
            # no reschedule when sched_update is true
            secure_timer.reschedule(update=(bytes(2), bytes(6)))
            assert secure_timer.sched_update
            mock_reschedule.reset_mock()
            secure_group.send(
                KNXIPFrame.init_from_body(RoutingIndication(raw_cemi=raw_test_cemi))
            )
            mock_reschedule.assert_not_called()

    async def test_receive_plain_frames(
        self,
        mock_super_send,
        mock_super_connect,
    ):
        """Test class for KNXnet/IP secure routing."""
        frame_received_mock = Mock()
        secure_group = SecureGroup(
            local_addr=self.mock_addr,
            remote_addr=(DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            backbone_key=self.mock_backbone_key,
            latency_ms=1000,
        )
        secure_group.register_callback(frame_received_mock)
        plain_routing_indication = bytes.fromhex("0610 0530 0010 2900b06010fa10ff0080")
        secure_group.data_received_callback(
            plain_routing_indication, ("192.168.1.2", 3671)
        )
        frame_received_mock.assert_not_called()
        plain_search_response = bytes.fromhex(
            "0610020c006608010a0100280e57360102001000000000082d40834de000170c"
            "000ab3274a3247697261204b4e582f49502d526f757465720000000000000000"
            "000000000e02020203020402050207010901140700dc10f1fffe10f2ffff10f3"
            "ffff10f4ffff"
        )
        secure_group.data_received_callback(
            plain_search_response, ("192.168.1.2", 3671)
        )
        frame_received_mock.assert_called_once()
