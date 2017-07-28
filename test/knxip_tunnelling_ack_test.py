"""Unit test for KNX/IP TunnelingAck objects."""
import unittest

from xknx.knxip import KNXIPFrame, KNXIPServiceType, TunnellingAck, \
    ErrorCode


class Test_KNXIP_TunnelingReq(unittest.TestCase):
    """Test class for KNX/IP TunelingAck objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_connect_request(self):
        """Test parsing and streaming tunneling ACK KNX/IP packet."""
        raw = ((0x06, 0x10, 0x04, 0x21, 0x00, 0x0a, 0x04, 0x2a,
                0x17, 0x00))
        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, TunnellingAck))
        self.assertEqual(knxipframe.body.communication_channel_id, 42)
        self.assertEqual(knxipframe.body.sequence_counter, 23)
        self.assertEqual(
            knxipframe.body.status_code,
            ErrorCode.E_NO_ERROR)

        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.TUNNELLING_ACK)
        knxipframe2.body.communication_channel_id = 42
        knxipframe2.body.sequence_counter = 23
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))


SUITE = unittest.TestLoader().loadTestsFromTestCase(Test_KNXIP_TunnelingReq)
unittest.TextTestRunner(verbosity=2).run(SUITE)
