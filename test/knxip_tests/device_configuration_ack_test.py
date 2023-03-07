"""Unit test for KNX/IP DeviceConfigurationAck objects."""
import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import DeviceConfigurationAck, ErrorCode, KNXIPFrame


class TestKNXIPDeviceConfigurationAck:
    """Test class for KNX/IP DeviceConfigurationAck objects."""

    def test_device_configuration_ack(self):
        """Test parsing and streaming device configuration ACK KNX/IP packet."""
        raw = bytes((0x06, 0x10, 0x03, 0x11, 0x00, 0x0A, 0x04, 0x2A, 0x17, 0x00))
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, DeviceConfigurationAck)
        assert knxipframe.body.communication_channel_id == 42
        assert knxipframe.body.sequence_counter == 23
        assert knxipframe.body.status_code == ErrorCode.E_NO_ERROR

        device_configuration_ack = DeviceConfigurationAck(
            communication_channel_id=42,
            sequence_counter=23,
        )
        knxipframe2 = KNXIPFrame.init_from_body(device_configuration_ack)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_ack_information(self):
        """Test parsing and streaming wrong DeviceConfigurationAck (wrong length byte)."""
        raw = bytes((0x06, 0x10, 0x03, 0x11, 0x00, 0x0A, 0x03, 0x2A, 0x17, 0x00))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_from_knx_wrong_ack_information2(self):
        """Test parsing and streaming wrong DeviceConfigurationAck (wrong length)."""
        raw = bytes((0x06, 0x10, 0x03, 0x11, 0x00, 0x0A, 0x04, 0x2A, 0x17))
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
