"""Test Secure Session."""

import asyncio
from unittest.mock import Mock, patch

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
import pytest

from xknx.exceptions import CommunicationError, CouldNotParseKNXIP
from xknx.io.const import SESSION_KEEPALIVE_RATE
from xknx.io.ip_secure import SecureSession
from xknx.knxip import (
    HPAI,
    KNXIPFrame,
    SecureWrapper,
    SessionAuthenticate,
    SessionRequest,
    SessionResponse,
    SessionStatus,
)
from xknx.knxip.knxip_enum import SecureSessionStatusCode

from ..conftest import EventLoopClockAdvancer, skip_3_10


class TestSecureSession:
    """Test class for xknx/io/SecureSession objects."""

    mock_addr = ("127.0.0.1", 12345)
    mock_private_key = X25519PrivateKey.from_private_bytes(
        bytes.fromhex(
            "b8 fa bd 62 66 5d 8b 9e 8a 9d 8b 1f 4b ca 42 c8"
            "c2 78 9a 61 10 f5 0e 9d d7 85 b3 ed e8 83 f3 78"
        )
    )
    mock_public_key = bytes.fromhex(
        "0a a2 27 b4 fd 7a 32 31 9b a9 96 0a c0 36 ce 0e"
        "5c 45 07 b5 ae 55 16 1f 10 78 b1 dc fb 3c b6 31"
    )
    mock_server_public_key = bytes.fromhex(
        "bd f0 99 90 99 23 14 3e f0 a5 de 0b 3b e3 68 7b"
        "c5 bd 3c f5 f9 e6 f9 01 69 9c d8 70 ec 1f f8 24"
    )
    mock_session_id = 1
    mock_device_authentication_password = "trustme"
    mock_user_id = 1
    mock_user_password = "secret"
    mock_serial_number = bytes.fromhex("00 fa 12 34 56 78")
    mock_message_tag = bytes.fromhex("af fe")

    def setup_method(self) -> None:
        """Set up test class."""
        # pylint: disable=attribute-defined-outside-init
        self.patch_serial_number = patch(
            "xknx.io.ip_secure.XKNX_SERIAL_NUMBER", self.mock_serial_number
        )
        self.patch_serial_number.start()
        self.patch_message_tag = patch(
            "xknx.io.ip_secure.MESSAGE_TAG_TUNNELLING", self.mock_message_tag
        )
        self.patch_message_tag.start()

        self.session = SecureSession(
            remote_addr=self.mock_addr,
            user_id=self.mock_user_id,
            user_password=self.mock_user_password,
            device_authentication_password=self.mock_device_authentication_password,
        )

    def teardown_method(self) -> None:
        """Tear down test class."""
        self.patch_serial_number.stop()
        self.patch_message_tag.stop()

    @skip_3_10
    @patch("xknx.io.transport.tcp_transport.TCPTransport.connect")
    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    @patch(
        "xknx.io.ip_secure.generate_ecdh_key_pair",
        return_value=(mock_private_key, mock_public_key),
    )
    @patch(
        "xknx.io.ip_secure.SecureSession.send",
        wraps=SecureSession.send,
        autospec=True,
    )
    async def test_lifecycle(
        self,
        mock_session_send: Mock,
        _mock_generate: Mock,
        mock_super_send: Mock,
        mock_super_connect: Mock,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test connection, handshake, keepalive and shutdown."""
        connect_task = asyncio.create_task(self.session.connect())
        await time_travel(0)
        mock_super_connect.assert_called_once()
        # outgoing
        session_request_frame = KNXIPFrame.init_from_body(
            SessionRequest(ecdh_client_public_key=self.mock_public_key)
        )
        mock_session_send.assert_called_once_with(  # unencrypted
            self.session,  # account for self argument in wraps
            session_request_frame,
        )
        mock_session_send.reset_mock()
        mock_super_send.assert_called_once_with(  # unencrypted
            session_request_frame,
            None,  # None for addr in TCP transport
        )
        mock_super_send.reset_mock()
        # incoming
        session_response_frame = KNXIPFrame.init_from_body(
            SessionResponse(
                secure_session_id=1,
                ecdh_server_public_key=self.mock_server_public_key,
                message_authentication_code=bytes.fromhex(
                    "a9 22 50 5a aa 43 61 63 57 0b d5 49 4c 2d f2 a3"
                ),
            )
        )
        self.session.handle_knxipframe(session_response_frame, HPAI(*self.mock_addr))
        await time_travel(0)
        # outgoing
        authenticate_frame = KNXIPFrame.init_from_body(
            SessionAuthenticate(
                user_id=self.mock_user_id,
                message_authentication_code=bytes.fromhex(
                    "1f 1d 59 ea 9f 12 a1 52 e5 d9 72 7f 08 46 2c de"
                ),
            )
        )
        mock_session_send.assert_called_once_with(
            self.session,  # account for self argument in wraps
            authenticate_frame,
        )
        mock_session_send.reset_mock()
        encrypted_authenticate_frame = KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.mock_session_id,
                sequence_information=bytes.fromhex("00 00 00 00 00 00"),
                serial_number=self.mock_serial_number,
                message_tag=self.mock_message_tag,
                encrypted_data=bytes.fromhex(
                    "79 15 a4 f3 6e 6e 42 08"
                    "d2 8b 4a 20 7d 8f 35 c0"
                    "d1 38 c2 6a 7b 5e 71 69"
                ),
                message_authentication_code=bytes.fromhex(
                    "52 db a8 e7 e4 bd 80 bd 7d 86 8a 3a e7 87 49 de"
                ),
            )
        )
        mock_super_send.assert_called_once_with(
            encrypted_authenticate_frame,
            None,  # None for addr in TCP transport
        )
        mock_super_send.reset_mock()
        # incoming
        encrypted_session_status_frame = KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.mock_session_id,
                sequence_information=bytes.fromhex("00 00 00 00 00 00"),
                serial_number=bytes.fromhex("00 fa aa aa aa aa"),
                message_tag=self.mock_message_tag,
                encrypted_data=bytes.fromhex("26 15 6d b5 c7 49 88 8f"),
                message_authentication_code=bytes.fromhex(
                    "a3 73 c3 e0 b4 bd e4 49 7c 39 5e 4b 1c 2f 46 a1"
                ),
            )
        )
        self.session.handle_knxipframe(
            encrypted_session_status_frame, HPAI(*self.mock_addr)
        )

        await connect_task
        assert self.session.initialized is True
        assert not self.session._keepalive_task.done()

        # handle incoming SessionStatus (unencrypted for sake of simplicity)
        session_status_close_frame = KNXIPFrame.init_from_body(
            SessionStatus(status=SecureSessionStatusCode.STATUS_CLOSE)
        )
        with patch.object(self.session, "transport") as mock_transport:
            self.session.handle_knxipframe(
                session_status_close_frame, HPAI(*self.mock_addr)
            )
            mock_transport.close.assert_called_once()

        # keepalive SessionStatus (not specific for sake of simplicity)
        await time_travel(SESSION_KEEPALIVE_RATE)
        mock_session_send.assert_called_once()  # unencrypted
        mock_session_send.reset_mock()
        mock_super_send.assert_called_once()  # encrypted
        mock_super_send.reset_mock()

        # SessionStatus CLOSE sent on graceful disconnect
        with (
            patch.object(self.session, "transport") as mock_transport,
        ):
            self.session.stop()
            mock_session_send.assert_called_once_with(
                self.session,  # account for self argument in wraps
                session_status_close_frame,
            )
            mock_super_send.assert_called_once()
            mock_transport.close.assert_called_once()
            assert self.session._keepalive_task is None

    def test_uninitialized(self) -> None:
        """Test for raising when an encrypted Frame arrives at an uninitialized Session."""
        secure_wrapper_frame = KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.mock_session_id,
                sequence_information=bytes.fromhex("00 00 00 00 00 00"),
                serial_number=bytes.fromhex("00 fa aa aa aa aa"),
                message_tag=self.mock_message_tag,
                encrypted_data=bytes.fromhex("26 15 6d b5 c7 49 88 8f"),
                message_authentication_code=bytes.fromhex(
                    "a3 73 c3 e0 b4 bd e4 49 7c 39 5e 4b 1c 2f 46 a1"
                ),
            )
        )
        with pytest.raises(CouldNotParseKNXIP):
            self.session.handle_knxipframe(secure_wrapper_frame, HPAI(*self.mock_addr))

    @patch("xknx.io.transport.tcp_transport.TCPTransport.connect")
    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    @patch(
        "xknx.io.ip_secure.generate_ecdh_key_pair",
        return_value=(mock_private_key, mock_public_key),
    )
    async def test_invalid_frames(
        self,
        _mock_generate: Mock,
        mock_super_send: Mock,
        mock_super_connect: Mock,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test handling invalid frames."""
        callback_mock = Mock()
        self.session.register_callback(callback_mock)
        # setup session
        connect_task = asyncio.create_task(self.session.connect())
        await time_travel(0)
        session_response_frame = KNXIPFrame.init_from_body(
            SessionResponse(
                secure_session_id=1,
                ecdh_server_public_key=self.mock_server_public_key,
                message_authentication_code=bytes.fromhex(
                    "a9 22 50 5a aa 43 61 63 57 0b d5 49 4c 2d f2 a3"
                ),
            )
        )
        self.session.handle_knxipframe(session_response_frame, HPAI(*self.mock_addr))
        await time_travel(0)
        callback_mock.reset_mock()
        encrypted_session_status_frame = KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.mock_session_id,
                sequence_information=bytes.fromhex("00 00 00 00 00 00"),
                serial_number=bytes.fromhex("00 fa aa aa aa aa"),
                message_tag=self.mock_message_tag,
                encrypted_data=bytes.fromhex("26 15 6d b5 c7 49 88 8f"),
                message_authentication_code=bytes.fromhex(
                    "a3 73 c3 e0 b4 bd e4 49 7c 39 5e 4b 1c 2f 46 a1"
                ),
            )
        )
        self.session.handle_knxipframe(
            encrypted_session_status_frame, HPAI(*self.mock_addr)
        )
        await connect_task
        assert self.session.initialized
        callback_mock.assert_called_once()
        callback_mock.reset_mock()

        # receive sequence_information 0 again
        self.session.handle_knxipframe(
            encrypted_session_status_frame, HPAI(*self.mock_addr)
        )
        await time_travel(0)
        callback_mock.assert_not_called()

        # receive invalid message_authentication_code
        # (which is invalid brecause the sequence_information is changed)
        wrong_session_status_frame = KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.mock_session_id,
                sequence_information=bytes.fromhex("00 00 00 00 00 01"),
                serial_number=bytes.fromhex("00 fa aa aa aa aa"),
                message_tag=self.mock_message_tag,
                encrypted_data=bytes.fromhex("26 15 6d b5 c7 49 88 8f"),
                message_authentication_code=bytes.fromhex(
                    "a3 73 c3 e0 b4 bd e4 49 7c 39 5e 4b 1c 2f 46 a1"
                ),
            )
        )
        self.session.handle_knxipframe(
            wrong_session_status_frame, HPAI(*self.mock_addr)
        )
        await time_travel(0)
        callback_mock.assert_not_called()
        # async teardown
        self.session.stop()
        assert self.session.initialized is False

    @patch("xknx.io.transport.tcp_transport.TCPTransport.connect")
    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    @patch(
        "xknx.io.ip_secure.generate_ecdh_key_pair",
        return_value=(mock_private_key, mock_public_key),
    )
    async def test_invalid_session_response(
        self,
        _mock_generate: Mock,
        mock_super_send: Mock,
        mock_super_connect: Mock,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test handling invalid session response."""
        connect_task = asyncio.create_task(self.session.connect())
        await time_travel(0)
        session_response_frame = KNXIPFrame.init_from_body(
            SessionResponse(
                secure_session_id=1,
                ecdh_server_public_key=self.mock_server_public_key,
                message_authentication_code=bytes.fromhex(
                    "ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff"
                ),
            )
        )
        with pytest.raises(CommunicationError):
            self.session.handle_knxipframe(
                session_response_frame, HPAI(*self.mock_addr)
            )
            await connect_task
        # only SessionRequest, no SessionAuthenticate
        mock_super_send.assert_called_once()

    @patch("xknx.io.transport.tcp_transport.TCPTransport.connect")
    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    @patch(
        "xknx.io.ip_secure.generate_ecdh_key_pair",
        return_value=(mock_private_key, mock_public_key),
    )
    async def test_no_authentication(
        self,
        _mock_generate: Mock,
        mock_super_send: Mock,
        mock_super_connect: Mock,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test handling initializing session without verifying server authenticity."""
        self.session._device_authentication_code = None
        connect_task = asyncio.create_task(self.session.connect())
        await time_travel(0)
        mock_super_send.reset_mock()
        invalid_session_response_frame = KNXIPFrame.init_from_body(
            SessionResponse(
                secure_session_id=1,
                ecdh_server_public_key=self.mock_server_public_key,
                message_authentication_code=bytes.fromhex(
                    "ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff"
                ),
            )
        )
        self.session.handle_knxipframe(
            invalid_session_response_frame, HPAI(*self.mock_addr)
        )
        await time_travel(0)
        # outgoing
        encrypted_authenticate_frame = KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.mock_session_id,
                sequence_information=bytes.fromhex("00 00 00 00 00 00"),
                serial_number=self.mock_serial_number,
                message_tag=self.mock_message_tag,
                encrypted_data=bytes.fromhex(
                    "79 15 a4 f3 6e 6e 42 08"
                    "d2 8b 4a 20 7d 8f 35 c0"
                    "d1 38 c2 6a 7b 5e 71 69"
                ),
                message_authentication_code=bytes.fromhex(
                    "52 db a8 e7 e4 bd 80 bd 7d 86 8a 3a e7 87 49 de"
                ),
            )
        )
        mock_super_send.assert_called_once_with(
            encrypted_authenticate_frame,
            None,  # None for addr in TCP transport
        )
        # incoming
        encrypted_session_status_frame = KNXIPFrame.init_from_body(
            SecureWrapper(
                secure_session_id=self.mock_session_id,
                sequence_information=bytes.fromhex("00 00 00 00 00 00"),
                serial_number=bytes.fromhex("00 fa aa aa aa aa"),
                message_tag=self.mock_message_tag,
                encrypted_data=bytes.fromhex("26 15 6d b5 c7 49 88 8f"),
                message_authentication_code=bytes.fromhex(
                    "a3 73 c3 e0 b4 bd e4 49 7c 39 5e 4b 1c 2f 46 a1"
                ),
            )
        )
        self.session.handle_knxipframe(
            encrypted_session_status_frame, HPAI(*self.mock_addr)
        )
        await connect_task
        assert self.session.initialized is True
        # async teardown
        self.session.stop()
        assert self.session.initialized is False

    @patch("xknx.io.transport.tcp_transport.TCPTransport.connect")
    @patch("xknx.io.transport.tcp_transport.TCPTransport.send")
    @patch(
        "xknx.io.ip_secure.generate_ecdh_key_pair",
        return_value=(mock_private_key, mock_public_key),
    )
    async def test_invalid_authentication(
        self,
        _mock_generate: Mock,
        mock_super_send: Mock,
        mock_super_connect: Mock,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test handling no session status while authenticating."""
        connect_task = asyncio.create_task(self.session.connect())
        await time_travel(0)
        session_response_frame = KNXIPFrame.init_from_body(
            SessionResponse(
                secure_session_id=1,
                ecdh_server_public_key=self.mock_server_public_key,
                message_authentication_code=bytes.fromhex(
                    "a9 22 50 5a aa 43 61 63 57 0b d5 49 4c 2d f2 a3"
                ),
            )
        )
        self.session.handle_knxipframe(session_response_frame, HPAI(*self.mock_addr))
        with pytest.raises(CommunicationError):
            await time_travel(10)
            await connect_task
