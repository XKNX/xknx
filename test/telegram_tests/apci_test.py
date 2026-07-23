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
    FunctionPropertyExtCommand,
    FunctionPropertyExtStateRead,
    FunctionPropertyExtStateResponse,
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
    SystemNetworkParameterRead,
    SystemNetworkParameterResponse,
    SystemNetworkParameterWrite,
    UserManufacturerInfoRead,
    UserManufacturerInfoResponse,
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
            # Unsupported extended service.
            APCI.from_knx(bytes((0x03, 0xC0)))


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

        assert payload.calculated_length() == 8

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

        assert payload.calculated_length() == 10

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

        assert payload.calculated_length() == 10

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

        assert payload.calculated_length() == 9

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

    def test_from_knx_dispatches_and_raises_not_implemented(self) -> None:
        """Test the APCI is routed to the class, which raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtValue_WriteUnCon.*"
        ):
            APCI.from_knx(bytes.fromhex("01d0"))

    def test_to_knx_raises_not_implemented(self) -> None:
        """Test to_knx raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtValue_WriteUnCon.*"
        ):
            PropertyExtValueWriteUnCon().to_knx()

    def test_calculated_length_raises_not_implemented(self) -> None:
        """Test calculated_length raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtValue_WriteUnCon.*"
        ):
            PropertyExtValueWriteUnCon().calculated_length()

    def test_str(self) -> None:
        """Test the __str__ method."""
        assert (
            str(PropertyExtValueWriteUnCon())
            == "<PropertyExtValueWriteUnCon (not implemented) />"
        )


class TestPropertyExtValueInfoReport:
    """Test class for PropertyExtValueInfoReport objects."""

    def test_from_knx_dispatches_and_raises_not_implemented(self) -> None:
        """Test the APCI is routed to the class, which raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtValue_InfoReport.*"
        ):
            APCI.from_knx(bytes.fromhex("01d1"))

    def test_to_knx_raises_not_implemented(self) -> None:
        """Test to_knx raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtValue_InfoReport.*"
        ):
            PropertyExtValueInfoReport().to_knx()

    def test_calculated_length_raises_not_implemented(self) -> None:
        """Test calculated_length raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtValue_InfoReport.*"
        ):
            PropertyExtValueInfoReport().calculated_length()

    def test_str(self) -> None:
        """Test the __str__ method."""
        assert (
            str(PropertyExtValueInfoReport())
            == "<PropertyExtValueInfoReport (not implemented) />"
        )


class TestPropertyExtDescriptionRead:
    """Test class for PropertyExtDescriptionRead objects."""

    def test_from_knx_dispatches_and_raises_not_implemented(self) -> None:
        """Test the APCI is routed to the class, which raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtDescription_Read.*"
        ):
            APCI.from_knx(bytes.fromhex("01d2"))

    def test_to_knx_raises_not_implemented(self) -> None:
        """Test to_knx raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtDescription_Read.*"
        ):
            PropertyExtDescriptionRead().to_knx()

    def test_calculated_length_raises_not_implemented(self) -> None:
        """Test calculated_length raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtDescription_Read.*"
        ):
            PropertyExtDescriptionRead().calculated_length()

    def test_str(self) -> None:
        """Test the __str__ method."""
        assert (
            str(PropertyExtDescriptionRead())
            == "<PropertyExtDescriptionRead (not implemented) />"
        )


class TestPropertyExtDescriptionResponse:
    """Test class for PropertyExtDescriptionResponse objects."""

    def test_from_knx_dispatches_and_raises_not_implemented(self) -> None:
        """Test the APCI is routed to the class, which raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtDescription_Response.*"
        ):
            APCI.from_knx(bytes.fromhex("01d3"))

    def test_to_knx_raises_not_implemented(self) -> None:
        """Test to_knx raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtDescription_Response.*"
        ):
            PropertyExtDescriptionResponse().to_knx()

    def test_calculated_length_raises_not_implemented(self) -> None:
        """Test calculated_length raises NotImplementedError."""
        with pytest.raises(
            NotImplementedError, match=r".*A_PropertyExtDescription_Response.*"
        ):
            PropertyExtDescriptionResponse().calculated_length()

    def test_str(self) -> None:
        """Test the __str__ method."""
        assert (
            str(PropertyExtDescriptionResponse())
            == "<PropertyExtDescriptionResponse (not implemented) />"
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
