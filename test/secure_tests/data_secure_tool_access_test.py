"""Tests for KNX Data Secure point-to-point communication with the Tool Key."""

from pathlib import Path
from unittest.mock import patch

import pytest

from xknx.cemi import CEMILData
from xknx.cemi.flags import CEMIAddressType, CEMIFrameFormat
from xknx.exceptions import DataSecureError
from xknx.secure.data_secure import DataSecure
from xknx.secure.data_secure_asdu import (
    SecureData,
    SecurityControlField,
    block_0,
)
from xknx.secure.keyring import sync_load_keyring
from xknx.telegram import IndividualAddress, Telegram, apci, tpci

# KNX v02.01.01 - Application Layer 03.03.07 - Annex C.1: a tool 15.15.103 programs a
# device 15.15.0 with the Tool Key 000102...0f.
TOOL = IndividualAddress("15.15.103")
DEVICE = IndividualAddress("15.15.0")
TOOL_KEY = bytes(range(16))
CHALLENGE = bytes.fromhex("000000000003")
TOOL_TO_DEVICE = bytes.fromhex("FF67FF00")
DEVICE_TO_TOOL = bytes.fromhex("FF00FF67")
# Annex C.1.3 S-A_Sync.req (SCF 92h, SeqNr_local 1, KNX Serial Number 0, Challenge 3)
SYNC_REQ = bytes.fromhex("03F1" "92" "000000000001" "000000000000" "c1cf4506f09bd79fab55")
# Annex C.1.4 S-A_Sync.res (SCF 93h, Random AA..AA, SeqNr_remote 3, SeqNr_local 4)
SYNC_RES = bytes.fromhex(
    "03F1" "93" "aaaaaaaaaaa9" "9c023ad25e146470693e638d" "5b70cac4"
)
# Annex C.1.1: A_PropertyValue_Write of PID_GRP_KEY_TABLE as S-A_Data with SeqNr 4
PROPERTY_WRITE = apci.PropertyValueWrite(
    object_index=5,
    property_id=0x35,
    count=1,
    start_index=1,
    data=bytes(range(0x20, 0x30)),
)
SECURE_PROPERTY_WRITE = bytes.fromhex(
    "03F1" "90" "000000000004" "6767242a2308ca76a11774214ee4cf5d94909f743d05" "0d8fc168"
)
# Annex C.1.2: its A_PropertyValue_Response as S-A_Data with SeqNr 3
SECURE_PROPERTY_RESPONSE = bytes.fromhex(
    "03F1" "90" "000000000003" "706f533105503557cb2b24f1dd341b60b7e017ecd6b0" "6849a72b"
)


def _cemi(
    src: IndividualAddress,
    dst: IndividualAddress,
    tpci_: tpci.TPCI,
    payload: apci.APCI | None = None,
) -> CEMILData:
    return CEMILData.init_from_telegram(
        Telegram(destination_address=dst, tpci=tpci_, payload=payload),
        src_addr=src,
    )


def _secure(raw: bytes) -> apci.SecureAPDU:
    return apci.SecureAPDU.from_knx(raw)


def test_block_0_with_connection_oriented_tpci() -> None:
    """The TPCI octet of B0 is the TPCI as sent - Annex C.1.3."""
    assert block_0(
        sequence_number=bytes.fromhex("000000000001"),
        address_fields_raw=TOOL_TO_DEVICE,
        address_type=CEMIAddressType.INDIVIDUAL,
        frame_format=CEMIFrameFormat.STANDARD,
        tpci_int=tpci.TDataConnected(sequence_number=0).to_knx(),
        payload_length=6,
    ) == bytes.fromhex("000000000001FF67FF00000043F10006")


class TestSyncSecureData:
    """S-A_Sync PDUs of Annex C.1.3 and C.1.4."""

    def test_sync_request(self) -> None:
        """Build and verify the S-A_Sync_Req-PDU."""
        scf = SecurityControlField.from_knx(0x92)
        secured_data = SecureData.init_sync_request(
            key=TOOL_KEY,
            scf=scf,
            sequence_number=1,
            serial_number=bytes(6),
            challenge=CHALLENGE,
            address_fields_raw=TOOL_TO_DEVICE,
            address_type=CEMIAddressType.INDIVIDUAL,
            frame_format=CEMIFrameFormat.STANDARD,
            tpci=tpci.TDataConnected(sequence_number=0),
        )
        assert apci.SecureAPDU(scf=scf, secured_data=secured_data).to_knx() == SYNC_REQ
        assert secured_data.get_sync_request_challenge(
            key=TOOL_KEY,
            scf=scf,
            address_fields_raw=TOOL_TO_DEVICE,
            address_type=CEMIAddressType.INDIVIDUAL,
            frame_format=CEMIFrameFormat.STANDARD,
            tpci=tpci.TDataConnected(sequence_number=0),
        ) == (bytes(6), CHALLENGE)

    def test_sync_response(self) -> None:
        """Build and verify the S-A_Sync_Res-PDU."""
        scf = SecurityControlField.from_knx(0x93)
        secured_data = SecureData.init_sync_response(
            key=TOOL_KEY,
            scf=scf,
            challenge=CHALLENGE,
            random=bytes.fromhex("aaaaaaaaaaaa"),
            sequence_number_remote=3,
            sequence_number_local=4,
            address_fields_raw=DEVICE_TO_TOOL,
            address_type=CEMIAddressType.INDIVIDUAL,
            frame_format=CEMIFrameFormat.STANDARD,
            tpci=tpci.TDataConnected(sequence_number=0),
        )
        assert apci.SecureAPDU(scf=scf, secured_data=secured_data).to_knx() == SYNC_RES
        assert secured_data.get_sync_response_sequence_numbers(
            key=TOOL_KEY,
            scf=scf,
            challenge=CHALLENGE,
            address_fields_raw=DEVICE_TO_TOOL,
            address_type=CEMIAddressType.INDIVIDUAL,
            frame_format=CEMIFrameFormat.STANDARD,
            tpci=tpci.TDataConnected(sequence_number=0),
        ) == (3, 4)

    def test_sync_response_wrong_key(self) -> None:
        """A response that does not verify with the key is rejected."""
        s_apdu = _secure(SYNC_RES)
        with pytest.raises(DataSecureError):
            s_apdu.secured_data.get_sync_response_sequence_numbers(
                key=bytes(16),
                scf=s_apdu.scf,
                challenge=CHALLENGE,
                address_fields_raw=DEVICE_TO_TOOL,
                address_type=CEMIAddressType.INDIVIDUAL,
                frame_format=CEMIFrameFormat.STANDARD,
                tpci=tpci.TDataConnected(sequence_number=0),
            )


class TestToolAccess:
    """Point-to-point communication with the Tool Key through DataSecure."""

    def setup_method(self) -> None:
        """Set up a DataSecure with the Tool Key of the device."""
        # pylint: disable=attribute-defined-outside-init
        self.data_secure = DataSecure(
            group_key_table={},
            individual_address_table={},
            last_sequence_number_sending=1,
            tool_key_table={DEVICE: TOOL_KEY},
        )

    def _synchronize(self) -> None:
        with patch("secrets.token_bytes", return_value=CHALLENGE):
            request = self.data_secure.sync_request(DEVICE)
        outgoing = self.data_secure.outgoing_cemi(
            _cemi(TOOL, DEVICE, tpci.TDataConnected(sequence_number=0), request)
        )
        assert outgoing.payload is not None
        assert outgoing.payload.to_knx() == SYNC_REQ
        response = _cemi(
            DEVICE, TOOL, tpci.TDataConnected(sequence_number=0), _secure(SYNC_RES)
        )
        # passed on unchanged, so the pending request receives it
        assert self.data_secure.received_cemi(response) == response

    def test_exchange(self) -> None:
        """S-A_Sync, then a request and its response as in Annex C.1.1 - C.1.4."""
        assert not self.data_secure.tool_access_synchronized(DEVICE)
        self._synchronize()
        assert self.data_secure.tool_access_synchronized(DEVICE)

        # The device expects SeqNr 4 next (SeqNr_local of the response).
        outgoing = self.data_secure.outgoing_cemi(
            _cemi(TOOL, DEVICE, tpci.TDataIndividual(), PROPERTY_WRITE)
        )
        assert outgoing.payload is not None
        assert outgoing.payload.to_knx() == SECURE_PROPERTY_WRITE

        # The device sends with SeqNr 3 (SeqNr_remote of the response).
        incoming = _cemi(
            DEVICE, TOOL, tpci.TDataIndividual(), _secure(SECURE_PROPERTY_RESPONSE)
        )
        plain = self.data_secure.received_cemi(incoming)
        assert plain.payload == apci.PropertyValueResponse(
            object_index=5,
            property_id=0x35,
            count=1,
            start_index=1,
            data=bytes(range(0x20, 0x30)),
        )
        # a replayed frame is rejected
        with pytest.raises(DataSecureError, match="Sequence number too low"):
            self.data_secure.received_cemi(incoming)

    def test_sync_request_retransmission(self) -> None:
        """A repeated frame carries the identical S-A_Sync_Req-PDU."""
        with patch("secrets.token_bytes", return_value=CHALLENGE):
            request = self.data_secure.sync_request(DEVICE)
        frame = _cemi(TOOL, DEVICE, tpci.TDataConnected(sequence_number=0), request)
        first = self.data_secure.outgoing_cemi(frame)
        second = self.data_secure.outgoing_cemi(frame)
        assert first.payload is not None
        assert second.payload is not None
        assert first.payload.to_knx() == second.payload.to_knx()
        # sending the request does not use a Sequence Number
        assert self.data_secure.get_sequence_number() == 1

    def test_not_synchronized(self) -> None:
        """Without S-A_Sync the Sequence Number of the device is unknown."""
        incoming = _cemi(
            DEVICE, TOOL, tpci.TDataIndividual(), _secure(SECURE_PROPERTY_RESPONSE)
        )
        with pytest.raises(DataSecureError, match="not known"):
            self.data_secure.received_cemi(incoming)

    def test_unexpected_sync_response(self) -> None:
        """A response without a request is ignored."""
        response = _cemi(
            DEVICE, TOOL, tpci.TDataConnected(sequence_number=0), _secure(SYNC_RES)
        )
        with pytest.raises(DataSecureError, match="Unexpected S-A_Sync response"):
            self.data_secure.received_cemi(response)

    def test_sync_response_from_other_key(self) -> None:
        """A response secured with another key does not synchronize."""
        with patch("secrets.token_bytes", return_value=CHALLENGE):
            self.data_secure.sync_request(DEVICE)
        self.data_secure.set_tool_key(DEVICE, bytes(16))
        with patch("secrets.token_bytes", return_value=CHALLENGE):
            self.data_secure.sync_request(DEVICE)
        response = _cemi(
            DEVICE, TOOL, tpci.TDataConnected(sequence_number=0), _secure(SYNC_RES)
        )
        with pytest.raises(DataSecureError, match="MAC verification failed"):
            self.data_secure.received_cemi(response)
        assert not self.data_secure.tool_access_synchronized(DEVICE)

    def test_control_frames_plain(self) -> None:
        """Transport layer control frames have no APDU and stay plain."""
        connect = _cemi(TOOL, DEVICE, tpci.TConnect())
        assert self.data_secure.outgoing_cemi(connect) == connect

    def test_other_devices_plain(self) -> None:
        """Frames to devices without a Tool Key stay plain."""
        frame = _cemi(
            TOOL, IndividualAddress("1.1.1"), tpci.TDataIndividual(), PROPERTY_WRITE
        )
        assert self.data_secure.outgoing_cemi(frame) == frame

    def test_remove_tool_key(self) -> None:
        """Without the Tool Key, frames to the device stay plain."""
        self._synchronize()
        self.data_secure.remove_tool_key(DEVICE)
        assert not self.data_secure.tool_access_synchronized(DEVICE)
        frame = _cemi(TOOL, DEVICE, tpci.TDataIndividual(), PROPERTY_WRITE)
        assert self.data_secure.outgoing_cemi(frame) == frame
        with pytest.raises(DataSecureError, match="No Tool Key"):
            self.data_secure.sync_request(DEVICE)

    def test_invalid_tool_key(self) -> None:
        """A Tool Key has 16 octets."""
        with pytest.raises(DataSecureError):
            self.data_secure.set_tool_key(DEVICE, bytes(15))


def test_keyring_tool_keys() -> None:
    """The Tool Keys of the devices in a keyring."""
    keyring = sync_load_keyring(
        Path(__file__).parent / "resources/SecureTest.knxkeys", "test"
    )
    assert keyring.get_tool_keys() == {
        IndividualAddress("4.0.0"): bytes.fromhex("02d40ef405b79b369c04d3928866352a"),
        IndividualAddress("4.0.9"): bytes.fromhex("37f80b3c96ab13fa0b1c7a3123ef8059"),
        IndividualAddress("5.0.0"): bytes.fromhex("d92fa13bf5b316ad72d6e9c2fa359488"),
    }
