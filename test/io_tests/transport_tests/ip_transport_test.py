"""Unit test for KNX/IP transport base class."""

from unittest.mock import Mock, patch

from xknx.io.transport import KNXIPTransport
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
