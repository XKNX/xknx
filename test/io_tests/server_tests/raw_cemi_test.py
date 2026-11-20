"""Tests for the raw cEMI frames of the KNXnet/IP tunnelling server."""

import pytest

from xknx.cemi import CEMIMessageCode
from xknx.exceptions import CouldNotParseCEMI
from xknx.io.server.properties import (
    property_info_indication,
    property_service_response,
)
from xknx.io.server.raw_cemi import LDataFrame
from xknx.telegram import GroupAddress, IndividualAddress

# L_Data.req with 2 octets of additional information, 1.1.10 to 1/2/3
RAW = bytes.fromhex("1102 0300 bce0 110a 0a03 01 0081")


class TestLDataFrame:
    """Test LDataFrame."""

    def test_fields(self) -> None:
        """Test reading the fields behind the additional information."""
        frame = LDataFrame(RAW)
        assert frame.code is CEMIMessageCode.L_DATA_REQ
        assert frame.source == IndividualAddress("1.1.10")
        assert frame.destination == GroupAddress("1/2/3")
        assert not frame.confirm_error
        assert repr(frame) == f'<LDataFrame code="L_DATA_REQ" raw="{RAW.hex()}" />'

    def test_point_to_point(self) -> None:
        """Test an individual destination address."""
        frame = LDataFrame(bytes.fromhex("2900 b060 110a 1105 00 80"))
        assert frame.destination == IndividualAddress("1.1.5")

    def test_changes(self) -> None:
        """Test changing message code, confirm flag and source."""
        frame = LDataFrame(RAW)
        confirmation = frame.with_code(CEMIMessageCode.L_DATA_CON, confirm_error=True)
        assert confirmation.raw == bytes.fromhex("2e02 0300 bde0 110a 0a03 01 0081")
        assert confirmation.confirm_error
        indication = confirmation.with_code(CEMIMessageCode.L_DATA_IND)
        assert indication.raw == bytes.fromhex("2902 0300 bce0 110a 0a03 01 0081")
        assert frame.with_source(IndividualAddress("1.1.240")).source == (
            IndividualAddress("1.1.240")
        )

    def test_cemi_frame(self) -> None:
        """Test that the CEMIFrame for an interface serializes to the same octets."""
        cemi = LDataFrame(RAW).cemi_frame()
        assert cemi.code is CEMIMessageCode.L_DATA_REQ
        assert cemi.calculated_length() == len(RAW)
        assert cemi.to_knx() == RAW
        assert cemi.data is not None
        assert cemi.data.from_knx(b"\x01").to_knx() == b"\x01"
        assert "_RawCEMIData" in repr(cemi)
        # Routing changes the message code of the frame it sends
        cemi.code = CEMIMessageCode.L_DATA_IND
        assert cemi.to_knx()[0] == CEMIMessageCode.L_DATA_IND.value

    @pytest.mark.parametrize(
        "raw",
        [
            b"",
            bytes.fromhex("fc00"),
            bytes.fromhex("2900bce0110a0a03"),
            bytes.fromhex("2905bce0110a0a030100"),
        ],
    )
    def test_invalid(self, raw: bytes) -> None:
        """Test that anything but a complete L_Data frame is refused."""
        assert LDataFrame.parse(raw) is None
        with pytest.raises(CouldNotParseCEMI):
            LDataFrame(raw)


class TestProperties:
    """Test the property services."""

    @staticmethod
    def _elements(object_type: int, property_id: int) -> list[bytes] | None:
        """Return two elements of property 1 of object type 0."""
        if (object_type, property_id) == (0, 1):
            return [b"\x01", b"\x02"]
        return None

    @pytest.mark.parametrize(
        ("request_hex", "response_hex"),
        [
            # number of elements, both elements, the second one
            ("fc 0000 01 01 1000", "fb 0000 01 01 1000 0002"),
            ("fc 0000 01 01 2001", "fb 0000 01 01 2001 0102"),
            ("fc 0000 01 01 1002", "fb 0000 01 01 1002 02"),
            # index 0 with more than one element, past the end, no element
            ("fc 0000 01 01 2000", "fb 0000 01 01 0000 09"),
            ("fc 0000 01 01 1003", "fb 0000 01 01 0003 09"),
            ("fc 0000 01 01 0001", "fb 0000 01 01 0001 09"),
            # unknown property, object instance, object type
            ("fc 0000 01 02 1001", "fb 0000 01 02 0001 07"),
            ("fc 0000 02 01 1001", "fb 0000 02 01 0001 07"),
            ("fc 0099 01 01 1001", "fb 0099 01 01 0001 07"),
            # write: read only, void, index range
            ("f6 0000 01 01 1001 05", "f5 0000 01 01 0001 05"),
            ("f6 0000 01 02 1001 05", "f5 0000 01 02 0001 07"),
            ("f6 0000 01 01 1005 05", "f5 0000 01 01 0005 09"),
        ],
    )
    def test_property_service_response(
        self, request_hex: str, response_hex: str
    ) -> None:
        """Test the responses and the order of the error checks."""
        assert property_service_response(
            bytes.fromhex(request_hex), self._elements
        ) == bytes.fromhex(response_hex)

    @pytest.mark.parametrize(
        "raw", ["fc 0000 01 01 10", "f1", "1100 bce0 110a 0a03 01"]
    )
    def test_no_property_service(self, raw: str) -> None:
        """Test that other frames aren't answered."""
        assert property_service_response(bytes.fromhex(raw), self._elements) is None

    def test_property_info_indication(self) -> None:
        """Test an M_PropInfo.ind."""
        assert property_info_indication(11, 69, b"\x01") == bytes.fromhex(
            "f7 000b 01 45 1001 01"
        )
