"""Test Secure Session."""
import asyncio
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from xknx import XKNX
from xknx.io.secure_session import SecureSession
from xknx.knxip import HPAI, KNXIPFrame, SecureWrapper, SessionRequest, SessionResponse


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
    mock_serial_number = 0x00_FA_12_34_56_78
    mock_message_tag = 0xAF_FE

    async def test_connect(self, time_travel):
        """Test handshake."""
        xknx = XKNX()
        session = SecureSession(
            xknx,
            remote_addr=self.mock_addr,
            device_authentication_password=self.mock_device_authentication_password,
            user_id=self.mock_user_id,
            user_password=self.mock_user_password,
        )
        session.serial_number = self.mock_serial_number.to_bytes(6, "big")
        session.message_tag = self.mock_message_tag.to_bytes(2, "big")

        with patch(
            "xknx.io.transport.tcp_transport.TCPTransport.connect"
        ) as mock_super_connect, patch(
            "xknx.io.transport.tcp_transport.TCPTransport.send"
        ) as mock_super_send, patch(
            "xknx.io.secure_session.generate_ecdh_key_pair",
            return_value=(self.mock_private_key, self.mock_public_key),
        ):
            connect_task = asyncio.create_task(session.connect())
            await time_travel(0)
            mock_super_connect.assert_called_once()
            # outgoing
            session_request_frame = KNXIPFrame.init_from_body(
                SessionRequest(xknx, ecdh_client_public_key=self.mock_public_key)
            )
            mock_super_send.assert_called_once_with(
                session_request_frame, None  # None for addr in TCP transport
            )
            mock_super_send.reset_mock()
            # incoming
            session_response_frame = KNXIPFrame.init_from_body(
                SessionResponse(
                    xknx,
                    secure_session_id=1,
                    ecdh_server_public_key=self.mock_server_public_key,
                    message_authentication_code=bytes.fromhex(
                        "a9 22 50 5a aa 43 61 63 57 0b d5 49 4c 2d f2 a3"
                    ),
                )
            )
            session.handle_knxipframe(session_response_frame, HPAI(*self.mock_addr))
            await time_travel(0)
            # outgoing
            encrypted_authenticate_frame = KNXIPFrame.init_from_body(
                SecureWrapper(
                    xknx,
                    secure_session_id=self.mock_session_id,
                    sequence_information=0,
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
                encrypted_authenticate_frame, None  # None for addr in TCP transport
            )
            # incoming
            encrypted_session_status_frame = KNXIPFrame.init_from_body(
                SecureWrapper(
                    xknx,
                    secure_session_id=self.mock_session_id,
                    sequence_information=0,
                    serial_number=0x00_FA_AA_AA_AA_AA,
                    message_tag=self.mock_message_tag,
                    encrypted_data=bytes.fromhex("26 15 6d b5 c7 49 88 8f"),
                    message_authentication_code=bytes.fromhex(
                        "a3 73 c3 e0 b4 bd e4 49 7c 39 5e 4b 1c 2f 46 a1"
                    ),
                )
            )
            session.handle_knxipframe(
                encrypted_session_status_frame, HPAI(*self.mock_addr)
            )
            await connect_task
        session.stop()