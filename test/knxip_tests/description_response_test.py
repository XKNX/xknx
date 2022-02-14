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
        raw = bytes.fromhex(
            "061002040048360102001000000000082d40834de000170c000ab3274a324b4e582f49502d526f7574657200000000000000000000000000000000000c0202020302040205020701",
        )
        xknx = XKNX()
        knxipframe = KNXIPFrame(xknx)
        assert knxipframe.from_knx(raw) == 72
        assert knxipframe.to_knx() == raw

        assert isinstance(knxipframe.body, DescriptionResponse)
        assert len(knxipframe.body.dibs) == 2
        # Specific testing of parsing and serializing of
        # DIBDeviceInformation and DIBSuppSVCFamilies is
        # done within knxip_dib_test.py
        assert isinstance(knxipframe.body.dibs[0], DIBDeviceInformation)
        assert isinstance(knxipframe.body.dibs[1], DIBSuppSVCFamilies)
        assert knxipframe.body.device_name == "KNX/IP-Router"
        assert knxipframe.body.dibs[1].supports(DIBServiceFamily.CORE, version=2)
        assert knxipframe.body.dibs[1].supports(
            DIBServiceFamily.DEVICE_MANAGEMENT, version=2
        )
        assert knxipframe.body.dibs[1].supports(DIBServiceFamily.ROUTING, version=2)
        assert knxipframe.body.dibs[1].supports(DIBServiceFamily.TUNNELING, version=2)
        assert knxipframe.body.dibs[1].supports(
            DIBServiceFamily.REMOTE_CONFIGURATION_DIAGNOSIS
        )
        assert not knxipframe.body.dibs[1].supports(DIBServiceFamily.OBJECT_SERVER)

        description_response = DescriptionResponse(xknx)
        description_response.dibs.append(knxipframe.body.dibs[0])
        description_response.dibs.append(knxipframe.body.dibs[1])
        knxipframe2 = KNXIPFrame.init_from_body(description_response)

        assert knxipframe2.to_knx() == raw

    def test_unknown_device_name(self):
        """Test device_name if no DIBDeviceInformation is present."""
        xknx = XKNX()
        description_response = DescriptionResponse(xknx)
        assert description_response.device_name == "UNKNOWN"
