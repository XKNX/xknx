"""Unit test for APCI objects."""
import unittest

from pytest import raises
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.telegram.address import IndividualAddress
from xknx.telegram.apci import (
    APCI,
    ADCRead,
    ADCResponse,
    APCIExtendedService,
    APCIService,
    APCIUserService,
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


class TestAPCI(unittest.TestCase):
    """Test class for APCI objects."""

    def test_resolve_apci(self):
        """Test resolve_apci for supported APCI services."""
        test_cases = [
            (APCIService.GROUP_READ.value, GroupValueRead),
            (APCIService.GROUP_WRITE.value, GroupValueWrite),
            (APCIService.GROUP_RESPONSE.value, GroupValueResponse),
            (APCIService.INDIVIDUAL_ADDRESS_WRITE.value, IndividualAddressWrite),
            (APCIService.INDIVIDUAL_ADDRESS_READ.value, IndividualAddressRead),
            (APCIService.INDIVIDUAL_ADDRESS_RESPONSE.value, IndividualAddressResponse),
            (APCIService.ADC_READ.value, ADCRead),
            (APCIService.ADC_RESPONSE.value, ADCResponse),
            (APCIService.MEMORY_READ.value, MemoryRead),
            (APCIService.MEMORY_WRITE.value, MemoryWrite),
            (APCIService.MEMORY_RESPONSE.value, MemoryResponse),
            (APCIService.DEVICE_DESCRIPTOR_READ.value, DeviceDescriptorRead),
            (APCIService.DEVICE_DESCRIPTOR_RESPONSE.value, DeviceDescriptorResponse),
            (APCIService.RESTART.value, Restart),
        ]

        for code, clazz in test_cases:
            self.assertIsInstance(APCI.resolve_apci(code), clazz)

    def test_resolve_class_user(self):
        """Test resolve_class for supported user APCI services."""
        test_cases = [
            (APCIUserService.USER_MEMORY_READ.value, UserMemoryRead),
            (APCIUserService.USER_MEMORY_RESPONSE.value, UserMemoryResponse),
            (APCIUserService.USER_MEMORY_WRITE.value, UserMemoryWrite),
            (
                APCIUserService.USER_MANUFACTURER_INFO_READ.value,
                UserManufacturerInfoRead,
            ),
            (
                APCIUserService.USER_MANUFACTURER_INFO_RESPONSE.value,
                UserManufacturerInfoResponse,
            ),
            (APCIUserService.FUNCTION_PROPERTY_COMMAND.value, FunctionPropertyCommand),
            (
                APCIUserService.FUNCTION_PROPERTY_STATE_READ.value,
                FunctionPropertyStateRead,
            ),
            (
                APCIUserService.FUNCTION_PROPERTY_STATE_RESPONSE.value,
                FunctionPropertyStateResponse,
            ),
        ]

        for code, clazz in test_cases:
            self.assertIsInstance(APCI.resolve_apci(code), clazz)

    def test_resolve_class_extended(self):
        """Test resolve_class for supported extended APCI services."""
        test_cases = [
            (APCIExtendedService.AUTHORIZE_REQUEST.value, AuthorizeRequest),
            (APCIExtendedService.AUTHORIZE_RESPONSE.value, AuthorizeResponse),
            (APCIExtendedService.PROPERTY_VALUE_READ.value, PropertyValueRead),
            (APCIExtendedService.PROPERTY_VALUE_WRITE.value, PropertyValueWrite),
            (APCIExtendedService.PROPERTY_VALUE_RESPONSE.value, PropertyValueResponse),
            (
                APCIExtendedService.PROPERTY_DESCRIPTION_READ.value,
                PropertyDescriptionRead,
            ),
            (
                APCIExtendedService.PROPERTY_DESCRIPTION_RESPONSE.value,
                PropertyDescriptionResponse,
            ),
            (
                APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_READ.value,
                IndividualAddressSerialRead,
            ),
            (
                APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_RESPONSE.value,
                IndividualAddressSerialResponse,
            ),
            (
                APCIExtendedService.INDIVIDUAL_ADDRESS_SERIAL_WRITE.value,
                IndividualAddressSerialWrite,
            ),
        ]

        for code, clazz in test_cases:
            self.assertIsInstance(APCI.resolve_apci(code), clazz)

    def test_resolve_apci_unsupported(self):
        """Test resolve_apci for unsupported services."""

        with raises(ConversionError, match=r".*Class not implemented for APCI.*"):
            # Unsupported user service.
            APCI.resolve_apci(0x02C3)

        with raises(ConversionError, match=r".*Class not implemented for APCI.*"):
            # Unsupported extended service.
            APCI.resolve_apci(0x03C0)


class TestGroupValueRead(unittest.TestCase):
    """Test class for GroupValueRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = GroupValueRead()

        self.assertEqual(payload.calculated_length(), 1)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = GroupValueRead()
        payload.from_knx(bytes([0x00, 0x00]))

        self.assertEqual(payload, GroupValueRead())

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = GroupValueRead()

        self.assertEqual(payload.to_knx(), bytes([0x00, 0x00]))

    def test_str(self):
        """Test the __str__ method."""
        payload = GroupValueRead()

        self.assertEqual(str(payload), "<GroupValueRead />")


class TestGroupValueWrite(unittest.TestCase):
    """Test class for GroupValueWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload_a = GroupValueWrite(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueWrite(DPTBinary(1))

        self.assertEqual(payload_a.calculated_length(), 4)
        self.assertEqual(payload_b.calculated_length(), 1)

    def test_calculated_length_exception(self):
        """Test the test_calculated_length method for unsupported dpt."""
        payload = GroupValueWrite(object())

        with self.assertRaises(TypeError):
            payload.calculated_length()

    def test_from_knx(self):
        """Test the from_knx method."""
        payload_a = GroupValueWrite()
        payload_a.from_knx(bytes([0x00, 0x80, 0x05, 0x04, 0x03, 0x02, 0x01]))
        payload_b = GroupValueWrite()
        payload_b.from_knx(bytes([0x00, 0x82]))

        self.assertEqual(
            payload_a, GroupValueWrite(DPTArray((0x05, 0x04, 0x03, 0x02, 0x01)))
        )
        self.assertEqual(payload_b, GroupValueWrite(DPTBinary(0x02)))

    def test_to_knx(self):
        """Test the to_knx method."""

        payload_a = GroupValueWrite(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueWrite(DPTBinary(1))

        self.assertEqual(payload_a.to_knx(), bytes([0x00, 0x80, 0x01, 0x02, 0x03]))
        self.assertEqual(payload_b.to_knx(), bytes([0x00, 0x81]))

    def test_to_knx_exception(self):
        """Test the to_knx method for unsupported dpt."""
        payload = GroupValueWrite(object())

        with self.assertRaises(TypeError):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = GroupValueWrite(DPTBinary(1))

        self.assertEqual(
            str(payload), '<GroupValueWrite value="<DPTBinary value="1" />" />'
        )


class TestGroupValueResponse(unittest.TestCase):
    """Test class for GroupValueResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload_a = GroupValueResponse(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueResponse(DPTBinary(1))

        self.assertEqual(payload_a.calculated_length(), 4)
        self.assertEqual(payload_b.calculated_length(), 1)

    def test_calculated_length_exception(self):
        """Test the test_calculated_length method for unsupported dpt."""
        payload = GroupValueResponse(object())

        with self.assertRaises(TypeError):
            payload.calculated_length()

    def test_from_knx(self):
        """Test the from_knx method."""
        payload_a = GroupValueResponse()
        payload_a.from_knx(bytes([0x00, 0x80, 0x05, 0x04, 0x03, 0x02, 0x01]))
        payload_b = GroupValueResponse()
        payload_b.from_knx(bytes([0x00, 0x82]))

        self.assertEqual(
            payload_a, GroupValueResponse(DPTArray((0x05, 0x04, 0x03, 0x02, 0x01)))
        )
        self.assertEqual(payload_b, GroupValueResponse(DPTBinary(0x02)))

    def test_to_knx(self):
        """Test the to_knx method."""

        payload_a = GroupValueResponse(DPTArray((0x01, 0x02, 0x03)))
        payload_b = GroupValueResponse(DPTBinary(1))

        self.assertEqual(payload_a.to_knx(), bytes([0x00, 0x40, 0x01, 0x02, 0x03]))
        self.assertEqual(payload_b.to_knx(), bytes([0x00, 0x41]))

    def test_to_knx_exception(self):
        """Test the to_knx method for unsupported dpt."""
        payload = GroupValueResponse(object())

        with self.assertRaises(TypeError):
            payload.to_knx()

    def test_str(self):
        """Test the __str__ method."""
        payload = GroupValueResponse(DPTBinary(1))

        self.assertEqual(
            str(payload), '<GroupValueResponse value="<DPTBinary value="1" />" />'
        )


class TestIndividualAddressWrite(unittest.TestCase):
    """Test class for IndividualAddressWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressWrite()

        self.assertEqual(payload.calculated_length(), 3)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = IndividualAddressWrite()
        payload.from_knx(bytes([0x00, 0xC0, 0x12, 0x03]))

        self.assertEqual(payload, IndividualAddressWrite(IndividualAddress("1.2.3")))

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressWrite(IndividualAddress("1.2.3"))

        self.assertEqual(payload.to_knx(), bytes([0x00, 0xC0, 0x12, 0x03]))

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressWrite(IndividualAddress("1.2.3"))

        self.assertEqual(str(payload), '<IndividualAddressWrite address="1.2.3" />')


class TestIndividualAddressRead(unittest.TestCase):
    """Test class for IndividualAddressRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressRead()

        self.assertEqual(payload.calculated_length(), 1)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = IndividualAddressRead()
        payload.from_knx(bytes([0x01, 0x00]))

        self.assertEqual(payload, IndividualAddressRead())

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressRead()

        self.assertEqual(payload.to_knx(), bytes([0x01, 0x00]))

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressRead()

        self.assertEqual(str(payload), "<IndividualAddressRead />")


class TestIndividualAddressResponse(unittest.TestCase):
    """Test class for IndividualAddressResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressRead()

        self.assertEqual(payload.calculated_length(), 1)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = IndividualAddressResponse()
        payload.from_knx(bytes([0x01, 0x40]))

        self.assertEqual(payload, IndividualAddressResponse())

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressResponse()

        self.assertEqual(payload.to_knx(), bytes([0x01, 0x40]))

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressResponse()

        self.assertEqual(str(payload), "<IndividualAddressResponse />")


class TestADCRead(unittest.TestCase):
    """Test class for ADCRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = ADCRead()

        self.assertEqual(payload.calculated_length(), 2)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = ADCRead()
        payload.from_knx(bytes([0x01, 0x82, 0x04]))

        self.assertEqual(payload, ADCRead(channel=2, count=4))

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = ADCRead(channel=1, count=3)

        self.assertEqual(payload.to_knx(), bytes([0x01, 0x81, 0x03]))

    def test_str(self):
        """Test the __str__ method."""
        payload = ADCRead(channel=1, count=3)

        self.assertEqual(str(payload), '<ADCRead channel="1" count="3" />')


class TestADCResponse(unittest.TestCase):
    """Test class for ADCResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = ADCResponse()

        self.assertEqual(payload.calculated_length(), 4)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = ADCResponse()
        payload.from_knx(bytes([0x01, 0xC2, 0x04, 0x03, 0xFF]))

        self.assertEqual(payload, ADCResponse(channel=2, count=4, value=1023))

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = ADCResponse(channel=1, count=3, value=456)

        self.assertEqual(payload.to_knx(), bytes([0x01, 0xC1, 0x03, 0x01, 0xC8]))

    def test_str(self):
        """Test the __str__ method."""
        payload = ADCResponse(channel=1, count=3, value=456)

        self.assertEqual(
            str(payload), '<ADCResponse channel="1" count="3" value="456" />'
        )


class TestMemoryRead(unittest.TestCase):
    """Test class for MemoryRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryRead()

        self.assertEqual(payload.calculated_length(), 3)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = MemoryRead(address=0x1234, count=11)
        payload.from_knx(bytes([0x02, 0x0B, 0x12, 0x34]))

        self.assertEqual(payload, MemoryRead(address=0x1234, count=11))

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryRead(address=0x1234, count=11)

        self.assertEqual(payload.to_knx(), bytes([0x02, 0x0B, 0x12, 0x34]))

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryRead(address=0x1234, count=11)

        self.assertEqual(str(payload), '<MemoryRead address="0x1234" count="11" />')


class TestMemoryWrite(unittest.TestCase):
    """Test class for MemoryWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))

        self.assertEqual(payload.calculated_length(), 6)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))
        payload.from_knx(bytes([0x02, 0x83, 0x12, 0x34, 0xAA, 0xBB, 0xCC]))

        self.assertEqual(
            payload,
            MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))

        self.assertEqual(
            payload.to_knx(), bytes([0x02, 0x83, 0x12, 0x34, 0xAA, 0xBB, 0xCC])
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryWrite(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC]))

        self.assertEqual(
            str(payload), '<MemoryWrite address="0x1234" count="3" data="aabbcc" />'
        )


class TestMemoryResponse(unittest.TestCase):
    """Test class for MemoryResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        self.assertEqual(payload.calculated_length(), 6)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )
        payload.from_knx(bytes([0x02, 0x43, 0x12, 0x34, 0xAA, 0xBB, 0xCC]))

        self.assertEqual(
            payload,
            MemoryResponse(address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        self.assertEqual(
            payload.to_knx(), bytes([0x02, 0x43, 0x12, 0x34, 0xAA, 0xBB, 0xCC])
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = MemoryResponse(
            address=0x1234, count=3, data=bytes([0xAA, 0xBB, 0xCC])
        )

        self.assertEqual(
            str(payload), '<MemoryResponse address="0x1234" count="3" data="aabbcc" />'
        )


class TestDeviceDescriptorRead(unittest.TestCase):
    """Test class for DeviceDescriptorRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = DeviceDescriptorRead(0)

        self.assertEqual(payload.calculated_length(), 1)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = DeviceDescriptorRead(13)
        payload.from_knx(bytes([0x03, 0x0D]))

        self.assertEqual(payload, DeviceDescriptorRead(13))

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = DeviceDescriptorRead(13)

        self.assertEqual(payload.to_knx(), bytes([0x03, 0x0D]))

    def test_str(self):
        """Test the __str__ method."""
        payload = DeviceDescriptorRead(0)

        self.assertEqual(str(payload), '<DeviceDescriptorRead descriptor="0" />')


class TestDeviceDescriptorResponse(unittest.TestCase):
    """Test class for DeviceDescriptorResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = DeviceDescriptorResponse(descriptor=0, value=123)

        self.assertEqual(payload.calculated_length(), 3)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = DeviceDescriptorResponse(descriptor=13, value=123)
        payload.from_knx(bytes([0x03, 0x4D, 0x00, 0x7B]))

        self.assertEqual(payload, DeviceDescriptorResponse(descriptor=13, value=123))

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = DeviceDescriptorResponse(descriptor=13, value=123)

        self.assertEqual(payload.to_knx(), bytes([0x03, 0x4D, 0x00, 0x7B]))

    def test_str(self):
        """Test the __str__ method."""
        payload = DeviceDescriptorResponse(descriptor=0, value=123)

        self.assertEqual(
            str(payload), '<DeviceDescriptorResponse descriptor="0" value="123" />'
        )


class TestRestart(unittest.TestCase):
    """Test class for Restart objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = Restart()

        self.assertEqual(payload.calculated_length(), 1)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = Restart()
        payload.from_knx(bytes([0x03, 0x80]))

        self.assertEqual(payload, Restart())

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = Restart()

        self.assertEqual(payload.to_knx(), bytes([0x03, 0x80]))

    def test_str(self):
        """Test the __str__ method."""
        payload = Restart()

        self.assertEqual(str(payload), "<Restart />")


class TestUserManufacturerInfoRead(unittest.TestCase):
    """Test class for UserManufacturerInfoRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = UserManufacturerInfoRead()

        self.assertEqual(payload.calculated_length(), 1)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = UserManufacturerInfoRead()
        payload.from_knx(bytes([0x02, 0xC5]))

        self.assertEqual(payload, UserManufacturerInfoRead())

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = UserManufacturerInfoRead()

        self.assertEqual(payload.to_knx(), bytes([0x02, 0xC5]))

    def test_str(self):
        """Test the __str__ method."""
        payload = UserManufacturerInfoRead()

        self.assertEqual(str(payload), "<UserManufacturerInfoRead />")


class TestUserManufacturerInfoResponse(unittest.TestCase):
    """Test class for UserManufacturerInfoResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")

        self.assertEqual(payload.calculated_length(), 4)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = UserManufacturerInfoResponse()
        payload.from_knx(bytes([0x02, 0xC6, 0x7B, 0x12, 0x34]))

        self.assertEqual(
            payload, UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")

        self.assertEqual(payload.to_knx(), bytes([0x02, 0xC6, 0x7B, 0x12, 0x34]))

    def test_str(self):
        """Test the __str__ method."""
        payload = UserManufacturerInfoResponse(manufacturer_id=123, data=b"\x12\x34")

        self.assertEqual(
            str(payload),
            '<UserManufacturerInfoResponse manufacturer_id="123" data="1234" />',
        )


class TestFunctionPropertyCommand(unittest.TestCase):
    """Test class for FunctionPropertyCommand objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        self.assertEqual(payload.calculated_length(), 5)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = FunctionPropertyCommand()
        payload.from_knx(bytes([0x02, 0xC7, 0x01, 0x04, 0x12, 0x34]))

        self.assertEqual(
            payload,
            FunctionPropertyCommand(object_index=1, property_id=4, data=b"\x12\x34"),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        self.assertEqual(payload.to_knx(), bytes([0x02, 0xC7, 0x01, 0x04, 0x12, 0x34]))

    def test_str(self):
        """Test the __str__ method."""
        payload = FunctionPropertyCommand(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        self.assertEqual(
            str(payload),
            '<FunctionPropertyCommand object_index="1" property_id="4" data="1234" />',
        )


class TestFunctionPropertyStateRead(unittest.TestCase):
    """Test class for FunctionPropertyStateRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        self.assertEqual(payload.calculated_length(), 5)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = FunctionPropertyStateRead()
        payload.from_knx(bytes([0x02, 0xC8, 0x01, 0x04, 0x12, 0x34]))

        self.assertEqual(
            payload,
            FunctionPropertyStateRead(object_index=1, property_id=4, data=b"\x12\x34"),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        self.assertEqual(payload.to_knx(), bytes([0x02, 0xC8, 0x01, 0x04, 0x12, 0x34]))

    def test_str(self):
        """Test the __str__ method."""
        payload = FunctionPropertyStateRead(
            object_index=1, property_id=4, data=b"\x12\x34"
        )

        self.assertEqual(
            str(payload),
            '<FunctionPropertyStateRead object_index="1" property_id="4" data="1234" />',
        )


class TestFunctionPropertyStateResponse(unittest.TestCase):
    """Test class for FunctionPropertyStateResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

        self.assertEqual(payload.calculated_length(), 6)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = FunctionPropertyStateResponse()
        payload.from_knx(bytes([0x02, 0xC8, 0x01, 0x04, 0x08, 0x12, 0x34]))

        self.assertEqual(
            payload,
            FunctionPropertyStateResponse(
                object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
            ),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

        self.assertEqual(
            payload.to_knx(), bytes([0x02, 0xC8, 0x01, 0x04, 0x08, 0x12, 0x34])
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = FunctionPropertyStateResponse(
            object_index=1, property_id=4, return_code=8, data=b"\x12\x34"
        )

        self.assertEqual(
            str(payload),
            '<FunctionPropertyStateResponse object_index="1" property_id="4" return_code="8" data="1234" />',
        )


class TestAuthorizeRequest(unittest.TestCase):
    """Test class for AuthorizeRequest objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = AuthorizeRequest(key=12345678)

        self.assertEqual(payload.calculated_length(), 5)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = AuthorizeRequest()
        payload.from_knx(bytes([0x03, 0xD1, 0x00, 0x00, 0xBC, 0x61, 0x4E]))

        self.assertEqual(payload, AuthorizeRequest(key=12345678))

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = AuthorizeRequest(key=12345678)

        self.assertEqual(
            payload.to_knx(), bytes([0x03, 0xD1, 0x00, 0x00, 0xBC, 0x61, 0x4E])
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = AuthorizeRequest(key=12345678)

        self.assertEqual(str(payload), '<AuthorizeRequest key="12345678" />')


class TestAuthorizeResponse(unittest.TestCase):
    """Test class for AuthorizeResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = AuthorizeResponse(level=123)

        self.assertEqual(payload.calculated_length(), 2)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = AuthorizeResponse()
        payload.from_knx(bytes([0x03, 0xD2, 0x7B]))

        self.assertEqual(payload, AuthorizeResponse(level=123))

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = AuthorizeResponse(level=123)

        self.assertEqual(payload.to_knx(), bytes([0x03, 0xD2, 0x7B]))

    def test_str(self):
        """Test the __str__ method."""
        payload = AuthorizeResponse(level=123)

        self.assertEqual(str(payload), '<AuthorizeResponse level="123"/>')


class TestPropertyValueRead(unittest.TestCase):
    """Test class for PropertyValueRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

        self.assertEqual(payload.calculated_length(), 5)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = PropertyValueRead()
        payload.from_knx(bytes([0x03, 0xD5, 0x01, 0x04, 0x20, 0x08]))

        self.assertEqual(
            payload,
            PropertyValueRead(object_index=1, property_id=4, count=2, start_index=8),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

        self.assertEqual(payload.to_knx(), bytes([0x03, 0xD5, 0x01, 0x04, 0x20, 0x08]))

    def test_str(self):
        """Test the __str__ method."""
        payload = PropertyValueRead(
            object_index=1, property_id=4, count=2, start_index=8
        )

        self.assertEqual(
            str(payload),
            '<PropertyValueRead object_index="1" property_id="4" count="2" start_index="8" />',
        )


class TestPropertyValueWrite(unittest.TestCase):
    """Test class for PropertyValueWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        self.assertEqual(payload.calculated_length(), 7)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = PropertyValueWrite()
        payload.from_knx(bytes([0x03, 0xD7, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]))

        self.assertEqual(
            payload,
            PropertyValueWrite(
                object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
            ),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        self.assertEqual(
            payload.to_knx(), bytes([0x03, 0xD7, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34])
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = PropertyValueWrite(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        self.assertEqual(
            str(payload),
            '<PropertyValueWrite object_index="1" property_id="4" count="2" start_index="8" data="1234" />',
        )


class TestPropertyValueResponse(unittest.TestCase):
    """Test class for PropertyValueResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        self.assertEqual(payload.calculated_length(), 7)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = PropertyValueResponse()
        payload.from_knx(bytes([0x03, 0xD6, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34]))

        self.assertEqual(
            payload,
            PropertyValueResponse(
                object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
            ),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        self.assertEqual(
            payload.to_knx(), bytes([0x03, 0xD6, 0x01, 0x04, 0x20, 0x08, 0x12, 0x34])
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = PropertyValueResponse(
            object_index=1, property_id=4, count=2, start_index=8, data=b"\x12\x34"
        )

        self.assertEqual(
            str(payload),
            '<PropertyValueResponse object_index="1" property_id="4" count="2" start_index="8" data="1234" />',
        )


class TestPropertyDescriptionRead(unittest.TestCase):
    """Test class for PropertyDescriptionRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

        self.assertEqual(payload.calculated_length(), 4)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = PropertyDescriptionRead()
        payload.from_knx(bytes([0x03, 0xD8, 0x01, 0x04, 0x08]))

        self.assertEqual(
            payload,
            PropertyDescriptionRead(object_index=1, property_id=4, property_index=8),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

        self.assertEqual(payload.to_knx(), bytes([0x03, 0xD8, 0x01, 0x04, 0x08]))

    def test_str(self):
        """Test the __str__ method."""
        payload = PropertyDescriptionRead(
            object_index=1, property_id=4, property_index=8
        )

        self.assertEqual(
            str(payload),
            '<PropertyDescriptionRead object_index="1" property_id="4" property_index="8" />',
        )


class TestPropertyDescriptionResponse(unittest.TestCase):
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

        self.assertEqual(payload.calculated_length(), 8)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = PropertyDescriptionResponse()
        payload.from_knx(bytes([0x03, 0xD9, 0x01, 0x04, 0x08, 0x03, 0x00, 0x05, 0x07]))

        self.assertEqual(
            payload,
            PropertyDescriptionResponse(
                object_index=1,
                property_id=4,
                property_index=8,
                type_=3,
                max_count=5,
                access=7,
            ),
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

        self.assertEqual(
            payload.to_knx(),
            bytes([0x03, 0xD9, 0x01, 0x04, 0x08, 0x03, 0x00, 0x05, 0x07]),
        )

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

        self.assertEqual(
            str(payload),
            '<PropertyDescriptionResponse object_index="1" property_id="4" property_index="8" type="3" max_count="5" access="7" />',
        )


class TestIndividualAddressSerialRead(unittest.TestCase):
    """Test class for IndividualAddressSerialRead objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

        self.assertEqual(payload.calculated_length(), 7)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = IndividualAddressSerialRead()
        payload.from_knx(bytes([0x03, 0xDC, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33]))

        self.assertEqual(
            payload, IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

        self.assertEqual(
            payload.to_knx(), bytes([0x03, 0xDC, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33])
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressSerialRead(b"\xaa\xbb\xcc\x11\x22\x33")

        self.assertEqual(
            str(payload), '<IndividualAddressSerialRead serial="aabbcc112233" />'
        )


class TestIndividualAddressSerialResponse(unittest.TestCase):
    """Test class for IndividualAddressSerialResponse objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        self.assertEqual(payload.calculated_length(), 11)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = IndividualAddressSerialResponse()
        payload.from_knx(
            bytes(
                [0x03, 0xDD, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33, 0x12, 0x03, 0x00, 0x00]
            )
        )

        self.assertEqual(
            payload,
            IndividualAddressSerialResponse(
                serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
            ),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        self.assertEqual(
            payload.to_knx(),
            bytes(
                [0x03, 0xDD, 0xAA, 0xBB, 0xCC, 0x11, 0x22, 0x33, 0x12, 0x03, 0x00, 0x00]
            ),
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressSerialResponse(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        self.assertEqual(
            str(payload),
            '<IndividualAddressSerialResponse serial="aabbcc112233" address="1.2.3" />',
        )


class TestIndividualAddressSerialWrite(unittest.TestCase):
    """Test class for IndividualAddressSerialWrite objects."""

    def test_calculated_length(self):
        """Test the test_calculated_length method."""
        payload = IndividualAddressSerialWrite(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        self.assertEqual(payload.calculated_length(), 13)

    def test_from_knx(self):
        """Test the from_knx method."""
        payload = IndividualAddressSerialWrite()
        payload.from_knx(
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

        self.assertEqual(
            payload,
            IndividualAddressSerialWrite(
                serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
            ),
        )

    def test_to_knx(self):
        """Test the to_knx method."""
        payload = IndividualAddressSerialWrite(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        self.assertEqual(
            payload.to_knx(),
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
            ),
        )

    def test_str(self):
        """Test the __str__ method."""
        payload = IndividualAddressSerialWrite(
            serial=b"\xaa\xbb\xcc\x11\x22\x33", address=IndividualAddress("1.2.3")
        )

        self.assertEqual(
            str(payload),
            '<IndividualAddressSerialWrite serial="aabbcc112233" address="1.2.3" />',
        )
