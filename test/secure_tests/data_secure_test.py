"""Tests for KNX Data Secure."""
import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMILData, CEMIMessageCode
from xknx.dpt import DPTArray
from xknx.exceptions import DataSecureError
from xknx.secure.data_secure_asdu import (
    SecurityAlgorithmIdentifier,
    SecurityALService,
    SecurityControlField,
)
from xknx.secure.keyring import Keyring, sync_load_keyring
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
    apci,
    tpci,
)


@pytest.fixture
def test_group_response_cemi():
    """Return a CEMI frame for a group response telegram."""
    # src = 4.0.9; dst = 0/4/0; GroupValueResponse; value=(116, 41, 41)
    # A+C; seq_num=155806854986
    return CEMIFrame.from_knx(
        bytes.fromhex("29003ce0400904001103f110002446cfef4ac085e7092ab062b44d")
    )


@pytest.fixture
def test_point_to_point_cemi():
    """Return a CEMI frame for a group response telegram."""
    # Property Value Write PID_GRP_KEY_TABLE connectionless
    # Object Idx = 5, PropId = 35h, Element Count = 1, Index = 1
    # Data = 20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F
    # A+C
    # from AN158 v07 KNX Data Security AS - Annex A example
    return CEMIFrame.from_knx(
        bytes.fromhex(
            "29 00 b0 60 ff 67 ff 00 22 03 f1 90 00 00 00 00"
            "00 04 67 67 24 2a 23 08 ca 76 a1 17 74 21 4e e4"
            "cf 5d 94 90 9f 74 3d 05 0d 8f c1 68"
        )
    )


class TestDataSecure:
    """Test class for KNX Data Secure."""

    secure_test_keyring: Keyring

    @classmethod
    def setup_class(cls):
        """Set up any state specific to the execution of the given class."""
        secure_test_keyfile = os.path.join(
            os.path.dirname(__file__), "resources/SecureTest.knxkeys"
        )
        cls.secure_test_keyring = sync_load_keyring(secure_test_keyfile, "test")

    def setup_method(self):
        """Set up test methods."""
        # pylint: disable=attribute-defined-outside-init
        self.xknx = XKNX()
        self.xknx.knxip_interface = AsyncMock()
        self.xknx.current_address = IndividualAddress("5.0.1")
        self.xknx.cemi_handler.data_secure_init(TestDataSecure.secure_test_keyring)

        self.data_secure = self.xknx.cemi_handler.data_secure

    async def test_data_secure_init(self):
        """Test DataSecure init and passing frames from CEMIHandler to DataSecure."""
        assert self.data_secure is not None

        assert len(self.data_secure._group_key_table) == 4
        for ga_raw in [1024, 1027, 1028, 1029]:
            assert GroupAddress(ga_raw) in self.data_secure._group_key_table

        assert len(self.data_secure._individual_address_table) == 5
        for ia_raw in ["4.0.0", "4.0.1", "4.0.9", "5.0.0", "5.0.1"]:
            assert (
                IndividualAddress(ia_raw) in self.data_secure._individual_address_table
            )

        # this is based on clock milliseconds
        assert self.data_secure._sequence_number_sending > 0

        test_telegram = Telegram(
            destination_address=GroupAddress("0/4/0"),
            payload=apci.GroupValueRead(),
        )
        with patch.object(self.data_secure, "outgoing_cemi") as mock_ds_outgoing_cemi:
            task = asyncio.create_task(
                self.xknx.cemi_handler.send_telegram(test_telegram)
            )
            await asyncio.sleep(0)
            mock_ds_outgoing_cemi.assert_called_once()
            self.xknx.cemi_handler._l_data_confirmation_event.set()
            await task

        test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(test_telegram),
        )
        with patch.object(
            self.data_secure,
            "received_cemi",
            return_value=test_cemi.data,  # Reuse incoming plain APDU. Decryption is not tested here
        ) as mock_ds_received_cemi, patch.object(
            self.xknx.cemi_handler, "telegram_received"
        ) as mock_telegram_received:  # suppress forwarding to telegras/management
            self.xknx.cemi_handler.handle_cemi_frame(test_cemi)
            mock_ds_received_cemi.assert_called_once()
            mock_telegram_received.assert_called_once()

    def test_data_secure_init_invalid_system_time(self):
        """Test DataSecure init with invalid system time."""
        with (
            patch("time.time", return_value=1515108203.0),  # 2018-01-04T23:23:23+00:00
            pytest.raises(DataSecureError, match=r"Initial sequence number out of .*"),
        ):
            self.xknx.cemi_handler.data_secure_init(TestDataSecure.secure_test_keyring)

    def test_data_secure_group_send(self):
        """Test outgoing DataSecure group communication."""
        self.data_secure._sequence_number_sending = 160170101607

        test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_REQ,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=GroupAddress("0/4/0"),
                    payload=apci.GroupValueRead(),
                ),
                src_addr=self.xknx.current_address,
            ),
        )
        secured_frame_data = self.data_secure.outgoing_cemi(test_cemi.data)
        assert isinstance(secured_frame_data, CEMILData)
        assert isinstance(secured_frame_data.payload, apci.SecureAPDU)
        secured_asdu = secured_frame_data.payload.secured_data

        assert int.from_bytes(secured_asdu.sequence_number_bytes, "big") == 160170101607
        assert secured_asdu.secured_apdu == bytes.fromhex("cd18")
        assert secured_asdu.message_authentication_code == bytes.fromhex("4afe5744")
        # sequence number sending was incremented
        assert self.data_secure._sequence_number_sending == 160170101608

        assert secured_frame_data.to_knx() == bytes.fromhex(
            "bce0500104000e03f11000254ae1cb67cd184afe5744"
        )

    def test_data_secure_group_receive(self, test_group_response_cemi):
        """Test incoming DataSecure group communication."""
        assert (
            self.data_secure._individual_address_table[IndividualAddress("4.0.9")]
            == 155806854915
        )
        assert isinstance(test_group_response_cemi.data, CEMILData)
        assert test_group_response_cemi.data.src_addr == IndividualAddress("4.0.9")
        assert isinstance(test_group_response_cemi.data.payload, apci.SecureAPDU)

        plain_frame_data = self.data_secure.received_cemi(test_group_response_cemi.data)
        assert isinstance(plain_frame_data, CEMILData)
        assert plain_frame_data.payload == apci.GroupValueResponse(
            DPTArray((116, 41, 41))
        )
        # individual_address_table sequence number was updated
        assert (
            self.data_secure._individual_address_table[IndividualAddress("4.0.9")]
            == 155806854986
        )

    def test_data_secure_individual_receive_tool_key(self, test_point_to_point_cemi):
        """Test incoming DataSecure point-to-point communication via tool key."""
        self.xknx.current_address = IndividualAddress("15.15.0")
        assert isinstance(test_point_to_point_cemi.data.payload, apci.SecureAPDU)

        with pytest.raises(
            DataSecureError, match=r"System broadcast and tool access not supported.*"
        ):
            self.data_secure.received_cemi(test_point_to_point_cemi.data)
        # don't raise through handle_cemi_frame()
        assert (
            self.xknx.cemi_handler.handle_cemi_frame(test_point_to_point_cemi) is None
        )

    def test_data_secure_individual_receive(self, test_point_to_point_cemi):
        """Test incoming DataSecure point-to-point communication."""
        self.xknx.current_address = IndividualAddress("15.15.0")
        assert isinstance(test_point_to_point_cemi.data.payload, apci.SecureAPDU)
        # don't use tool key or system broadcast
        # further validation is skipped so we can use the same test data
        test_point_to_point_cemi.data.payload.scf.tool_access = False
        test_point_to_point_cemi.data.payload.scf.system_broadcast = False
        with pytest.raises(
            DataSecureError,
            match=r"Secure Point-to-Point communication not supported.*",
        ):
            self.data_secure.received_cemi(test_point_to_point_cemi.data)
        # don't raise through handle_cemi_frame()
        assert (
            self.xknx.cemi_handler.handle_cemi_frame(test_point_to_point_cemi) is None
        )

    def test_data_secure_group_receive_unknown_source(self, test_group_response_cemi):
        """Test incoming DataSecure group communication from unknown source."""
        test_group_response_cemi.data.src_addr = IndividualAddress("1.2.3")
        with pytest.raises(
            DataSecureError,
            match=r"Source address not found in Security Individual Address Table.*",
        ):
            self.data_secure.received_cemi(test_group_response_cemi.data)

    def test_data_secure_group_receive_unknown_destination(
        self, test_group_response_cemi
    ):
        """Test incoming DataSecure group communication for unknown destination."""
        test_group_response_cemi.data.dst_addr = GroupAddress("1/2/3")
        with pytest.raises(
            DataSecureError,
            match=r"No key found for group address.*",
        ):
            self.data_secure.received_cemi(test_group_response_cemi.data)

    def test_data_secure_group_receive_wrong_sequence_number(
        self, test_group_response_cemi
    ):
        """Test incoming DataSecure group communication with wrong sequence number."""
        seq_num = 155806854986
        assert (
            test_group_response_cemi.data.payload.secured_data.sequence_number_bytes
            == seq_num.to_bytes(6, "big")
        )
        # sequence number already used
        self.data_secure._individual_address_table[IndividualAddress("4.0.9")] = seq_num
        with pytest.raises(
            DataSecureError,
            match=r"Sequence number too low.*",
        ):
            self.data_secure.received_cemi(test_group_response_cemi.data)

    def test_data_secure_group_receive_wrong_mac(self, test_group_response_cemi):
        """Test incoming DataSecure group communication with wrong MAC."""
        test_group_response_cemi.data.payload.secured_data.message_authentication_code = bytes(
            4
        )
        with pytest.raises(
            DataSecureError,
            match=r"Data Secure MAC verification failed.*",
        ):
            self.data_secure.received_cemi(test_group_response_cemi.data)

    def test_data_secure_group_receive_plain_frame(self):
        """Test incoming DataSecure group communication with plain frame."""
        src_addr = IndividualAddress("4.0.9")
        test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=GroupAddress("0/4/0"),
                    direction=TelegramDirection.INCOMING,
                    payload=apci.GroupValueResponse(DPTArray((116, 41, 41))),
                ),
                src_addr=src_addr,
            ),
        )
        assert src_addr in self.data_secure._individual_address_table
        with pytest.raises(
            DataSecureError,
            match=r"Discarding frame with plain APDU for secure group address.*",
        ):
            self.data_secure.received_cemi(test_cemi.data)

    def test_non_secure_group_receive_plain_frame(self):
        """Test incoming non-secure group communication with plain frame."""
        dst_addr = GroupAddress("1/2/3")
        test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=dst_addr,
                    direction=TelegramDirection.INCOMING,
                    payload=apci.GroupValueResponse(DPTArray((116, 41, 41))),
                ),
                src_addr=IndividualAddress("4.0.9"),
            ),
        )
        assert dst_addr not in self.data_secure._group_key_table
        assert self.data_secure.received_cemi(test_cemi.data) == test_cemi.data

    def test_non_secure_group_send_plain_frame(self):
        """Test outgoing non-secure group communication with plain frame."""
        dst_addr = GroupAddress("1/2/3")
        test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_REQ,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=dst_addr,
                    direction=TelegramDirection.OUTGOING,
                    payload=apci.GroupValueResponse(DPTArray((116, 41, 41))),
                ),
                src_addr=self.xknx.current_address,
            ),
        )
        assert dst_addr not in self.data_secure._group_key_table
        assert self.data_secure.outgoing_cemi(test_cemi.data) == test_cemi.data

    def test_non_secure_individual_receive_plain_frame(self):
        """Test incoming non-secure group communication with plain frame."""
        src_addr = IndividualAddress("1.2.3")
        test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_IND,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=self.xknx.current_address,
                    direction=TelegramDirection.INCOMING,
                    payload=apci.PropertyValueWrite(
                        object_index=5,
                        property_id=0x35,
                        count=1,
                        start_index=1,
                        data=bytes.fromhex(
                            "20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F"
                        ),
                    ),
                    tpci=tpci.TDataIndividual(),
                ),
                src_addr=IndividualAddress("4.0.9"),
            ),
        )
        assert src_addr not in self.data_secure._individual_address_table
        assert self.data_secure.received_cemi(test_cemi.data) == test_cemi.data

    def test_non_secure_individual_send_plain_frame(self):
        """Test outgoing non-secure group communication with plain frame."""
        dst_addr = IndividualAddress("1.2.3")
        test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_REQ,
            data=CEMILData.init_from_telegram(
                Telegram(
                    destination_address=dst_addr,
                    direction=TelegramDirection.INCOMING,
                    payload=apci.PropertyValueWrite(
                        object_index=5,
                        property_id=0x35,
                        count=1,
                        start_index=1,
                        data=bytes.fromhex(
                            "20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F"
                        ),
                    ),
                    tpci=tpci.TDataIndividual(),
                ),
                src_addr=self.xknx.current_address,
            ),
        )
        assert dst_addr not in self.data_secure._individual_address_table
        assert self.data_secure.outgoing_cemi(test_cemi.data) == test_cemi.data

    def test_data_secure_authentication_only(self):
        """Test frame de-/serialization for DataSecure authentication only."""
        # This is currently not used from xknx and I also don't know if it is used
        # in any ETS or runtime KNX communication. Therefore a very generic test.
        dst_addr = GroupAddress("0/4/0")
        test_telegram = Telegram(
            destination_address=dst_addr,
            direction=TelegramDirection.OUTGOING,
            payload=apci.GroupValueWrite(DPTArray((1, 2))),
        )
        test_cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_REQ,
            data=CEMILData.init_from_telegram(
                telegram=test_telegram,
                src_addr=self.xknx.current_address,
            ),
        )
        scf = SecurityControlField(
            algorithm=SecurityAlgorithmIdentifier.CCM_AUTHENTICATION,
            service=SecurityALService.S_A_DATA,
            system_broadcast=False,
            tool_access=False,
        )
        key = self.data_secure._group_key_table[dst_addr]

        outgoing_signed_cemi_data = self.data_secure._secure_data_cemi(
            key=key, scf=scf, cemi_data=test_cemi.data
        )
        assert outgoing_signed_cemi_data.payload.secured_data is not None

        # create new cemi to avoid mixed bytearray / byte parts
        incoming_cemi = CEMIFrame.from_knx(
            b"\x11\x00" + outgoing_signed_cemi_data.to_knx()
        )
        assert isinstance(incoming_cemi.data, CEMILData)
        # receive same cemi - fake individual address table entry
        self.data_secure._individual_address_table[incoming_cemi.data.src_addr] = 1
        assert self.data_secure.received_cemi(incoming_cemi.data) == test_cemi.data

        # Test wrong MAC
        self.data_secure._individual_address_table[incoming_cemi.data.src_addr] = 1
        incoming_cemi.data.payload.secured_data.message_authentication_code = bytes(4)
        with pytest.raises(
            DataSecureError,
            match=r"Data Secure MAC verification failed.*",
        ):
            self.data_secure.received_cemi(incoming_cemi.data)
