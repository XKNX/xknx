import unittest

from xknx.knxip import KNXIPFrame, KNXIPServiceType, DisconnectResponse,\
    ErrorCode


class Test_KNXIP_DisconnectResp(unittest.TestCase):
    # pylint: disable=too-many-public-methods,invalid-name

    def test_disconnect_response(self):
        raw = ((0x06, 0x10, 0x02, 0x0A, 0x00, 0x08, 0x15, 0x25))


        knxipframe = KNXIPFrame()
        knxipframe.from_knx(raw)

        self.assertTrue(isinstance(knxipframe.body, DisconnectResponse))

        self.assertEqual(
            knxipframe.body.communication_channel_id, 21)
        self.assertEqual(
            knxipframe.body.status_code, ErrorCode.E_NO_FREE_CHANNEL)


        knxipframe2 = KNXIPFrame()
        knxipframe2.init(KNXIPServiceType.DISCONNECT_RESPONSE)
        knxipframe2.body.communication_channel_id = 21
        knxipframe2.body.status_code = ErrorCode.E_NO_FREE_CHANNEL
        knxipframe2.normalize()

        self.assertEqual(knxipframe2.to_knx(), list(raw))


SUITE = unittest.TestLoader().loadTestsFromTestCase(Test_KNXIP_DisconnectResp)
unittest.TextTestRunner(verbosity=2).run(SUITE)
