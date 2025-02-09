"""Unit test for KNX/IP SecureWrapper objects."""

from xknx.knxip import KNXIPFrame, SecureWrapper


class TestKNXIPSecureWrapper:
    """Test class for KNX/IP SecureWrapper objects."""

    def test_secure_wrapper(self) -> None:
        """Test parsing and streaming secure wrapper KNX/IP packet."""
        sequence_number = bytes.fromhex("00 00 00 00 00 00")
        knx_serial_number = bytes.fromhex("00 fa 12 34 56 78")
        message_tag = bytes.fromhex("af fe")
        encrypted_data = bytes.fromhex(
            "79 15 a4 f3 6e 6e 42 08"  # SessionAuthenticate Frame
            "d2 8b 4a 20 7d 8f 35 c0"
            "d1 38 c2 6a 7b 5e 71 69"
        )
        message_authentication_code = bytes.fromhex(
            "52 db a8 e7 e4 bd 80 bd 7d 86 8a 3a e7 87 49 de"
        )
        raw = (
            bytes.fromhex(
                "06 10 09 50 00 3e"  # KNXnet/IP header
                "00 01"  # Secure Session Identifier
            )
            + sequence_number
            + knx_serial_number
            + message_tag
            + encrypted_data
            + message_authentication_code
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, SecureWrapper)
        assert knxipframe.body.secure_session_id == 1
        assert knxipframe.body.sequence_information == sequence_number
        assert knxipframe.body.serial_number == knx_serial_number
        assert knxipframe.body.message_tag == message_tag
        assert knxipframe.body.encrypted_data == encrypted_data
        assert (
            knxipframe.body.message_authentication_code == message_authentication_code
        )

        assert knxipframe.to_knx() == raw

        secure_wrapper = SecureWrapper(
            secure_session_id=1,
            sequence_information=sequence_number,
            serial_number=knx_serial_number,
            message_tag=message_tag,
            encrypted_data=encrypted_data,
            message_authentication_code=message_authentication_code,
        )
        knxipframe2 = KNXIPFrame.init_from_body(secure_wrapper)
        assert knxipframe2.to_knx() == raw
