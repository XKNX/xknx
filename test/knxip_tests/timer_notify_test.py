"""Unit test for KNX/IP TimerNotify objects."""

from xknx.knxip import KNXIPFrame, TimerNotify


class TestKNXIPTimerNotify:
    """Test class for KNX/IP TimerNotify objects."""

    def test_timer_notify(self):
        """Test parsing and streaming TimerNotify KNX/IP packet."""
        message_authentication_code = bytes.fromhex(
            "72 12 a0 3a aa e4 9d a8 56 89 77 4c 1d 2b 4d a4"
        )
        raw = (
            bytes.fromhex(
                "06 10 09 55 00 24"  # KNXnet/IP header - length 36 octets
                "c0 c1 c2 c3 c4 c5"  # timer value
                "00 fa 12 34 56 78"  # KNX serial number
                "af fe"  # message tag
            )
            + message_authentication_code
        )
        knxipframe, _ = KNXIPFrame.from_knx(raw)

        assert isinstance(knxipframe.body, TimerNotify)
        assert knxipframe.body.timer_value == 211938428830917
        assert knxipframe.body.serial_number == bytes.fromhex("00 fa 12 34 56 78")
        assert knxipframe.body.message_tag == bytes.fromhex("af fe")
        assert (
            knxipframe.body.message_authentication_code == message_authentication_code
        )

        assert knxipframe.to_knx() == raw

        timer_notify = TimerNotify(
            timer_value=211938428830917,
            serial_number=bytes.fromhex("00 fa 12 34 56 78"),
            message_tag=bytes.fromhex("af fe"),
            message_authentication_code=message_authentication_code,
        )
        knxipframe2 = KNXIPFrame.init_from_body(timer_notify)

        assert knxipframe2.to_knx() == raw
