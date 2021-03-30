"""Unit test for KNX/IP Body base class."""
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.knxip import KNXIPBody, KNXIPBodyResponse


class Test_KNXIPBody(unittest.TestCase):
    """Test base class for KNX/IP bodys."""

    def setUp(self):
        """Set up test class."""
        self.xknx = XKNX()

    @patch.multiple(KNXIPBody, __abstractmethods__=set())
    def test_body_attributes(self):
        """Test attributes of KNXIPBody base class."""
        body = KNXIPBody(self.xknx)
        self.assertTrue(hasattr(body, "SERVICE_TYPE"))

    @patch.multiple(KNXIPBodyResponse, __abstractmethods__=set())
    def test_response_attributes(self):
        """Test attributes of KNXIPBodyResponse base class."""
        response = KNXIPBodyResponse(self.xknx)
        self.assertTrue(hasattr(response, "SERVICE_TYPE"))
        self.assertTrue(hasattr(response, "status_code"))
