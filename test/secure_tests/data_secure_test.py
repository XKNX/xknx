"""Tests for KNX Data Secure."""
import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from xknx import XKNX
from xknx.cemi import CEMIFrame, CEMIMessageCode
from xknx.dpt import DPTArray
from xknx.exceptions import DataSecureError

# from xknx.secure.data_secure_asdu import DataSecureASDU
from xknx.secure.keyring import Keyring, _load_keyring
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, apci, tpci


class TestDataSecure:
    """Test class for KNX Data Secure."""

    secure_test_keyring: Keyring

    @classmethod
    def setup_class(cls) -> None:
        """Setup any state specific to the execution of the given class."""
        secure_test_keyfile = os.path.join(
            os.path.dirname(__file__), "resources/SecureTest.knxkeys"
        )
        cls.secure_test_keyring = _load_keyring(secure_test_keyfile, "test")

    async def test_data_secure_init(self) -> None:
        """Test DataSecure init and passing frames from CEMIHandler to DataSecure."""
        xknx = XKNX()
        xknx.knxip_interface = AsyncMock()
        xknx.cemi_handler.data_secure_init(TestDataSecure.secure_test_keyring)
        assert xknx.cemi_handler._data_secure is not None
        data_secure = xknx.cemi_handler._data_secure

        assert len(data_secure.group_key_table) == 4
        for ga_raw in [1024, 1027, 1028, 1029]:
            assert GroupAddress(ga_raw) in data_secure.group_key_table

        assert len(data_secure._individual_address_table) == 3
        for ia_raw in ["4.0.0", "4.0.9", "5.0.0"]:
            assert IndividualAddress(ia_raw) in data_secure._individual_address_table

        # this is based on clock milliseconds
        assert data_secure._sequence_number_sending > 0

        test_telegram = Telegram(
            destination_address=GroupAddress("0/4/0"),
            payload=apci.GroupValueRead(),
        )
        with patch.object(data_secure, "outgoing_cemi") as mock_ds_outgoing_cemi:
            task = asyncio.create_task(xknx.cemi_handler.send_telegram(test_telegram))
            await asyncio.sleep(0)
            mock_ds_outgoing_cemi.assert_called_once()
            xknx.cemi_handler._l_data_confirmation_event.set()
            await task

        test_cemi = CEMIFrame.init_from_telegram(test_telegram)
        with patch.object(
            data_secure, "received_cemi"
        ) as mock_ds_received_cemi, patch.object(
            xknx.cemi_handler, "telegram_received"
        ) as mock_telegram_received:  # supress forwarding to telegras/management
            xknx.cemi_handler.handle_cemi_frame(test_cemi)
            mock_ds_received_cemi.assert_called_once()
            mock_telegram_received.assert_called_once()

    def test_data_secure_group_send(self) -> None:
        """Test outgoing DataSecure group communication."""
        xknx = XKNX()
        xknx.knxip_interface = AsyncMock()
        xknx.current_address = IndividualAddress("5.0.1")
        xknx.cemi_handler.data_secure_init(TestDataSecure.secure_test_keyring)
        xknx.cemi_handler._data_secure._sequence_number_sending = 160170101607
        data_secure = xknx.cemi_handler._data_secure

        test_cemi = CEMIFrame.init_from_telegram(
            Telegram(
                destination_address=GroupAddress("0/4/0"),
                payload=apci.GroupValueRead(),
            ),
            code=CEMIMessageCode.L_DATA_REQ,
            src_addr=xknx.current_address,
        )
        secured_frame = data_secure.outgoing_cemi(test_cemi)
        assert isinstance(secured_frame.payload, apci.SecureAPDU)
        secured_asdu = secured_frame.payload.secured_data

        assert int.from_bytes(secured_asdu.sequence_number_bytes, "big") == 160170101607
        assert secured_asdu.secured_apdu == bytes.fromhex("cd18")
        assert secured_asdu.message_authentication_code == bytes.fromhex("4afe5744")
        # sequence number sending was incremented
        assert data_secure._sequence_number_sending == 160170101608

        assert secured_frame.to_knx() == bytes.fromhex(
            "1100bce0500104000e03f11000254ae1cb67cd184afe5744"
        )

    def test_data_secure_group_receive(self) -> None:
        """Test incoming DataSecure group communication."""
        xknx = XKNX()
        xknx.current_address = IndividualAddress("5.0.1")
        xknx.cemi_handler.data_secure_init(TestDataSecure.secure_test_keyring)
        data_secure = xknx.cemi_handler._data_secure
        assert (
            data_secure._individual_address_table[IndividualAddress("4.0.9")]
            == 155806854915
        )

        test_cemi = CEMIFrame.from_knx(
            bytes.fromhex("29003ce0400904001103f110002446cfef4ac085e7092ab062b44d")
        )
        assert isinstance(test_cemi.payload, apci.SecureAPDU)
        plain_frame = data_secure.received_cemi(test_cemi)
        assert plain_frame.payload == apci.GroupValueResponse(DPTArray((116, 41, 41)))
        # individual_address_table sequnece number was updated
        assert (
            data_secure._individual_address_table[IndividualAddress("4.0.9")]
            == 155806854986
        )

    def test_data_secure_individual_receive(self) -> None:
        """Test incoming DataSecure point-to-point communication."""
        # Property Value Write PID_GRP_KEY_TABLE connectionless
        # Objet Idx = 5, PropId = 35h, Element Count = 1, Index = 1
        # Data = 20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F
        # A+C
        # from AN158 v07 KNX Data Security AS - Annex A example
        xknx = XKNX()
        xknx.current_address = IndividualAddress("15.15.0")
        xknx.cemi_handler.data_secure_init(TestDataSecure.secure_test_keyring)

        test_cemi = CEMIFrame.from_knx(
            bytes.fromhex(
                "29 00 b0 60 ff 67 ff 00 22 03 f1 90 00 00 00 00"
                "00 04 67 67 24 2a 23 08 ca 76 a1 17 74 21 4e e4"
                "cf 5d 94 90 9f 74 3d 05 0d 8f c1 68"
            )
        )
        assert isinstance(test_cemi.payload, apci.SecureAPDU)

        with pytest.raises(
            DataSecureError, match=r"System broadcast and tool access not supported.*"
        ):
            xknx.cemi_handler._data_secure.received_cemi(test_cemi)
        # don't raise through handle_cemi_frame()
        assert xknx.cemi_handler.handle_cemi_frame(test_cemi) is None
