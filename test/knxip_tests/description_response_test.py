"""Unit test for KNX/IP DescriptionResponse objects."""
from xknx import XKNX
from xknx.knxip import (
    DescriptionResponse,
    DIBDeviceInformation,
    DIBServiceFamily,
    DIBSuppSVCFamilies,
    KNXIPFrame,
)


class TestKNXIPDescriptionResponse:
    """Test class for KNX/IP DescriptionResponse objects."""

    def test_description_response(self):
        """Test parsing and streaming DescriptionResponse KNX/IP packet."""
        raw = (
            0x06,
            0x10,
            0x02,
            0x04,
            0x00,
            0x48,
            0x36,
            0x01,
            0x02,
            0x00,
            0x11,
            0x00,
            0x00,
            0x00,
            0x11,
            0x22,
            0x33,
            0x44,
            0x55,
            0x66,
            0xE0,
            0x00,
            0x17,
            0x0C,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x47,
            0x69,
            0x72,
            0x61,
            0x20,
            0x4B,
            0x4E,
            0x58,
            0x2F,
            0x49,
            0x50,
            0x2D,
            0x52,
            0x6F,
            0x75,
            0x74,
            0x65,
            0x72,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x0C,
            0x02,
            0x02,
            0x01,
            0x03,
            0x02,
            0x04,
            0x01,
            0x05,
            0x01,
            0x07,
            0x01,
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        assert knxipframe.from_knx(raw) == 72
        assert knxipframe.to_knx() == list(raw)

        assert isinstance(knxipframe.body, DescriptionResponse)
        assert len(knxipframe.body.dibs) == 2
        # Specific testing of parsing and serializing of
        # DIBDeviceInformation and DIBSuppSVCFamilies is
        # done within knxip_dib_test.py
        assert isinstance(knxipframe.body.dibs[0], DIBDeviceInformation)
        assert isinstance(knxipframe.body.dibs[1], DIBSuppSVCFamilies)
        assert knxipframe.body.device_name == "Gira KNX/IP-Router"
        assert knxipframe.body.dibs[1].supports(DIBServiceFamily.ROUTING)
        assert knxipframe.body.dibs[1].supports(DIBServiceFamily.TUNNELING)
        assert not knxipframe.body.dibs[1].supports(DIBServiceFamily.OBJECT_SERVER)

        description_response = DescriptionResponse(xknx)
        description_response.dibs.append(knxipframe.body.dibs[0])
        description_response.dibs.append(knxipframe.body.dibs[1])
        knxipframe2 = KNXIPFrame.init_from_body(description_response)

        assert knxipframe2.to_knx() == list(raw)

    def test_unknown_device_name(self):
        """Test device_name if no DIBDeviceInformation is present."""
        xknx = XKNX()
        description_response = DescriptionResponse(xknx)
        assert description_response.device_name == "UNKNOWN"
