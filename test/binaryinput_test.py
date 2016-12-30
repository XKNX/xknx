import unittest

from xknx import XKNX,BinaryInput,BinaryInputState,Telegram,DPT_Binary

class TestBinaryInput(unittest.TestCase):

    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX()
        binaryinput = BinaryInput(xknx, 'TestInput', '1/2/3')

        self.assertEqual( binaryinput.state, BinaryInputState.OFF )

        telegram_on = Telegram()
        telegram_on.payload = DPT_Binary(1)
        binaryinput.process( telegram_on )

        self.assertEqual( binaryinput.state, BinaryInputState.ON )

        telegram_off = Telegram()
        telegram_off.payload = DPT_Binary(0)
        binaryinput.process( telegram_off )

        self.assertEqual( binaryinput.state, BinaryInputState.OFF )

    #
    # TEST SWITCHED ON
    #
    def test_is_on(self):
        xknx = XKNX()
        binaryinput = BinaryInput(xknx, 'TestInput', '1/2/3')
        binaryinput.set_internal_state( BinaryInputState.ON )
        self.assertTrue(binaryinput.is_on())
        self.assertFalse(binaryinput.is_off())

    #
    # TEST SWITCHED OFF
    #
    def test_is_off(self):
        xknx = XKNX()
        binaryinput = BinaryInput(xknx, 'TestInput', '1/2/3')
        binaryinput.set_internal_state( BinaryInputState.OFF )
        self.assertFalse(binaryinput.is_on())
        self.assertTrue(binaryinput.is_off()) 


suite = unittest.TestLoader().loadTestsFromTestCase(TestBinaryInput)
unittest.TextTestRunner(verbosity=2).run(suite)
