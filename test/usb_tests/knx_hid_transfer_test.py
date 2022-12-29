from collections import namedtuple
import pytest

from xknx.usb.knx_hid_transfer import KNXUSBTransferProtocolBodyData, KNXUSBTransferProtocolHeader, KNXUSBTransferProtocolHeaderData


class TestKNXUSBTransferProtocolHeaderData:
    """ """
    @pytest.mark.parametrize(
    "body_length,protocol_id,emi_id",
    [
        (1, 2, 3),
        (3, 4, 1),
    ],
    )
    def test_initialization(self, body_length, protocol_id, emi_id):
        """ """
        knx_usb_transfer_protocol_header_data = KNXUSBTransferProtocolHeaderData(body_length, protocol_id, emi_id)
        assert knx_usb_transfer_protocol_header_data.body_length == body_length
        assert knx_usb_transfer_protocol_header_data.protocol_id == protocol_id
        assert knx_usb_transfer_protocol_header_data.emi_id == emi_id


class TestKNXUSBTransferProtocolBodyData:
    """ """
    @pytest.mark.parametrize(
    "data,partial",
    [
        (b"\x01", True),
        (b"\x0201", True),
        (b"\x0201", False),
        (b"\x01", False),
    ],
    )
    def test_initialization(self, data, partial):
        """ """
        knx_usb_transfer_protocol_body_data = KNXUSBTransferProtocolBodyData(data, partial)
        assert knx_usb_transfer_protocol_body_data.data == data
        assert knx_usb_transfer_protocol_body_data.partial == partial


TransferProtocolHeaderExpected = namedtuple(
    "TransferProtocolHeaderExpected",
    "protocol_version header_length body_length protocol_id emi_id manufacturer_code is_valid",
)


class TestKNXUSBTransferProtocolHeader:
    """ """

    def test_default_initialization(self):
        """ """
        transfer_header = KNXUSBTransferProtocolHeader()
        assert not transfer_header.is_valid
        assert transfer_header.header_length == 0x08

    @pytest.mark.parametrize(
        "input,expected",
        [
            (
                KNXUSBTransferProtocolHeaderData(body_length=8, protocol_id=1, emi_id=1),
                TransferProtocolHeaderExpected(
                    body_length=8,
                    emi_id=1,
                    header_length=8,  # always 8 for protocol version 0
                    is_valid=True,
                    manufacturer_code=0,
                    protocol_id=1,
                    protocol_version=0,  # for now always 0
                ),
            ),
        ],
    )
    def test_from_data(self, input, expected):
        """ """
        header = KNXUSBTransferProtocolHeader.from_data(input)
        assert header.body_length == expected.body_length
        assert header.emi_id == expected.emi_id
        assert header.header_length == expected.header_length
        assert header.is_valid == expected.is_valid
        assert header.manufacturer_code == expected.manufacturer_code
        assert header.protocol_id == expected.protocol_id
        assert header.protocol_version == expected.protocol_version

    @pytest.mark.parametrize(
    "data,is_valid",
    [
        (b"\x01\x08\x00\x10\x01\x03\x00\x00", False),  # invalid protocl version
        (b"\x00\x07\x00\x10\x01\x03\x00\x00", False),  # invalid header length
        (b"\x00\x07\x00\x10\x01\x06\x00\x00", False),  # invalid EMI ID
        (b"\x00\x08\x00\x10\x01\x03\x00\x00", True),
        (b"\x00\x08\x00\x20\x01\x03\x00\x00", True),  # one byte body length
        (b"\x00\x08\x20\x10\x01\x03\x00\x00", True),  # two byte body length
        (b"\x00\x08\x20\x10\x01\x02\x00\x00", True),  # different EMI ID
        (b"\x00\x08\x20\x10\x01\x02\x10\x20", True),  # different manufacturer code
    ],
    )
    def test_from_knx(self, data, is_valid):
        """ """
        knx_usb_transfer_protocol_header = KNXUSBTransferProtocolHeader.from_knx(data)
        assert knx_usb_transfer_protocol_header.protocol_version == data[0]
        assert knx_usb_transfer_protocol_header.header_length == data[1]
        assert knx_usb_transfer_protocol_header.body_length == int.from_bytes(data[2:4], byteorder="big")
        assert knx_usb_transfer_protocol_header.protocol_id == data[4]
        assert knx_usb_transfer_protocol_header.emi_id == data[5]
        assert knx_usb_transfer_protocol_header.manufacturer_code == int.from_bytes(data[6:8], byteorder="big")
        assert knx_usb_transfer_protocol_header.is_valid == is_valid

    @pytest.mark.parametrize(
    "data",
    [
        (b"\x01\x08\x00\x10\x01\x03\x00\x00", False),  # invalid protocl version
        (b"\x00\x08\x00\x10\x01\x03", False),  # not enough bytes
    ],
    )
    def test_from_knx_invalid(self, data):
        """ """
        knx_usb_transfer_protocol_header = KNXUSBTransferProtocolHeader.from_knx(data)
        assert knx_usb_transfer_protocol_header.protocol_version == 0
        assert knx_usb_transfer_protocol_header.header_length == 8
        assert knx_usb_transfer_protocol_header.body_length == 0
        assert knx_usb_transfer_protocol_header.protocol_id is None
        assert knx_usb_transfer_protocol_header.emi_id is None
        assert knx_usb_transfer_protocol_header.manufacturer_code == 0
        assert not knx_usb_transfer_protocol_header.is_valid

    @pytest.mark.parametrize(
    "data",
    [
        (b"\x00\x08\x00\x10\x01\x03\x00\x00"),
        (b"\x00\x08\x00\x20\x01\x03\x00\x00"),  # one byte body length
        (b"\x00\x08\x20\x10\x01\x03\x00\x00"),  # two byte body length
        (b"\x00\x08\x20\x10\x01\x02\x00\x00"),  # different EMI ID
        (b"\x00\x08\x20\x10\x01\x02\x10\x20"),  # different manufacturer code
    ],
    )
    def test_to_knx(self, data):
        knx_usb_transfer_protocol_header = KNXUSBTransferProtocolHeader.from_knx(data)
        assert data == knx_usb_transfer_protocol_header.to_knx()


class TestKNXUSBTransferProtocolBody:
    """ """
