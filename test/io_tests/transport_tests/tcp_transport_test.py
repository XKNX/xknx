"""Unit test for KNX/IP TCP transport."""

from unittest.mock import Mock, patch

from xknx.io.transport import TCPTransport
from xknx.knxip import ConnectionStateResponse, ErrorCode, KNXIPFrame, TunnellingAck

VALID_FRAME = KNXIPFrame.init_from_body(
    ConnectionStateResponse(communication_channel_id=1, status_code=ErrorCode.E_NO_ERROR)
)
VALID_RAW = VALID_FRAME.to_knx()
# ROUTING_SYSTEM_BROADCAST is a known service type without a body parser in xknx
UNKNOWN_SERVICE_RAW = bytes.fromhex("06 10 05 33 00 0a 00 00 00 00")
# TUNNELLING_ACK with unknown status code 0x55 - the body parser fails
INVALID_BODY_RAW = bytes.fromhex("06 10 04 21 00 0a 04 2a 17 55")
# header length byte is 5 - the stream framing can not be recovered
INVALID_HEADER_RAW = bytes.fromhex("05 10 02 08 00 08 01 00")


class TestTCPTransport:
    """Test class for KNX/IP TCP transport."""

    def setup_method(self) -> None:
        """Set up test class."""
        self.transport = TCPTransport(remote_addr=("192.168.1.2", 3671))
        self.handle_mock = Mock()
        self.transport.register_callback(self.handle_mock)

    def test_two_frames_in_one_chunk(self) -> None:
        """Test two frames received in one chunk are both dispatched."""
        self.transport.data_received_callback(VALID_RAW + VALID_RAW)
        assert self.handle_mock.call_count == 2
        assert self.transport._buffer == b""

    def test_incomplete_frame_is_buffered(self) -> None:
        """Test a frame split over two chunks is dispatched once complete."""
        self.transport.data_received_callback(VALID_RAW[:4])
        self.handle_mock.assert_not_called()
        assert self.transport._buffer == VALID_RAW[:4]
        self.transport.data_received_callback(VALID_RAW[4:] + VALID_RAW[:7])
        self.handle_mock.assert_called_once()
        assert self.handle_mock.call_args[0][0] == VALID_FRAME
        assert self.transport._buffer == VALID_RAW[:7]
        self.transport.data_received_callback(VALID_RAW[7:])
        assert self.handle_mock.call_count == 2
        assert self.transport._buffer == b""

    def test_unknown_service_type_followed_by_valid_frame(self) -> None:
        """Test an unparsable frame is skipped and the following frame is dispatched."""
        self.transport.data_received_callback(UNKNOWN_SERVICE_RAW + VALID_RAW)
        self.handle_mock.assert_called_once()
        assert self.handle_mock.call_args[0][0] == VALID_FRAME
        assert self.transport._buffer == b""

    def test_invalid_body_followed_by_valid_frame(self) -> None:
        """Test a frame with an unparsable body is skipped by its total length."""
        self.transport.data_received_callback(INVALID_BODY_RAW + VALID_RAW)
        self.handle_mock.assert_called_once()
        assert self.handle_mock.call_args[0][0] == VALID_FRAME
        assert self.transport._buffer == b""

    def test_invalid_body_followed_by_incomplete_frame(self) -> None:
        """Test the data after a skipped frame is still buffered when incomplete."""
        self.transport.data_received_callback(INVALID_BODY_RAW + VALID_RAW[:3])
        self.handle_mock.assert_not_called()
        assert self.transport._buffer == VALID_RAW[:3]
        self.transport.data_received_callback(VALID_RAW[3:])
        self.handle_mock.assert_called_once()
        assert self.handle_mock.call_args[0][0] == VALID_FRAME

    def test_valid_frame_dispatched_before_invalid_frame(self) -> None:
        """Test a valid frame is dispatched even when invalid data follows."""
        self.transport.data_received_callback(VALID_RAW + UNKNOWN_SERVICE_RAW)
        self.handle_mock.assert_called_once()
        assert self.transport._buffer == b""

    @patch("xknx.io.transport.tcp_transport.knx_logger.warning")
    def test_invalid_header_drops_buffer(self, mock_warning: Mock) -> None:
        """Test an unparsable header drops all received data without raising."""
        self.transport.data_received_callback(INVALID_HEADER_RAW + VALID_RAW)
        self.handle_mock.assert_not_called()
        assert self.transport._buffer == b""
        mock_warning.assert_called_once()
        # the transport keeps working afterwards
        self.transport.data_received_callback(VALID_RAW)
        self.handle_mock.assert_called_once()

    def test_total_length_zero_drops_buffer(self) -> None:
        """Test a header with total length 0 does not recurse endlessly."""
        self.transport.data_received_callback(bytes.fromhex("06 10 05 30 00 00") + VALID_RAW)
        self.handle_mock.assert_not_called()
        assert self.transport._buffer == b""

    def test_dib_length_zero_does_not_hang(self) -> None:
        """Test a DESCRIPTION_RESPONSE with a DIB of structure length 0 is skipped."""
        self.transport.data_received_callback(bytes.fromhex("06 10 02 04 00 08 00 03") + VALID_RAW)
        self.handle_mock.assert_called_once()
        assert self.handle_mock.call_args[0][0] == VALID_FRAME

    def test_tunnelling_ack_is_dispatched(self) -> None:
        """Test a valid frame of a body with a status code is dispatched."""
        ack = KNXIPFrame.init_from_body(
            TunnellingAck(communication_channel_id=4, sequence_counter=23)
        )
        self.transport.data_received_callback(ack.to_knx())
        self.handle_mock.assert_called_once()
        assert self.handle_mock.call_args[0][0] == ack
