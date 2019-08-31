"""Unit test for RemoteValueScaling objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.remote_value import RemoteValueScaling


class TestRemoteValueScaling(unittest.TestCase):
    """Test class for RemoteValueScaling objects."""

    # pylint: disable=protected-access

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_calc_0_10(self):
        """Test if from/to calculations work with small range."""
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 10, 0), 0)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 10, 1), 26)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 10, 9), 230)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 10, 10), 255)

        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 10, 0), 0)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 10, 1), 0)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 10, 12), 0)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 10, 13), 1)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 10, 254), 10)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 10, 255), 10)

    def test_calc_0_100(self):
        """Test if from/to calculations work range 0-100 with many test cases."""
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 0), 0)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 1), 3)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 2), 5)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 3), 8)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 30), 76)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 50), 128)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 70), 178)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 97), 247)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 98), 250)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 99), 252)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 100, 100), 255)

        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 0), 0)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 1), 0)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 2), 1)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 3), 1)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 4), 2)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 5), 2)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 76), 30)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 128), 50)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 178), 70)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 251), 98)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 252), 99)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 253), 99)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 254), 100)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 100, 255), 100)

    def test_calc_0_1000(self):
        """Test if from/to calculations work with large range."""
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 1000, 0), 0)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 1000, 1), 0)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 1000, 2), 1)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 1000, 3), 1)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 1000, 500), 128)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 1000, 997), 254)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 1000, 998), 254)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 1000, 999), 255)
        self.assertEqual(RemoteValueScaling._calc_to_knx(0, 1000, 1000), 255)

        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 1000, 0), 0)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 1000, 1), 4)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 1000, 2), 8)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 1000, 128), 502)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 1000, 251), 984)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 1000, 252), 988)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 1000, 253), 992)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 1000, 254), 996)
        self.assertEqual(RemoteValueScaling._calc_from_knx(0, 1000, 255), 1000)

    def test_calc_100_0(self):
        """Test if from/to calculations work with negative range."""
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 0), 255)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 1), 252)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 2), 250)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 3), 247)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 30), 178)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 50), 128)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 70), 76)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 97), 8)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 98), 5)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 99), 3)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 0, 100), 0)

        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 0), 100)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 1), 100)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 2), 99)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 3), 99)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 4), 98)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 5), 98)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 76), 70)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 128), 50)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 178), 30)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 251), 2)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 252), 1)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 253), 1)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 254), 0)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 0, 255), 0)

    def test_calc_100_200(self):
        """Test if from/to calculations work with rnage not starting at zero."""
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 200, 100), 0)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 200, 130), 76)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 200, 150), 128)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 200, 170), 178)
        self.assertEqual(RemoteValueScaling._calc_to_knx(100, 200, 200), 255)

        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 200, 0), 100)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 200, 76), 130)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 200, 128), 150)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 200, 178), 170)
        self.assertEqual(RemoteValueScaling._calc_from_knx(100, 200, 255), 200)

    def test_value_unit(self):
        """Test for the unit_of_measurement."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueScaling(xknx)
        self.assertEqual(remote_value.unit_of_measurement, "%")
