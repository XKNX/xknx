"""Unit test for APCI objects."""
import pytest

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.telegram.address import IndividualAddress
from xknx.telegram.apci import (
    APCI,
    ADCRead,
    ADCResponse,
    AuthorizeRequest,
    AuthorizeResponse,
    DeviceDescriptorRead,
    DeviceDescriptorResponse,
    FunctionPropertyCommand,
    FunctionPropertyStateRead,
    FunctionPropertyStateResponse,
    GroupValueRead,
    GroupValueResponse,
    GroupValueWrite,
    IndividualAddressRead,
    IndividualAddressResponse,
    IndividualAddressSerialRead,
    IndividualAddressSerialResponse,
    IndividualAddressSerialWrite,
    IndividualAddressWrite,
    MemoryExtendedRead,
    MemoryExtendedReadResponse,
    MemoryExtendedWrite,
    MemoryExtendedWriteResponse,
    MemoryRead,
    MemoryResponse,
    MemoryWrite,
    PropertyDescriptionRead,
    PropertyDescriptionResponse,
    PropertyValueRead,
    PropertyValueResponse,
    PropertyValueWrite,
    Restart,
    UserManufacturerInfoRead,
    UserManufacturerInfoResponse,
    UserMemoryRead,
    UserMemoryResponse,
    UserMemoryWrite,
)


class TestAPCI:
    """Test class for APCI objects."""

    def test_resolve_apci_unsupported(self):
        """Test resolve_apci for unsupported services."""

        with pytest.raises(
            ConversionError, match=r".*Class not implemented for APCI.*"
        ):
            # Unsupported user service.
            APCI.from_knx(bytes((0x02, 0xC3)))

        with pytest.raises(
            ConversionError, match=r".*Class not implemented for APCI.*"
        ):
            # Unsupported extended service.
            APCI.from_knx(bytes((0x03, 0xC0)))


class TestGroupValueRead:
    """Test class for GroupValueRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = GroupValueRead()

        assert payload.calculated_length() == 1

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x00, 0x00]))

        assert payload == GroupValueRead()

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = GroupValueRead()

        assert payload.to_knx() == bytes([0x00, 0x00])

    def test_str(self):
        """Test the __str__ method."""
        payload = GroupValueRead()

        assert str(payload) == "<GroupValueRead />"


class TestGroupValueWrite:
    """Test class for GroupValueWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload_a = GroupValueWrite(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueWrite(DPTBinary(1))

        assert payload_a.calculated_length() == 4
        assert payload_b.calculated_length() == 1

    def test_from_knx(self):
        """Test the from_knx method."""
        payload_a = APCI.from_knx(bytes([0x00, 0x80, 0x05, 0x04, 0x03, 0x02, 0x01]))
        payload_b = APCI.from_knx(bytes([0x00, 0x82]))

        assert payload_a == GroupValueWrite(DPTArray((0x05, 0x04, 0x03, 0x02, 0x01)))
        assert payload_b == GroupValueWrite(DPTBinary(0x02))

    def test_to_knx(self):
        """Test the to_knx method."""

        payload_a = GroupValueWrite(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueWrite(DPTBinary(1))

        assert payload_a.to_knx() == bytes([0x00, 0x80, 0x01, 0x02, 0x03])
        assert payload_b.to_knx() == bytes([0x00, 0x81])

    def test_str(self):
        """Test the __str__ method."""
        payload = GroupValueWrite(DPTBinary(1))

        assert str(payload) == '<GroupValueWrite value="<DPTBinary value="1" />" />'


class TestGroupValueResponse:
    """Test class for GroupValueResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload_a = GroupValueResponse(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueResponse(DPTBinary(1))

        assert payload_a.calculated_length() == 4
        assert payload_b.calculated_length() == 1

    def test_from_knx(self):
        """Test the from_knx method."""
        payload_a = APCI.from_knx(bytes([0x00, 0x40, 0x05, 0x04, 0x03, 0x02, 0x01]))
        payload_b = APCI.from_knx(bytes([0x00, 0x42]))

        assert payload_a == GroupValueResponse(DPTArray((0x05, 0x04, 0x03, 0x02, 0x01)))
        assert payload_b == GroupValueResponse(DPTBinary(0x02))

    def test_to_knx(self):
        """Test the to_knx method."""

        payload_a = GroupValueResponse(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueResponse(DPTBinary(1))

        assert payload_a.to_knx() == bytes([0x00, 0x40, 0x01, 0x02, 0x03])
        assert payload_b.to_knx() == bytes([0x00, 0x41])

    def test_str(self):
        """Test the __str__ method."""
        payload = GroupValueResponse(DPTBinary(1))

        assert str(payload) == '<GroupValueResponse value="<DPTBinary value="1" />" />'


class TestIndividualAddressWrite:
    """Test class for IndividualAddressWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressWrite(IndividualAddress("1.2.3"))

        assert payload.calculated_length() == 3

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x00, 0xC0, 0x12, 0x03]))

        assert payload == IndividualAddressWrite(IndividualAddress("1.2.3"))

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressWrite(IndividualAddress("1.2.3"))

        assert payload.to_knx() == bytes([0x00, 0xC0, 0x12, 0x03])

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressWrite(IndividualAddress("1.2.3"))

        assert str(payload) == '<IndividualAddressWrite address="1.2.3" />'


class TestIndividualAddressRead:
    """Test class for IndividualAddressRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressRead()

        assert payload.calculated_length() == 1

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0x00]))

        assert payload == IndividualAddressRead()

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressRead()

        assert payload.to_knx() == bytes([0x01, 0x00])

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressRead()

        assert str(payload) == "<IndividualAddressRead />"


class TestIndividualAddressResponse:
    """Test class for IndividualAddressResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressResponse()

        assert payload.calculated_length() == 1

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0x40]))

        assert payload == IndividualAddressResponse()

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressResponse()

        assert payload.to_knx() == bytes([0x01, 0x40])

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressResponse()

        assert str(payload) == "<IndividualAddressResponse />"


class TestADCRead:
    """Test class for ADCRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = ADCRead(channel=2, count=4)

        assert payload.calculated_length() == 2

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0x82, 0x04]))

        assert payload == ADCRead(channel=2, count=4)

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = ADCRead(channel=1, count=3)

        assert payload.to_knx() == bytes([0x01, 0x81, 0x03])

    def test_str(self):
        """Test the __str__ method."""
        payload = ADCRead(channel=1, count=3)

        assert str(payload) == '<ADCRead channel="1" count="3" />'


class TestADCResponse:
    """Test class for ADCResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = ADCResponse(channel=2, count=4, value=1023)

        assert payload.calculated_length() == 4

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0xC2, 0x04, 0x03, 0xFF]))

        assert payload == ADCResponse(channel=2, count=4, value=1023)

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = ADCResponse(channel=1, count=3, value=456)

        assert payload.to_knx() == bytes([0x01, 0xC1, 0x03, 0x01, 0xC8])

    def test_str(self):
        """Test the __str__ method."""
        payload = ADCResponse(channel=1, count=3, value=456)

        assert str(payload) == '<ADCResponse channel="1" count="3" value="456" />'


class TestMemoryExtendedWrite:
    """Test class for MemoryExtendedWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryExtendedWrite(
            address=0x123456, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )
        assert payload.calculated_length() == 8

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes([0x01, 0xFB, 0x03, 0x12, 0x34, 0x56, 0xAA, 0xBB, 0xCC])
        )

        assert payload == MemoryExtendedWrite(
            address=0x123456, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryExtendedWrite(
            address=0x123456, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes(
            [0x01, 0xFB, 0x03, 0x12, 0x34, 0x56, 0xAA, 0xBB, 0xCC]
        )

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = MemoryExtendedWrite(
            address=0xAABBCCDD, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryExtendedWrite(
            address=0x123456, count=256, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryExtendedWrite(
            address=0x123456, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert (
            str(payload)
            == '<MemoryExtendedWrite address="0x123456" count="3" data="aabbcc" />'
        )


class TestMemoryExtendedWriteResponse:
    """Test class for MemoryExtendedWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryExtendedWriteResponse(return_code=0, address=0x123456)
        assert payload.calculated_length() == 5

    def test_calculated_lengt_with_confirmation_data(self):
        """Test the test_calculated_length method."""
        payload = MemoryExtendedWriteResponse(
            return_code=0, address=0x123456, confirmation_data=bytes([0xAA, 0xBB])
        )
        assert payload.calculated_length() == 7

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0xFC, 0x00, 0x12, 0x34, 0x56]))

        assert payload == MemoryExtendedWriteResponse(
            return_code=0, address=0x123456, confirmation_data=b""
        )

    def test_from_knx_with_confirmation_data(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0xFC, 0x01, 0x12, 0x34, 0x56, 0xAA, 0xBB]))

        assert payload == MemoryExtendedWriteResponse(
            return_code=1, address=0x123456, confirmation_data=bytes([0xAA, 0xBB])
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryExtendedWriteResponse(return_code=0, address=0x123456)

        assert payload.to_knx() == bytes([0x01, 0xFC, 0x00, 0x12, 0x34, 0x56])

    def test_to_knx_with_confirmation_data(self):
        """Test the to_knx method."""
        payload = MemoryExtendedWriteResponse(
            return_code=1, address=0x123456, confirmation_data=bytes([0xAA, 0xBB])
        )

        assert payload.to_knx() == bytes(
            [0x01, 0xFC, 0x01, 0x12, 0x34, 0x56, 0xAA, 0xBB]
        )

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = MemoryExtendedWriteResponse(return_code=0, address=0xAABBCCDD)

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryExtendedWriteResponse(return_code=0x100, address=0x123456)

        with pytest.raises(ConversionError, match=r".*Return code.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryExtendedWriteResponse(return_code=0, address=0x123456)

        assert (
            str(payload)
            == '<MemoryExtendedWriteResponse return_code="0" address="0x123456" confirmation_data="" />'
        )

    def test_str_with_confirmation_data(self):
        """Test the __str__ method."""
        payload = MemoryExtendedWriteResponse(
            return_code=1, address=0x123456, confirmation_data=bytes([0xAA, 0xBB])
        )

        assert (
            str(payload)
            == '<MemoryExtendedWriteResponse return_code="1" address="0x123456" confirmation_data="aabb" />'
        )


class TestMemoryExtendedRead:
    """Test class for MemoryExtendedRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryExtendedRead(address=0x123456, count=3)
        assert payload.calculated_length() == 5

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0xFD, 0x03, 0x12, 0x34, 0x56]))

        assert payload == MemoryExtendedRead(address=0x123456, count=3)

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryExtendedRead(address=0x123456, count=3)

        assert payload.to_knx() == bytes([0x01, 0xFD, 0x03, 0x12, 0x34, 0x56])

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = MemoryExtendedRead(address=0xAABBCCDD, count=3)

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryExtendedRead(address=0x123456, count=256)

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryExtendedRead(address=0x123456, count=3)

        assert str(payload) == '<MemoryExtendedRead count="3" address="0x123456" />'


class TestMemoryExtendedReadResponse:
    """Test class for MemoryExtendedReadResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryExtendedReadResponse(
            return_code=0, address=0x123456, data=bytes([0xAA, 0xBB, 0xCC])
        )
        assert payload.calculated_length() == 8

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes([0x01, 0xFE, 0x00, 0x12, 0x34, 0x56, 0xAA, 0xBB, 0xCC])
        )

        assert payload == MemoryExtendedReadResponse(
            return_code=0, address=0x123456, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryExtendedReadResponse(
            return_code=0, address=0x123456, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes(
            [0x01, 0xFE, 0x00, 0x12, 0x34, 0x56, 0xAA, 0xBB, 0xCC]
        )

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = MemoryExtendedReadResponse(
            return_code=0, address=0xAABBCCDD, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryExtendedReadResponse(
            return_code=0x100, address=0x123456, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Return code.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryExtendedReadResponse(
            return_code=0, address=0x123456, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert (
            str(payload)
            == '<MemoryExtendedReadResponse return_code="0" address="0x123456" data="aabbcc" />'
        )


class TestMemoryRead:
    """Test class for MemoryRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryRead(address=0x1234, count=11)

        assert payload.calculated_length() == 3

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0x0B, 0x12, 0x34]))

        assert payload == MemoryRead(address=0x1234, count=11)

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryRead(address=0x1234, count=11)

        assert payload.to_knx() == bytes([0x02, 0x0B, 0x12, 0x34])

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = MemoryRead(address=0xAABBCCDD, count=11)

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryRead(address=0x1234, count=255)

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryRead(address=0x1234, count=11)

        assert str(payload) == '<MemoryRead address="0x1234" count="11" />'


class TestMemoryWrite:
    """Test class for MemoryWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))

        assert payload.calculated_length() == 6

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0x83, 0x12, 0x34, 0xAA, 0xBB, 0xCC]))

        assert payload == MemoryWrite(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))

        assert payload.to_knx() == bytes([0x02, 0x83, 0x12, 0x34, 0xAA, 0xBB, 0xCC])

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = MemoryWrite(
            address=0xAABBCCDD, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryWrite(address=0x1234, count=255, data=bytes([0xAA, 0xBB, 0xCC]))

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))

        assert (
            str(payload) == '<MemoryWrite address="0x1234" count="3" data="aabbcc" />'
        )


class TestMemoryResponse:
    """Test class for MemoryResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.calculated_length() == 6

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0x43, 0x12, 0x34, 0xAA, 0xBB, 0xCC]))

        assert payload == MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes([0x02, 0x43, 0x12, 0x34, 0xAA, 0xBB, 0xCC])

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = MemoryResponse(
            address=0xAABBCCDD, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryResponse(
            address=0x1234, count=255, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert (
            str(payload)
            == '<MemoryResponse address="0x1234" count="3" data="aabbcc" />'
        )


class TestDeviceDescriptorRead:
    """Test class for DeviceDescriptorRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = DeviceDescriptorRead(0)

        assert payload.calculated_length() == 1

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0x0D]))

        assert payload == DeviceDescriptorRead(13)

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = DeviceDescriptorRead(13)

        assert payload.to_knx() == bytes([0x03, 0x0D])

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = DeviceDescriptorRead(255)

        with pytest.raises(ConversionError, match=r".*Descriptor.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = DeviceDescriptorRead(0)

        assert str(payload) == '<DeviceDescriptorRead descriptor="0" />'


class TestDeviceDescriptorResponse:
    """Test class for DeviceDescriptorResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = DeviceDescriptorResponse(descriptor=0, value=123)

        assert payload.calculated_length() == 3

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0x4D, 0x00, 0x7B]))

        assert payload == DeviceDescriptorResponse(descriptor=13, value=123)

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = DeviceDescriptorResponse(descriptor=13, value=123)

        assert payload.to_knx() == bytes([0x03, 0x4D, 0x00, 0x7B])

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = DeviceDescriptorResponse(255)

        with pytest.raises(ConversionError, match=r".*Descriptor.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = DeviceDescriptorResponse(descriptor=0, value=123)

        assert str(payload) == '<DeviceDescriptorResponse descriptor="0" value="123" />'


class TestUserMemoryRead:
    """Test class for UserMemoryRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = UserMemoryRead()

        assert payload.calculated_length() == 4

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC0, 0x1B, 0x23, 0x45]))

        assert payload == UserMemoryRead(address=0x12345, count=11)

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = UserMemoryRead(address=0x12345, count=11)

        assert payload.to_knx() == bytes([0x02, 0xC0, 0x1B, 0x23, 0x45])

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = UserMemoryRead(address=0xAABBCCDD, count=11)

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = UserMemoryRead(address=0x12345, count=255)

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = UserMemoryRead(address=0x12345, count=11)

        assert str(payload) == '<UserMemoryRead address="0x12345" count="11" />'


class TestUserMemoryWrite:
    """Test class for UserMemoryWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = UserMemoryWrite(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.calculated_length() == 7

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC2, 0x13, 0x23, 0x45, 0xAA, 0xBB, 0xCC]))

        assert payload == UserMemoryWrite(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = UserMemoryWrite(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes(
            [0x02, 0xC2, 0x13, 0x23, 0x45, 0xAA, 0xBB, 0xCC]
        )

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = UserMemoryWrite(
            address=0xAABBCCDD, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = UserMemoryWrite(
            address=0x12345, count=255, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = UserMemoryWrite(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert (
            str(payload)
            == '<UserMemoryWrite address="0x12345" count="3" data="aabbcc" />'
        )


class TestUserMemoryResponse:
    """Test class for UserMemoryResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = UserMemoryResponse(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.calculated_length() == 7

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC1, 0x13, 0x23, 0x45, 0xAA, 0xBB, 0xCC]))

        assert payload == UserMemoryResponse(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = UserMemoryResponse(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes(
            [0x02, 0xC1, 0x13, 0x23, 0x45, 0xAA, 0xBB, 0xCC]
        )

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = UserMemoryResponse(
            address=0xAABBCCDD, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = UserMemoryResponse(
            address=0x12345, count=255, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = UserMemoryResponse(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert (
            str(payload)
            == '<UserMemoryResponse address="0x12345" count="3" data="aabbcc" />'
        )


class TestRestart:
    """Test class for Restart objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = Restart()

        assert payload.calculated_length() == 1

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0x80]))

        assert payload == Restart()

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = Restart()

        assert payload.to_knx() == bytes([0x03, 0x80])

    def test_str(self):
        """Test the __str__ method."""
        payload = Restart()

        assert str(payload) == "<Restart />"


class TestUserManufacturerInfoRead:
    """Test class for UserManufacturerInfoRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = UserManufacturerInfoRead()

        assert payload.calculated_length() == 1

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC5]))

        assert payload == UserManufacturerInfoRead()

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = UserManufacturerInfoRead()

        assert payload.to_knx() == bytes([0x02, 0xC5])

    def test_str(self):
        """Test the __str__ method."""
        payload = UserManufacturerInfoRead()

        assert str(payload) == "<UserManufacturerInfoRead />"


class TestUserManufacturerInfoResponse:
    """Test class for UserManufacturerInfoResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")

        assert payload.calculated_length() == 4

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC6, 0x7B, 0x12, 0x34]))

        assert payload == UserManufacturerInfoResponse(
            manufacturer_id=123, data=b"\x12\x34"
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")

        assert payload.to_knx() == bytes([0x02, 0xC6, 0x7B, 0x12, 0x34])

    def test_str(self):
        """Test the __str__ method."""
        payload = UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")

        assert (
            str(payload)
            == '<UserManufacturerInfoResponse manufacturer_id="123" data="1234" />'
        )


class TestFunctionPropertyCommand:
    """Test class for FunctionPropertyCommand objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 5

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC7, 0x01, 0x04, 0x12, 0x34]))

        assert payload == FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes([0x02, 0xC7, 0x01, 0x04, 0x12, 0x34])

    def test_str(self):
        """Test the __str__ method."""
        payload = FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert (
            str(payload)
            == '<FunctionPropertyCommand object_index="1" property_id="4" data="1234" />'
        )


class TestFunctionPropertyStateRead:
    """Test class for FunctionPropertyStateRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 5

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC8, 0x01, 0x04, 0x12, 0x34]))

        assert payload == FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes([0x02, 0xC8, 0x01, 0x04, 0x12, 0x34])

    def test_str(self):
        """Test the __str__ method."""
        payload = FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert (
            str(payload)
            == '<FunctionPropertyStateRead object_index="1" property_id="4" data="1234" />'
        )


class TestFunctionPropertyStateResponse:
    """Test class for FunctionPropertyStateResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 6

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC9, 0x01, 0x04, 0x08, 0x12, 0x34]))

        assert payload == FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes([0x02, 0xC9, 0x01, 0x04, 0x08, 0x12, 0x34])

    def test_str(self):
        """Test the __str__ method."""
        payload = FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

        assert (
            str(payload)
            == '<FunctionPropertyStateResponse object_index="1" property_id="4" return_code="8" data="1234" />'
        )


class TestAuthorizeRequest:
    """Test class for AuthorizeRequest objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = AuthorizeRequest(key=12345678)

        assert payload.calculated_length() == 6

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD1, 0x00, 0x00, 0xBC, 0x61, 0x4E]))

        assert payload == AuthorizeRequest(key=12345678)

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = AuthorizeRequest(key=12345678)

        assert payload.to_knx() == bytes([0x03, 0xD1, 0x00, 0x00, 0xBC, 0x61, 0x4E])

    def test_str(self):
        """Test the __str__ method."""
        payload = AuthorizeRequest(key=12345678)

        assert str(payload) == '<AuthorizeRequest key="12345678" />'


class TestAuthorizeResponse:
    """Test class for AuthorizeResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = AuthorizeResponse(level=123)

        assert payload.calculated_length() == 2

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD2, 0x7B]))

        assert payload == AuthorizeResponse(level=123)

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = AuthorizeResponse(level=123)

        assert payload.to_knx() == bytes([0x03, 0xD2, 0x7B])

    def test_str(self):
        """Test the __str__ method."""
        payload = AuthorizeResponse(level=123)

        assert str(payload) == '<AuthorizeResponse level="123"/>'


class TestPropertyValueRead:
    """Test class for PropertyValueRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

        assert payload.calculated_length() == 5

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD5, 0x01, 0x04, 0x20, 0x08]))

        assert payload == PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

        assert payload.to_knx() == bytes([0x03, 0xD5, 0x01, 0x04, 0x20, 0x08])

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=32, start_index=8
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

        assert (
            str(payload)
            == '<PropertyValueRead object_index="1" property_id="4" count="2" start_index="8" />'
        )


class TestPropertyValueWrite:
    """Test class for PropertyValueWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 7

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD7, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]))

        assert payload == PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes(
            [0x03, 0xD7, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]
        )

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=32, start_index=8, data=b"\x12\x34"
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert (
            str(payload)
            == '<PropertyValueWrite object_index="1" property_id="4" count="2" start_index="8" data="1234" />'
        )


class TestPropertyValueResponse:
    """Test class for PropertyValueResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 7

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD6, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]))

        assert payload == PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes(
            [0x03, 0xD6, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]
        )

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=32, start_index=8, data=b"\x12\x34"
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert (
            str(payload)
            == '<PropertyValueResponse object_index="1" property_id="4" count="2" start_index="8" data="1234" />'
        )


class TestPropertyDescriptionRead:
    """Test class for PropertyDescriptionRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

        assert payload.calculated_length() == 4

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD8, 0x01, 0x04, 0x08]))

        assert payload == PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

        assert payload.to_knx() == bytes([0x03, 0xD8, 0x01, 0x04, 0x08])

    def test_str(self):
        """Test the __str__ method."""
        payload = PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

        assert (
            str(payload)
            == '<PropertyDescriptionRead object_index="1" property_id="4" property_index="8" />'
        )


class TestPropertyDescriptionResponse:
    """Test class for PropertyDescriptionResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = PropertyDescriptionResponse(
            object_index=1,
            property_id=4,
            property_index=8,
            type_=3,
            max_count=5,
            access=7,
        )

        assert payload.calculated_length() == 8

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes([0x03, 0xD9, 0x01, 0x04, 0x08, 0x03, 0x00, 0x05, 0x07])
        )

        assert payload == PropertyDescriptionResponse(
            object_index=1,
            property_id=4,
            property_index=8,
            type_=3,
            max_count=5,
            access=7,
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = PropertyDescriptionResponse(
            object_index=1,
            property_id=4,
            property_index=8,
            type_=3,
            max_count=5,
            access=7,
        )

        assert payload.to_knx() == bytes(
            [0x03, 0xD9, 0x01, 0x04, 0x08, 0x03, 0x00, 0x05, 0x07]
        )

    def test_to_knx_conversion_error(self):
        """Test the to_knx method for conversion errors."""
        payload = PropertyDescriptionResponse(
            object_index=1,
            property_id=4,
            property_index=8,
            type_=3,
            max_count=4096,
            access=7,
        )

        with pytest.raises(ConversionError, match=r".*Max count.*"):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = PropertyDescriptionResponse(
            object_index=1,
            property_id=4,
            property_index=8,
            type_=3,
            max_count=5,
            access=7,
        )

        assert (
            str(payload)
            == '<PropertyDescriptionResponse object_index="1" property_id="4" property_index="8" type="3" max_count="5" access="7" />'
        )


class TestIndividualAddressSerialRead:
    """Test class for IndividualAddressSerialRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

        assert payload.calculated_length() == 7

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xDC, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33]))

        assert payload == IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

        assert payload.to_knx() == bytes(
            [0x03, 0xDC, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33]
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

        assert str(payload) == '<IndividualAddressSerialRead serial="aabbcc112233" />'


class TestIndividualAddressSerialResponse:
    """Test class for IndividualAddressSerialResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert payload.calculated_length() == 11

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes(
                [0x03, 0xDD, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33, 0x12, 0x03, 0x00, 0x00]
            )
        )

        assert payload == IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert payload.to_knx() == bytes(
            [0x03, 0xDD, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33, 0x12, 0x03, 0x00, 0x00]
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert (
            str(payload)
            == '<IndividualAddressSerialResponse serial="aabbcc112233" address="1.2.3" />'
        )


class TestIndividualAddressSerialWrite:
    """Test class for IndividualAddressSerialWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressSerialWrite(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert payload.calculated_length() == 13

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes(
                [
                    0x03,
                    0xDE,
                    0xAA,
                    0xBB,
                    0xCC,
                    0x11,
                    0x22,
                    0x33,
                    0x12,
                    0x03,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                ]
            )
        )

        assert payload == IndividualAddressSerialWrite(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressSerialWrite(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert payload.to_knx() == bytes(
            [
                0x03,
                0xDE,
                0xAA,
                0xBB,
                0xCC,
                0x11,
                0x22,
                0x33,
                0x12,
                0x03,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressSerialWrite(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert (
            str(payload)
            == '<IndividualAddressSerialWrite serial="aabbcc112233" address="1.2.3" />'
        )
