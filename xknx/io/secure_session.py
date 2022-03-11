"""SecureSession is an abstraction for handling a KNXnet/IP Secure session."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Callable, cast

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from xknx.exceptions import CommunicationError, CouldNotParseKNXIP
from xknx.knxip import (
    HPAI,
    KNXIPFrame,
    KNXIPServiceType,
    SecureWrapper,
    SessionResponse,
    SessionStatus,
)
from xknx.knxip.knxip_enum import SecureSessionStatusCode
from xknx.secure import sha256_hash

from .const import SESSION_KEEPALIVE_RATE
from .request_response import Authenticate, Session
from .transport import KNXIPTransport, TCPTransport

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")


COUNTER_0_HANDSHAKE = (  # used in SessionResponse and SessionAuthenticate
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00"
)


def bytes_xor(a: bytes, b: bytes) -> bytes:  # pylint: disable=invalid-name
    """XOR two bytes values."""
    return (int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).to_bytes(len(a), "big")


def byte_pad(data: bytes, block_size: int) -> bytes:
    """Padd data with 0x00 until its length is a multiple of block_size."""
    padding = bytes(block_size - (len(data) % block_size))
    return data + padding


def calculate_message_authentication_code_cbc(
    key: bytes,
    additional_data: bytes,
    payload: bytes = b"",
    block_0: bytes = bytes(16),
) -> bytes:
    """Calculate the message authentication code (MAC) for a message with AES-CBC."""
    blocks = (
        block_0 + len(additional_data).to_bytes(2, "big") + additional_data + payload
    )
    y_cipher = Cipher(algorithms.AES(key), modes.CBC(bytes(16)))
    y_encryptor = y_cipher.encryptor()  # type: ignore[no-untyped-call]
    y_blocks = (
        y_encryptor.update(byte_pad(blocks, block_size=16)) + y_encryptor.finalize()
    )
    # only calculate, no ctr encryption
    return cast(bytes, y_blocks[-16:])


def encrypt_data_ctr(
    key: bytes,
    mac_cbc: bytes,
    payload: bytes = b"",
    counter_0: bytes = COUNTER_0_HANDSHAKE,
) -> tuple[bytes, bytes]:
    """
    Encrypt data with AES-CTR.

    Payload is expected a full Plain KNX/IP frame with header.
    MAC shall be encrypted with coutner 0, KNXnet/IP frame with incremented counters.
    Returns a tuple of encrypted data (if there is any) and encrypted MAC.
    """
    s_cipher = Cipher(algorithms.AES(key), modes.CTR(counter_0))
    s_encryptor = s_cipher.encryptor()  # type: ignore[no-untyped-call]
    mac = s_encryptor.update(mac_cbc)
    encrypted_data = s_encryptor.update(payload) + s_encryptor.finalize()
    return (encrypted_data, mac)


def decrypt_ctr(
    session_key: bytes,
    mac: bytes,
    payload: bytes = b"",
    counter_0: bytes = COUNTER_0_HANDSHAKE,
) -> tuple[bytes, bytes]:
    """
    Decrypt data from SecureWrapper.

    MAC will be decoded first with counter 0.
    Returns a tuple of (KNX/IP frame bytes, MAC TR for verification).
    """
    cipher = Cipher(algorithms.AES(session_key), modes.CTR(counter_0))
    decryptor = cipher.decryptor()  # type: ignore[no-untyped-call]
    mac_tr = decryptor.update(mac)  # MAC is encrypted with counter 0
    decrypted_data = decryptor.update(payload) + decryptor.finalize()

    return (decrypted_data, mac_tr)


def derive_device_authentication_password(device_authentication_password: str) -> bytes:
    """Derive device authentication password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=b"device-authentication-code.1.secure.ip.knx.org",
        iterations=65536,
    )
    return kdf.derive(device_authentication_password.encode("latin-1"))


def derive_user_password(password_string: str) -> bytes:
    """Derive user password."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=b"user-password.1.secure.ip.knx.org",
        iterations=65536,
    )
    return kdf.derive(password_string.encode("latin-1"))


class SecureSession(TCPTransport):
    """Class for handling a KNXnet/IP Secure session."""

    def __init__(
        self,
        xknx: XKNX,
        remote_addr: tuple[str, int],
        device_authentication_password: str,
        user_id: int,
        user_password: str,
        connection_lost_cb: Callable[[], None] | None = None,
    ) -> None:
        """Initialize SecureSession class."""
        super().__init__(
            xknx,
            remote_addr=remote_addr,
            connection_lost_cb=connection_lost_cb,
        )
        self._device_authentication_code = derive_device_authentication_password(
            device_authentication_password
        )
        self.user_id = user_id
        self._user_password = derive_user_password(user_password)

        self._private_key: X25519PrivateKey
        self.public_key: bytes
        self._peer_public_key: X25519PublicKey
        self.session_id: int
        self._session_key: bytes

        self.message_tag = bytes.fromhex("00 00")  # use 0x00 0x00 for tunneling
        self.serial_number = bytes.fromhex("00 00 78 6b 6e 78")  # TODO configurable?
        self._sequence_number = 0
        self.initialized = False
        self._keepalive_task: asyncio.Task[None] | None = None
        self._session_status_handler: KNXIPTransport.Callback | None = None

    def handle_knxipframe(self, knxipframe: KNXIPFrame, source: HPAI) -> None:
        """Handle KNXIP Frame and call all callbacks matching the service type ident."""
        # TODO: disallow unencrypted frames with exceptions for discovery etc. eg. DescriptionResponse
        if isinstance(knxipframe.body, SecureWrapper):
            if not self.initialized:
                raise CouldNotParseKNXIP(
                    "Received SecureWrapper with Secure session not initialized"
                )
            try:
                knxipframe = self.decrypt_frame(knxipframe)
            except CouldNotParseKNXIP as couldnotparseknxip:
                # TODO: log raw data of unsupported frame
                knx_logger.debug(
                    "Unsupported encrypted KNXIPFrame: %s",
                    couldnotparseknxip.description,
                )
                return
            knx_logger.debug("Decrypted frame: %s", knxipframe)
        super().handle_knxipframe(knxipframe, source)

    async def connect(self) -> None:
        """Connect transport."""
        await super().connect()
        self._private_key = X25519PrivateKey.generate()
        self.public_key = self._private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        self._sequence_number = 0
        # setup secure session
        request_session = Session(
            self.xknx,
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
        request_authentication = Authenticate(
            self.xknx,
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

    def stop(self) -> None:
        """Stop transport."""
        # TODO: send SessionStatus CLOSE
        if self._session_status_handler:
            self.unregister_callback(self._session_status_handler)
            self._session_status_handler = None
        self.stop_keepalive_task()
        self.initialized = False
        super().stop()

    def increment_sequence_number(self) -> bytes:
        """Increment sequence number. Return byte representation of current sequence number."""
        next_sn = self._sequence_number.to_bytes(6, "big")
        self._sequence_number += 1
        return next_sn

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
        response_mac_cbc = calculate_message_authentication_code_cbc(
            self._device_authentication_code,
            additional_data=response_header_data
            + self.session_id.to_bytes(2, "big")
            + pub_keys_xor,  # knx_ip_header + secure_session_id + bytes_xor(client_pub_key, server_pub_key)
        )
        _, mac_tr = decrypt_ctr(
            self._device_authentication_code,
            mac=session_response.message_authentication_code,
        )
        if mac_tr != response_mac_cbc:
            raise CommunicationError("SessionResponse MAC verification failed.")
        # calculate session key
        ecdh_shared_secret = self._private_key.exchange(self._peer_public_key)
        self._session_key = sha256_hash(ecdh_shared_secret)[:16]
        self.initialized = True
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
            mac_cbc=authenticate_mac_cbc,
        )
        return authenticate_mac

    def encrypt_frame(self, plain_frame: KNXIPFrame) -> KNXIPFrame:
        """Wrap KNX/IP frame in SecureWrapper."""
        sequence_number = self.increment_sequence_number()
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
                sequence_number
                + self.serial_number
                + self.message_tag
                + payload_length.to_bytes(2, "big")
            ),
        )
        encrypted_data, mac = encrypt_data_ctr(
            key=self._session_key,
            mac_cbc=mac_cbc,
            payload=plain_payload,
            counter_0=(
                sequence_number
                + self.serial_number
                + self.message_tag
                + bytes.fromhex("ff 00")
            ),
        )
        return KNXIPFrame.init_from_body(
            SecureWrapper(
                self.xknx,
                secure_session_id=self.session_id,
                sequence_information=int.from_bytes(
                    sequence_number, "big"
                ),  # TODO: remove encoding, decoding, encoding
                serial_number=int.from_bytes(self.serial_number, "big"),
                message_tag=int.from_bytes(self.message_tag, "big"),
                encrypted_data=encrypted_data,
                message_authentication_code=mac,
            )
        )

    def decrypt_frame(self, encrypted_frame: KNXIPFrame) -> KNXIPFrame:
        """Unwrap and verify KNX/IP frame from SecureWrapper."""
        # TODO: get raw data from KNXIPFrame class directly instead of recalculating it with to_knx()
        # TODO: refactor so assert isn't needed (maybe subclass SecureWrapper from KNXIPFrame instead of being an attribute)
        assert isinstance(encrypted_frame.body, SecureWrapper)
        assert encrypted_frame.body.secure_session_id == self.session_id
        session_id_bytes = encrypted_frame.body.secure_session_id.to_bytes(2, "big")
        wrapper_header = encrypted_frame.header.to_knx()
        sequence_number_bytes = encrypted_frame.body.sequence_information.to_bytes(
            6, "big"
        )  # TODO: remove encoding, decoding, encoding
        serial_number_bytes = encrypted_frame.body.serial_number.to_bytes(6, "big")
        message_tag_bytes = encrypted_frame.body.message_tag.to_bytes(2, "big")

        dec_frame, mac_tr = decrypt_ctr(
            self._session_key,
            mac=encrypted_frame.body.message_authentication_code,
            payload=encrypted_frame.body.encrypted_data,
            counter_0=(
                sequence_number_bytes
                + serial_number_bytes
                + message_tag_bytes
                + bytes.fromhex("ff 00")
            ),
        )
        mac_cbc = calculate_message_authentication_code_cbc(
            key=self._session_key,
            additional_data=wrapper_header + session_id_bytes,
            payload=dec_frame,
            block_0=(
                sequence_number_bytes
                + serial_number_bytes
                + message_tag_bytes
                + len(dec_frame).to_bytes(2, "big")
            ),
        )
        assert mac_cbc == mac_tr

        knxipframe = KNXIPFrame(self.xknx)
        knxipframe.from_knx(dec_frame)
        # TODO: handle KNX/IP frame parsing errors or just put raw back into transport ?
        return knxipframe

    async def _session_keepalive(self) -> None:
        """Keep session alive."""
        await asyncio.sleep(SESSION_KEEPALIVE_RATE)
        self.send(
            KNXIPFrame.init_from_body(
                SessionStatus(
                    self.xknx,
                    status=SecureSessionStatusCode.STATUS_KEEPALIVE,
                )
            )
        )

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
