"""Unit test for KNX/IP TCP transport."""

from unittest.mock import Mock

from xknx.io.transport import TCPTransport
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    ConnectionStateResponse,
    KNXIPFrame,
    KNXIPHeader,
    KNXIPServiceType,
)


class TestTCPTransport:
    """Test class for TCPTransport."""

    def setup_method(self) -> None:
        """Set up transport with a callback receiving every frame."""
        # pylint: disable=attribute-defined-outside-init
        self.transport = TCPTransport(remote_addr=("127.0.0.1", 3671))
        self.callback = Mock()
        self.transport.register_callback(self.callback, None)
        self.request_raw = KNXIPFrame.init_from_body(ConnectionStateRequest()).to_knx()
        self.response_raw = KNXIPFrame.init_from_body(
            ConnectionStateResponse()
        ).to_knx()

    def received_bodies(self) -> list[type]:
        """Return the body classes of the frames passed to the callback."""
        return [type(call.args[0].body) for call in self.callback.call_args_list]

    def test_coalesced_frames(self) -> None:
        """Test a chunk holding many frames is parsed without recursion."""
        count = 2000  # recursion per frame hit the recursion limit at ~1000
        self.transport.data_received_callback(self.request_raw * count)
        assert self.callback.call_count == count
        assert self.transport._buffer == b""
        frame, source, transport = self.callback.call_args.args
        assert frame == KNXIPFrame.init_from_body(ConnectionStateRequest())
        assert source == HPAI(*self.transport.remote_addr, protocol=source.protocol)
        assert transport is self.transport

    def test_partial_frame_buffering(self) -> None:
        """Test a frame spread over chunks is buffered until complete."""
        raw = self.request_raw + self.response_raw
        # cut inside the header of the first frame, inside the body of the second
        self.transport.data_received_callback(raw[:3])
        self.callback.assert_not_called()
        assert self.transport._buffer == raw[:3]
        self.transport.data_received_callback(raw[3:20])
        assert self.received_bodies() == [ConnectionStateRequest]
        assert self.transport._buffer == raw[16:20]
        self.transport.data_received_callback(raw[20:])
        assert self.received_bodies() == [
            ConnectionStateRequest,
            ConnectionStateResponse,
        ]
        assert self.transport._buffer == b""

    def test_unparsable_frame_skipped(self) -> None:
        """Test an unparsable frame is skipped by its total length."""
        header = KNXIPHeader()
        header.service_type_ident = KNXIPServiceType.REMOTE_DIAG_RESPONSE
        header.total_length = KNXIPHeader.HEADERLENGTH + 4
        unsupported_raw = header.to_knx() + bytes(4)  # not implemented in xknx
        self.transport.data_received_callback(
            self.request_raw + unsupported_raw + self.response_raw
        )
        assert self.received_bodies() == [
            ConnectionStateRequest,
            ConnectionStateResponse,
        ]
        assert self.transport._buffer == b""

    def test_unparsable_frame_without_length_dropped(self) -> None:
        """Test the chunk is dropped when the unparsable frame has no usable length."""
        # header announcing a total length shorter than the header itself
        short_length_raw = bytes.fromhex("06 10 02 07 00 03") + bytes(4)
        self.transport.data_received_callback(short_length_raw + self.response_raw)
        self.callback.assert_not_called()
        assert self.transport._buffer == b""
        # wrong header length octet
        wrong_header_raw = bytes.fromhex("05 10 02 07 00 0a") + bytes(4)
        self.transport.data_received_callback(wrong_header_raw + self.response_raw)
        self.callback.assert_not_called()
        assert self.transport._buffer == b""
        # the transport keeps working for the next chunk
        self.transport.data_received_callback(self.response_raw)
        assert self.received_bodies() == [ConnectionStateResponse]
