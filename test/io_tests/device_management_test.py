"""Test for KNX/IP device management connections."""

from copy import deepcopy
from unittest.mock import Mock, call, patch

from xknx.io import DeviceManagement
from xknx.io.transport import UDPTransport
from xknx.knxip import (
    DeviceConfigurationAck,
    DeviceConfigurationRequest,
    DisconnectRequest,
    KNXIPFrame,
    KNXIPServiceType,
)


class TestDeviceManagement:
    """Test class for KNX/IP device management connections."""

    def setup_method(self) -> None:
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 3671))
        self.cemi_received_mock = Mock()
        self.device_management = DeviceManagement(
            transport=self.transport,
            communication_channel=1,
            cemi_received_callback=self.cemi_received_mock,
        )

    @staticmethod
    def _request(
        sequence_counter: int, communication_channel_id: int = 1
    ) -> KNXIPFrame:
        """Return a device configuration request carrying a M_PropRead.req."""
        return KNXIPFrame.init_from_body(
            DeviceConfigurationRequest(
                communication_channel_id=communication_channel_id,
                sequence_counter=sequence_counter,
                # M_PropRead.req for the KNXnet/IP parameter object's device state
                raw_cemi=bytes((0xFC, 0x00, 0x0B, 0x01, 0x45, 0x10, 0x01)),
            )
        )

    def test_start_stop(self) -> None:
        """Test registering and unregistering the callback."""
        assert not self.transport.callbacks

        self.device_management.start()
        assert len(self.transport.callbacks) == 1
        assert self.transport.callbacks[0].service_types == [
            KNXIPServiceType.DEVICE_CONFIGURATION_REQUEST
        ]
        # starting twice registers one callback
        self.device_management.start()
        assert len(self.transport.callbacks) == 1

        self.device_management.stop()
        assert not self.transport.callbacks
        # stopping twice is a no-op
        self.device_management.stop()
        assert not self.transport.callbacks

    def test_start_resets_sequence_number(self) -> None:
        """Test that starting a connection resets the expected sequence number."""
        self.device_management._sequence.expected = 42

        self.device_management.start()

        assert self.device_management._sequence.expected == 0

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    def test_device_configuration_request_received(
        self, mock_transport_send: Mock
    ) -> None:
        """Test acknowledging a received DeviceConfigurationRequest."""
        test_frame = self._request(sequence_counter=0)
        test_ack = KNXIPFrame.init_from_body(
            DeviceConfigurationAck(communication_channel_id=1, sequence_counter=0)
        )

        self.device_management._request_received(test_frame, None, None)

        assert mock_transport_send.call_args_list == [call(test_ack, addr=None)]
        assert self.device_management._sequence.expected == 1
        self.cemi_received_mock.assert_called_once_with(test_frame.body.raw_cemi)

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    def test_repeated_device_configuration_request(
        self, mock_transport_send: Mock
    ) -> None:
        """Test receiving repeated DeviceConfigurationRequest frames."""
        self.device_management._sequence.expected = 10

        test_frame = self._request(sequence_counter=10)
        test_ack = KNXIPFrame.init_from_body(
            DeviceConfigurationAck(communication_channel_id=1, sequence_counter=10)
        )
        test_frame_9 = deepcopy(test_frame)
        test_frame_9.body.sequence_counter = 9

        # first frame - ACK and processed
        self.device_management._request_received(test_frame, None, None)
        assert mock_transport_send.call_args_list == [call(test_ack, addr=None)]
        mock_transport_send.reset_mock()
        assert self.device_management._sequence.expected == 11
        assert self.cemi_received_mock.call_count == 1
        # same sequence number as before - ACK, not processed
        self.device_management._request_received(test_frame, None, None)
        assert mock_transport_send.call_args_list == [call(test_ack, addr=None)]
        mock_transport_send.reset_mock()
        assert self.device_management._sequence.expected == 11
        assert self.cemi_received_mock.call_count == 1
        # wrong sequence number - no ACK, not processed
        self.device_management._request_received(test_frame_9, None, None)
        assert mock_transport_send.call_args_list == []
        assert self.device_management._sequence.expected == 11
        assert self.cemi_received_mock.call_count == 1

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    def test_sequence_number_wraps(self, mock_transport_send: Mock) -> None:
        """Test that the expected sequence number wraps after 255."""
        self.device_management._sequence.expected = 255

        self.device_management._request_received(
            self._request(sequence_counter=255), None, None
        )

        assert self.device_management._sequence.expected == 0
        # the frame before the expected one is still acknowledged after the wrap
        mock_transport_send.reset_mock()
        self.device_management._request_received(
            self._request(sequence_counter=255), None, None
        )
        assert mock_transport_send.call_count == 1
        assert self.cemi_received_mock.call_count == 1

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    def test_foreign_communication_channel(self, mock_transport_send: Mock) -> None:
        """Test that a request for another communication channel is ignored."""
        self.device_management._request_received(
            self._request(sequence_counter=0, communication_channel_id=2), None, None
        )

        assert mock_transport_send.call_args_list == []
        assert self.device_management._sequence.expected == 0
        self.cemi_received_mock.assert_not_called()

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    def test_data_endpoint(self, mock_transport_send: Mock) -> None:
        """Test that the ACK is sent to the data endpoint when one is set."""
        self.device_management.data_endpoint_addr = ("192.168.1.2", 56789)
        test_ack = KNXIPFrame.init_from_body(
            DeviceConfigurationAck(communication_channel_id=1, sequence_counter=0)
        )

        self.device_management._request_received(
            self._request(sequence_counter=0), None, None
        )

        assert mock_transport_send.call_args_list == [
            call(test_ack, addr=("192.168.1.2", 56789))
        ]

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    def test_unsupported_frame(self, mock_transport_send: Mock) -> None:
        """Test that a frame that is not a DeviceConfigurationRequest is ignored."""
        with patch("logging.Logger.warning") as mock_warning:
            self.device_management._request_received(
                KNXIPFrame.init_from_body(
                    DisconnectRequest(communication_channel_id=1)
                ),
                None,
                None,
            )
            mock_warning.assert_called_once()

        mock_transport_send.assert_not_called()
        self.cemi_received_mock.assert_not_called()

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    def test_without_cemi_callback(self, mock_transport_send: Mock) -> None:
        """Test that a request is acknowledged without a cEMI callback set."""
        device_management = DeviceManagement(
            transport=self.transport, communication_channel=1
        )

        device_management._request_received(
            self._request(sequence_counter=0), None, None
        )

        assert mock_transport_send.call_count == 1
        assert device_management._sequence.expected == 1
