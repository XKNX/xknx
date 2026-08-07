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
from xknx.io import DeviceManagementConnection
from xknx.io.const import (
    DEVICE_CONFIGURATION_REQUEST_REPETITIONS,
    DEVICE_CONFIGURATION_REQUEST_TIMEOUT,
)
from xknx.knxip import (
    HPAI,
    ConnectRequest,
    ConnectRequestInformation,
    ConnectResponse,
    DeviceConfigurationAck,
    DeviceConfigurationRequest,
    DisconnectRequest,
    DisconnectResponse,
    KNXIPFrame,
)
from xknx.knxip.knxip_enum import ConnectRequestType
from xknx.profile.const import ResourceKNXNETIPPropertyId, ResourceObjectType

from ..conftest import EventLoopClockAdvancer

LOCAL_ADDR = ("192.168.1.1", 12345)
REMOTE_ADDR = ("192.168.1.2", 3671)
CHANNEL = 23


def prop_read_con(data: bytes, number_of_elements: int = 1) -> bytes:
    """Return a M_PropRead.con for the device state property."""
    return CEMIFrame(
        code=CEMIMessageCode.M_PROP_READ_CON,
        data=CEMIMPropReadResponse(
            property_info=CEMIMPropInfo(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_STATE,
                number_of_elements=number_of_elements,
            ),
            data=data,
        ),
    ).to_knx()


class TestDeviceManagementConnection:
    """Test class for KNX/IP device management connections."""

    def setup_method(self) -> None:
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.indication_mock = Mock()
        self.connection = DeviceManagementConnection(
            gateway_ip=REMOTE_ADDR[0],
            gateway_port=REMOTE_ADDR[1],
            local_ip=LOCAL_ADDR[0],
            local_port=LOCAL_ADDR[1],
            indication_callback=self.indication_mock,
        )

    async def _connect(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
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
                    ConnectResponse(communication_channel=CHANNEL)
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
            self.connection.transport.handle_knxipframe(
                KNXIPFrame.init_from_body(
                    DisconnectResponse(communication_channel_id=CHANNEL)
                ),
                HPAI(*REMOTE_ADDR),
            )
            await task

        assert self.connection.communication_channel is None
        assert not self.connection.transport.callbacks

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_read_property(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test reading a property over a device management connection."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.read_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_STATE,
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
                bytes((CEMIErrorCode.CEMI_ERROR_VOID_DP.value,)), number_of_elements=0
            )
        )
        await time_travel(0)

        with pytest.raises(CommunicationError):
            await task

    @patch("xknx.io.transport.udp_transport.UDPTransport.send")
    async def test_write_property(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test writing a property over a device management connection."""
        await self._connect(send_mock, time_travel)

        task = asyncio.create_task(
            self.connection.write_property(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                property_id=ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_STATE,
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
                        property_id=(
                            ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_STATE
                        ),
                    )
                ),
            ).to_knx()
        )
        await time_travel(0)

        await task

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
                    property_id=ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_STATE,
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
    async def test_unacknowledged_request_disconnects(
        self, send_mock: Mock, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test that a request that is never acknowledged closes the connection."""
        await self._connect(send_mock, time_travel)

        with patch("xknx.io.transport.udp_transport.UDPTransport.stop"):
            task = asyncio.create_task(
                self.connection.read_property(
                    object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                    property_id=ResourceKNXNETIPPropertyId.PID_KNXNETIP_DEVICE_STATE,
                )
            )
            # The first try plus every repetition has to time out
            for _ in range(DEVICE_CONFIGURATION_REQUEST_REPETITIONS + 1):
                await time_travel(DEVICE_CONFIGURATION_REQUEST_TIMEOUT)

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
