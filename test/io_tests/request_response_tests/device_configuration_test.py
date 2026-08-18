"""Unit test for KNX/IP DeviceConfiguration Request/Response."""

from unittest.mock import patch

import pytest

from xknx.cemi import CEMIFrame, CEMIMPropInfo, CEMIMPropReadRequest
from xknx.cemi.const import CEMIMessageCode
from xknx.exceptions import RequestResponseError
from xknx.io.const import DEVICE_CONFIGURATION_REQUEST_TIMEOUT
from xknx.io.request_response import DeviceConfiguration
from xknx.io.transport import UDPTransport
from xknx.knxip import (
    HPAI,
    ConnectionStateRequest,
    DeviceConfigurationAck,
    DeviceConfigurationRequest,
    ErrorCode,
    KNXIPFrame,
)
from xknx.profile.const import ResourceKNXNETIPPropertyId, ResourceObjectType


class TestDeviceConfiguration:
    """Test class for xknx/io/DeviceConfiguration objects."""

    async def test_device_configuration(self) -> None:
        """Test device_configuration from KNX bus."""
        data_endpoint = ("192.168.1.2", 4567)
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        raw_cemi = CEMIFrame(
            code=CEMIMessageCode.M_PROP_READ_REQ,
            data=CEMIMPropReadRequest(
                property_info=CEMIMPropInfo(
                    object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                    object_instance=1,
                    property_id=ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS,
                    start_index=1,
                    number_of_elements=1,
                )
            ),
        ).to_knx()
        device_configuration_request = DeviceConfigurationRequest(
            communication_channel_id=23,
            sequence_counter=42,
            raw_cemi=raw_cemi,
        )
        device_configuration = DeviceConfiguration(
            udp_transport, data_endpoint, device_configuration_request
        )
        device_configuration.timeout_in_seconds = 0

        assert device_configuration.AWAITED_RESPONSE_CLASS is DeviceConfigurationAck

        exp_knxipframe = KNXIPFrame.init_from_body(device_configuration_request)
        with (
            patch("xknx.io.transport.UDPTransport.send") as mock_udp_send,
            patch("xknx.io.transport.UDPTransport.getsockname") as mock_udp_getsockname,
        ):
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            with pytest.raises(RequestResponseError):
                await device_configuration.request()
            mock_udp_send.assert_called_with(exp_knxipframe, addr=data_endpoint)

        # Response KNX/IP-Frame with wrong type
        wrong_knxipframe = KNXIPFrame.init_from_body(ConnectionStateRequest())
        with patch("logging.Logger.warning") as mock_warning:
            device_configuration.response_rec_callback(wrong_knxipframe, HPAI(), None)
            mock_warning.assert_called_with("Could not understand knxipframe")

        # Response KNX/IP-Frame with error:
        err_knxipframe = KNXIPFrame.init_from_body(
            DeviceConfigurationAck(status_code=ErrorCode.E_CONNECTION_ID)
        )
        device_configuration.response_rec_callback(err_knxipframe, HPAI(), None)
        assert device_configuration._response is None
        assert device_configuration._error_code is ErrorCode.E_CONNECTION_ID

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame.init_from_body(DeviceConfigurationAck())
        device_configuration.response_rec_callback(res_knxipframe, HPAI(), None)
        assert device_configuration._response is not None

    async def test_default_timeout(self) -> None:
        """Test waiting the DEVICE_CONFIGURATION_REQUEST_TIMEOUT for the acknowledgement."""
        udp_transport = UDPTransport(("192.168.1.1", 0), ("192.168.1.2", 1234))
        device_configuration = DeviceConfiguration(
            udp_transport,
            ("192.168.1.2", 4567),
            DeviceConfigurationRequest(
                communication_channel_id=23,
                sequence_counter=42,
                raw_cemi=bytes((0xFC, 0x00, 0x0B, 0x01, 0x45, 0x10, 0x01)),
            ),
        )
        assert (
            device_configuration.timeout_in_seconds
            == DEVICE_CONFIGURATION_REQUEST_TIMEOUT
            == 10
        )
