"""Unit test for KNX/IP DeviceConfiguration Request/Response."""
from unittest.mock import patch

from xknx.cemi import CEMIFrame, CEMIMPropInfo, CEMIMPropReadRequest
from xknx.cemi.const import CEMIMessageCode
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

    async def test_device_configuration(self):
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

        assert device_configuration.awaited_response_class == DeviceConfigurationAck

        exp_knxipframe = KNXIPFrame.init_from_body(device_configuration_request)
        with patch("xknx.io.transport.UDPTransport.send") as mock_udp_send, patch(
            "xknx.io.transport.UDPTransport.getsockname"
        ) as mock_udp_getsockname:
            mock_udp_getsockname.return_value = ("192.168.1.3", 4321)
            await device_configuration.start()
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
        with patch("logging.Logger.debug") as mock_warning:
            device_configuration.response_rec_callback(err_knxipframe, HPAI(), None)
            mock_warning.assert_called_with(
                "Error: KNX bus responded to request of type '%s' with error in '%s': %s",
                type(device_configuration).__name__,
                type(err_knxipframe.body).__name__,
                ErrorCode.E_CONNECTION_ID,
            )

        # Correct Response KNX/IP-Frame:
        res_knxipframe = KNXIPFrame.init_from_body(DeviceConfigurationAck())
        device_configuration.response_rec_callback(res_knxipframe, HPAI(), None)
        assert device_configuration.success
