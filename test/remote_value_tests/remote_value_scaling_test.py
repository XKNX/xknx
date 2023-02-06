"""Unit test for RemoteValueScaling objects."""
from xknx import XKNX
from xknx.remote_value import RemoteValueScaling


class TestRemoteValueScaling:
    """Test class for RemoteValueScaling objects."""

    def test_calc_0_10(self):
        """Test if from/to calculations work with small range."""
        assert RemoteValueScaling._calc_to_knx(0, 10, 0) == 0
        assert RemoteValueScaling._calc_to_knx(0, 10, 1) == 26
        assert RemoteValueScaling._calc_to_knx(0, 10, 9) == 230
        assert RemoteValueScaling._calc_to_knx(0, 10, 10) == 255

        assert RemoteValueScaling._calc_from_knx(0, 10, 0) == 0
        assert RemoteValueScaling._calc_from_knx(0, 10, 1) == 0
        assert RemoteValueScaling._calc_from_knx(0, 10, 12) == 0
        assert RemoteValueScaling._calc_from_knx(0, 10, 13) == 1
        assert RemoteValueScaling._calc_from_knx(0, 10, 254) == 10
        assert RemoteValueScaling._calc_from_knx(0, 10, 255) == 10

    def test_calc_0_100(self):
        """Test if from/to calculations work range 0-100 with many test cases."""
        assert RemoteValueScaling._calc_to_knx(0, 100, 0) == 0
        assert RemoteValueScaling._calc_to_knx(0, 100, 1) == 3
        assert RemoteValueScaling._calc_to_knx(0, 100, 2) == 5
        assert RemoteValueScaling._calc_to_knx(0, 100, 3) == 8
        assert RemoteValueScaling._calc_to_knx(0, 100, 30) == 76
        assert RemoteValueScaling._calc_to_knx(0, 100, 50) == 128
        assert RemoteValueScaling._calc_to_knx(0, 100, 70) == 178
        assert RemoteValueScaling._calc_to_knx(0, 100, 97) == 247
        assert RemoteValueScaling._calc_to_knx(0, 100, 98) == 250
        assert RemoteValueScaling._calc_to_knx(0, 100, 99) == 252
        assert RemoteValueScaling._calc_to_knx(0, 100, 100) == 255

        assert RemoteValueScaling._calc_from_knx(0, 100, 0) == 0
        assert RemoteValueScaling._calc_from_knx(0, 100, 1) == 0
        assert RemoteValueScaling._calc_from_knx(0, 100, 2) == 1
        assert RemoteValueScaling._calc_from_knx(0, 100, 3) == 1
        assert RemoteValueScaling._calc_from_knx(0, 100, 4) == 2
        assert RemoteValueScaling._calc_from_knx(0, 100, 5) == 2
        assert RemoteValueScaling._calc_from_knx(0, 100, 76) == 30
        assert RemoteValueScaling._calc_from_knx(0, 100, 128) == 50
        assert RemoteValueScaling._calc_from_knx(0, 100, 178) == 70
        assert RemoteValueScaling._calc_from_knx(0, 100, 251) == 98
        assert RemoteValueScaling._calc_from_knx(0, 100, 252) == 99
        assert RemoteValueScaling._calc_from_knx(0, 100, 253) == 99
        assert RemoteValueScaling._calc_from_knx(0, 100, 254) == 100
        assert RemoteValueScaling._calc_from_knx(0, 100, 255) == 100

    def test_calc_0_1000(self):
        """Test if from/to calculations work with large range."""
        assert RemoteValueScaling._calc_to_knx(0, 1000, 0) == 0
        assert RemoteValueScaling._calc_to_knx(0, 1000, 1) == 0
        assert RemoteValueScaling._calc_to_knx(0, 1000, 2) == 1
        assert RemoteValueScaling._calc_to_knx(0, 1000, 3) == 1
        assert RemoteValueScaling._calc_to_knx(0, 1000, 500) == 128
        assert RemoteValueScaling._calc_to_knx(0, 1000, 997) == 254
        assert RemoteValueScaling._calc_to_knx(0, 1000, 998) == 254
        assert RemoteValueScaling._calc_to_knx(0, 1000, 999) == 255
        assert RemoteValueScaling._calc_to_knx(0, 1000, 1000) == 255

        assert RemoteValueScaling._calc_from_knx(0, 1000, 0) == 0
        assert RemoteValueScaling._calc_from_knx(0, 1000, 1) == 4
        assert RemoteValueScaling._calc_from_knx(0, 1000, 2) == 8
        assert RemoteValueScaling._calc_from_knx(0, 1000, 128) == 502
        assert RemoteValueScaling._calc_from_knx(0, 1000, 251) == 984
        assert RemoteValueScaling._calc_from_knx(0, 1000, 252) == 988
        assert RemoteValueScaling._calc_from_knx(0, 1000, 253) == 992
        assert RemoteValueScaling._calc_from_knx(0, 1000, 254) == 996
        assert RemoteValueScaling._calc_from_knx(0, 1000, 255) == 1000

    def test_calc_100_0(self):
        """Test if from/to calculations work with negative range."""
        assert RemoteValueScaling._calc_to_knx(100, 0, 0) == 255
        assert RemoteValueScaling._calc_to_knx(100, 0, 1) == 252
        assert RemoteValueScaling._calc_to_knx(100, 0, 2) == 250
        assert RemoteValueScaling._calc_to_knx(100, 0, 3) == 247
        assert RemoteValueScaling._calc_to_knx(100, 0, 30) == 178
        assert RemoteValueScaling._calc_to_knx(100, 0, 50) == 128
        assert RemoteValueScaling._calc_to_knx(100, 0, 70) == 76
        assert RemoteValueScaling._calc_to_knx(100, 0, 97) == 8
        assert RemoteValueScaling._calc_to_knx(100, 0, 98) == 5
        assert RemoteValueScaling._calc_to_knx(100, 0, 99) == 3
        assert RemoteValueScaling._calc_to_knx(100, 0, 100) == 0

        assert RemoteValueScaling._calc_from_knx(100, 0, 0) == 100
        assert RemoteValueScaling._calc_from_knx(100, 0, 1) == 100
        assert RemoteValueScaling._calc_from_knx(100, 0, 2) == 99
        assert RemoteValueScaling._calc_from_knx(100, 0, 3) == 99
        assert RemoteValueScaling._calc_from_knx(100, 0, 4) == 98
        assert RemoteValueScaling._calc_from_knx(100, 0, 5) == 98
        assert RemoteValueScaling._calc_from_knx(100, 0, 76) == 70
        assert RemoteValueScaling._calc_from_knx(100, 0, 128) == 50
        assert RemoteValueScaling._calc_from_knx(100, 0, 178) == 30
        assert RemoteValueScaling._calc_from_knx(100, 0, 251) == 2
        assert RemoteValueScaling._calc_from_knx(100, 0, 252) == 1
        assert RemoteValueScaling._calc_from_knx(100, 0, 253) == 1
        assert RemoteValueScaling._calc_from_knx(100, 0, 254) == 0
        assert RemoteValueScaling._calc_from_knx(100, 0, 255) == 0

    def test_calc_100_200(self):
        """Test if from/to calculations work with range not starting at zero."""
        assert RemoteValueScaling._calc_to_knx(100, 200, 100) == 0
        assert RemoteValueScaling._calc_to_knx(100, 200, 130) == 76
        assert RemoteValueScaling._calc_to_knx(100, 200, 150) == 128
        assert RemoteValueScaling._calc_to_knx(100, 200, 170) == 178
        assert RemoteValueScaling._calc_to_knx(100, 200, 200) == 255

        assert RemoteValueScaling._calc_from_knx(100, 200, 0) == 100
        assert RemoteValueScaling._calc_from_knx(100, 200, 76) == 130
        assert RemoteValueScaling._calc_from_knx(100, 200, 128) == 150
        assert RemoteValueScaling._calc_from_knx(100, 200, 178) == 170
        assert RemoteValueScaling._calc_from_knx(100, 200, 255) == 200

    def test_value_unit(self):
        """Test for the unit_of_measurement."""
        xknx = XKNX()
        remote_value = RemoteValueScaling(xknx)
        assert remote_value.unit_of_measurement == "%"
