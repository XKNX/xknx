import unittest

from xknx import DPT_Binary,DPT_Array

class TestDPT(unittest.TestCase):

    def test_compare_binary(self):
        self.assertEqual( DPT_Binary(0), DPT_Binary(0))
        self.assertEqual( DPT_Binary(2), DPT_Binary(2))
        self.assertNotEqual( DPT_Binary(1), DPT_Binary(4))
        self.assertNotEqual( DPT_Binary(2), DPT_Binary(0))
        self.assertNotEqual( DPT_Binary(0), DPT_Binary(2))

    def test_compare_array(self):
        self.assertEqual( DPT_Array(()), DPT_Array(()))
        self.assertEqual( DPT_Array([1]), DPT_Array((1,)))
        self.assertEqual( DPT_Array([1,2,3]), DPT_Array([1,2,3]))
        self.assertEqual( DPT_Array([1,2,3]), DPT_Array((1,2,3)))
        self.assertEqual( DPT_Array((1,2,3)), DPT_Array([1,2,3]))
        self.assertNotEqual( DPT_Array((1,2,3)), DPT_Array([1,2,3,4]))
        self.assertNotEqual( DPT_Array((1,2,3,4)), DPT_Array([1,2,3]))
        self.assertNotEqual( DPT_Array((1,2,3)), DPT_Array([1,2,4]))

    def test_compare_none(self):
        self.assertEqual( DPT_Array(()), None )
        self.assertEqual( None, DPT_Array(()) )
        self.assertEqual( DPT_Binary(0), None )
        self.assertEqual( None, DPT_Binary(0) )
        self.assertNotEqual( DPT_Array((1,2,3)), None )
        self.assertNotEqual( None, DPT_Array((1,2,3)) )
        self.assertNotEqual( DPT_Binary(1 ), None)
        self.assertNotEqual( None, DPT_Binary(1) )

    def test_compare_array_binary(self):
        self.assertEqual( DPT_Array(()), DPT_Binary(0) )
        self.assertEqual( DPT_Binary(0), DPT_Array(()) )
        self.assertNotEqual( DPT_Array((1,2,3)), DPT_Binary(2) )
        self.assertNotEqual( DPT_Binary(2), DPT_Array((1,2,3)) )
        self.assertNotEqual( DPT_Array((2,)), DPT_Binary(2) )
        self.assertNotEqual( DPT_Binary(2), DPT_Array((2,)) )
        

suite = unittest.TestLoader().loadTestsFromTestCase(TestDPT)
unittest.TextTestRunner(verbosity=2).run(suite)
