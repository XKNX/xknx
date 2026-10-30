"""Unit test for KNX/IP transport base class."""

from unittest.mock import Mock, patch

import pytest

from xknx.io.transport import KNXIPTransport, TCPTransport, UDPTransport
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    ConnectionStateResponse,
    KNXIPFrame,
    KNXIPServiceType,
)


class TestKNXIPTransport:
    """Test class for KNXIPTransport base class."""

    @patch.multiple(KNXIPTransport, __abstractmethods__=set())
    def test_callback(self) -> None:
        """Test if callback is called correctly."""
        transport = KNXIPTransport()
        transport.callbacks = []
        callback_mock = Mock()
        # Registering callback
        callback_instance = transport.register_callback(
            callback_mock, [KNXIPServiceType.CONNECTIONSTATE_RESPONSE]
        )
        assert len(transport.callbacks) == 1
        # Handle KNX/IP frame with different service type
        wrong_service_type_frame = KNXIPFrame.init_from_body(
            ConnectionStateRequest(),
        )
        transport.handle_knxipframe(wrong_service_type_frame, HPAI())
        callback_mock.assert_not_called()
        # Handle KNX/IP frame with correct service type
        correct_service_type_frame = KNXIPFrame.init_from_body(
            ConnectionStateResponse(),
        )
        transport.handle_knxipframe(correct_service_type_frame, HPAI())
        callback_mock.assert_called_once_with(
            correct_service_type_frame, HPAI(), transport
        )
        # Unregistering callback
        callback_mock.reset_mock()
        transport.unregister_callback(callback_instance)
        assert not transport.callbacks
        transport.handle_knxipframe(correct_service_type_frame, HPAI())
        callback_mock.assert_not_called()
        # Registering callback for any service type
        callback_instance = transport.register_callback(callback_mock, None)
        transport.handle_knxipframe(correct_service_type_frame, HPAI())
        callback_mock.assert_called_once_with(
            correct_service_type_frame, HPAI(), transport
        )

    @patch.multiple(KNXIPTransport, __abstractmethods__=set())
    def test_callback_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test a raising callback neither propagates nor skips other callbacks."""
        transport = KNXIPTransport()
        transport.callbacks = []
        raising_callback = Mock(side_effect=RuntimeError("boom"))
        other_callback = Mock()
        transport.register_callback(raising_callback)
        transport.register_callback(other_callback)
        frame = KNXIPFrame.init_from_body(ConnectionStateResponse())

        transport.handle_knxipframe(frame, HPAI())

        raising_callback.assert_called_once_with(frame, HPAI(), transport)
        other_callback.assert_called_once_with(frame, HPAI(), transport)
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert "Unexpected error in callback" in caplog.records[0].message
        assert caplog.records[0].exc_info is not None
        assert "Unhandled" not in caplog.text

    @patch.multiple(KNXIPTransport, __abstractmethods__=set())
    def test_callback_unregisters_itself(self) -> None:
        """Test a callback unregistering itself while being called."""
        transport = KNXIPTransport()
        transport.callbacks = []
        other_callback = Mock()

        def unregister_self(*args: object) -> None:
            transport.unregister_callback(self_unregistering)

        self_unregistering = transport.register_callback(unregister_self)
        transport.register_callback(other_callback)
        frame = KNXIPFrame.init_from_body(ConnectionStateResponse())

        transport.handle_knxipframe(frame, HPAI())
        other_callback.assert_called_once_with(frame, HPAI(), transport)
        assert transport.callbacks == [transport.callbacks[0]]
        assert transport.callbacks[0].callback is other_callback

    def test_udp_data_received_callback_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test an exception in a callback doesn't escape the UDP receive callback."""
        transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 3671))
        raising_callback = Mock(side_effect=RuntimeError("boom"))
        other_callback = Mock()
        transport.register_callback(raising_callback)
        transport.register_callback(other_callback)
        raw = KNXIPFrame.init_from_body(ConnectionStateResponse()).to_knx()

        transport.data_received_callback(raw, ("192.168.1.2", 3671))

        raising_callback.assert_called_once()
        other_callback.assert_called_once()
        assert "Unexpected error in callback" in caplog.text

    def test_tcp_data_received_callback_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test an exception in a callback doesn't escape the TCP receive callback."""
        transport = TCPTransport(("192.168.1.2", 3671))
        raising_callback = Mock(side_effect=RuntimeError("boom"))
        other_callback = Mock()
        transport.register_callback(raising_callback)
        transport.register_callback(other_callback)
        raw = KNXIPFrame.init_from_body(ConnectionStateResponse()).to_knx()

        # two frames in one TCP segment - the second is still handled
        transport.data_received_callback(raw + raw)

        assert raising_callback.call_count == 2
        assert other_callback.call_count == 2
        assert caplog.text.count("Unexpected error in callback") == 2
