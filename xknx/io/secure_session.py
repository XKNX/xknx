"""SecureSession is an abstraction for handling a KNXnet/IP Secure session."""
from __future__ import annotations

import asyncio
import logging
from typing import Callable

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)

from xknx.exceptions import (
    CommunicationError,
    CouldNotParseKNXIP,
    KNXSecureValidationError,
)
from xknx.knxip import (
    HPAI,
    KNXIPFrame,
    KNXIPServiceType,
    SecureWrapper,
    SessionResponse,
    SessionStatus,
)
from xknx.knxip.knxip_enum import SecureSessionStatusCode
from xknx.secure.ip_secure import (
    calculate_message_authentication_code_cbc,
    decrypt_ctr,
    derive_device_authentication_password,
    derive_user_password,
    encrypt_data_ctr,
    generate_ecdh_key_pair,
)
from xknx.secure.util import bytes_xor, sha256_hash

from .const import SESSION_KEEPALIVE_RATE, XKNX_SERIAL_NUMBER
from .request_response import Authenticate, Session
from .transport import KNXIPTransport, TCPTransport

logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")


COUNTER_0_HANDSHAKE = (  # used in SessionResponse and SessionAuthenticate
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00"
)
MESSAGE_TAG_TUNNELLING = bytes.fromhex("00 00")  # use 0x00 0x00 for tunneling


class SecureSession(TCPTransport):
    """Class for handling a KNXnet/IP Secure session."""

    def __init__(
        self,
        remote_addr: tuple[str, int],
        user_id: int,
        user_password: str,
        device_authentication_password: str | None = None,
        connection_lost_cb: Callable[[], None] | None = None,
    ) -> None:
        """Initialize SecureSession class."""
        super().__init__(
            remote_addr=remote_addr,
            connection_lost_cb=connection_lost_cb,
        )
        self._device_authentication_code: bytes | None = (
            derive_device_authentication_password(device_authentication_password)
            if device_authentication_password
            else None
        )
        self.user_id = user_id
        self._user_password = derive_user_password(user_password)

        self._private_key: X25519PrivateKey
        self.public_key: bytes
        self._peer_public_key: X25519PublicKey
        self._session_key: bytes
        self.session_id: int

        self._sequence_number = 0
        self._sequence_number_received = -1
        self.initialized = False
        self._keepalive_task: asyncio.Task[None] | None = None
        self._session_status_handler: KNXIPTransport.Callback | None = None

    async def connect(self) -> None:
        """Connect transport."""
        await super().connect()
        self._private_key, self.public_key = generate_ecdh_key_pair()
        self._sequence_number = 0
        self._sequence_number_received = -1
        request_session = Session(
            transport=self,
            ecdh_client_public_key=self.public_key,
        )
        await request_session.start()
        if request_session.response is None:
            raise CommunicationError(
                "Secure session could not be established. No response received."
            )
        # SessionAuthenticate and everything else after now shall be wrapped in SecureWrapper
        authenticate_mac = self.handshake(request_session.response)
        self.initialized = True

        request_authentication = Authenticate(
            transport=self,
            user_id=self.user_id,
            message_authentication_code=authenticate_mac,
        )
        await request_authentication.start()
        if request_authentication.response is None:
            raise CommunicationError(
                "Secure session could not be established. No response received."
            )
        if (  # TODO: look for status in request/response and use `success` instead of response ?
            request_authentication.response.status
            != SecureSessionStatusCode.STATUS_AUTHENTICATION_SUCCESS
        ):
            raise CommunicationError(
                f"Secure session authentication failed: {request_authentication.response.status}"
            )
        self._session_status_handler = self.register_callback(
            self._handle_session_status, [KNXIPServiceType.SESSION_STATUS]
        )

    def handshake(self, session_response: SessionResponse) -> bytes:
        """
        Handshake with device.

        Returns a SessionAuthenticate KNX/IP body.
        """
        self._peer_public_key = X25519PublicKey.from_public_bytes(
            session_response.ecdh_server_public_key
        )
        self.session_id = session_response.secure_session_id
        # verify SessionResponse MAC
        # TODO: get header data from actual KNX/IP frame
        response_header_data = bytes.fromhex("06 10 09 52 00 38")
        pub_keys_xor = bytes_xor(
            self.public_key,
            session_response.ecdh_server_public_key,
        )
        if self._device_authentication_code:
            response_mac_cbc = calculate_message_authentication_code_cbc(
                key=self._device_authentication_code,
                additional_data=response_header_data
                + self.session_id.to_bytes(2, "big")
                + pub_keys_xor,  # knx_ip_header + secure_session_id + bytes_xor(client_pub_key, server_pub_key)
            )
            _, mac_tr = decrypt_ctr(
                key=self._device_authentication_code,
                counter_0=COUNTER_0_HANDSHAKE,
                mac=session_response.message_authentication_code,
            )
            if mac_tr != response_mac_cbc:
                raise CommunicationError("SessionResponse MAC verification failed.")
        # calculate session key
        ecdh_shared_secret = self._private_key.exchange(self._peer_public_key)
        self._session_key = sha256_hash(ecdh_shared_secret)[:16]
        # generate SessionAuthenticate MAC
        authenticate_header_data = bytes.fromhex("06 10 09 53 00 18")
        authenticate_mac_cbc = calculate_message_authentication_code_cbc(
            key=self._user_password,
            additional_data=authenticate_header_data
            + bytes(1)  # reserved
            + self.user_id.to_bytes(1, "big")
            + pub_keys_xor,
            block_0=bytes(16),
        )
        _, authenticate_mac = encrypt_data_ctr(
            key=self._user_password,
            counter_0=COUNTER_0_HANDSHAKE,
            mac_cbc=authenticate_mac_cbc,
        )
        return authenticate_mac

    def stop(self) -> None:
        """Stop session and transport."""
        if self._session_status_handler:
            self.unregister_callback(self._session_status_handler)
            self._session_status_handler = None
        if self.transport and self.initialized:
            self.send(
                KNXIPFrame.init_from_body(
                    SessionStatus(status=SecureSessionStatusCode.STATUS_CLOSE)
                )
            )
        self.stop_keepalive_task()
        self.initialized = False
        super().stop()

    def handle_knxipframe(self, knxipframe: KNXIPFrame, source: HPAI) -> None:
        """Handle KNXIP Frame and call all callbacks matching the service type ident."""
        # TODO: disallow unencrypted frames with exceptions for discovery etc. eg. DescriptionResponse
        if isinstance(knxipframe.body, SecureWrapper):
            if not self.initialized:
                raise CouldNotParseKNXIP(
                    "Received SecureWrapper while Secure session not initialized"
                )
            new_sequence_number = int.from_bytes(
                knxipframe.body.sequence_information, "big"
            )
            if not new_sequence_number > self._sequence_number_received:
                knx_logger.warning(
                    "Discarding SecureWrapper with invalid sequence number: %s",
                    knxipframe,
                )
                return
            try:
                knxipframe = self.decrypt_frame(knxipframe)
            except KNXSecureValidationError as err:
                knx_logger.warning("Could not decrypt KNXIPFrame: %s", err)
                # Frame shall be discarded
                return
            except CouldNotParseKNXIP as couldnotparseknxip:
                knx_logger.debug(
                    "Unsupported encrypted KNXIPFrame: %s",
                    couldnotparseknxip.description,
                )
                return
            self._sequence_number_received = new_sequence_number
            knx_logger.debug("Decrypted frame: %s", knxipframe)
        super().handle_knxipframe(knxipframe, source)

    def decrypt_frame(self, encrypted_frame: KNXIPFrame) -> KNXIPFrame:
        """Unwrap and verify KNX/IP frame from SecureWrapper."""
        # TODO: get raw data from KNXIPFrame class directly instead of recalculating it with to_knx()
        # TODO: refactor so assert isn't needed (maybe subclass SecureWrapper from KNXIPFrame instead of being an attribute)
        assert isinstance(encrypted_frame.body, SecureWrapper)
        if encrypted_frame.body.secure_session_id != self.session_id:
            raise KNXSecureValidationError("Wrong secure session id")

        session_id_bytes = encrypted_frame.body.secure_session_id.to_bytes(2, "big")
        wrapper_header = encrypted_frame.header.to_knx()

        dec_frame, mac_tr = decrypt_ctr(
            key=self._session_key,
            counter_0=(
                encrypted_frame.body.sequence_information
                + encrypted_frame.body.serial_number
                + encrypted_frame.body.message_tag
                + bytes.fromhex("ff 00")
            ),
            mac=encrypted_frame.body.message_authentication_code,
            payload=encrypted_frame.body.encrypted_data,
        )
        mac_cbc = calculate_message_authentication_code_cbc(
            key=self._session_key,
            additional_data=wrapper_header + session_id_bytes,
            payload=dec_frame,
            block_0=(
                encrypted_frame.body.sequence_information
                + encrypted_frame.body.serial_number
                + encrypted_frame.body.message_tag
                + len(dec_frame).to_bytes(2, "big")
            ),
        )
        if mac_cbc != mac_tr:
            raise KNXSecureValidationError(
                "Verification of message authentication code failed"
            )

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(dec_frame)
        return knxipframe

    async def _session_keepalive(self) -> None:
        """Keep session alive."""
        await asyncio.sleep(SESSION_KEEPALIVE_RATE)
        self.send(
            KNXIPFrame.init_from_body(
                SessionStatus(status=SecureSessionStatusCode.STATUS_KEEPALIVE)
            )
        )

    def send(self, knxipframe: KNXIPFrame, addr: tuple[str, int] | None = None) -> None:
        """Send KNXIPFrame to socket. `addr` is ignored on TCP."""
        if self.initialized:
            knx_logger.debug("Encrypting frame: %s", knxipframe)
            knxipframe = self.encrypt_frame(plain_frame=knxipframe)
            # keepalive timer is started with first and resetted with every other
            # SecureWrapper frame (including wrapped keepalive frames themselves)
            self.start_keepalive_task()
        # TODO: disallow sending unencrypted frames over non-initialized session with
        # exceptions for discovery and SessionRequest
        super().send(knxipframe, addr)

    def encrypt_frame(self, plain_frame: KNXIPFrame) -> KNXIPFrame:
        """Wrap KNX/IP frame in SecureWrapper."""
        sequence_information = self.increment_sequence_number()
        plain_payload = plain_frame.to_knx()  # P
        payload_length = len(plain_payload)  # Q
        # 6 KNXnet/IP header, 2 session_id, 6 sequence_number, 6 serial_number, 2 message_tag, 16 MAC = 38
        total_length = 38 + payload_length
        # TODO: get header data and total_length from SecureWrapper class
        wrapper_header = bytes.fromhex("06 10 09 50") + total_length.to_bytes(2, "big")

        mac_cbc = calculate_message_authentication_code_cbc(
            key=self._session_key,
            additional_data=wrapper_header + self.session_id.to_bytes(2, "big"),
            payload=plain_payload,
            block_0=(
                sequence_information
                + XKNX_SERIAL_NUMBER
                + MESSAGE_TAG_TUNNELLING
                + payload_length.to_bytes(2, "big")
            ),
        )
        encrypted_data, mac = encrypt_data_ctr(
            key=self._session_key,
            counter_0=(
                sequence_information
                + XKNX_SERIAL_NUMBER
                + MESSAGE_TAG_TUNNELLING
                + bytes.fromhex("ff 00")
            ),
            mac_cbc=mac_cbc,
            payload=plain_payload,
        )
        return KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.session_id,
                sequence_information=sequence_information,
                serial_number=XKNX_SERIAL_NUMBER,
                message_tag=MESSAGE_TAG_TUNNELLING,
                encrypted_data=encrypted_data,
                message_authentication_code=mac,
            )
        )

    def increment_sequence_number(self) -> bytes:
        """Increment sequence number. Return byte representation of current sequence number."""
        next_sn = self._sequence_number.to_bytes(6, "big")
        self._sequence_number += 1
        return next_sn

    def start_keepalive_task(self) -> None:
        """Start or restart session keepalive task."""
        if self._keepalive_task:
            self._keepalive_task.cancel()
        self._keepalive_task = asyncio.create_task(self._session_keepalive())

    def stop_keepalive_task(self) -> None:
        """Stop keepalive task."""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            self._keepalive_task = None

    def _handle_session_status(
        self, knxipframe: KNXIPFrame, source: HPAI, transport: KNXIPTransport
    ) -> None:
        """Handle session status."""
        assert isinstance(knxipframe.body, SessionStatus)
        if knxipframe.body.status in (
            SecureSessionStatusCode.STATUS_CLOSE,
            SecureSessionStatusCode.STATUS_TIMEOUT,
            SecureSessionStatusCode.STATUS_UNAUTHENTICATED,
        ):
            logger.info("Secure session closed by server: %s.", knxipframe.body.status)
            if self.transport:
                # closing transport will call `asyncio.Protocol.connection_lost`
                # and its callback from SecureTunnel
                self.transport.close()
