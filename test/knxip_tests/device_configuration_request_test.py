"""Unit test for KNX/IP DeviceConfigurationRequest objects."""
import pytest

from xknx.cemi import CEMIFrame, CEMIMessageCode, CEMIMPropInfo, CEMIMPropReadRequest
from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import DeviceConfigurationRequest, KNXIPFrame
from xknx.profile.const import ResourceKNXNETIPPropertyId, ResourceObjectType


class TestKNXIPDeviceConfigurationRequest:
    """Test class for KNX/IP DeviceConfigurationRequest objects."""

    def test_device_configuration_request(self):
        """Test parsing and streaming device configuration ACK KNX/IP packet."""
        raw = bytes.fromhex("06 10 03 10 00 11 04 2A 17 00 FC 00 0B 01 34 10 01")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, DeviceConfigurationRequest)
        assert knxipframe.body.communication_channel_id == 42
        assert knxipframe.body.sequence_counter == 23
        assert isinstance(knxipframe.body.raw_cemi, bytes)

        incoming_cemi = CEMIFrame.from_knx(knxipframe.body.raw_cemi)
        assert incoming_cemi.code == CEMIMessageCode.M_PROP_READ_REQ
        assert incoming_cemi.data == CEMIMPropReadRequest(
            property_info=CEMIMPropInfo(
                object_type=ResourceObjectType.OBJECT_KNXNETIP_PARAMETER,
                object_instance=1,
                property_id=ResourceKNXNETIPPropertyId.PID_KNX_INDIVIDUAL_ADDRESS,
                start_index=1,
                number_of_elements=1,
            )
        )

        outgoing_cemi = CEMIFrame(
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
        )
        device_configuration_req = DeviceConfigurationRequest(
            communication_channel_id=42,
            sequence_counter=23,
            raw_cemi=outgoing_cemi.to_knx(),
        )
        knxipframe2 = KNXIPFrame.init_from_body(device_configuration_req)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_header(self):
        """Test parsing and streaming wrong DeviceConfigurationRequest (wrong length byte)."""
        raw = bytes((0x06, 0x10, 0x03, 0x10, 0x00, 0x15, 0x03))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_from_knx_wrong_header2(self):
        """Test parsing and streaming wrong DeviceConfigurationRequest (wrong length)."""
        raw = bytes((0x06, 0x10, 0x03, 0x10, 0x00, 0x15, 0x04))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
