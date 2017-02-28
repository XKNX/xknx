import unittest

from xknx.knxip import KNXIPFrame, KNXIPServiceType, ConnectionStateRequest, HPAI


class Test_KNXIP_ConnStateReq(unittest.TestCase):
    # pylint: disable=too-many-public-methods,invalid-name

    def test_disconnect_request(self):

        raw = ((0x06, 0x10, 0x02, 0x07, 0x00, 0x10, 0x15, 0x00,
                0x08, 0x01, 0xC0, 0xA8, 0xC8, 0x0C, 0xC3, 0xB4))

        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, ConnectionStateRequest))

        self.assertEqual(
            knxipframe.body.communication_channel_id, 21)
        self.assertEqual(
            knxipframe.body.control_endpoint,
            HPAI(ip_addr='192.168.200.12', port=50100))


        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.CONNECTIONSTATE_REQUEST)
        knxipframe2.body.communication_channel_id = 21
        knxipframe2.body.control_endpoint = HPAI(
            ip_addr='192.168.200.12', port=50100)
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))


SUITE = unittest.TestLoader().loadTestsFromTestCase(Test_KNXIP_ConnStateReq)
unittest.TextTestRunner(verbosity=2).run(SUITE)
