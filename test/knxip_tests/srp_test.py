"""Unit test for KNX/IP SRP objects."""
import pytest

from xknx.exceptions import ConversionError
from xknx.knxip import DIBServiceFamily, DIBTypeCode, SearchRequestParameterType
from xknx.knxip.srp import Srp


class TestKNXIPSRP:
    """Test class for KNX/IP SRP objects."""

    def test_basic(self):
        """Test SRP with mac contains mac address."""
        srp: Srp = Srp.with_mac_address(bytes([1, 2, 3, 4, 5, 6]))
        assert len(srp) == Srp.SRP_HEADER_SIZE + 6
        assert srp.type == SearchRequestParameterType.SELECT_BY_MAC_ADDRESS

        srp: Srp = Srp.with_service(DIBServiceFamily.TUNNELING, 2)
        assert len(srp) == Srp.SRP_HEADER_SIZE + 2
        assert srp.type == SearchRequestParameterType.SELECT_BY_SERVICE

        srp: Srp = Srp.with_programming_mode()
        assert len(srp) == Srp.SRP_HEADER_SIZE
        assert srp.type == SearchRequestParameterType.SELECT_BY_PROGRAMMING_MODE

        dibs: list[DIBTypeCode] = [
            DIBTypeCode.SUPP_SVC_FAMILIES,
            DIBTypeCode.ADDITIONAL_DEVICE_INFO,
        ]
        srp: Srp = Srp.with_device_description(dibs)
        assert len(srp) == Srp.SRP_HEADER_SIZE + len(dibs)
        assert srp.type == SearchRequestParameterType.REQUEST_DIBS

    def test_invalid_payload_raises(self):
        """Test SRP with invalid data size raises."""
        with pytest.raises(ConversionError):
            Srp.with_mac_address(bytes([1, 2, 3, 4, 5, 6, 7, 8]))

        with pytest.raises(ConversionError):
            Srp(SearchRequestParameterType.SELECT_BY_SERVICE, True)

        with pytest.raises(ConversionError):
            Srp(SearchRequestParameterType.REQUEST_DIBS, True)

    def test_invalid_payload_from_knx_raises(self):
        """Test from_knx with invalid data size raises."""
        # size is too big
        with pytest.raises(ConversionError):
            Srp.from_knx(bytes.fromhex("08 82"))

        # too small
        with pytest.raises(ConversionError):
            Srp.from_knx(bytes.fromhex("08"))

    @pytest.mark.parametrize(
        "srp,expected_bytes",
        [
            (
                Srp.with_mac_address(bytes([1, 2, 3, 4, 5, 6])),
                bytes.fromhex("08 82 01 02 03 04 05 06"),
            ),
            (
                Srp.with_service(DIBServiceFamily.TUNNELING, 2),
                bytes.fromhex("04 83 04 02"),
            ),
            (
                Srp.with_programming_mode(),
                bytes.fromhex("02 81"),
            ),
            (
                Srp.with_device_description(
                    [DIBTypeCode.SUPP_SVC_FAMILIES, DIBTypeCode.TUNNELING_INFO]
                ),
                bytes.fromhex("04 84 02 07"),
            ),
            (
                Srp.with_device_description([DIBTypeCode.SUPP_SVC_FAMILIES]),
                bytes.fromhex("04 84 02 00"),
            ),
        ],
    )
    def test_to_and_from_knx(self, srp, expected_bytes):
        """Test to and from KNX."""
        assert bytes(srp) == expected_bytes
        assert Srp.from_knx(expected_bytes) == srp
