"""Unit test for APCI objects."""

import pytest

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.telegram.address import GroupAddress, IndividualAddress
from xknx.telegram.apci import (
    APCI,
    ADCRead,
    ADCResponse,
    AuthorizeRequest,
    AuthorizeResponse,
    DeviceDescriptorRead,
    DeviceDescriptorResponse,
    DomainAddressRead,
    DomainAddressResponse,
    DomainAddressSelectiveRead,
    DomainAddressSerialNumberRead,
    DomainAddressSerialNumberResponse,
    DomainAddressSerialNumberWrite,
    DomainAddressWrite,
    FileStreamInfoReport,
    FilterTableOpen,
    FilterTableRead,
    FilterTableResponse,
    FilterTableWrite,
    FunctionPropertyCommand,
    FunctionPropertyExtCommand,
    FunctionPropertyExtStateRead,
    FunctionPropertyExtStateResponse,
    FunctionPropertyStateRead,
    FunctionPropertyStateResponse,
    GroupPropValueInfoReport,
    GroupPropValueRead,
    GroupPropValueResponse,
    GroupPropValueWrite,
    GroupValueRead,
    GroupValueResponse,
    GroupValueWrite,
    IndividualAddressRead,
    IndividualAddressResponse,
    IndividualAddressSerialRead,
    IndividualAddressSerialResponse,
    IndividualAddressSerialWrite,
    IndividualAddressWrite,
    KeyResponse,
    KeyWrite,
    LinkRead,
    LinkResponse,
    LinkWrite,
    MemoryBitWrite,
    MemoryExtendedRead,
    MemoryExtendedReadResponse,
    MemoryExtendedWrite,
    MemoryExtendedWriteResponse,
    MemoryRead,
    MemoryResponse,
    MemoryWrite,
    NetworkParameterRead,
    NetworkParameterResponse,
    NetworkParameterWrite,
    PropertyDescriptionRead,
    PropertyDescriptionResponse,
    PropertyExtDescriptionRead,
    PropertyExtDescriptionResponse,
    PropertyExtValueInfoReport,
    PropertyExtValueRead,
    PropertyExtValueResponse,
    PropertyExtValueWriteCon,
    PropertyExtValueWriteConRes,
    PropertyExtValueWriteUnCon,
    PropertyValueRead,
    PropertyValueResponse,
    PropertyValueWrite,
    Restart,
    RestartMasterReset,
    RestartMasterResetResponse,
    ReturnCode,
    RouterMemoryRead,
    RouterMemoryResponse,
    RouterMemoryWrite,
    RouterStatusRead,
    RouterStatusResponse,
    RouterStatusWrite,
    SystemNetworkParameterRead,
    SystemNetworkParameterResponse,
    SystemNetworkParameterWrite,
    UserManufacturerInfoRead,
    UserManufacturerInfoResponse,
    UserMemoryBitWrite,
    UserMemoryRead,
    UserMemoryResponse,
    UserMemoryWrite,
)


class TestAPCI:
    """Test class for APCI objects."""

    def test_resolve_apci_unsupported(self) -> None:
        """Test resolve_apci for unsupported services."""

        with pytest.raises(
            ConversionError, match=r".*Class not implemented for APCI.*"
        ):
            # Unsupported user service.
            APCI.from_knx(bytes((0x02, 0xC3)))

        with pytest.raises(
            ConversionError, match=r".*Class not implemented for APCI.*"
        ):
            # Unsupported extended service (reserved gap between
            # A_FilterTable_Write and A_RouterMemory_Read).
            APCI.from_knx(bytes((0x03, 0xC4)))


class TestGroupValueRead:
    """Test class for GroupValueRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = GroupValueRead()

        assert payload.calculated_length() == 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x00, 0x00]))

        assert payload == GroupValueRead()

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = GroupValueRead()

        assert payload.to_knx() == bytes([0x00, 0x00])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = GroupValueRead()

        assert str(payload) == "<GroupValueRead />"


class TestGroupValueWrite:
    """Test class for GroupValueWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload_a = GroupValueWrite(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueWrite(DPTBinary(1))

        assert payload_a.calculated_length() == 4
        assert payload_b.calculated_length() == 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload_a = APCI.from_knx(bytes([0x00, 0x80, 0x05, 0x04, 0x03, 0x02, 0x01]))
        payload_b = APCI.from_knx(bytes([0x00, 0x82]))

        assert payload_a == GroupValueWrite(DPTArray((0x05, 0x04, 0x03, 0x02, 0x01)))
        assert payload_b == GroupValueWrite(DPTBinary(0x02))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""

        payload_a = GroupValueWrite(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueWrite(DPTBinary(1))

        assert payload_a.to_knx() == bytes([0x00, 0x80, 0x01, 0x02, 0x03])
        assert payload_b.to_knx() == bytes([0x00, 0x81])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = GroupValueWrite(DPTBinary(1))

        assert str(payload) == '<GroupValueWrite value="<DPTBinary value="1" />" />'


class TestGroupValueResponse:
    """Test class for GroupValueResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload_a = GroupValueResponse(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueResponse(DPTBinary(1))

        assert payload_a.calculated_length() == 4
        assert payload_b.calculated_length() == 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload_a = APCI.from_knx(bytes([0x00, 0x40, 0x05, 0x04, 0x03, 0x02, 0x01]))
        payload_b = APCI.from_knx(bytes([0x00, 0x42]))

        assert payload_a == GroupValueResponse(DPTArray((0x05, 0x04, 0x03, 0x02, 0x01)))
        assert payload_b == GroupValueResponse(DPTBinary(0x02))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""

        payload_a = GroupValueResponse(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueResponse(DPTBinary(1))

        assert payload_a.to_knx() == bytes([0x00, 0x40, 0x01, 0x02, 0x03])
        assert payload_b.to_knx() == bytes([0x00, 0x41])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = GroupValueResponse(DPTBinary(1))

        assert str(payload) == '<GroupValueResponse value="<DPTBinary value="1" />" />'


class TestIndividualAddressWrite:
    """Test class for IndividualAddressWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = IndividualAddressWrite(IndividualAddress("1.2.3"))

        assert payload.calculated_length() == 3

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x00, 0xC0, 0x12, 0x03]))

        assert payload == IndividualAddressWrite(IndividualAddress("1.2.3"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = IndividualAddressWrite(IndividualAddress("1.2.3"))

        assert payload.to_knx() == bytes([0x00, 0xC0, 0x12, 0x03])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = IndividualAddressWrite(IndividualAddress("1.2.3"))

        assert str(payload) == '<IndividualAddressWrite address="1.2.3" />'


class TestIndividualAddressRead:
    """Test class for IndividualAddressRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = IndividualAddressRead()

        assert payload.calculated_length() == 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0x00]))

        assert payload == IndividualAddressRead()

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = IndividualAddressRead()

        assert payload.to_knx() == bytes([0x01, 0x00])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = IndividualAddressRead()

        assert str(payload) == "<IndividualAddressRead />"


class TestIndividualAddressResponse:
    """Test class for IndividualAddressResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = IndividualAddressResponse()

        assert payload.calculated_length() == 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0x40]))

        assert payload == IndividualAddressResponse()

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = IndividualAddressResponse()

        assert payload.to_knx() == bytes([0x01, 0x40])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = IndividualAddressResponse()

        assert str(payload) == "<IndividualAddressResponse />"


class TestADCRead:
    """Test class for ADCRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = ADCRead(channel=2, count=4)

        assert payload.calculated_length() == 2

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0x82, 0x04]))

        assert payload == ADCRead(channel=2, count=4)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = ADCRead(channel=1, count=3)

        assert payload.to_knx() == bytes([0x01, 0x81, 0x03])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = ADCRead(channel=1, count=3)

        assert str(payload) == '<ADCRead channel="1" count="3" />'


class TestADCResponse:
    """Test class for ADCResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = ADCResponse(channel=2, count=4, value=1023)

        assert payload.calculated_length() == 4

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0xC2, 0x04, 0x03, 0xFF]))

        assert payload == ADCResponse(channel=2, count=4, value=1023)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = ADCResponse(channel=1, count=3, value=456)

        assert payload.to_knx() == bytes([0x01, 0xC1, 0x03, 0x01, 0xC8])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = ADCResponse(channel=1, count=3, value=456)

        assert str(payload) == '<ADCResponse channel="1" count="3" value="456" />'


class TestFunctionPropertyExtCommand:
    """Test class for FunctionPropertyExtCommand objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FunctionPropertyExtCommand(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("0000"),
        )

        assert payload.calculated_length() == 8

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01d400110010330000"))

        assert payload == FunctionPropertyExtCommand(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("0000"),
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        # only 6 octets - the ASDU header (interface_object_type +
        # object_instance + property_id) needs 5 octets after the 2 APCI
        # header octets.
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01d400110010"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FunctionPropertyExtCommand(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("0000"),
        )

        assert payload.to_knx() == bytes.fromhex("01d400110010330000")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01d400110010330000")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_interface_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range interface_object_type."""
        payload = FunctionPropertyExtCommand(
            interface_object_type=0x10000, object_instance=1, property_id=51
        )

        with pytest.raises(ConversionError, match=r".*Interface object type.*"):
            payload.to_knx()

    def test_to_knx_object_instance_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_instance."""
        payload = FunctionPropertyExtCommand(
            interface_object_type=17, object_instance=0x1000, property_id=51
        )

        with pytest.raises(ConversionError, match=r".*Object instance.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = FunctionPropertyExtCommand(
            interface_object_type=17, object_instance=1, property_id=0x1000
        )

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = FunctionPropertyExtCommand(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("0000"),
        )

        assert str(payload) == (
            '<FunctionPropertyExtCommand interface_object_type="17" '
            'object_instance="1" property_id="51" data="0000" />'
        )


class TestFunctionPropertyExtStateRead:
    """Test class for FunctionPropertyExtStateRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FunctionPropertyExtStateRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("0000"),
        )

        assert payload.calculated_length() == 8

    def test_from_knx(self) -> None:
        """Test the from_knx method - real frame captured from an ETS session."""
        payload = APCI.from_knx(bytes.fromhex("01d500110010330000"))

        assert payload == FunctionPropertyExtStateRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("0000"),
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        # only 6 octets - the ASDU header (interface_object_type +
        # object_instance + property_id) needs 5 octets after the 2 APCI
        # header octets.
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01d500110010"))

    def test_to_knx(self) -> None:
        """Test the to_knx method round-trips the real captured frame exactly."""
        payload = FunctionPropertyExtStateRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("0000"),
        )

        assert payload.to_knx() == bytes.fromhex("01d500110010330000")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original ETS frame exactly."""
        raw = bytes.fromhex("01d500110010330000")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_interface_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range interface_object_type."""
        payload = FunctionPropertyExtStateRead(
            interface_object_type=0x10000, object_instance=1, property_id=51
        )

        with pytest.raises(ConversionError, match=r".*Interface object type.*"):
            payload.to_knx()

    def test_to_knx_object_instance_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_instance."""
        payload = FunctionPropertyExtStateRead(
            interface_object_type=17, object_instance=0x1000, property_id=51
        )

        with pytest.raises(ConversionError, match=r".*Object instance.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = FunctionPropertyExtStateRead(
            interface_object_type=17, object_instance=1, property_id=0x1000
        )

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = FunctionPropertyExtStateRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("0000"),
        )

        assert str(payload) == (
            '<FunctionPropertyExtStateRead interface_object_type="17" '
            'object_instance="1" property_id="51" data="0000" />'
        )


class TestFunctionPropertyExtStateResponse:
    """Test class for FunctionPropertyExtStateResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FunctionPropertyExtStateResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
            data=bytes.fromhex("0000"),
        )

        assert payload.calculated_length() == 9

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01d60011001033000000"))

        assert payload == FunctionPropertyExtStateResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
            data=bytes.fromhex("0000"),
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        # only 7 octets - the ASDU header (interface_object_type +
        # object_instance + property_id) plus return_code needs 6
        # octets after the 2 APCI header octets.
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01d60011001033"))

    def test_from_knx_invalid_return_code(self) -> None:
        """Test from_knx raises ConversionError for an unknown return code."""
        # return_code byte 0x01 is in the "Generic positive" range (01-1F)
        # reserved by the spec but not assigned to any ReturnCode member.
        with pytest.raises(ConversionError, match=r".*[Ii]nvalid.*return code.*"):
            APCI.from_knx(bytes.fromhex("01d6001100103301"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FunctionPropertyExtStateResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_ERROR,
            data=bytes.fromhex("0000"),
        )

        assert payload.to_knx() == bytes.fromhex("01d60011001033ff0000")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01d60011001033000000")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_interface_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range interface_object_type."""
        payload = FunctionPropertyExtStateResponse(
            interface_object_type=0x10000,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
        )

        with pytest.raises(ConversionError, match=r".*Interface object type.*"):
            payload.to_knx()

    def test_to_knx_object_instance_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_instance."""
        payload = FunctionPropertyExtStateResponse(
            interface_object_type=17,
            object_instance=0x1000,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
        )

        with pytest.raises(ConversionError, match=r".*Object instance.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = FunctionPropertyExtStateResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=0x1000,
            return_code=ReturnCode.E_SUCCESS,
        )

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = FunctionPropertyExtStateResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
            data=bytes.fromhex("0000"),
        )

        assert str(payload) == (
            '<FunctionPropertyExtStateResponse interface_object_type="17" '
            'object_instance="1" property_id="51" '
            'return_code="E_SUCCESS" data="0000" />'
        )


class TestSystemNetworkParameterRead:
    """Test class for SystemNetworkParameterRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = SystemNetworkParameterRead(
            object_type=0, property_id=11, test_info=bytes.fromhex("01")
        )

        assert payload.calculated_length() == 6

    def test_from_knx(self) -> None:
        """
        Test the from_knx method.

        Real world frame observed via ETS bus monitor (system broadcast,
        src 0.0.1, dst 0/0/0): APCI 0x1C8, object_type=0 (Device Object),
        property_id=11 (PID_SERIAL_NUMBER), test_info=01 - the standard
        "which devices are in programming mode" system broadcast.
        """
        payload = APCI.from_knx(bytes.fromhex("01c8000000b001"))

        assert payload == SystemNetworkParameterRead(
            object_type=0, property_id=11, test_info=bytes.fromhex("01")
        )

    def test_from_knx_strips_reserved_bits(self) -> None:
        """Test from_knx discards the reserved 4 bits instead of exposing them."""
        # raw[4]=0x00 (PID high byte), raw[5]=0xbf: upper nibble (0xb)
        # completes property_id=11, lower nibble (0xf) is garbage reserved
        # bits that must not leak into property_id or test_info.
        payload = APCI.from_knx(bytes.fromhex("01c8000000bf01"))

        assert payload == SystemNetworkParameterRead(
            object_type=0, property_id=11, test_info=bytes.fromhex("01")
        )

    def test_from_knx_no_test_info(self) -> None:
        """
        Test from_knx accepts the minimum 6 octet APDU with no test_info.

        Eg. a device signalling "unsupported object type / PID" by
        echoing object_type=0xFFFF, property_id=0xFFF with no test data.
        """
        payload = APCI.from_knx(bytes.fromhex("01c8fffffff0"))

        assert payload == SystemNetworkParameterRead(
            object_type=0xFFFF, property_id=0xFFF, test_info=b""
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        # only 5 octets - the ASDU header (object_type + property_id +
        # reserved) needs 4 octets after the 2 APCI header octets.
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01c8000000"))

    def test_to_knx(self) -> None:
        """Test the to_knx method round-trips the raw ETS frame."""
        payload = SystemNetworkParameterRead(
            object_type=0, property_id=11, test_info=bytes.fromhex("01")
        )

        assert payload.to_knx() == bytes.fromhex("01c8000000b001")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original ETS frame exactly."""
        raw = bytes.fromhex("01c8000000b001")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_round_trip_normalizes_reserved_bits(self) -> None:
        """Test a frame with garbage reserved bits reserializes to its canonical form."""
        dirty = bytes.fromhex("01c8000000bf01")
        canonical = bytes.fromhex("01c8000000b001")

        payload = APCI.from_knx(dirty)
        reserialized = payload.to_knx()

        assert reserialized == canonical
        assert APCI.from_knx(bytes(reserialized)) == payload

    def test_to_knx_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_type."""
        payload = SystemNetworkParameterRead(object_type=0x10000, property_id=0)

        with pytest.raises(ConversionError, match=r".*Object type.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = SystemNetworkParameterRead(object_type=0, property_id=0x1000)

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = SystemNetworkParameterRead(
            object_type=0, property_id=11, test_info=bytes.fromhex("01")
        )

        assert str(payload) == (
            '<SystemNetworkParameterRead object_type="0" property_id="11" '
            'test_info="01" />'
        )


class TestSystemNetworkParameterResponse:
    """Test class for SystemNetworkParameterResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = SystemNetworkParameterResponse(
            object_type=11, property_id=5, test_info_and_result=bytes.fromhex("aabbcc")
        )

        assert payload.calculated_length() == 8

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01c9000b0050aabbcc"))

        assert payload == SystemNetworkParameterResponse(
            object_type=11, property_id=5, test_info_and_result=bytes.fromhex("aabbcc")
        )

    def test_from_knx_strips_reserved_bits(self) -> None:
        """Test from_knx discards the reserved 4 bits instead of exposing them."""
        # raw[5]=0x5f: upper nibble (0x5) completes property_id=5, lower
        # nibble (0xf) is garbage reserved bits that must not leak into
        # property_id or test_info_and_result.
        payload = APCI.from_knx(bytes.fromhex("01c9000b005faabbcc"))

        assert payload == SystemNetworkParameterResponse(
            object_type=11, property_id=5, test_info_and_result=bytes.fromhex("aabbcc")
        )

    def test_from_knx_no_test_info_and_result(self) -> None:
        """
        Test from_knx accepts the minimum 6 octet APDU with no trailing data.

        Eg. a device signalling "unsupported object type / PID" by
        echoing object_type=0xFFFF, property_id=0xFFF with no test data.
        """
        payload = APCI.from_knx(bytes.fromhex("01c9fffffff0"))

        assert payload == SystemNetworkParameterResponse(
            object_type=0xFFFF, property_id=0xFFF, test_info_and_result=b""
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        # only 5 octets - the ASDU header (object_type + property_id +
        # reserved) needs 4 octets after the 2 APCI header octets.
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01c9000b00"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = SystemNetworkParameterResponse(
            object_type=11, property_id=5, test_info_and_result=bytes.fromhex("aabbcc")
        )

        assert payload.to_knx() == bytes.fromhex("01c9000b0050aabbcc")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original bytes exactly."""
        raw = bytes.fromhex("01c9000b0050aabbcc")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_round_trip_normalizes_reserved_bits(self) -> None:
        """Test a frame with garbage reserved bits reserializes to its canonical form."""
        dirty = bytes.fromhex("01c9000b005faabbcc")
        canonical = bytes.fromhex("01c9000b0050aabbcc")

        payload = APCI.from_knx(dirty)
        reserialized = payload.to_knx()

        assert reserialized == canonical
        assert APCI.from_knx(bytes(reserialized)) == payload

    def test_to_knx_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_type."""
        payload = SystemNetworkParameterResponse(object_type=-1, property_id=0)

        with pytest.raises(ConversionError, match=r".*Object type.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = SystemNetworkParameterResponse(object_type=0, property_id=-1)

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = SystemNetworkParameterResponse(
            object_type=11, property_id=5, test_info_and_result=bytes.fromhex("aabbcc")
        )

        assert str(payload) == (
            '<SystemNetworkParameterResponse object_type="11" property_id="5" '
            'test_info_and_result="aabbcc" />'
        )


class TestSystemNetworkParameterWrite:
    """Test class for SystemNetworkParameterWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = SystemNetworkParameterWrite(
            object_type=11, property_id=5, value=bytes.fromhex("aabbcc")
        )

        assert payload.calculated_length() == 8

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01ca000b0050aabbcc"))

        assert payload == SystemNetworkParameterWrite(
            object_type=11, property_id=5, value=bytes.fromhex("aabbcc")
        )

    def test_from_knx_strips_reserved_bits(self) -> None:
        """Test from_knx discards the reserved 4 bits instead of exposing them."""
        # raw[5]=0x5f: upper nibble (0x5) completes property_id=5, lower
        # nibble (0xf) is garbage reserved bits that must not leak into
        # property_id or value.
        payload = APCI.from_knx(bytes.fromhex("01ca000b005faabbcc"))

        assert payload == SystemNetworkParameterWrite(
            object_type=11, property_id=5, value=bytes.fromhex("aabbcc")
        )

    def test_from_knx_no_value(self) -> None:
        """
        Test from_knx accepts the minimum 6 octet APDU with no value.

        Eg. a device signalling "unsupported object type / PID" by
        echoing object_type=0xFFFF, property_id=0xFFF with no value.
        """
        payload = APCI.from_knx(bytes.fromhex("01cafffffff0"))

        assert payload == SystemNetworkParameterWrite(
            object_type=0xFFFF, property_id=0xFFF, value=b""
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        # only 5 octets - the ASDU header (object_type + property_id +
        # reserved) needs 4 octets after the 2 APCI header octets.
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01ca000b00"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = SystemNetworkParameterWrite(
            object_type=11, property_id=5, value=bytes.fromhex("aabbcc")
        )

        assert payload.to_knx() == bytes.fromhex("01ca000b0050aabbcc")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original bytes exactly."""
        raw = bytes.fromhex("01ca000b0050aabbcc")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_round_trip_normalizes_reserved_bits(self) -> None:
        """Test a frame with garbage reserved bits reserializes to its canonical form."""
        dirty = bytes.fromhex("01ca000b005faabbcc")
        canonical = bytes.fromhex("01ca000b0050aabbcc")

        payload = APCI.from_knx(dirty)
        reserialized = payload.to_knx()

        assert reserialized == canonical
        assert APCI.from_knx(bytes(reserialized)) == payload

    def test_to_knx_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_type."""
        payload = SystemNetworkParameterWrite(object_type=-1, property_id=0)

        with pytest.raises(ConversionError, match=r".*Object type.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = SystemNetworkParameterWrite(object_type=0, property_id=-1)

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = SystemNetworkParameterWrite(
            object_type=11, property_id=5, value=bytes.fromhex("aabbcc")
        )

        assert str(payload) == (
            '<SystemNetworkParameterWrite object_type="11" property_id="5" '
            'value="aabbcc" />'
        )


class TestPropertyExtValueRead:
    """Test class for PropertyExtValueRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyExtValueRead(
            interface_object_type=17, object_instance=1, property_id=51
        )

        assert payload.calculated_length() == 9
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01cc0011001033010001"))

        assert payload == PropertyExtValueRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01cc00110010330100"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyExtValueRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
        )

        assert payload.to_knx() == bytes.fromhex("01cc0011001033010001")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01cc0011001033010001")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_nr_of_elem_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range nr_of_elem."""
        payload = PropertyExtValueRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=0x100,
        )

        with pytest.raises(ConversionError, match=r".*Number of elements.*"):
            payload.to_knx()

    def test_to_knx_start_index_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range start_index."""
        payload = PropertyExtValueRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            start_index=0x10000,
        )

        with pytest.raises(ConversionError, match=r".*Start index.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = PropertyExtValueRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
        )

        assert str(payload) == (
            '<PropertyExtValueRead interface_object_type="17" '
            'object_instance="1" property_id="51" nr_of_elem="1" '
            'start_index="1" />'
        )


class TestPropertyExtValueResponse:
    """Test class for PropertyExtValueResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyExtValueResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.calculated_length() == 11
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01cd0011001033010001aabb"))

        assert payload == PropertyExtValueResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

    def test_from_knx_no_data(self) -> None:
        """Test from_knx accepts the minimum 10 octet APDU with no data."""
        payload = APCI.from_knx(bytes.fromhex("01cd0011001033010001"))

        assert payload == PropertyExtValueResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=b"",
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01cd00110010330100"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyExtValueResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

        assert payload.to_knx() == bytes.fromhex("01cd0011001033010001aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01cd0011001033010001aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_nr_of_elem_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range nr_of_elem."""
        payload = PropertyExtValueResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=0x100,
        )

        with pytest.raises(ConversionError, match=r".*Number of elements.*"):
            payload.to_knx()

    def test_to_knx_start_index_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range start_index."""
        payload = PropertyExtValueResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            start_index=0x10000,
        )

        with pytest.raises(ConversionError, match=r".*Start index.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = PropertyExtValueResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

        assert str(payload) == (
            '<PropertyExtValueResponse interface_object_type="17" '
            'object_instance="1" property_id="51" nr_of_elem="1" '
            'start_index="1" data="aabb" />'
        )


class TestPropertyExtValueWriteCon:
    """Test class for PropertyExtValueWriteCon objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyExtValueWriteCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.calculated_length() == 11
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01ce0011001033010001aabb"))

        assert payload == PropertyExtValueWriteCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

    def test_from_knx_no_data(self) -> None:
        """Test from_knx accepts the minimum 10 octet APDU with no data."""
        payload = APCI.from_knx(bytes.fromhex("01ce0011001033010001"))

        assert payload == PropertyExtValueWriteCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=b"",
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01ce00110010330100"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyExtValueWriteCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

        assert payload.to_knx() == bytes.fromhex("01ce0011001033010001aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01ce0011001033010001aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_nr_of_elem_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range nr_of_elem."""
        payload = PropertyExtValueWriteCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=0x100,
        )

        with pytest.raises(ConversionError, match=r".*Number of elements.*"):
            payload.to_knx()

    def test_to_knx_start_index_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range start_index."""
        payload = PropertyExtValueWriteCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            start_index=0x10000,
        )

        with pytest.raises(ConversionError, match=r".*Start index.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = PropertyExtValueWriteCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

        assert str(payload) == (
            '<PropertyExtValueWriteCon interface_object_type="17" '
            'object_instance="1" property_id="51" nr_of_elem="1" '
            'start_index="1" data="aabb" />'
        )


class TestPropertyExtValueWriteConRes:
    """Test class for PropertyExtValueWriteConRes objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyExtValueWriteConRes(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
        )

        assert payload.calculated_length() == 10
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01cf001100103301000100"))

        assert payload == PropertyExtValueWriteConRes(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
            nr_of_elem=1,
            start_index=1,
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01cf0011001033010001"))

    def test_from_knx_invalid_return_code(self) -> None:
        """Test from_knx raises ConversionError for an unknown return code."""
        # return_code byte 0x01 is in the "Generic positive" range (01-1F)
        # reserved by the spec but not assigned to any ReturnCode member.
        with pytest.raises(ConversionError, match=r".*[Ii]nvalid.*return code.*"):
            APCI.from_knx(bytes.fromhex("01cf001100103301000101"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyExtValueWriteConRes(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
            nr_of_elem=1,
            start_index=1,
        )

        assert payload.to_knx() == bytes.fromhex("01cf001100103301000100")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01cf001100103301000100")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_nr_of_elem_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range nr_of_elem."""
        payload = PropertyExtValueWriteConRes(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
            nr_of_elem=0x100,
        )

        with pytest.raises(ConversionError, match=r".*Number of elements.*"):
            payload.to_knx()

    def test_to_knx_start_index_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range start_index."""
        payload = PropertyExtValueWriteConRes(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
            start_index=0x10000,
        )

        with pytest.raises(ConversionError, match=r".*Start index.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = PropertyExtValueWriteConRes(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            return_code=ReturnCode.E_SUCCESS,
            nr_of_elem=1,
            start_index=1,
        )

        assert str(payload) == (
            '<PropertyExtValueWriteConRes interface_object_type="17" '
            'object_instance="1" property_id="51" nr_of_elem="1" '
            'start_index="1" return_code="E_SUCCESS" />'
        )


class TestPropertyExtValueWriteUnCon:
    """Test class for PropertyExtValueWriteUnCon objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyExtValueWriteUnCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.calculated_length() == 11
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01d00011001033010001aabb"))

        assert payload == PropertyExtValueWriteUnCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

    def test_from_knx_no_data(self) -> None:
        """Test from_knx accepts the minimum 10 octet APDU with no data."""
        payload = APCI.from_knx(bytes.fromhex("01d00011001033010001"))

        assert payload == PropertyExtValueWriteUnCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=b"",
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01d000110010330100"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyExtValueWriteUnCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

        assert payload.to_knx() == bytes.fromhex("01d00011001033010001aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01d00011001033010001aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_nr_of_elem_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range nr_of_elem."""
        payload = PropertyExtValueWriteUnCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=0x100,
        )

        with pytest.raises(ConversionError, match=r".*Number of elements.*"):
            payload.to_knx()

    def test_to_knx_start_index_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range start_index."""
        payload = PropertyExtValueWriteUnCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            start_index=0x10000,
        )

        with pytest.raises(ConversionError, match=r".*Start index.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = PropertyExtValueWriteUnCon(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

        assert str(payload) == (
            '<PropertyExtValueWriteUnCon interface_object_type="17" '
            'object_instance="1" property_id="51" nr_of_elem="1" '
            'start_index="1" data="aabb" />'
        )


class TestPropertyExtValueInfoReport:
    """Test class for PropertyExtValueInfoReport objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyExtValueInfoReport(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.calculated_length() == 11
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01d10011001033010001aabb"))

        assert payload == PropertyExtValueInfoReport(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

    def test_from_knx_no_data(self) -> None:
        """Test from_knx accepts the minimum 10 octet APDU with no data."""
        payload = APCI.from_knx(bytes.fromhex("01d10011001033010001"))

        assert payload == PropertyExtValueInfoReport(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=b"",
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01d100110010330100"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyExtValueInfoReport(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

        assert payload.to_knx() == bytes.fromhex("01d10011001033010001aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01d10011001033010001aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_nr_of_elem_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range nr_of_elem."""
        payload = PropertyExtValueInfoReport(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=0x100,
        )

        with pytest.raises(ConversionError, match=r".*Number of elements.*"):
            payload.to_knx()

    def test_to_knx_start_index_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range start_index."""
        payload = PropertyExtValueInfoReport(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            start_index=0x10000,
        )

        with pytest.raises(ConversionError, match=r".*Start index.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = PropertyExtValueInfoReport(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            nr_of_elem=1,
            start_index=1,
            data=bytes.fromhex("aabb"),
        )

        assert str(payload) == (
            '<PropertyExtValueInfoReport interface_object_type="17" '
            'object_instance="1" property_id="51" nr_of_elem="1" '
            'start_index="1" data="aabb" />'
        )


class TestPropertyExtDescriptionRead:
    """Test class for PropertyExtDescriptionRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyExtDescriptionRead(
            interface_object_type=17, object_instance=1, property_id=51
        )

        assert payload.calculated_length() == 8
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01d200110010332005"))

        assert payload == PropertyExtDescriptionRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            description_type=2,
            property_index=5,
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01d2001100103320"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyExtDescriptionRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            description_type=2,
            property_index=5,
        )

        assert payload.to_knx() == bytes.fromhex("01d200110010332005")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01d200110010332005")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_description_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range description_type."""
        payload = PropertyExtDescriptionRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            description_type=0x10,
        )

        with pytest.raises(ConversionError, match=r".*Property description type.*"):
            payload.to_knx()

    def test_to_knx_property_index_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_index."""
        payload = PropertyExtDescriptionRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            property_index=0x1000,
        )

        with pytest.raises(ConversionError, match=r".*Property index.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = PropertyExtDescriptionRead(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            description_type=2,
            property_index=5,
        )

        assert str(payload) == (
            '<PropertyExtDescriptionRead interface_object_type="17" '
            'object_instance="1" property_id="51" description_type="2" '
            'property_index="5" />'
        )


class TestPropertyExtDescriptionResponse:
    """Test class for PropertyExtDescriptionResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyExtDescriptionResponse(
            interface_object_type=17, object_instance=1, property_id=51
        )

        assert payload.calculated_length() == 16
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("01d3001100103320050009000197000130"))

        assert payload == PropertyExtDescriptionResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            description_type=2,
            property_index=5,
            dpt_main=9,
            dpt_sub=1,
            writable=True,
            pdt=0x17,
            max_nr_of_elem=1,
            read_level=3,
            write_level=0,
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("01d3001100103320050009000197000130aa"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyExtDescriptionResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            description_type=2,
            property_index=5,
            dpt_main=9,
            dpt_sub=1,
            writable=True,
            pdt=0x17,
            max_nr_of_elem=1,
            read_level=3,
            write_level=0,
        )

        assert payload.to_knx() == bytes.fromhex("01d3001100103320050009000197000130")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("01d3001100103320050009000197000130")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_pdt_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range pdt."""
        payload = PropertyExtDescriptionResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            pdt=0x40,
        )

        with pytest.raises(ConversionError, match=r".*PDT.*"):
            payload.to_knx()

    def test_to_knx_read_level_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range read_level."""
        payload = PropertyExtDescriptionResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            read_level=0x10,
        )

        with pytest.raises(ConversionError, match=r".*Read level.*"):
            payload.to_knx()

    def test_to_knx_write_level_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range write_level."""
        payload = PropertyExtDescriptionResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            write_level=0x10,
        )

        with pytest.raises(ConversionError, match=r".*Write level.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = PropertyExtDescriptionResponse(
            interface_object_type=17,
            object_instance=1,
            property_id=51,
            description_type=2,
            property_index=5,
            dpt_main=9,
            dpt_sub=1,
            writable=True,
            pdt=0x17,
            max_nr_of_elem=1,
            read_level=3,
            write_level=0,
        )

        assert str(payload) == (
            '<PropertyExtDescriptionResponse interface_object_type="17" '
            'object_instance="1" property_id="51" description_type="2" '
            'property_index="5" dpt_main="9" dpt_sub="1" writable="True" '
            'pdt="23" max_nr_of_elem="1" read_level="3" write_level="0" />'
        )


class TestMemoryExtendedWrite:
    """Test class for MemoryExtendedWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = MemoryExtendedWrite(
            address=0x123456, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )
        assert payload.calculated_length() == 8

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes([0x01, 0xFB, 0x03, 0x12, 0x34, 0x56, 0xAA, 0xBB, 0xCC])
        )

        assert payload == MemoryExtendedWrite(
            address=0x123456, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = MemoryExtendedWrite(
            address=0x123456, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes(
            [0x01, 0xFB, 0x03, 0x12, 0x34, 0x56, 0xAA, 0xBB, 0xCC]
        )

    def test_to_knx_conversion_error(self) -> None:
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

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = MemoryExtendedWriteResponse(return_code=0, address=0x123456)
        assert payload.calculated_length() == 5

    def test_calculated_lengt_with_confirmation_data(self) -> None:
        """Test the test_calculated_length method."""
        payload = MemoryExtendedWriteResponse(
            return_code=0, address=0x123456, confirmation_data=bytes([0xAA, 0xBB])
        )
        assert payload.calculated_length() == 7

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0xFC, 0x00, 0x12, 0x34, 0x56]))

        assert payload == MemoryExtendedWriteResponse(
            return_code=0, address=0x123456, confirmation_data=b""
        )

    def test_from_knx_with_confirmation_data(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0xFC, 0x01, 0x12, 0x34, 0x56, 0xAA, 0xBB]))

        assert payload == MemoryExtendedWriteResponse(
            return_code=1, address=0x123456, confirmation_data=bytes([0xAA, 0xBB])
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = MemoryExtendedWriteResponse(return_code=0, address=0x123456)

        assert payload.to_knx() == bytes([0x01, 0xFC, 0x00, 0x12, 0x34, 0x56])

    def test_to_knx_with_confirmation_data(self) -> None:
        """Test the to_knx method."""
        payload = MemoryExtendedWriteResponse(
            return_code=1, address=0x123456, confirmation_data=bytes([0xAA, 0xBB])
        )

        assert payload.to_knx() == bytes(
            [0x01, 0xFC, 0x01, 0x12, 0x34, 0x56, 0xAA, 0xBB]
        )

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = MemoryExtendedWriteResponse(return_code=0, address=0xAABBCCDD)

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryExtendedWriteResponse(return_code=0x100, address=0x123456)

        with pytest.raises(ConversionError, match=r".*Return code.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = MemoryExtendedWriteResponse(return_code=0, address=0x123456)

        assert (
            str(payload)
            == '<MemoryExtendedWriteResponse return_code="0" address="0x123456" confirmation_data="" />'
        )

    def test_str_with_confirmation_data(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = MemoryExtendedRead(address=0x123456, count=3)
        assert payload.calculated_length() == 5

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x01, 0xFD, 0x03, 0x12, 0x34, 0x56]))

        assert payload == MemoryExtendedRead(address=0x123456, count=3)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = MemoryExtendedRead(address=0x123456, count=3)

        assert payload.to_knx() == bytes([0x01, 0xFD, 0x03, 0x12, 0x34, 0x56])

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = MemoryExtendedRead(address=0xAABBCCDD, count=3)

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryExtendedRead(address=0x123456, count=256)

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = MemoryExtendedRead(address=0x123456, count=3)

        assert str(payload) == '<MemoryExtendedRead count="3" address="0x123456" />'


class TestMemoryExtendedReadResponse:
    """Test class for MemoryExtendedReadResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = MemoryExtendedReadResponse(
            return_code=0, address=0x123456, data=bytes([0xAA, 0xBB, 0xCC])
        )
        assert payload.calculated_length() == 8

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes([0x01, 0xFE, 0x00, 0x12, 0x34, 0x56, 0xAA, 0xBB, 0xCC])
        )

        assert payload == MemoryExtendedReadResponse(
            return_code=0, address=0x123456, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = MemoryExtendedReadResponse(
            return_code=0, address=0x123456, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes(
            [0x01, 0xFE, 0x00, 0x12, 0x34, 0x56, 0xAA, 0xBB, 0xCC]
        )

    def test_to_knx_conversion_error(self) -> None:
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

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = MemoryRead(address=0x1234, count=11)

        assert payload.calculated_length() == 3

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0x0B, 0x12, 0x34]))

        assert payload == MemoryRead(address=0x1234, count=11)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = MemoryRead(address=0x1234, count=11)

        assert payload.to_knx() == bytes([0x02, 0x0B, 0x12, 0x34])

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = MemoryRead(address=0xAABBCCDD, count=11)

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryRead(address=0x1234, count=255)

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = MemoryRead(address=0x1234, count=11)

        assert str(payload) == '<MemoryRead address="0x1234" count="11" />'


class TestMemoryWrite:
    """Test class for MemoryWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))

        assert payload.calculated_length() == 6

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0x83, 0x12, 0x34, 0xAA, 0xBB, 0xCC]))

        assert payload == MemoryWrite(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))

        assert payload.to_knx() == bytes([0x02, 0x83, 0x12, 0x34, 0xAA, 0xBB, 0xCC])

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = MemoryWrite(
            address=0xAABBCCDD, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = MemoryWrite(address=0x1234, count=255, data=bytes([0xAA, 0xBB, 0xCC]))

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))

        assert (
            str(payload) == '<MemoryWrite address="0x1234" count="3" data="aabbcc" />'
        )


class TestMemoryResponse:
    """Test class for MemoryResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.calculated_length() == 6

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0x43, 0x12, 0x34, 0xAA, 0xBB, 0xCC]))

        assert payload == MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes([0x02, 0x43, 0x12, 0x34, 0xAA, 0xBB, 0xCC])

    def test_to_knx_conversion_error(self) -> None:
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

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = DeviceDescriptorRead(0)

        assert payload.calculated_length() == 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0x0D]))

        assert payload == DeviceDescriptorRead(13)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = DeviceDescriptorRead(13)

        assert payload.to_knx() == bytes([0x03, 0x0D])

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = DeviceDescriptorRead(255)

        with pytest.raises(ConversionError, match=r".*Descriptor.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = DeviceDescriptorRead(0)

        assert str(payload) == '<DeviceDescriptorRead descriptor="0" />'


class TestDeviceDescriptorResponse:
    """Test class for DeviceDescriptorResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = DeviceDescriptorResponse(descriptor=0, value=123)

        assert payload.calculated_length() == 3

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0x4D, 0x00, 0x7B]))

        assert payload == DeviceDescriptorResponse(descriptor=13, value=123)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = DeviceDescriptorResponse(descriptor=13, value=123)

        assert payload.to_knx() == bytes([0x03, 0x4D, 0x00, 0x7B])

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = DeviceDescriptorResponse(255)

        with pytest.raises(ConversionError, match=r".*Descriptor.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = DeviceDescriptorResponse(descriptor=0, value=123)

        assert str(payload) == '<DeviceDescriptorResponse descriptor="0" value="123" />'


class TestUserMemoryRead:
    """Test class for UserMemoryRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = UserMemoryRead()

        assert payload.calculated_length() == 4

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC0, 0x1B, 0x23, 0x45]))

        assert payload == UserMemoryRead(address=0x12345, count=11)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = UserMemoryRead(address=0x12345, count=11)

        assert payload.to_knx() == bytes([0x02, 0xC0, 0x1B, 0x23, 0x45])

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = UserMemoryRead(address=0xAABBCCDD, count=11)

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

        payload = UserMemoryRead(address=0x12345, count=255)

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = UserMemoryRead(address=0x12345, count=11)

        assert str(payload) == '<UserMemoryRead address="0x12345" count="11" />'


class TestUserMemoryWrite:
    """Test class for UserMemoryWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = UserMemoryWrite(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.calculated_length() == 7

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC2, 0x13, 0x23, 0x45, 0xAA, 0xBB, 0xCC]))

        assert payload == UserMemoryWrite(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = UserMemoryWrite(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes(
            [0x02, 0xC2, 0x13, 0x23, 0x45, 0xAA, 0xBB, 0xCC]
        )

    def test_to_knx_conversion_error(self) -> None:
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

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = UserMemoryResponse(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.calculated_length() == 7

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC1, 0x13, 0x23, 0x45, 0xAA, 0xBB, 0xCC]))

        assert payload == UserMemoryResponse(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = UserMemoryResponse(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert payload.to_knx() == bytes(
            [0x02, 0xC1, 0x13, 0x23, 0x45, 0xAA, 0xBB, 0xCC]
        )

    def test_to_knx_conversion_error(self) -> None:
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

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = UserMemoryResponse(
            address=0x12345, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        assert (
            str(payload)
            == '<UserMemoryResponse address="0x12345" count="3" data="aabbcc" />'
        )


class TestUserMemoryBitWrite:
    """Test class for UserMemoryBitWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = UserMemoryBitWrite(
            address=0x1234, and_data=bytes([0xAA, 0xBB]), xor_data=bytes([0x11, 0x22])
        )

        assert payload.calculated_length() == 8
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes([0x02, 0xC4, 0x02, 0x12, 0x34, 0xAA, 0xBB, 0x11, 0x22])
        )

        assert payload == UserMemoryBitWrite(
            address=0x1234, and_data=bytes([0xAA, 0xBB]), xor_data=bytes([0x11, 0x22])
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a mismatched number/length."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            # number=2 but only 1 octet of and_data/xor_data follows
            APCI.from_knx(bytes([0x02, 0xC4, 0x02, 0x12, 0x34, 0xAA, 0x11]))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = UserMemoryBitWrite(
            address=0x1234, and_data=bytes([0xAA, 0xBB]), xor_data=bytes([0x11, 0x22])
        )

        assert payload.to_knx() == bytes(
            [0x02, 0xC4, 0x02, 0x12, 0x34, 0xAA, 0xBB, 0x11, 0x22]
        )

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes([0x02, 0xC4, 0x02, 0x12, 0x34, 0xAA, 0xBB, 0x11, 0x22])

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_address_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range address."""
        payload = UserMemoryBitWrite(
            address=0x10000, and_data=bytes([0xAA]), xor_data=bytes([0x11])
        )

        with pytest.raises(ConversionError, match=r".*Address.*"):
            payload.to_knx()

    def test_to_knx_mismatched_data_length(self) -> None:
        """Test to_knx raises ConversionError when and_data/xor_data lengths differ."""
        payload = UserMemoryBitWrite(
            address=0x1234, and_data=bytes([0xAA, 0xBB]), xor_data=bytes([0x11])
        )

        with pytest.raises(
            ConversionError, match=r".*and_data and xor_data.*same length.*"
        ):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = UserMemoryBitWrite(
            address=0x1234, and_data=bytes([0xAA, 0xBB]), xor_data=bytes([0x11, 0x22])
        )

        assert str(payload) == (
            '<UserMemoryBitWrite address="0x1234" and_data="aabb" xor_data="1122" />'
        )


class TestRestart:
    """Test class for Restart objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = Restart()

        assert payload.calculated_length() == 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0x80]))

        assert payload == Restart()

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = Restart()

        assert payload.to_knx() == bytes([0x03, 0x80])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = Restart()

        assert str(payload) == "<Restart />"


class TestRestartMasterReset:
    """Test class for RestartMasterReset objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = RestartMasterReset(erase_code=1, channel_number=0)

        assert payload.calculated_length() == 3

    def test_from_knx(self) -> None:
        """Test the from_knx method - real frame captured from an ETS session."""
        payload = APCI.from_knx(bytes.fromhex("03810100"))

        assert payload == RestartMasterReset(erase_code=1, channel_number=0)

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("038101"))

    def test_to_knx(self) -> None:
        """Test the to_knx method round-trips the real captured frame exactly."""
        payload = RestartMasterReset(erase_code=1, channel_number=0)

        assert payload.to_knx() == bytes.fromhex("03810100")

    def test_to_knx_erase_code_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range erase_code."""
        payload = RestartMasterReset(erase_code=0x100, channel_number=0)

        with pytest.raises(ConversionError, match=r".*Erase code.*"):
            payload.to_knx()

    def test_to_knx_channel_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range channel_number."""
        payload = RestartMasterReset(erase_code=1, channel_number=0x100)

        with pytest.raises(ConversionError, match=r".*Channel number.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = RestartMasterReset(erase_code=1, channel_number=0)

        assert (
            str(payload) == '<RestartMasterReset erase_code="1" channel_number="0" />'
        )


class TestRestartMasterResetResponse:
    """Test class for RestartMasterResetResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = RestartMasterResetResponse(error_code=0, process_time=1000)

        assert payload.calculated_length() == 4

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03a10003e8"))

        assert payload == RestartMasterResetResponse(error_code=0, process_time=1000)

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03a10003"))

    def test_to_knx(self) -> None:
        """Test the to_knx method round-trips exactly."""
        payload = RestartMasterResetResponse(error_code=0, process_time=1000)

        assert payload.to_knx() == bytes.fromhex("03a10003e8")

    def test_to_knx_error_code_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range error_code."""
        payload = RestartMasterResetResponse(error_code=0x100, process_time=1000)

        with pytest.raises(ConversionError, match=r".*Error code.*"):
            payload.to_knx()

    def test_to_knx_process_time_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range process_time."""
        payload = RestartMasterResetResponse(error_code=0, process_time=0x10000)

        with pytest.raises(ConversionError, match=r".*Process time.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = RestartMasterResetResponse(error_code=0, process_time=1000)

        assert str(payload) == (
            '<RestartMasterResetResponse error_code="0" process_time="1000" />'
        )


class TestUserManufacturerInfoRead:
    """Test class for UserManufacturerInfoRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = UserManufacturerInfoRead()

        assert payload.calculated_length() == 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC5]))

        assert payload == UserManufacturerInfoRead()

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = UserManufacturerInfoRead()

        assert payload.to_knx() == bytes([0x02, 0xC5])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = UserManufacturerInfoRead()

        assert str(payload) == "<UserManufacturerInfoRead />"


class TestUserManufacturerInfoResponse:
    """Test class for UserManufacturerInfoResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")

        assert payload.calculated_length() == 4

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC6, 0x7B, 0x12, 0x34]))

        assert payload == UserManufacturerInfoResponse(
            manufacturer_id=123, data=b"\x12\x34"
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")

        assert payload.to_knx() == bytes([0x02, 0xC6, 0x7B, 0x12, 0x34])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")

        assert (
            str(payload)
            == '<UserManufacturerInfoResponse manufacturer_id="123" data="1234" />'
        )


class TestFunctionPropertyCommand:
    """Test class for FunctionPropertyCommand objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 5

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC7, 0x01, 0x04, 0x12, 0x34]))

        assert payload == FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes([0x02, 0xC7, 0x01, 0x04, 0x12, 0x34])

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 5

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC8, 0x01, 0x04, 0x12, 0x34]))

        assert payload == FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes([0x02, 0xC8, 0x01, 0x04, 0x12, 0x34])

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 6

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x02, 0xC9, 0x01, 0x04, 0x08, 0x12, 0x34]))

        assert payload == FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes([0x02, 0xC9, 0x01, 0x04, 0x08, 0x12, 0x34])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

        assert (
            str(payload)
            == '<FunctionPropertyStateResponse object_index="1" property_id="4" return_code="8" data="1234" />'
        )


class TestFilterTableOpen:
    """Test class for FilterTableOpen objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FilterTableOpen()

        assert payload.calculated_length() == 1
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes((0x03, 0xC0)))

        assert payload == FilterTableOpen()

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FilterTableOpen()

        assert payload.to_knx() == bytes((0x03, 0xC0))

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = FilterTableOpen()

        assert str(payload) == "<FilterTableOpen />"


class TestFilterTableRead:
    """Test class for FilterTableRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FilterTableRead(filter_table_address=0x1234, number=5)

        assert payload.calculated_length() == 4
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03c1051234"))

        assert payload == FilterTableRead(filter_table_address=0x1234, number=5)

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03c10512"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FilterTableRead(filter_table_address=0x1234, number=5)

        assert payload.to_knx() == bytes.fromhex("03c1051234")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03c1051234")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range number."""
        payload = FilterTableRead(filter_table_address=0x1234, number=255)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_number_zero(self) -> None:
        """Test to_knx raises ConversionError for number=0 (not valid for a read)."""
        payload = FilterTableRead(filter_table_address=0x1234, number=0)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_address_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range address."""
        payload = FilterTableRead(filter_table_address=0x10000, number=5)

        with pytest.raises(ConversionError, match=r".*Filter table address.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = FilterTableRead(filter_table_address=0x1234, number=5)

        assert str(payload) == (
            '<FilterTableRead filter_table_address="0x1234" number="5" />'
        )


class TestFilterTableResponse:
    """Test class for FilterTableResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FilterTableResponse(
            filter_table_address=0x1234, data=bytes([0xAA, 0xBB])
        )

        assert payload.calculated_length() == 6
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03c2021234aabb"))

        assert payload == FilterTableResponse(
            filter_table_address=0x1234, number=2, data=bytes([0xAA, 0xBB])
        )

    def test_from_knx_error_response(self) -> None:
        """Test from_knx accepts the number=0/no-data error response."""
        payload = APCI.from_knx(bytes.fromhex("03c2001234"))

        assert payload == FilterTableResponse(
            filter_table_address=0x1234, number=0, data=b""
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03c20212"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FilterTableResponse(
            filter_table_address=0x1234, data=bytes([0xAA, 0xBB])
        )

        assert payload.to_knx() == bytes.fromhex("03c2021234aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03c2021234aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range number."""
        payload = FilterTableResponse(filter_table_address=0x1234, data=b"", number=255)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_number_zero_error_response(self) -> None:
        """Test to_knx accepts number=0 (the documented error response)."""
        payload = FilterTableResponse(filter_table_address=0x1234, data=b"", number=0)

        assert payload.to_knx() == bytes.fromhex("03c2001234")

    def test_to_knx_address_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range address."""
        payload = FilterTableResponse(filter_table_address=0x10000, data=b"")

        with pytest.raises(ConversionError, match=r".*Filter table address.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = FilterTableResponse(
            filter_table_address=0x1234, data=bytes([0xAA, 0xBB])
        )

        assert str(payload) == (
            '<FilterTableResponse filter_table_address="0x1234" number="2" '
            'data="aabb" />'
        )


class TestFilterTableWrite:
    """Test class for FilterTableWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FilterTableWrite(
            filter_table_address=0x1234, data=bytes([0xAA, 0xBB])
        )

        assert payload.calculated_length() == 6
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03c3021234aabb"))

        assert payload == FilterTableWrite(
            filter_table_address=0x1234, number=2, data=bytes([0xAA, 0xBB])
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03c3021234"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FilterTableWrite(
            filter_table_address=0x1234, data=bytes([0xAA, 0xBB])
        )

        assert payload.to_knx() == bytes.fromhex("03c3021234aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03c3021234aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range number."""
        payload = FilterTableWrite(filter_table_address=0x1234, data=b"", number=255)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_number_zero(self) -> None:
        """Test to_knx raises ConversionError for number=0 (not valid for a write)."""
        payload = FilterTableWrite(filter_table_address=0x1234, data=b"", number=0)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_address_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range address."""
        payload = FilterTableWrite(filter_table_address=0x10000, data=bytes([0xAA]))

        with pytest.raises(ConversionError, match=r".*Filter table address.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = FilterTableWrite(
            filter_table_address=0x1234, data=bytes([0xAA, 0xBB])
        )

        assert str(payload) == (
            '<FilterTableWrite filter_table_address="0x1234" number="2" data="aabb" />'
        )


class TestRouterMemoryRead:
    """Test class for RouterMemoryRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = RouterMemoryRead(memory_address=0x1234, number=5)

        assert payload.calculated_length() == 4
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03c8051234"))

        assert payload == RouterMemoryRead(memory_address=0x1234, number=5)

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03c80512"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = RouterMemoryRead(memory_address=0x1234, number=5)

        assert payload.to_knx() == bytes.fromhex("03c8051234")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03c8051234")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range number."""
        payload = RouterMemoryRead(memory_address=0x1234, number=255)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_number_zero(self) -> None:
        """Test to_knx raises ConversionError for number=0 (not valid for a read)."""
        payload = RouterMemoryRead(memory_address=0x1234, number=0)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_address_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range address."""
        payload = RouterMemoryRead(memory_address=0x10000, number=5)

        with pytest.raises(ConversionError, match=r".*Memory address.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = RouterMemoryRead(memory_address=0x1234, number=5)

        assert str(payload) == (
            '<RouterMemoryRead memory_address="0x1234" number="5" />'
        )


class TestRouterMemoryResponse:
    """Test class for RouterMemoryResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = RouterMemoryResponse(memory_address=0x1234, data=bytes([0xAA, 0xBB]))

        assert payload.calculated_length() == 6
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03c9021234aabb"))

        assert payload == RouterMemoryResponse(
            memory_address=0x1234, number=2, data=bytes([0xAA, 0xBB])
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03c90212"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = RouterMemoryResponse(memory_address=0x1234, data=bytes([0xAA, 0xBB]))

        assert payload.to_knx() == bytes.fromhex("03c9021234aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03c9021234aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range number."""
        payload = RouterMemoryResponse(memory_address=0x1234, data=b"", number=255)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_address_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range address."""
        payload = RouterMemoryResponse(memory_address=0x10000, data=b"")

        with pytest.raises(ConversionError, match=r".*Memory address.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = RouterMemoryResponse(memory_address=0x1234, data=bytes([0xAA, 0xBB]))

        assert str(payload) == (
            '<RouterMemoryResponse memory_address="0x1234" number="2" data="aabb" />'
        )


class TestRouterMemoryWrite:
    """Test class for RouterMemoryWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = RouterMemoryWrite(memory_address=0x1234, data=bytes([0xAA, 0xBB]))

        assert payload.calculated_length() == 6
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03ca021234aabb"))

        assert payload == RouterMemoryWrite(
            memory_address=0x1234, number=2, data=bytes([0xAA, 0xBB])
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03ca021234"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = RouterMemoryWrite(memory_address=0x1234, data=bytes([0xAA, 0xBB]))

        assert payload.to_knx() == bytes.fromhex("03ca021234aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03ca021234aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range number."""
        payload = RouterMemoryWrite(memory_address=0x1234, data=b"", number=255)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_number_zero(self) -> None:
        """Test to_knx raises ConversionError for number=0 (not valid for a write)."""
        payload = RouterMemoryWrite(memory_address=0x1234, data=b"", number=0)

        with pytest.raises(ConversionError, match=r".*Number.*"):
            payload.to_knx()

    def test_to_knx_address_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range address."""
        payload = RouterMemoryWrite(memory_address=0x10000, data=bytes([0xAA]))

        with pytest.raises(ConversionError, match=r".*Memory address.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = RouterMemoryWrite(memory_address=0x1234, data=bytes([0xAA, 0xBB]))

        assert str(payload) == (
            '<RouterMemoryWrite memory_address="0x1234" number="2" data="aabb" />'
        )


class TestRouterStatusRead:
    """Test class for RouterStatusRead objects."""

    def test_from_knx_dispatches_and_raises_not_implemented(self) -> None:
        """Test the APCI is routed to the class, which raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match=r".*A_RouterStatus_Read.*"):
            APCI.from_knx(bytes((0x03, 0xCD)))

    def test_to_knx_raises_not_implemented(self) -> None:
        """Test to_knx raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match=r".*A_RouterStatus_Read.*"):
            RouterStatusRead().to_knx()

    def test_calculated_length_raises_not_implemented(self) -> None:
        """Test calculated_length raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match=r".*A_RouterStatus_Read.*"):
            RouterStatusRead().calculated_length()

    def test_str(self) -> None:
        """Test the __str__ method."""
        assert str(RouterStatusRead()) == "<RouterStatusRead (not implemented) />"


class TestRouterStatusResponse:
    """Test class for RouterStatusResponse objects."""

    def test_from_knx_dispatches_and_raises_not_implemented(self) -> None:
        """Test the APCI is routed to the class, which raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match=r".*A_RouterStatus_Response.*"):
            APCI.from_knx(bytes((0x03, 0xCE)))

    def test_to_knx_raises_not_implemented(self) -> None:
        """Test to_knx raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match=r".*A_RouterStatus_Response.*"):
            RouterStatusResponse().to_knx()

    def test_calculated_length_raises_not_implemented(self) -> None:
        """Test calculated_length raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match=r".*A_RouterStatus_Response.*"):
            RouterStatusResponse().calculated_length()

    def test_str(self) -> None:
        """Test the __str__ method."""
        assert (
            str(RouterStatusResponse()) == "<RouterStatusResponse (not implemented) />"
        )


class TestRouterStatusWrite:
    """Test class for RouterStatusWrite objects."""

    def test_from_knx_dispatches_and_raises_not_implemented(self) -> None:
        """Test the APCI is routed to the class, which raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match=r".*A_RouterStatus_Write.*"):
            APCI.from_knx(bytes((0x03, 0xCF)))

    def test_to_knx_raises_not_implemented(self) -> None:
        """Test to_knx raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match=r".*A_RouterStatus_Write.*"):
            RouterStatusWrite().to_knx()

    def test_calculated_length_raises_not_implemented(self) -> None:
        """Test calculated_length raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match=r".*A_RouterStatus_Write.*"):
            RouterStatusWrite().calculated_length()

    def test_str(self) -> None:
        """Test the __str__ method."""
        assert str(RouterStatusWrite()) == "<RouterStatusWrite (not implemented) />"


class TestMemoryBitWrite:
    """Test class for MemoryBitWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = MemoryBitWrite(
            memory_address=0x1234,
            and_data=bytes([0xAA, 0xBB]),
            xor_data=bytes([0x11, 0x22]),
        )

        assert payload.calculated_length() == 8
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes([0x03, 0xD0, 0x02, 0x12, 0x34, 0xAA, 0xBB, 0x11, 0x22])
        )

        assert payload == MemoryBitWrite(
            memory_address=0x1234,
            and_data=bytes([0xAA, 0xBB]),
            xor_data=bytes([0x11, 0x22]),
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a mismatched number/length."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            # number=2 but only 1 octet of and_data/xor_data follows
            APCI.from_knx(bytes([0x03, 0xD0, 0x02, 0x12, 0x34, 0xAA, 0x11]))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = MemoryBitWrite(
            memory_address=0x1234,
            and_data=bytes([0xAA, 0xBB]),
            xor_data=bytes([0x11, 0x22]),
        )

        assert payload.to_knx() == bytes(
            [0x03, 0xD0, 0x02, 0x12, 0x34, 0xAA, 0xBB, 0x11, 0x22]
        )

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes([0x03, 0xD0, 0x02, 0x12, 0x34, 0xAA, 0xBB, 0x11, 0x22])

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_address_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range address."""
        payload = MemoryBitWrite(
            memory_address=0x10000, and_data=bytes([0xAA]), xor_data=bytes([0x11])
        )

        with pytest.raises(ConversionError, match=r".*Memory address.*"):
            payload.to_knx()

    def test_to_knx_mismatched_data_length(self) -> None:
        """Test to_knx raises ConversionError when and_data/xor_data lengths differ."""
        payload = MemoryBitWrite(
            memory_address=0x1234, and_data=bytes([0xAA, 0xBB]), xor_data=bytes([0x11])
        )

        with pytest.raises(
            ConversionError, match=r".*and_data and xor_data.*same length.*"
        ):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = MemoryBitWrite(
            memory_address=0x1234,
            and_data=bytes([0xAA, 0xBB]),
            xor_data=bytes([0x11, 0x22]),
        )

        assert str(payload) == (
            '<MemoryBitWrite memory_address="0x1234" and_data="aabb" xor_data="1122" />'
        )


class TestAuthorizeRequest:
    """Test class for AuthorizeRequest objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = AuthorizeRequest(key=12345678)

        assert payload.calculated_length() == 6

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD1, 0x00, 0x00, 0xBC, 0x61, 0x4E]))

        assert payload == AuthorizeRequest(key=12345678)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = AuthorizeRequest(key=12345678)

        assert payload.to_knx() == bytes([0x03, 0xD1, 0x00, 0x00, 0xBC, 0x61, 0x4E])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = AuthorizeRequest(key=12345678)

        assert str(payload) == '<AuthorizeRequest key="12345678" />'


class TestAuthorizeResponse:
    """Test class for AuthorizeResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = AuthorizeResponse(level=123)

        assert payload.calculated_length() == 2

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD2, 0x7B]))

        assert payload == AuthorizeResponse(level=123)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = AuthorizeResponse(level=123)

        assert payload.to_knx() == bytes([0x03, 0xD2, 0x7B])

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = AuthorizeResponse(level=123)

        assert str(payload) == '<AuthorizeResponse level="123"/>'


class TestKeyWrite:
    """Test class for KeyWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = KeyWrite(level=1, key=0x12345678)

        assert payload.calculated_length() == 6
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03d30112345678"))

        assert payload == KeyWrite(level=1, key=0x12345678)

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03d301123456"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = KeyWrite(level=1, key=0x12345678)

        assert payload.to_knx() == bytes.fromhex("03d30112345678")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03d30112345678")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_level_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range level."""
        payload = KeyWrite(level=0x100, key=0x12345678)

        with pytest.raises(ConversionError, match=r".*Level.*"):
            payload.to_knx()

    def test_to_knx_key_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range key."""
        payload = KeyWrite(level=1, key=0x100000000)

        with pytest.raises(ConversionError, match=r".*Key.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = KeyWrite(level=1, key=0x12345678)

        assert str(payload) == '<KeyWrite level="1" key="0x12345678" />'


class TestKeyResponse:
    """Test class for KeyResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = KeyResponse(level=123)

        assert payload.calculated_length() == 2
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03d47b"))

        assert payload == KeyResponse(level=123)

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03d4"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = KeyResponse(level=123)

        assert payload.to_knx() == bytes.fromhex("03d47b")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03d47b")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = KeyResponse(level=123)

        assert str(payload) == '<KeyResponse level="123" />'


class TestPropertyValueRead:
    """Test class for PropertyValueRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

        assert payload.calculated_length() == 5

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD5, 0x01, 0x04, 0x20, 0x08]))

        assert payload == PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

        assert payload.to_knx() == bytes([0x03, 0xD5, 0x01, 0x04, 0x20, 0x08])

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=32, start_index=8
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 7

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD7, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]))

        assert payload == PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes(
            [0x03, 0xD7, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]
        )

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=32, start_index=8, data=b"\x12\x34"
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert payload.calculated_length() == 7

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD6, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]))

        assert payload == PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        assert payload.to_knx() == bytes(
            [0x03, 0xD6, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]
        )

    def test_to_knx_conversion_error(self) -> None:
        """Test the to_knx method for conversion errors."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=32, start_index=8, data=b"\x12\x34"
        )

        with pytest.raises(ConversionError, match=r".*Count.*"):
            payload.to_knx()

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

        assert payload.calculated_length() == 4

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xD8, 0x01, 0x04, 0x08]))

        assert payload == PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

        assert payload.to_knx() == bytes([0x03, 0xD8, 0x01, 0x04, 0x08])

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
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

    def test_from_knx(self) -> None:
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

    def test_to_knx(self) -> None:
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

    def test_to_knx_conversion_error(self) -> None:
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

    def test_str(self) -> None:
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


class TestNetworkParameterRead:
    """Test class for NetworkParameterRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = NetworkParameterRead(
            object_type=0, property_id=11, test_info=bytes.fromhex("01")
        )

        assert payload.calculated_length() == 5
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03da00000b01"))

        assert payload == NetworkParameterRead(
            object_type=0, property_id=11, test_info=bytes.fromhex("01")
        )

    def test_from_knx_no_test_info(self) -> None:
        """Test from_knx accepts the minimum 5 octet APDU with no test_info."""
        payload = APCI.from_knx(bytes.fromhex("03daffffff"))

        assert payload == NetworkParameterRead(
            object_type=0xFFFF, property_id=0xFF, test_info=b""
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03da0000"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = NetworkParameterRead(
            object_type=0, property_id=11, test_info=bytes.fromhex("01")
        )

        assert payload.to_knx() == bytes.fromhex("03da00000b01")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03da00000b01")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_type."""
        payload = NetworkParameterRead(object_type=0x10000, property_id=11)

        with pytest.raises(ConversionError, match=r".*Object type.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = NetworkParameterRead(object_type=0, property_id=0x100)

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = NetworkParameterRead(
            object_type=0, property_id=11, test_info=bytes.fromhex("01")
        )

        assert str(payload) == (
            '<NetworkParameterRead object_type="0" property_id="11" test_info="01" />'
        )


class TestNetworkParameterResponse:
    """Test class for NetworkParameterResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = NetworkParameterResponse(
            object_type=0, property_id=11, test_info_and_result=bytes.fromhex("aabbcc")
        )

        assert payload.calculated_length() == 7
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03db00000baabbcc"))

        assert payload == NetworkParameterResponse(
            object_type=0, property_id=11, test_info_and_result=bytes.fromhex("aabbcc")
        )

    def test_from_knx_no_data(self) -> None:
        """Test from_knx accepts the minimum 5 octet APDU with no data."""
        payload = APCI.from_knx(bytes.fromhex("03db00000b"))

        assert payload == NetworkParameterResponse(
            object_type=0, property_id=11, test_info_and_result=b""
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03db0000"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = NetworkParameterResponse(
            object_type=0, property_id=11, test_info_and_result=bytes.fromhex("aabbcc")
        )

        assert payload.to_knx() == bytes.fromhex("03db00000baabbcc")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03db00000baabbcc")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_type."""
        payload = NetworkParameterResponse(object_type=0x10000, property_id=11)

        with pytest.raises(ConversionError, match=r".*Object type.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = NetworkParameterResponse(object_type=0, property_id=0x100)

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = NetworkParameterResponse(
            object_type=0, property_id=11, test_info_and_result=bytes.fromhex("aabbcc")
        )

        assert str(payload) == (
            '<NetworkParameterResponse object_type="0" property_id="11" '
            'test_info_and_result="aabbcc" />'
        )


class TestIndividualAddressSerialRead:
    """Test class for IndividualAddressSerialRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

        assert payload.calculated_length() == 7

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xDC, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33]))

        assert payload == IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

        assert payload.to_knx() == bytes(
            [0x03, 0xDC, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33]
        )

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

        assert str(payload) == '<IndividualAddressSerialRead serial="aabbcc112233" />'


class TestIndividualAddressSerialResponse:
    """Test class for IndividualAddressSerialResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert payload.calculated_length() == 11

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(
            bytes(
                [0x03, 0xDD, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33, 0x12, 0x03, 0x00, 0x00]
            )
        )

        assert payload == IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert payload.to_knx() == bytes(
            [0x03, 0xDD, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33, 0x12, 0x03, 0x00, 0x00]
        )

    def test_str(self) -> None:
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

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = IndividualAddressSerialWrite(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert payload.calculated_length() == 13

    def test_from_knx(self) -> None:
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

    def test_to_knx(self) -> None:
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

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = IndividualAddressSerialWrite(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        assert (
            str(payload)
            == '<IndividualAddressSerialWrite serial="aabbcc112233" address="1.2.3" />'
        )


class TestDomainAddressWrite:
    """Test class for DomainAddressWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = DomainAddressWrite(domain_address=bytes.fromhex("1234"))

        assert payload.calculated_length() == 3
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx_pl110(self) -> None:
        """Test the from_knx method for a 2 octet KNX-PL110 domain address."""
        payload = APCI.from_knx(bytes.fromhex("03e01234"))

        assert payload == DomainAddressWrite(domain_address=bytes.fromhex("1234"))

    def test_from_knx_rf(self) -> None:
        """Test the from_knx method for a 6 octet KNX-RF domain address."""
        payload = APCI.from_knx(bytes.fromhex("03e0aabbccddeeff"))

        assert payload == DomainAddressWrite(
            domain_address=bytes.fromhex("aabbccddeeff")
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a neither-2-nor-6 octet address."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03e0aabbcc"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = DomainAddressWrite(domain_address=bytes.fromhex("1234"))

        assert payload.to_knx() == bytes.fromhex("03e01234")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03e0aabbccddeeff")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_wrong_length(self) -> None:
        """Test to_knx raises ConversionError for a neither-2-nor-6 octet address."""
        payload = DomainAddressWrite(domain_address=b"\xaa")

        with pytest.raises(ConversionError, match=r".*Domain address.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = DomainAddressWrite(domain_address=bytes.fromhex("1234"))

        assert str(payload) == '<DomainAddressWrite domain_address="1234" />'


class TestDomainAddressRead:
    """Test class for DomainAddressRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = DomainAddressRead()

        assert payload.calculated_length() == 1
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes((0x03, 0xE1)))

        assert payload == DomainAddressRead()

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = DomainAddressRead()

        assert payload.to_knx() == bytes((0x03, 0xE1))

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = DomainAddressRead()

        assert str(payload) == "<DomainAddressRead />"


class TestDomainAddressResponse:
    """Test class for DomainAddressResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = DomainAddressResponse(domain_address=bytes.fromhex("1234"))

        assert payload.calculated_length() == 3
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx_pl110(self) -> None:
        """Test the from_knx method for a 2 octet KNX-PL110 domain address."""
        payload = APCI.from_knx(bytes.fromhex("03e21234"))

        assert payload == DomainAddressResponse(domain_address=bytes.fromhex("1234"))

    def test_from_knx_rf(self) -> None:
        """Test the from_knx method for a 6 octet KNX-RF domain address."""
        payload = APCI.from_knx(bytes.fromhex("03e2aabbccddeeff"))

        assert payload == DomainAddressResponse(
            domain_address=bytes.fromhex("aabbccddeeff")
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a neither-2-nor-6 octet address."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03e2aabbcc"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = DomainAddressResponse(domain_address=bytes.fromhex("1234"))

        assert payload.to_knx() == bytes.fromhex("03e21234")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03e2aabbccddeeff")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_wrong_length(self) -> None:
        """Test to_knx raises ConversionError for a neither-2-nor-6 octet address."""
        payload = DomainAddressResponse(domain_address=b"\xaa")

        with pytest.raises(ConversionError, match=r".*Domain address.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = DomainAddressResponse(domain_address=bytes.fromhex("1234"))

        assert str(payload) == '<DomainAddressResponse domain_address="1234" />'


class TestDomainAddressSelectiveRead:
    """Test class for DomainAddressSelectiveRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = DomainAddressSelectiveRead(asdu=bytes.fromhex("1234aabbcc"))

        assert payload.calculated_length() == 6
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03e31234aabbcc"))

        assert payload == DomainAddressSelectiveRead(asdu=bytes.fromhex("1234aabbcc"))

    def test_from_knx_no_asdu(self) -> None:
        """Test from_knx accepts the minimum 2 octet APDU with no asdu."""
        payload = APCI.from_knx(bytes((0x03, 0xE3)))

        assert payload == DomainAddressSelectiveRead(asdu=b"")

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = DomainAddressSelectiveRead(asdu=bytes.fromhex("1234aabbcc"))

        assert payload.to_knx() == bytes.fromhex("03e31234aabbcc")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03e31234aabbcc")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = DomainAddressSelectiveRead(asdu=bytes.fromhex("1234aabbcc"))

        assert str(payload) == ('<DomainAddressSelectiveRead asdu="1234aabbcc" />')


class TestNetworkParameterWrite:
    """Test class for NetworkParameterWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = NetworkParameterWrite(
            object_type=0, property_id=11, value=bytes.fromhex("aabbcc")
        )

        assert payload.calculated_length() == 7
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03e400000baabbcc"))

        assert payload == NetworkParameterWrite(
            object_type=0, property_id=11, value=bytes.fromhex("aabbcc")
        )

    def test_from_knx_no_value(self) -> None:
        """Test from_knx accepts the minimum 5 octet APDU with no value."""
        payload = APCI.from_knx(bytes.fromhex("03e4ffffff"))

        assert payload == NetworkParameterWrite(
            object_type=0xFFFF, property_id=0xFF, value=b""
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03e40000"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = NetworkParameterWrite(
            object_type=0, property_id=11, value=bytes.fromhex("aabbcc")
        )

        assert payload.to_knx() == bytes.fromhex("03e400000baabbcc")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03e400000baabbcc")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_type."""
        payload = NetworkParameterWrite(object_type=0x10000, property_id=11)

        with pytest.raises(ConversionError, match=r".*Object type.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = NetworkParameterWrite(object_type=0, property_id=0x100)

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = NetworkParameterWrite(
            object_type=0, property_id=11, value=bytes.fromhex("aabbcc")
        )

        assert str(payload) == (
            '<NetworkParameterWrite object_type="0" property_id="11" value="aabbcc" />'
        )


class TestLinkRead:
    """Test class for LinkRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = LinkRead(group_object_number=5, start_index=3)

        assert payload.calculated_length() == 3
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03e50503"))

        assert payload == LinkRead(group_object_number=5, start_index=3)

    def test_from_knx_strips_reserved_bits(self) -> None:
        """Test from_knx discards the reserved upper nibble of byte1."""
        payload = APCI.from_knx(bytes.fromhex("03e505f3"))

        assert payload == LinkRead(group_object_number=5, start_index=3)

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03e505"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = LinkRead(group_object_number=5, start_index=3)

        assert payload.to_knx() == bytes.fromhex("03e50503")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03e50503")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_group_object_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range group_object_number."""
        payload = LinkRead(group_object_number=0x100, start_index=3)

        with pytest.raises(ConversionError, match=r".*Group object number.*"):
            payload.to_knx()

    def test_to_knx_start_index_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range start_index."""
        payload = LinkRead(group_object_number=5, start_index=0x10)

        with pytest.raises(ConversionError, match=r".*Start index.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = LinkRead(group_object_number=5, start_index=3)

        assert str(payload) == ('<LinkRead group_object_number="5" start_index="3" />')


class TestLinkResponse:
    """Test class for LinkResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = LinkResponse(
            group_object_number=5,
            sending_address=2,
            start_index=3,
            group_address_list=[GroupAddress(1), GroupAddress(2)],
        )

        assert payload.calculated_length() == 7
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03e6052300010002"))

        assert payload == LinkResponse(
            group_object_number=5,
            sending_address=2,
            start_index=3,
            group_address_list=[GroupAddress(1), GroupAddress(2)],
        )

    def test_from_knx_negative_response(self) -> None:
        """Test from_knx accepts the negative response (no addresses, start_index=0)."""
        payload = APCI.from_knx(bytes.fromhex("03e60500"))

        assert payload == LinkResponse(
            group_object_number=5,
            sending_address=0,
            start_index=0,
            group_address_list=[],
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for an odd-length address list."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03e60523000100"))

    def test_from_knx_too_many_addresses(self) -> None:
        """Test from_knx raises ConversionError for more than 6 addresses."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03e60500") + b"\x00\x01" * 7)

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = LinkResponse(
            group_object_number=5,
            sending_address=2,
            start_index=3,
            group_address_list=[GroupAddress(1), GroupAddress(2)],
        )

        assert payload.to_knx() == bytes.fromhex("03e6052300010002")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03e6052300010002")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_too_many_addresses(self) -> None:
        """Test to_knx raises ConversionError for more than 6 addresses."""
        payload = LinkResponse(
            group_object_number=5,
            group_address_list=[GroupAddress(i) for i in range(1, 8)],
        )

        with pytest.raises(ConversionError, match=r".*at most 6.*"):
            payload.to_knx()

    def test_to_knx_group_object_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range group_object_number."""
        payload = LinkResponse(group_object_number=0x100)

        with pytest.raises(ConversionError, match=r".*Group object number.*"):
            payload.to_knx()

    def test_to_knx_sending_address_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range sending_address."""
        payload = LinkResponse(group_object_number=5, sending_address=0x10)

        with pytest.raises(ConversionError, match=r".*Sending address.*"):
            payload.to_knx()

    def test_to_knx_start_index_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range start_index."""
        payload = LinkResponse(group_object_number=5, start_index=0x10)

        with pytest.raises(ConversionError, match=r".*Start index.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = LinkResponse(
            group_object_number=5,
            sending_address=2,
            start_index=3,
            group_address_list=[GroupAddress(1), GroupAddress(2)],
        )

        assert str(payload) == (
            '<LinkResponse group_object_number="5" sending_address="2" '
            'start_index="3" group_address_list="0/0/1, 0/0/2" />'
        )


class TestLinkWrite:
    """Test class for LinkWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = LinkWrite(
            group_object_number=5, group_address=GroupAddress(1), sending=True
        )

        assert payload.calculated_length() == 5
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx_add_sending(self) -> None:
        """Test the from_knx method for adding a sending Group Address."""
        payload = APCI.from_knx(bytes.fromhex("03e705010001"))

        assert payload == LinkWrite(
            group_object_number=5,
            group_address=GroupAddress(1),
            delete=False,
            sending=True,
        )

    def test_from_knx_delete(self) -> None:
        """Test the from_knx method for deleting a Group Address."""
        payload = APCI.from_knx(bytes.fromhex("03e705020001"))

        assert payload == LinkWrite(
            group_object_number=5,
            group_address=GroupAddress(1),
            delete=True,
            sending=False,
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03e7050100"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = LinkWrite(
            group_object_number=5, group_address=GroupAddress(1), sending=True
        )

        assert payload.to_knx() == bytes.fromhex("03e705010001")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03e705010001")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_group_object_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range group_object_number."""
        payload = LinkWrite(group_object_number=0x100, group_address=GroupAddress(1))

        with pytest.raises(ConversionError, match=r".*Group object number.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = LinkWrite(
            group_object_number=5, group_address=GroupAddress(1), sending=True
        )

        assert str(payload) == (
            '<LinkWrite group_object_number="5" delete="False" sending="True" '
            'group_address="0/0/1" />'
        )


class TestGroupPropValueRead:
    """Test class for GroupPropValueRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = GroupPropValueRead(object_type=17, object_instance=1, property_id=51)

        assert payload.calculated_length() == 5
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03e800110133"))

        assert payload == GroupPropValueRead(
            object_type=17, object_instance=1, property_id=51
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03e8001101"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = GroupPropValueRead(object_type=17, object_instance=1, property_id=51)

        assert payload.to_knx() == bytes.fromhex("03e800110133")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03e800110133")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_object_type_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_type."""
        payload = GroupPropValueRead(
            object_type=0x10000, object_instance=1, property_id=51
        )

        with pytest.raises(ConversionError, match=r".*Object type.*"):
            payload.to_knx()

    def test_to_knx_object_instance_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range object_instance."""
        payload = GroupPropValueRead(
            object_type=17, object_instance=0x100, property_id=51
        )

        with pytest.raises(ConversionError, match=r".*Object instance.*"):
            payload.to_knx()

    def test_to_knx_property_id_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range property_id."""
        payload = GroupPropValueRead(
            object_type=17, object_instance=1, property_id=0x100
        )

        with pytest.raises(ConversionError, match=r".*Property ID.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = GroupPropValueRead(object_type=17, object_instance=1, property_id=51)

        assert str(payload) == (
            '<GroupPropValueRead object_type="17" object_instance="1" '
            'property_id="51" />'
        )


class TestGroupPropValueResponse:
    """Test class for GroupPropValueResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = GroupPropValueResponse(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.calculated_length() == 7
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03e900110133aabb"))

        assert payload == GroupPropValueResponse(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

    def test_from_knx_no_data(self) -> None:
        """Test from_knx accepts the minimum 6 octet APDU with no data."""
        payload = APCI.from_knx(bytes.fromhex("03e900110133"))

        assert payload == GroupPropValueResponse(
            object_type=17, object_instance=1, property_id=51, data=b""
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03e9001101"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = GroupPropValueResponse(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.to_knx() == bytes.fromhex("03e900110133aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03e900110133aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = GroupPropValueResponse(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert str(payload) == (
            '<GroupPropValueResponse object_type="17" object_instance="1" '
            'property_id="51" data="aabb" />'
        )


class TestGroupPropValueWrite:
    """Test class for GroupPropValueWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = GroupPropValueWrite(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.calculated_length() == 7
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03ea00110133aabb"))

        assert payload == GroupPropValueWrite(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03ea001101"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = GroupPropValueWrite(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.to_knx() == bytes.fromhex("03ea00110133aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03ea00110133aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = GroupPropValueWrite(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert str(payload) == (
            '<GroupPropValueWrite object_type="17" object_instance="1" '
            'property_id="51" data="aabb" />'
        )


class TestGroupPropValueInfoReport:
    """Test class for GroupPropValueInfoReport objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = GroupPropValueInfoReport(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.calculated_length() == 7
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03eb00110133aabb"))

        assert payload == GroupPropValueInfoReport(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03eb001101"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = GroupPropValueInfoReport(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert payload.to_knx() == bytes.fromhex("03eb00110133aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03eb00110133aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = GroupPropValueInfoReport(
            object_type=17,
            object_instance=1,
            property_id=51,
            data=bytes.fromhex("aabb"),
        )

        assert str(payload) == (
            '<GroupPropValueInfoReport object_type="17" object_instance="1" '
            'property_id="51" data="aabb" />'
        )


class TestDomainAddressSerialNumberRead:
    """Test class for DomainAddressSerialNumberRead objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = DomainAddressSerialNumberRead(b"\xaa\xbb\xcc\x11\x22\x33")

        assert payload.calculated_length() == 7
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes([0x03, 0xEC, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33]))

        assert payload == DomainAddressSerialNumberRead(b"\xaa\xbb\xcc\x11\x22\x33")

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = DomainAddressSerialNumberRead(b"\xaa\xbb\xcc\x11\x22\x33")

        assert payload.to_knx() == bytes(
            [0x03, 0xEC, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33]
        )

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes([0x03, 0xEC, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33])

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_wrong_length(self) -> None:
        """Test to_knx raises ConversionError for a non-6-byte serial."""
        payload = DomainAddressSerialNumberRead(b"\xaa\xbb\xcc")

        with pytest.raises(ConversionError, match=r".*Serial.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = DomainAddressSerialNumberRead(b"\xaa\xbb\xcc\x11\x22\x33")

        assert str(payload) == (
            '<DomainAddressSerialNumberRead serial="aabbcc112233" />'
        )


class TestDomainAddressSerialNumberResponse:
    """Test class for DomainAddressSerialNumberResponse objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = DomainAddressSerialNumberResponse(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("1234"),
        )

        assert payload.calculated_length() == 9
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx_pl110(self) -> None:
        """Test the from_knx method for a 2 octet KNX-PL110 domain address."""
        payload = APCI.from_knx(bytes.fromhex("03edaabbcc1122331234"))

        assert payload == DomainAddressSerialNumberResponse(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("1234"),
        )

    def test_from_knx_rf(self) -> None:
        """Test the from_knx method for a 6 octet KNX-RF domain address."""
        payload = APCI.from_knx(bytes.fromhex("03edaabbcc112233445566778899"))

        assert payload == DomainAddressSerialNumberResponse(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("445566778899"),
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a neither-2-nor-6 octet address."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03edaabbcc112233112233"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = DomainAddressSerialNumberResponse(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("1234"),
        )

        assert payload.to_knx() == bytes.fromhex("03edaabbcc1122331234")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03edaabbcc1122331234")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_serial_wrong_length(self) -> None:
        """Test to_knx raises ConversionError for a non-6-byte serial."""
        payload = DomainAddressSerialNumberResponse(
            serial=bytes.fromhex("aabbcc"),
            domain_address=bytes.fromhex("1234"),
        )

        with pytest.raises(ConversionError, match=r".*Serial.*"):
            payload.to_knx()

    def test_to_knx_domain_address_wrong_length(self) -> None:
        """Test to_knx raises ConversionError for a neither-2-nor-6 octet address."""
        payload = DomainAddressSerialNumberResponse(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("112233"),
        )

        with pytest.raises(ConversionError, match=r".*Domain address.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = DomainAddressSerialNumberResponse(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("1234"),
        )

        assert str(payload) == (
            '<DomainAddressSerialNumberResponse serial="aabbcc112233" '
            'domain_address="1234" />'
        )


class TestDomainAddressSerialNumberWrite:
    """Test class for DomainAddressSerialNumberWrite objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("1234"),
        )

        assert payload.calculated_length() == 9
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx_pl110(self) -> None:
        """Test the from_knx method for a 2 octet KNX-PL110 domain address."""
        payload = APCI.from_knx(bytes.fromhex("03eeaabbcc1122331234"))

        assert payload == DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("1234"),
        )

    def test_from_knx_ip_multicast(self) -> None:
        """Test the from_knx method for a 4 octet IP multicast domain address."""
        payload = APCI.from_knx(bytes.fromhex("03eeaabbcc11223311223344"))

        assert payload == DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("11223344"),
        )

    def test_from_knx_rf(self) -> None:
        """Test the from_knx method for a 6 octet KNX-RF domain address."""
        payload = APCI.from_knx(bytes.fromhex("03eeaabbcc112233445566778899"))

        assert payload == DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("445566778899"),
        )

    def test_from_knx_ip_secure(self) -> None:
        """Test the from_knx method for the KNX IP Secure variant."""
        payload = APCI.from_knx(
            bytes.fromhex("03eeaabbcc11223311223344") + b"\x01" + b"\x00" * 16
        )

        assert payload == DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("11223344"),
            routing_security_version=1,
            backbone_key=b"\x00" * 16,
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for an unsupported address length."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03eeaabbcc112233112233"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("1234"),
        )

        assert payload.to_knx() == bytes.fromhex("03eeaabbcc1122331234")

    def test_to_knx_ip_secure(self) -> None:
        """Test the to_knx method for the KNX IP Secure variant."""
        payload = DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("11223344"),
            routing_security_version=1,
            backbone_key=b"\x00" * 16,
        )

        assert payload.to_knx() == (
            bytes.fromhex("03eeaabbcc11223311223344") + b"\x01" + b"\x00" * 16
        )

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03eeaabbcc11223311223344") + b"\x01" + b"\x00" * 16

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_serial_wrong_length(self) -> None:
        """Test to_knx raises ConversionError for a non-6-byte serial."""
        payload = DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc"),
            domain_address=bytes.fromhex("1234"),
        )

        with pytest.raises(ConversionError, match=r".*Serial.*"):
            payload.to_knx()

    def test_to_knx_domain_address_wrong_length(self) -> None:
        """Test to_knx raises ConversionError for an unsupported address length."""
        payload = DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("112233"),
        )

        with pytest.raises(ConversionError, match=r".*Domain address.*"):
            payload.to_knx()

    def test_to_knx_secure_fields_require_4_byte_address(self) -> None:
        """Test to_knx rejects secure fields with a non-4-byte domain address."""
        payload = DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("1234"),
            routing_security_version=1,
            backbone_key=b"\x00" * 16,
        )

        with pytest.raises(ConversionError, match=r".*4 octet.*"):
            payload.to_knx()

    def test_to_knx_secure_fields_must_be_set_together(self) -> None:
        """Test to_knx rejects a routing_security_version without a backbone_key."""
        payload = DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("11223344"),
            routing_security_version=1,
        )

        with pytest.raises(ConversionError, match=r".*must be set together.*"):
            payload.to_knx()

    def test_to_knx_backbone_key_wrong_length(self) -> None:
        """Test to_knx raises ConversionError for a non-16-byte backbone_key."""
        payload = DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("11223344"),
            routing_security_version=1,
            backbone_key=b"\x00",
        )

        with pytest.raises(ConversionError, match=r".*Backbone key.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = DomainAddressSerialNumberWrite(
            serial=bytes.fromhex("aabbcc112233"),
            domain_address=bytes.fromhex("1234"),
        )

        assert str(payload) == (
            '<DomainAddressSerialNumberWrite serial="aabbcc112233" '
            'domain_address="1234" routing_security_version="None" '
            'backbone_key="None" />'
        )


class TestFileStreamInfoReport:
    """Test class for FileStreamInfoReport objects."""

    def test_calculated_length(self) -> None:
        """Test the test_calculated_length method."""
        payload = FileStreamInfoReport(
            file_handle=5, file_block_seq_number=3, file_block=bytes.fromhex("aabb")
        )

        assert payload.calculated_length() == 4
        assert payload.calculated_length() == len(payload.to_knx()) - 1

    def test_from_knx(self) -> None:
        """Test the from_knx method."""
        payload = APCI.from_knx(bytes.fromhex("03f053aabb"))

        assert payload == FileStreamInfoReport(
            file_handle=5, file_block_seq_number=3, file_block=bytes.fromhex("aabb")
        )

    def test_from_knx_no_file_block(self) -> None:
        """Test from_knx accepts the minimum 3 octet APDU with no file_block."""
        payload = APCI.from_knx(bytes.fromhex("03f053"))

        assert payload == FileStreamInfoReport(
            file_handle=5, file_block_seq_number=3, file_block=b""
        )

    def test_from_knx_wrong_length(self) -> None:
        """Test from_knx raises ConversionError for a too-short APDU."""
        with pytest.raises(ConversionError, match=r".*Invalid length.*"):
            APCI.from_knx(bytes.fromhex("03f0"))

    def test_to_knx(self) -> None:
        """Test the to_knx method."""
        payload = FileStreamInfoReport(
            file_handle=5, file_block_seq_number=3, file_block=bytes.fromhex("aabb")
        )

        assert payload.to_knx() == bytes.fromhex("03f053aabb")

    def test_round_trip(self) -> None:
        """Test from_knx().to_knx() reproduces the original frame exactly."""
        raw = bytes.fromhex("03f053aabb")

        assert APCI.from_knx(raw).to_knx() == raw

    def test_to_knx_file_handle_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range file_handle."""
        payload = FileStreamInfoReport(file_handle=0x10, file_block_seq_number=3)

        with pytest.raises(ConversionError, match=r".*File handle.*"):
            payload.to_knx()

    def test_to_knx_file_block_seq_number_out_of_range(self) -> None:
        """Test to_knx raises ConversionError for an out of range seq number."""
        payload = FileStreamInfoReport(file_handle=5, file_block_seq_number=0x10)

        with pytest.raises(ConversionError, match=r".*sequence number.*"):
            payload.to_knx()

    def test_str(self) -> None:
        """Test the __str__ method."""
        payload = FileStreamInfoReport(
            file_handle=5, file_block_seq_number=3, file_block=bytes.fromhex("aabb")
        )

        assert str(payload) == (
            '<FileStreamInfoReport file_handle="5" file_block_seq_number="3" '
            'file_block="aabb" />'
        )
