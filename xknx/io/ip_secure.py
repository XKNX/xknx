"""IPSecure is an abstraction for handling a KNXnet/IP Secure layer."""
from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
import logging
import random
from typing import Callable, Final

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
    RoutingIndication,
    SecureWrapper,
    SessionResponse,
    SessionStatus,
    TimerNotify,
)
from xknx.knxip.knxip_enum import SecureSessionStatusCode
from xknx.secure.security_primitives import (
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
from .transport import KNXIPTransport, TCPTransport, UDPTransport

logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")
ip_secure_logger = logging.getLogger("xknx.ip_secure")


COUNTER_0_HANDSHAKE = (  # used in SessionResponse and SessionAuthenticate
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00"
)
MESSAGE_TAG_TUNNELLING = bytes.fromhex("00 00")  # use 0x00 0x00 for tunneling


class _IPSecureTransportLayer(ABC):
    """Abstract for Secure transport layer."""

    session_id: int
    _key: bytes

    @abstractmethod
    def get_sequence_information(self) -> bytes:
        """Return byte representation of sequence information."""

    @abstractmethod
    def get_message_tag(self) -> bytes:
        """Return byte representation of message tag."""

    def decrypt_frame(self, encrypted_frame: KNXIPFrame) -> KNXIPFrame:
        """Unwrap and verify KNX/IP frame from SecureWrapper."""
        # TODO: get raw data from KNXIPFrame class directly instead of recalculating it with to_knx()
        # TODO: refactor so assert isn't needed (maybe subclass SecureWrapper from KNXIPFrame instead of being an attribute)
        assert isinstance(encrypted_frame.body, SecureWrapper)
        if encrypted_frame.body.secure_session_id != self.session_id:
            raise KNXSecureValidationError("Invalid secure session id")

        session_id_bytes = encrypted_frame.body.secure_session_id.to_bytes(2, "big")
        wrapper_header = encrypted_frame.header.to_knx()

        dec_frame, mac_tr = decrypt_ctr(
            key=self._key,
            counter_0=(
                encrypted_frame.body.sequence_information
                + encrypted_frame.body.serial_number
                + encrypted_frame.body.message_tag
                + b"\xff\x00"
            ),
            mac=encrypted_frame.body.message_authentication_code,
            payload=encrypted_frame.body.encrypted_data,
        )
        mac_cbc = calculate_message_authentication_code_cbc(
            key=self._key,
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

        knxipframe, _ = KNXIPFrame.from_knx(dec_frame)
        return knxipframe

    def encrypt_frame(self, plain_frame: KNXIPFrame) -> KNXIPFrame:
        """Wrap KNX/IP frame in SecureWrapper."""
        sequence_information = self.get_sequence_information()
        message_tag = self.get_message_tag()
        plain_payload = plain_frame.to_knx()  # P
        payload_length = len(plain_payload)  # Q
        # 6 KNXnet/IP header, 2 session_id, 6 sequence_number, 6 serial_number, 2 message_tag, 16 MAC = 38
        total_length = 38 + payload_length
        # TODO: get header data and total_length from SecureWrapper class
        wrapper_header = bytes.fromhex("06 10 09 50") + total_length.to_bytes(2, "big")

        mac_cbc = calculate_message_authentication_code_cbc(
            key=self._key,
            additional_data=wrapper_header + self.session_id.to_bytes(2, "big"),
            payload=plain_payload,
            block_0=(
                sequence_information
                + XKNX_SERIAL_NUMBER
                + message_tag
                + payload_length.to_bytes(2, "big")
            ),
        )
        encrypted_data, mac = encrypt_data_ctr(
            key=self._key,
            counter_0=(
                sequence_information + XKNX_SERIAL_NUMBER + message_tag + b"\xff\x00"
            ),
            mac_cbc=mac_cbc,
            payload=plain_payload,
        )
        return KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.session_id,
                sequence_information=sequence_information,
                serial_number=XKNX_SERIAL_NUMBER,
                message_tag=message_tag,
                encrypted_data=encrypted_data,
                message_authentication_code=mac,
            )
        )


class SecureSession(TCPTransport, _IPSecureTransportLayer):
    """Class for handling a KNXnet/IP Secure tunnelling session."""

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
        self._key: bytes  # Session Key
        self.session_id: int

        self._sequence_number: int = 0
        self._sequence_number_received: int = -1
        self.initialized: bool = False
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
        self._key = sha256_hash(ecdh_shared_secret)[:16]
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
                ip_secure_logger.warning(
                    "Discarding SecureWrapper with invalid sequence number: %s",
                    knxipframe,
                )
                return
            try:
                knxipframe = self.decrypt_frame(knxipframe)
            except KNXSecureValidationError as err:
                ip_secure_logger.warning("Could not decrypt KNXIPFrame: %s", err)
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
            # keepalive timer is started with first and reset with every other
            # SecureWrapper frame (including wrapped keepalive frames themselves)
            self.start_keepalive_task()
        # TODO: disallow sending unencrypted frames over non-initialized session with
        # exceptions for discovery and SessionRequest
        super().send(knxipframe, addr)

    def get_sequence_information(self) -> bytes:
        """Increment sequence number. Return byte representation of current sequence number."""
        next_sn = self._sequence_number.to_bytes(6, "big")
        self._sequence_number += 1
        return next_sn

    def get_message_tag(self) -> bytes:
        """Return byte representation of current message tag."""
        return MESSAGE_TAG_TUNNELLING

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


class SecureGroup(UDPTransport, _IPSecureTransportLayer):
    """Class for secure KNXnet/IP multicast communication."""

    session_id = 0  # Routing uses fixed session id 0

    def __init__(
        self,
        local_addr: tuple[str, int],
        remote_addr: tuple[str, int],
        backbone_key: bytes,
        latency_ms: int = 1000,
    ):
        """Initialize SecureGroup class."""
        super().__init__(
            local_addr=local_addr,
            remote_addr=remote_addr,
            multicast=True,
        )
        self._key = backbone_key
        self.secure_timer = SecureSequenceTimer(
            backbone_key=backbone_key,
            latency_ms=latency_ms,
            transport_send=super().send,
        )

    async def connect(self) -> None:
        """Connect transport."""
        await super().connect()
        await self.secure_timer.synchronize()

    def stop(self) -> None:
        """Stop tasks and transport."""
        self.secure_timer.stop()
        super().stop()

    def handle_knxipframe(self, knxipframe: KNXIPFrame, source: HPAI) -> None:
        """Handle KNXIP Frame and call all callbacks matching the service type ident."""
        if isinstance(knxipframe.body, RoutingIndication):
            ip_secure_logger.info(
                "Discarding received unencrypted RoutingIndication: %s",
                knxipframe,
            )
            return
        if isinstance(knxipframe.body, TimerNotify):
            self.secure_timer.handle_timer_notify(knxipframe.body)
            return
        if isinstance(knxipframe.body, SecureWrapper):
            if not self.secure_timer.timer_authenticated:
                ip_secure_logger.debug(
                    "Discarding received SecureWrapper before timer synchronisazion finished: %s",
                    knxipframe,
                )
                return
            secure_wrapper = knxipframe.body
            try:
                knxipframe = self.decrypt_frame(knxipframe)
            except KNXSecureValidationError as err:
                ip_secure_logger.warning("Could not decrypt KNXIPFrame: %s", err)
                # Frame shall be discarded
                return
            except CouldNotParseKNXIP as couldnotparseknxip:
                knx_logger.debug(
                    "Unsupported encrypted KNXIPFrame: %s",
                    couldnotparseknxip.description,
                )
                return
            if not self.secure_timer.validate_secure_wrapper(secure_wrapper):
                ip_secure_logger.warning(
                    "Discarding SecureWrapper with invalid timer value: %s",
                    secure_wrapper,
                )
                return
            knx_logger.debug("Decrypted frame: %s", knxipframe)
        # handle decrypted frames and plain frames (e.g. SearchRequest for discovery)
        super().handle_knxipframe(knxipframe, source)

    def send(self, knxipframe: KNXIPFrame, addr: tuple[str, int] | None = None) -> None:
        """Send KNXIPFrame to socket. `addr` is ignored on TCP."""
        knx_logger.debug("Encrypting frame: %s", knxipframe)
        knxipframe = self.encrypt_frame(plain_frame=knxipframe)
        # TODO: disallow sending unencrypted frames over non-initialized session with
        # exceptions for discovery and SessionRequest
        super().send(knxipframe, addr)

    def get_sequence_information(self) -> bytes:
        """Return byte representation of current timer value."""
        return self.secure_timer.get_for_outgoing_secure_wrapper().to_bytes(6, "big")

    def get_message_tag(self) -> bytes:
        """Return byte representation of current message tag."""
        return random.randbytes(2)


class SecureSequenceTimer:
    """
    Class for holding and synchronizing the timer for secure sequence information.

    According to AN159 v06 KNXnet-IP Secure AS §2.2.2.3 Timer synchronizing
    """

    TIMER_NOTIFY_HEADER = bytes.fromhex("06 10 09 55 00 24")

    min_delay_time_keeper_periodic_notify: Final = 10  # pylint: disable=invalid-name
    min_delay_time_keeper_update_notify: Final = 0.1  # pylint: disable=invalid-name
    sync_latency_fraction: int = 10  # 10%

    def __init__(
        self,
        backbone_key: bytes,
        latency_ms: int,
        transport_send: Callable[[KNXIPFrame, tuple[str, int] | None], None],
    ) -> None:
        """Initialize SecureSequenceTimer class."""
        self._backbone_key = backbone_key
        self._clock_difference: int = 0
        self._expected_notify_handler: tuple[
            bytes, asyncio.Future[int]  # message_tag, synchronization future
        ] | None = None
        self._loop = asyncio.get_running_loop()
        self._notify_timer_handle: asyncio.TimerHandle | None = None
        self._transport_send = transport_send

        self.sched_update: bool = False
        self.timekeeper: bool = False
        self.timer_authenticated: bool = False

        self.latency_tolerance_ms = latency_ms
        self.sync_latency_tolerance_ms: int = round(
            latency_ms / 100 * self.sync_latency_fraction
        )
        _sync_latency_tolerance_seconds = self.sync_latency_tolerance_ms / 1000
        self.max_delay_time_keeper_periodic_notify = (
            self.min_delay_time_keeper_periodic_notify
            + _sync_latency_tolerance_seconds * 3
        )
        self.min_delay_time_follower_periodic_notify = (
            self.max_delay_time_keeper_periodic_notify
            + _sync_latency_tolerance_seconds * 1
        )
        self.max_delay_time_follower_periodic_notify = (
            self.min_delay_time_follower_periodic_notify
            + _sync_latency_tolerance_seconds * 10
        )
        self.max_delay_time_keeper_update_notify = (
            self.min_delay_time_keeper_update_notify
            + _sync_latency_tolerance_seconds * 1
        )
        self.min_delay_time_follower_update_notify = (
            self.max_delay_time_keeper_update_notify
            + _sync_latency_tolerance_seconds * 1
        )
        self.max_delay_time_follower_update_notify = (
            self.min_delay_time_follower_update_notify
            + _sync_latency_tolerance_seconds * 10
        )

    def stop(self) -> None:
        """Cancel notify timer."""
        if self._notify_timer_handle:
            self._notify_timer_handle.cancel()
            self._notify_timer_handle = None
        if self._expected_notify_handler:
            self._expected_notify_handler[1].cancel()

    def _monotonic_ms(self) -> int:
        """Return current monotonic time in milliseconds."""
        return int(self._loop.time() * 1000.0)

    def current_timer_value(self) -> int:
        """Return current timer value in milliseconds."""
        return self._monotonic_ms() + self._clock_difference

    def update(self, new_value: int) -> None:
        """Update timer value."""
        self._clock_difference = new_value - self._monotonic_ms()

    def reschedule(self, update: tuple[bytes, bytes] | None = None) -> None:
        """
        Reschedule notify timer.

        If `update` is set, the timer is rescheduled for an update notify,
        else for a periodic notify.
        `update` is expected to be a tuple of (message_tag, serial_number).
        """
        if self._notify_timer_handle is not None:
            self._notify_timer_handle.cancel()
        self.sched_update = bool(update)
        min_delay: float
        max_delay: float
        if self.sched_update:
            if self.timekeeper:
                min_delay = self.min_delay_time_keeper_update_notify
                max_delay = self.max_delay_time_keeper_update_notify
            else:
                min_delay = self.min_delay_time_follower_update_notify
                max_delay = self.max_delay_time_follower_update_notify
        elif self.timekeeper:
            min_delay = self.min_delay_time_keeper_periodic_notify
            max_delay = self.max_delay_time_keeper_periodic_notify
        else:
            min_delay = self.min_delay_time_follower_periodic_notify
            max_delay = self.max_delay_time_follower_periodic_notify
        self._notify_timer_handle = self._loop.call_later(
            random.uniform(min_delay, max_delay), self._notify_timer_expired, update
        )

    def _notify_timer_expired(self, update: tuple[bytes, bytes] | None) -> None:
        """Notify timer expired."""
        if update:
            self.send_timer_notify(message_tag=update[0], serial_number=update[1])
        else:
            self.send_timer_notify()
        if not self.timekeeper:
            self.timekeeper = True
            ip_secure_logger.debug("Becoming timekeeper")
        self.reschedule()

    def send_timer_notify(
        self,
        message_tag: bytes | None = None,
        serial_number: bytes = XKNX_SERIAL_NUMBER,
    ) -> None:
        """Send a TimerNotify frame."""
        timer_value = self.current_timer_value()
        timer_bytes = timer_value.to_bytes(6, "big")
        _message_tag = message_tag or random.randbytes(2)
        b_0 = timer_bytes + serial_number + _message_tag + b"\x00\x00"
        # TODO: get header data and total_length from TimerNotify class
        #       or handle mac calculation in TimerNotify class directly
        mac_cbc = calculate_message_authentication_code_cbc(
            key=self._backbone_key,
            additional_data=self.TIMER_NOTIFY_HEADER,
            block_0=b_0,
        )
        c_0 = timer_bytes + serial_number + _message_tag + b"\xff\x00"
        _, mac = encrypt_data_ctr(
            key=self._backbone_key,
            counter_0=c_0,
            mac_cbc=mac_cbc,
        )
        self._transport_send(
            KNXIPFrame.init_from_body(
                TimerNotify(
                    timer_value=timer_value,
                    serial_number=serial_number,
                    message_tag=_message_tag,
                    message_authentication_code=mac,
                )
            ),
            None,
        )

    def verify_timer_notify_mac(self, timer_notify: TimerNotify) -> None:
        """Verify MAC of timer notify."""
        timer_bytes = timer_notify.timer_value.to_bytes(6, "big")
        b_0 = (
            timer_bytes
            + timer_notify.serial_number
            + timer_notify.message_tag
            + b"\x00\x00"
        )
        c_0 = (
            timer_bytes
            + timer_notify.serial_number
            + timer_notify.message_tag
            + b"\xff\x00"
        )
        _, mac_tr = decrypt_ctr(
            key=self._backbone_key,
            counter_0=c_0,
            mac=timer_notify.message_authentication_code,
        )
        mac_cbc = calculate_message_authentication_code_cbc(
            key=self._backbone_key,
            additional_data=self.TIMER_NOTIFY_HEADER,
            block_0=b_0,
        )
        if mac_cbc != mac_tr:
            raise KNXSecureValidationError("MAC verification failed")

    async def synchronize(self) -> None:
        """Synchronize timer with remote time keeper."""
        message_tag = random.randbytes(2)
        waiter_fut: asyncio.Future[int] = self._loop.create_future()
        self._expected_notify_handler = message_tag, waiter_fut
        self.send_timer_notify(message_tag=message_tag)
        try:
            timer_value = await asyncio.wait_for(
                waiter_fut,
                timeout=(  # 3.3 seconds at latency_ms=1000, sync_latency_fraction=10%
                    self.max_delay_time_follower_update_notify
                    + 2 * self.latency_tolerance_ms / 1000
                ),
            )
            self.update(new_value=timer_value)
        except asyncio.TimeoutError:
            # use highest received timer value of TimerNotify or SecureWrapper frames
            ip_secure_logger.warning(
                "Timer synchronization not answered. Becoming time keeper."
            )
            self.timekeeper = True
        except asyncio.CancelledError:
            return
        finally:
            self._expected_notify_handler = None
        self.timer_authenticated = True
        self.reschedule()

    def validate_secure_wrapper(self, secure_wrapper: SecureWrapper) -> bool:
        """Validate a SecureWrapper frames and handle timer update schedule."""
        local_timer_value = self.current_timer_value()
        received_timer_value = int.from_bytes(
            secure_wrapper.sequence_information, "big"
        )
        # §2.2.2.3.2.5 Events: E5 - E8
        if received_timer_value > local_timer_value:
            self._clock_difference += received_timer_value - local_timer_value
            if not self.sched_update:
                self.reschedule()
            return True
        if received_timer_value > local_timer_value - self.sync_latency_tolerance_ms:
            if not self.sched_update:
                self.reschedule()
            return True
        if received_timer_value > local_timer_value - self.latency_tolerance_ms:
            return True
        if not self.sched_update:
            self.reschedule(
                update=(secure_wrapper.message_tag, secure_wrapper.serial_number)
            )
        return False

    def handle_timer_notify(self, timer_notify: TimerNotify) -> None:
        """Handle received TimerNotify frame."""
        local_timer_value = self.current_timer_value()
        try:
            self.verify_timer_notify_mac(timer_notify)
        except KNXSecureValidationError:
            ip_secure_logger.warning(
                "Discarding TimerNotify with invalid MAC: %s", timer_notify
            )
            return
        received_timer_value = timer_notify.timer_value
        # §2.2.2.3.2.5 Events: E11
        if (
            self._expected_notify_handler is not None
            and timer_notify.serial_number == XKNX_SERIAL_NUMBER
            and timer_notify.message_tag == self._expected_notify_handler[0]
        ):
            fut = self._expected_notify_handler[1]
            fut.set_result(received_timer_value)
            return
        # §2.2.2.3.2.5 Events: E1 - E4
        if received_timer_value > local_timer_value:
            self._clock_difference += received_timer_value - local_timer_value
            if self.timekeeper:
                ip_secure_logger.debug("Becoming time follower")
                self.timekeeper = False
            self.reschedule()
            return
        if received_timer_value > local_timer_value - self.sync_latency_tolerance_ms:
            if self.timekeeper:
                ip_secure_logger.debug("Becoming time follower")
                self.timekeeper = False
            self.reschedule()
            return
        if received_timer_value > local_timer_value - self.latency_tolerance_ms:
            return
        if not self.sched_update:
            self.reschedule(
                update=(timer_notify.message_tag, timer_notify.serial_number)
            )

    def get_for_outgoing_secure_wrapper(self) -> int:
        """Return current timer value and handle timer update schedule."""
        # §2.2.2.3.2.5 Events: E9
        if not self.sched_update:
            self.reschedule()
        return self.current_timer_value()
