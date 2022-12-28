from collections import namedtuple
import pytest

from xknx.usb.knx_hid_transfer import KNXUSBTransferProtocolHeader, KNXUSBTransferProtocolHeaderData


class TestKNXUSBTransferProtocolHeaderData:
    """ """


class TestKNXUSBTransferProtocolBodyData:
    """ """


TransferProtocolHeaderExpected = namedtuple(
    "TransferProtocolHeaderExpected",
    "protocol_version header_length body_length protocol_id emi_id manufacturer_code is_valid",
)


class TestKNXUSBTransferProtocolHeader:
    """ """

    def test_default_initialization(self):
        """ """
        transfer_header = KNXUSBTransferProtocolHeader()
        assert transfer_header.is_valid == False

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
        "input,expected",
        [(1,2),],
    )
    def test_from_knx(self, input, expected):
        pass

    @pytest.mark.parametrize(
        "input,expected",
        [(1,2),],
    )
    def test_to_knx(self, input, expected):
        pass


class TestKNXUSBTransferProtocolBody:
    """ """
