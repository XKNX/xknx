"""Test for KNX/IP device management connections."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from xknx.cemi import (
    CEMIErrorCode,
    CEMIFrame,
    CEMIMessageCode,
    CEMIMPropInfo,
    CEMIMPropReadResponse,
    CEMIMPropWriteResponse,
)
from xknx.exceptions import CommunicationError
from xknx.io import (
    SecureDeviceManagementConnection,
    TCPDeviceManagementConnection,
    UDPDeviceManagementConnection,
)
from xknx.io.const import (
    CONNECTIONSTATE_REQUEST_TIMEOUT,
    DEVICE_CONFIGURATION_REQUEST_REPETITIONS,
    DEVICE_CONFIGURATION_REQUEST_TIMEOUT,
    HEARTBEAT_RATE,
)
from xknx.io.ip_secure import SecureSession
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    ConnectionStateResponse,
    ConnectRequest,
    ConnectRequestInformation,
    ConnectResponse,
    DeviceConfigurationAck,
    DeviceConfigurationRequest,
    DisconnectRequest,
    DisconnectResponse,
    ErrorCode,
    HostProtocol,
    KNXIPFrame,
)
from xknx.knxip.knxip_enum import ConnectRequestType
from xknx.profile.const import ResourceKNXNETIPPropertyId, ResourceObjectType

from ..conftest import EventLoopClockAdvancer

LOCAL_ADDR = ("192.168.1.1", 12345)
REMOTE_ADDR = ("192.168.1.2", 3671)
CHANNEL = 23

DEVICE_STATE = ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_STATE


def prop_read_con(
    data: bytes,
    number_of_elements: int = 1,
    property_id: ResourceKNXNETIPPropertyId | int = DEVICE_STATE,
) -> bytes:
    """Return a M_PropRead.con for a property of the KNXnet/IP parameter object."""
    return CEMIFrame(
        code=CEMIMessageCode.M_PROP_READ_CON,
        data=CEMIMPropReadResponse(
            property_info=CEMIMPropInfo(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=property_id,
                number_of_elements=number_of_elements,
            ),
            data=data,
        ),
    ).to_knx()


class TestUDPDeviceManagementConnection:
    """Test class for KNX/IP device management connections over UDP."""

    def setup_method(self) -> None:
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.indication_mock = Mock()
        self.connection = UDPDeviceManagementConnection(
            gateway_ip=REMOTE_ADDR[0],
            gateway_port=REMOTE_ADDR[1],
            local_ip=LOCAL_ADDR[0],
            local_port=LOCAL_ADDR[1],
            indication_callback=self.indication_mock,
        )

    async def _connect(
        self,
        send_mock: Mock,
        time_travel: EventLoopClockAdvancer,
        data_endpoint: HPAI | None = None,
    ) -> None:
        """Drive the connect handshake to completion."""
        with (
            patch("xknx.io.transport.udp_transport.UDPTransport.connect"),
            patch(
                "xknx.io.transport.udp_transport.UDPTransport.getsockname",
                return_value=LOCAL_ADDR,
            ),
        ):
            task = asyncio.create_task(self.connection.connect())
            await time_travel(0)
            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    ConnectResponse(
                        communication_channel=CHANNEL,
                        data_endpoint=data_endpoint or HPAI(),
                    )
                ),
                HPAI(*REMOTE_ADDR),
            )
            await task
        send_mock.reset_mock()

    def _server_sends(self, raw_cemi: bytes, sequence_counter: int = 0) -> None:
        """Deliver a server initiated device configuration request."""
        self.connection.transport.handle_knxipframe(
            KNXIPFrame.init_from_body(
                DeviceConfigurationRequest(
                    communication_channel_id=CHANNEL,
                    sequence_counter=sequence_counter,
                    raw_cemi=raw_cemi,
                )
            ),
            HPAI(*REMOTE_ADDR),
        )

    def _ack_last_request(self, sequence_counter: int = 0) -> None:
        """Acknowledge the request the connection just sent."""
        self.connection.transport.handle_knxipframe(
            KNXIPFrame.init_from_body(
                DeviceConfigurationAck(
                    communication_channel_id=CHANNEL,
                    sequence_counter=sequence_counter,
                )
            ),
            HPAI(*REMOTE_ADDR),
        )

    def _answer_disconnect_request(self) -> None:
        """Answer the DisconnectRequest the connection just sent."""
        self.connection.transport.handle_knxipframe(
            KNXIPFrame.init_from_body(
                DisconnectResponse(communication_channel_id=CHANNEL)
            ),
            HPAI(*REMOTE_ADDR),
        )

    def _answer_heartbeat(self, status_code: ErrorCode = ErrorCode.E_NO_ERROR) -> None:
        """Answer the ConnectionStateRequest the connection just sent."""
        self.connection.transport.handle_knxipframe(
            KNXIPFrame.init_from_body(
                ConnectionStateResponse(
                    communication_channel_id=CHANNEL,
                    status_code=status_code,
                )
            ),
            HPAI(*REMOTE_ADDR),
        )

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_connect_disconnect(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test opening and closing a device management connection."""
        with (
            patch("xknx.io.transport.udp_transport.UDPTransport.connect"),
            patch(
                "xknx.io.transport.udp_transport.UDPTransport.getsockname",
                return_value=LOCAL_ADDR,
            ),
        ):
            task = asyncio.create_task(self.connection.connect())
            await time_travel(0)

            # The connection is requested for device management, not tunnelling
            sent = send_mock.call_args[0][0]
            assert isinstance(sent.body, ConnectRequest)
            assert sent.body.cri == ConnectRequestInformation(
                connection_type=ConnectRequestType.DEVICE_MGMT_CONNECTION
            )

            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    ConnectResponse(communication_channel=CHANNEL)
                ),
                HPAI(*REMOTE_ADDR),
            )
            await task

        assert self.connection.communication_channel == CHANNEL
        # incoming requests are answered from now on
        assert self.connection.transport.callbacks

        send_mock.reset_mock()
        with patch("xknx.io.transport.udp_transport.UDPTransport.stop"):
            task = asyncio.create_task(self.connection.disconnect())
            await time_travel(0)
            assert isinstance(send_mock.call_args[0][0].body, DisconnectRequest)
            self._answer_disconnect_request()
            await task

        assert not self.connection.transport.callbacks
        assert self.connection.communication_channel is None

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_connect_twice(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that opening an open connection raises."""
        await self._connect(send_mock, time_travel)

        with pytest.raises(CommunicationError):
            await self.connection.connect()

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_connect_fails(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a refused ConnectRequest raises."""
        with (
            patch("xknx.io.transport.udp_transport.UDPTransport.connect"),
            patch(
                "xknx.io.transport.udp_transport.UDPTransport.getsockname",
                return_value=LOCAL_ADDR,
            ),
            patch("xknx.io.transport.udp_transport.UDPTransport.stop") as stop_mock,
        ):
            task = asyncio.create_task(self.connection.connect())
            await time_travel(0)
            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    ConnectResponse(
                        communication_channel=CHANNEL,
                        status_code=ErrorCode.E_NO_MORE_CONNECTIONS,
                    )
                ),
                HPAI(*REMOTE_ADDR),
            )
            with pytest.raises(CommunicationError):
                await task
            stop_mock.assert_called_once()

        assert self.connection.communication_channel is None

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_context_manager(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test connecting and disconnecting via the context manager."""

        async def use_connection() -> None:
            async with self.connection as connection:
                assert connection is self.connection
                assert self.connection.communication_channel == CHANNEL

        with (
            patch("xknx.io.transport.udp_transport.UDPTransport.connect"),
            patch(
                "xknx.io.transport.udp_transport.UDPTransport.getsockname",
                return_value=LOCAL_ADDR,
            ),
            patch("xknx.io.transport.udp_transport.UDPTransport.stop"),
        ):
            task = asyncio.create_task(use_connection())
            await time_travel(0)
            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    ConnectResponse(communication_channel=CHANNEL)
                ),
                HPAI(*REMOTE_ADDR),
            )
            await time_travel(0)
            self._answer_disconnect_request()
            await task

        assert self.connection.communication_channel is None

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_read_property(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test reading a property over a device management connection."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)

        request = send_mock.call_args[0][0].body
        assert isinstance(request, DeviceConfigurationRequest)
        assert request.communication_channel_id == CHANNEL
        assert request.sequence_counter == 0
        assert CEMIFrame.from_knx(request.raw_cemi).code is (
            CEMIMessageCode.M_PROP_READ_REQ
        )

        self._ack_last_request()
        send_mock.reset_mock()
        self._server_sends(prop_read_con(b"\x01"))
        await time_travel(0)

        assert await task == b"\x01"
        # the answer was acknowledged in turn
        assert isinstance(send_mock.call_args[0][0].body, DeviceConfigurationAck)
        # and the outgoing counter moved on
        assert self.connection.sequence_number == 1

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_read_property_error(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a property read reporting an error raises."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=0xF0,
            )
        )
        await time_travel(0)
        self._ack_last_request()
        # No elements returned, the payload carries the reason instead
        self._server_sends(
            prop_read_con(
                bytes((CEMIErrorCode.CEMI_ERROR_VOID_DP.value,)),
                number_of_elements=0,
                property_id=0xF0,
            )
        )
        await time_travel(0)

        with pytest.raises(CommunicationError):
            await task

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_read_property_unknown_error_code(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that an error code the specification does not define raises cleanly."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)
        self._ack_last_request()
        # 0x99 is not a CEMIErrorCode - resolving it raises ValueError
        self._server_sends(prop_read_con(b"\x99", number_of_elements=0))
        await time_travel(0)

        with pytest.raises(CommunicationError):
            await task

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_read_property_not_connected(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a request without an open connection raises."""
        with pytest.raises(CommunicationError):
            await self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_write_property(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test writing a property over a device management connection."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.write_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
                data=b"\x00",
            )
        )
        await time_travel(0)
        assert CEMIFrame.from_knx(send_mock.call_args[0][0].body.raw_cemi).code is (
            CEMIMessageCode.M_PROP_WRITE_REQ
        )

        self._ack_last_request()
        self._server_sends(
            CEMIFrame(
                code=CEMIMessageCode.M_PROP_WRITE_CON,
                data=CEMIMPropWriteResponse(
                    property_info=CEMIMPropInfo(
                        object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                        property_id=DEVICE_STATE,
                    )
                ),
            ).to_knx()
        )
        await time_travel(0)

        await task

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_stale_answer_is_discarded(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that an answer to another property request does not satisfy this one."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)
        self._ack_last_request()
        # eg. the late answer to an earlier, timed out request
        self._server_sends(prop_read_con(b"\xff", property_id=0x34))
        await time_travel(0)
        assert not task.done()
        self._server_sends(prop_read_con(b"\x01"), sequence_counter=1)
        await time_travel(0)

        assert await task == b"\x01"

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_sequence_number_wraps(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that the outgoing sequence number wraps after 255."""
        await self._connect(send_mock, time_travel)
        self.connection.sequence_number = 255

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)
        assert send_mock.call_args[0][0].body.sequence_counter == 255

        self._ack_last_request(sequence_counter=255)
        self._server_sends(prop_read_con(b"\x01"))
        await time_travel(0)

        await task
        assert self.connection.sequence_number == 0

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_property_info_indication(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that an unprompted M_PropInfo.ind reaches the callback."""
        await self._connect(send_mock, time_travel)

        raw_cemi = CEMIFrame(
            code=CEMIMessageCode.M_PROP_INFO_IND,
            data=CEMIMPropReadResponse(
                property_info=CEMIMPropInfo(
                    object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                    property_id=DEVICE_STATE,
                ),
                data=b"\x01",
            ),
        ).to_knx()
        self._server_sends(raw_cemi)
        await time_travel(0)

        self.indication_mock.assert_called_once()
        assert self.indication_mock.call_args[0][0].code is (
            CEMIMessageCode.M_PROP_INFO_IND
        )
        # it is acknowledged like any other received request
        assert isinstance(send_mock.call_args[0][0].body, DeviceConfigurationAck)

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_indication_callback_exception(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that an exception in the indication callback does not propagate."""
        await self._connect(send_mock, time_travel)
        self.indication_mock.side_effect = RuntimeError("boom")

        raw_cemi = CEMIFrame(
            code=CEMIMessageCode.M_PROP_INFO_IND,
            data=CEMIMPropReadResponse(
                property_info=CEMIMPropInfo(
                    object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                    property_id=DEVICE_STATE,
                ),
                data=b"\x01",
            ),
        ).to_knx()
        with patch("logging.Logger.exception") as mock_log:
            self._server_sends(raw_cemi)
            mock_log.assert_called_once()

        self.indication_mock.assert_called_once()
        # the frame was acknowledged nevertheless
        assert isinstance(send_mock.call_args[0][0].body, DeviceConfigurationAck)

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_unparsable_cemi_is_acknowledged(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a request carrying an unparsable cEMI frame is still acknowledged."""
        await self._connect(send_mock, time_travel)

        with patch("logging.Logger.warning") as mock_log:
            # M_PropRead.con cut short - raises CouldNotParseCEMI when parsed
            self._server_sends(bytes((0xFB, 0x00)))
            mock_log.assert_called_once()

        assert isinstance(send_mock.call_args[0][0].body, DeviceConfigurationAck)

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_unacknowledged_request_disconnects(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a request that is never acknowledged closes the connection."""
        await self._connect(send_mock, time_travel)

        with patch("xknx.io.transport.udp_transport.UDPTransport.stop"):
            task = asyncio.create_task(
                self.connection.read_property(
                    object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                    property_id=DEVICE_STATE,
                )
            )
            # The first try plus every repetition has to time out
            for _ in range(DEVICE_CONFIGURATION_REQUEST_REPETITIONS + 1):
                await time_travel(DEVICE_CONFIGURATION_REQUEST_TIMEOUT)
            # then the connection is terminated with a DisconnectRequest
            assert isinstance(send_mock.call_args[0][0].body, DisconnectRequest)
            self._answer_disconnect_request()

            with pytest.raises(CommunicationError):
                await task

        requests = [
            call.args[0].body
            for call in send_mock.call_args_list
            if isinstance(call.args[0].body, DeviceConfigurationRequest)
        ]
        assert len(requests) == DEVICE_CONFIGURATION_REQUEST_REPETITIONS + 1
        # A repetition keeps the sequence counter of the frame it repeats
        assert {request.sequence_counter for request in requests} == {0}
        assert self.connection.communication_channel is None
        assert not self.connection.transport.callbacks

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_disconnect_cancels_pending_request(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that disconnecting fails a request waiting for an answer."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)
        self._ack_last_request()
        await time_travel(0)
        # acknowledged, but the answer never comes

        with patch("xknx.io.transport.udp_transport.UDPTransport.stop"):
            disconnect_task = asyncio.create_task(self.connection.disconnect())
            await time_travel(0)
            self._answer_disconnect_request()
            await disconnect_task

        with pytest.raises(CommunicationError):
            await task

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_server_disconnect(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a DisconnectRequest of the server is answered and ends the connection."""
        await self._connect(send_mock, time_travel)

        with patch("xknx.io.transport.udp_transport.UDPTransport.stop") as stop_mock:
            # one for a foreign channel is ignored
            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    DisconnectRequest(communication_channel_id=CHANNEL + 1)
                ),
                HPAI(*REMOTE_ADDR),
            )
            assert self.connection.communication_channel == CHANNEL
            send_mock.assert_not_called()

            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    DisconnectRequest(communication_channel_id=CHANNEL)
                ),
                HPAI(*REMOTE_ADDR),
            )
            sent = send_mock.call_args[0][0].body
            assert isinstance(sent, DisconnectResponse)
            assert sent.communication_channel_id == CHANNEL
            stop_mock.assert_called_once()

        assert not self.connection.transport.callbacks
        assert self.connection._heartbeat_task is None
        assert self.connection.communication_channel is None

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_heartbeat(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that the connection is kept alive with ConnectionStateRequests."""
        await self._connect(send_mock, time_travel)
        heartbeat_request = KNXIPFrame.init_from_body(
            ConnectionStateRequest(
                communication_channel_id=CHANNEL,
                control_endpoint=HPAI(*LOCAL_ADDR),
            )
        )

        await time_travel(HEARTBEAT_RATE)
        send_mock.assert_called_once_with(heartbeat_request)
        send_mock.reset_mock()
        self._answer_heartbeat()
        # answered - no retry is sent
        await time_travel(CONNECTIONSTATE_REQUEST_TIMEOUT)
        send_mock.assert_not_called()
        # the next regular heartbeat
        await time_travel(HEARTBEAT_RATE - CONNECTIONSTATE_REQUEST_TIMEOUT)
        send_mock.assert_called_once_with(heartbeat_request)

        assert self.connection.communication_channel == CHANNEL

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_heartbeat_no_answer_disconnects(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that unanswered heartbeats are repeated 3 times, then disconnect."""
        await self._connect(send_mock, time_travel)

        with patch("xknx.io.transport.udp_transport.UDPTransport.stop"):
            await time_travel(HEARTBEAT_RATE)
            # the initial request plus 3 repetitions time out
            for _ in range(3):
                assert isinstance(
                    send_mock.call_args[0][0].body, ConnectionStateRequest
                )
                await time_travel(CONNECTIONSTATE_REQUEST_TIMEOUT)
            await time_travel(CONNECTIONSTATE_REQUEST_TIMEOUT)

            state_requests = [
                call.args[0].body
                for call in send_mock.call_args_list
                if isinstance(call.args[0].body, ConnectionStateRequest)
            ]
            assert len(state_requests) == 4
            # then the connection is terminated
            assert isinstance(send_mock.call_args[0][0].body, DisconnectRequest)
            self._answer_disconnect_request()
            await time_travel(0)

        assert self.connection.communication_channel is None
        assert not self.connection.transport.callbacks

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_heartbeat_error_disconnects(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that heartbeats answered with an error are repeated, then disconnect."""
        await self._connect(send_mock, time_travel)

        with patch("xknx.io.transport.udp_transport.UDPTransport.stop"):
            await time_travel(HEARTBEAT_RATE)
            # the initial request plus 3 repetitions are answered with an error
            for _ in range(4):
                assert isinstance(
                    send_mock.call_args[0][0].body, ConnectionStateRequest
                )
                self._answer_heartbeat(status_code=ErrorCode.E_CONNECTION_ID)
                await time_travel(0)

            # then the connection is terminated
            assert isinstance(send_mock.call_args[0][0].body, DisconnectRequest)
            self._answer_disconnect_request()
            await time_travel(0)

        assert self.connection.communication_channel is None
        assert not self.connection.transport.callbacks

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_data_endpoint(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that requests are sent to the data endpoint the server assigned."""
        data_endpoint = ("192.168.1.2", 56789)
        await self._connect(send_mock, time_travel, data_endpoint=HPAI(*data_endpoint))

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)

        assert isinstance(send_mock.call_args[0][0].body, DeviceConfigurationRequest)
        assert send_mock.call_args.kwargs == {"addr": data_endpoint}

        self._ack_last_request()
        self._server_sends(prop_read_con(b"\x01"))
        await time_travel(0)
        await task

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_request_answer_timeout(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a request that is acknowledged but never answered raises."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)
        self._ack_last_request()
        await time_travel(DEVICE_CONFIGURATION_REQUEST_TIMEOUT)

        with pytest.raises(CommunicationError):
            await task
        # only an unacknowledged request closes the connection
        assert self.connection.communication_channel == CHANNEL

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_request_cancelled(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that cancelling a request from the outside propagates."""
        await self._connect(send_mock, time_travel)

        # cancelled while awaiting the acknowledgement
        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        # cancelled while awaiting the answer
        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)
        self._ack_last_request()
        await time_travel(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert self.connection.communication_channel == CHANNEL

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_heartbeat_recovery(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that an answered heartbeat repetition keeps the connection open."""
        await self._connect(send_mock, time_travel)

        await time_travel(HEARTBEAT_RATE)
        # not answered - a repetition is sent and answered
        await time_travel(CONNECTIONSTATE_REQUEST_TIMEOUT)
        self._answer_heartbeat()
        await time_travel(0)

        state_requests = [
            call.args[0].body
            for call in send_mock.call_args_list
            if isinstance(call.args[0].body, ConnectionStateRequest)
        ]
        assert len(state_requests) == 2
        assert self.connection.communication_channel == CHANNEL
        # the next regular heartbeat is sent again
        send_mock.reset_mock()
        await time_travel(HEARTBEAT_RATE)
        assert isinstance(send_mock.call_args[0][0].body, ConnectionStateRequest)

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_heartbeat_ends_without_connection(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that the heartbeat ends when the connection is gone."""
        await self._connect(send_mock, time_travel)
        heartbeat_task = self.connection._heartbeat_task
        assert heartbeat_task is not None

        self.connection.communication_channel = None
        await time_travel(HEARTBEAT_RATE)

        send_mock.assert_not_called()
        assert heartbeat_task.done()

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_route_back(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test connecting with route back - the control endpoint is unspecified."""
        connection = UDPDeviceManagementConnection(
            gateway_ip=REMOTE_ADDR[0],
            gateway_port=REMOTE_ADDR[1],
            local_ip=LOCAL_ADDR[0],
            route_back=True,
        )
        with patch("xknx.io.transport.udp_transport.UDPTransport.connect"):
            task = asyncio.create_task(connection.connect())
            await time_travel(0)
            sent = send_mock.call_args[0][0]
            assert isinstance(sent.body, ConnectRequest)
            assert sent.body.control_endpoint == HPAI()
            connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    ConnectResponse(communication_channel=CHANNEL)
                ),
                HPAI(*REMOTE_ADDR),
            )
            await task

        assert connection.local_hpai == HPAI()
        connection._stop()

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_send_request_without_connection(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that sending without an open channel raises."""
        cemi = CEMIFrame.from_knx(bytes((0xFC, 0x00, 0x0B, 0x01, 0x45, 0x10, 0x01)))

        with pytest.raises(CommunicationError):
            await self.connection._send_request(cemi)

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_unexpected_frame_body_ignored(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a frame that is not a DisconnectRequest is ignored."""
        await self._connect(send_mock, time_travel)

        self.connection._disconnect_request_received(
            KNXIPFrame.init_from_body(
                DisconnectResponse(communication_channel_id=CHANNEL)
            ),
            HPAI(*REMOTE_ADDR),
            None,
        )

        send_mock.assert_not_called()
        assert self.connection.communication_channel == CHANNEL

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_unexpected_parsing_error(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that an unforeseen parsing bug does not escape the callback."""
        await self._connect(send_mock, time_travel)

        with (
            patch("xknx.cemi.CEMIFrame.from_knx", side_effect=RuntimeError("boom")),
            patch("logging.Logger.exception") as mock_log,
        ):
            self._server_sends(prop_read_con(b"\x01"))
            mock_log.assert_called_once()

        # the frame was acknowledged and the connection is unaffected
        assert isinstance(send_mock.call_args[0][0].body, DeviceConfigurationAck)
        assert self.connection.communication_channel == CHANNEL

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_write_property_error(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a property write reporting an error raises."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.write_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
                data=b"\x00",
            )
        )
        await time_travel(0)
        self._ack_last_request()
        self._server_sends(
            CEMIFrame(
                code=CEMIMessageCode.M_PROP_WRITE_CON,
                data=CEMIMPropWriteResponse(
                    property_info=CEMIMPropInfo(
                        object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                        property_id=DEVICE_STATE,
                        number_of_elements=0,
                    ),
                    error_code=CEMIErrorCode.CEMI_ERROR_VOID_DP,
                ),
            ).to_knx()
        )
        await time_travel(0)

        with pytest.raises(CommunicationError):
            await task


class TestTCPDeviceManagementConnection:
    """Test class for KNX/IP device management connections over TCP."""

    def setup_method(self) -> None:
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.indication_mock = Mock()
        self.connection = TCPDeviceManagementConnection(
            gateway_ip=REMOTE_ADDR[0],
            gateway_port=REMOTE_ADDR[1],
            indication_callback=self.indication_mock,
        )

    async def _connect(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Drive the connect handshake to completion."""
        with patch("xknx.io.transport.tcp_transport.TCPTransport.connect"):
            task = asyncio.create_task(self.connection.connect())
            await time_travel(0)
            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    ConnectResponse(
                        communication_channel=CHANNEL,
                        data_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
                    )
                ),
                HPAI(*REMOTE_ADDR, protocol=HostProtocol.IPV4_TCP),
            )
            await task
        send_mock.reset_mock()

    def _server_sends(self, raw_cemi: bytes, sequence_counter: int = 0) -> None:
        """Deliver a server initiated device configuration request."""
        self.connection.transport.handle_knxipframe(
            KNXIPFrame.init_from_body(
                DeviceConfigurationRequest(
                    communication_channel_id=CHANNEL,
                    sequence_counter=sequence_counter,
                    raw_cemi=raw_cemi,
                )
            ),
            HPAI(*REMOTE_ADDR, protocol=HostProtocol.IPV4_TCP),
        )

    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    async def test_connect_disconnect(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test opening and closing a TCP device management connection."""
        with patch("xknx.io.transport.tcp_transport.TCPTransport.connect"):
            task = asyncio.create_task(self.connection.connect())
            await time_travel(0)

            sent = send_mock.call_args[0][0]
            assert isinstance(sent.body, ConnectRequest)
            assert sent.body.cri == ConnectRequestInformation(
                connection_type=ConnectRequestType.DEVICE_MGMT_CONNECTION
            )
            # TCP always uses the route back HPAI
            assert sent.body.control_endpoint == HPAI(protocol=HostProtocol.IPV4_TCP)

            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    ConnectResponse(
                        communication_channel=CHANNEL,
                        data_endpoint=HPAI(protocol=HostProtocol.IPV4_TCP),
                    )
                ),
                HPAI(*REMOTE_ADDR, protocol=HostProtocol.IPV4_TCP),
            )
            await task

        assert self.connection.communication_channel == CHANNEL

        send_mock.reset_mock()
        with patch("xknx.io.transport.tcp_transport.TCPTransport.stop"):
            task = asyncio.create_task(self.connection.disconnect())
            await time_travel(0)
            assert isinstance(send_mock.call_args[0][0].body, DisconnectRequest)
            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    DisconnectResponse(communication_channel_id=CHANNEL)
                ),
                HPAI(*REMOTE_ADDR, protocol=HostProtocol.IPV4_TCP),
            )
            await task

        assert not self.connection.transport.callbacks
        assert self.connection.communication_channel is None

    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    async def test_read_property_without_acknowledgement(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that TCP requests are answered directly, without acknowledgements."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)

        request = send_mock.call_args[0][0].body
        assert isinstance(request, DeviceConfigurationRequest)
        assert CEMIFrame.from_knx(request.raw_cemi).code is (
            CEMIMessageCode.M_PROP_READ_REQ
        )
        send_mock.reset_mock()

        # a received acknowledgement is ignored
        self.connection.transport.handle_knxipframe(
            KNXIPFrame.init_from_body(
                DeviceConfigurationAck(
                    communication_channel_id=CHANNEL, sequence_counter=0
                )
            ),
            HPAI(*REMOTE_ADDR, protocol=HostProtocol.IPV4_TCP),
        )
        assert not task.done()

        # the answer is not acknowledged either - its sequence counter is
        # not evaluated
        self._server_sends(prop_read_con(b"\x01"), sequence_counter=42)
        await time_travel(0)

        assert await task == b"\x01"
        send_mock.assert_not_called()

    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    async def test_indication_not_acknowledged(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that an M_PropInfo.ind reaches the callback and is not acknowledged."""
        await self._connect(send_mock, time_travel)

        raw_cemi = CEMIFrame(
            code=CEMIMessageCode.M_PROP_INFO_IND,
            data=CEMIMPropReadResponse(
                property_info=CEMIMPropInfo(
                    object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                    property_id=DEVICE_STATE,
                ),
                data=b"\x01",
            ),
        ).to_knx()
        self._server_sends(raw_cemi)
        await time_travel(0)

        self.indication_mock.assert_called_once()
        assert self.indication_mock.call_args[0][0].code is (
            CEMIMessageCode.M_PROP_INFO_IND
        )
        send_mock.assert_not_called()

    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    async def test_connection_lost(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a lost TCP connection ends the device management connection."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=DEVICE_STATE,
            )
        )
        await time_travel(0)

        # the TCP connection drops
        self.connection.transport.transport = Mock()
        self.connection.transport._connection_lost()

        with pytest.raises(CommunicationError):
            await task
        assert not self.connection.transport.callbacks
        assert self.connection.communication_channel is None

    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    async def test_unexpected_frames_ignored(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that unrelated incoming frames are ignored."""
        await self._connect(send_mock, time_travel)

        # a request for another communication channel
        self.connection.transport.handle_knxipframe(
            KNXIPFrame.init_from_body(
                DeviceConfigurationRequest(
                    communication_channel_id=CHANNEL + 1,
                    sequence_counter=0,
                    raw_cemi=prop_read_con(b"\x01"),
                )
            ),
            HPAI(*REMOTE_ADDR, protocol=HostProtocol.IPV4_TCP),
        )
        # a frame that is not a DeviceConfigurationRequest
        self.connection._request_received(
            KNXIPFrame.init_from_body(
                DeviceConfigurationAck(communication_channel_id=CHANNEL)
            ),
            HPAI(*REMOTE_ADDR, protocol=HostProtocol.IPV4_TCP),
            None,
        )

        send_mock.assert_not_called()
        assert self.connection.communication_channel == CHANNEL

    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    async def test_send_request_without_connection(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that sending without an open channel raises."""
        cemi = CEMIFrame.from_knx(bytes((0xFC, 0x00, 0x0B, 0x01, 0x45, 0x10, 0x01)))

        with pytest.raises(CommunicationError):
            await self.connection._send_request(cemi)


class TestSecureDeviceManagementConnection:
    """Test class for KNX/IP device management connections over IP Secure."""

    def test_transport(self) -> None:
        """Test that the transport is a secure session with the given credentials."""
        connection = SecureDeviceManagementConnection(
            gateway_ip=REMOTE_ADDR[0],
            gateway_port=REMOTE_ADDR[1],
            user_id=2,
            user_password="password",
            device_authentication_password="authenticate",
        )
        assert isinstance(connection.transport, SecureSession)
        assert connection.transport.remote_addr == REMOTE_ADDR
        assert connection.transport.user_id == 2
        # a lost session ends the device management connection
        assert (  # pylint: disable=comparison-with-callable
            connection.transport._connection_lost_cb
            == connection._transport_connection_lost
        )
