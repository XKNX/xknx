"""Unit test for KNX/IP TunnellingRequest objects."""
import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import (
    ErrorCode,
    KNXIPFrame,
    TunnellingFeatureGet,
    TunnellingFeatureInfo,
    TunnellingFeatureResponse,
    TunnellingFeatureSet,
    TunnellingFeatureType,
)


class TestKNXIPTunnellingFeature:
    """Test class for KNX/IP TunnelingFeature objects."""

    def test_get(self):
        """Test parsing and streaming connection tunneling feature get KNX/IP packet."""
        raw = bytes.fromhex("06 10 04 22 00 0c 04 01 17 00 03 00")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, TunnellingFeatureGet)
        assert knxipframe.body.communication_channel_id == 1
        assert knxipframe.body.sequence_counter == 23
        assert (
            knxipframe.body.feature_type == TunnellingFeatureType.BUS_CONNECTION_STATUS
        )
        assert len(knxipframe.body.data) == 0

        tunnelling_request = TunnellingFeatureGet(
            communication_channel_id=1,
            sequence_counter=23,
            feature_type=TunnellingFeatureType.BUS_CONNECTION_STATUS,
        )
        knxipframe2 = KNXIPFrame.init_from_body(tunnelling_request)

        assert knxipframe2.to_knx() == raw

    def test_info(self):
        """Test parsing and streaming connection tunneling feature info KNX/IP packet."""
        raw = bytes.fromhex("06 10 04 25 00 0e 04 01 17 00 03 00 01 00")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, TunnellingFeatureInfo)
        assert knxipframe.body.communication_channel_id == 1
        assert knxipframe.body.sequence_counter == 23
        assert (
            knxipframe.body.feature_type == TunnellingFeatureType.BUS_CONNECTION_STATUS
        )
        assert knxipframe.body.data == b"\x01\x00"

        tunnelling_request = TunnellingFeatureInfo(
            communication_channel_id=1,
            sequence_counter=23,
            feature_type=TunnellingFeatureType.BUS_CONNECTION_STATUS,
            data=b"\x01\x00",
        )
        knxipframe2 = KNXIPFrame.init_from_body(tunnelling_request)

        assert knxipframe2.to_knx() == raw

    def test_response(self):
        """Test parsing and streaming connection tunneling feature response KNX/IP packet."""
        raw = bytes.fromhex("06 10 04 23 00 0e 04 01 17 00 03 00 01 00")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, TunnellingFeatureResponse)
        assert knxipframe.body.communication_channel_id == 1
        assert knxipframe.body.sequence_counter == 23
        assert knxipframe.body.status_code == ErrorCode.E_NO_ERROR
        assert (
            knxipframe.body.feature_type == TunnellingFeatureType.BUS_CONNECTION_STATUS
        )
        assert knxipframe.body.data == b"\x01\x00"

        tunnelling_request = TunnellingFeatureResponse(
            communication_channel_id=1,
            sequence_counter=23,
            status_code=ErrorCode.E_NO_ERROR,
            feature_type=TunnellingFeatureType.BUS_CONNECTION_STATUS,
            data=b"\x01\x00",
        )
        knxipframe2 = KNXIPFrame.init_from_body(tunnelling_request)

        assert knxipframe2.to_knx() == raw

    def test_set(self):
        """Test parsing and streaming connection tunneling feature set KNX/IP packet."""
        raw = bytes.fromhex("06 10 04 24 00 0e 04 01 17 00 08 00 01 00")
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, TunnellingFeatureSet)
        assert knxipframe.body.communication_channel_id == 1
        assert knxipframe.body.sequence_counter == 23
        assert (
            knxipframe.body.feature_type
            == TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE
        )
        assert knxipframe.body.data == b"\x01\x00"

        tunnelling_request = TunnellingFeatureSet(
            communication_channel_id=1,
            sequence_counter=23,
            feature_type=TunnellingFeatureType.INTERFACE_FEATURE_INFO_ENABLE,
            data=b"\x01\x00",
        )
        knxipframe2 = KNXIPFrame.init_from_body(tunnelling_request)

        assert knxipframe2.to_knx() == raw

    def test_from_knx_wrong_header(self):
        """Test parsing and streaming wrong Tunnelling Feature (wrong header length byte)."""
        raw = bytes.fromhex("06 10 04 22 00 0c 06 01 17 00 03 00")
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_get_with_data(self):
        """Test parsing and streaming wrong Get (unexpected data)."""
        raw = bytes.fromhex("06 10 04 22 00 0e 04 01 17 00 03 00 01 00")
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)

    def test_set_without_data(self):
        """Test parsing and streaming wrong Get (missing data)."""
        raw = bytes.fromhex("06 10 04 24 00 0c 04 01 17 00 03 00")
        with pytest.raises(CouldNotParseKNXIP):
            KNXIPFrame.from_knx(raw)
