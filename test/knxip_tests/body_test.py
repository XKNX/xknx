"""Unit test for KNX/IP Body base class."""
from unittest.mock import patch

from xknx import XKNX
from xknx.knxip import KNXIPBody, KNXIPBodyResponse


class Test_KNXIPBody:
    """Test base class for KNX/IP bodys."""

    @patch.multiple(KNXIPBody, __abstractmethods__=set())
    def test_body_attributes(self):
        """Test attributes of KNXIPBody base class."""
        self.xknx = XKNX()
        body = KNXIPBody(self.xknx)
        assert hasattr(body, "SERVICE_TYPE")

    @patch.multiple(KNXIPBodyResponse, __abstractmethods__=set())
    def test_response_attributes(self):
        """Test attributes of KNXIPBodyResponse base class."""
        self.xknx = XKNX()
        response = KNXIPBodyResponse(self.xknx)
        assert hasattr(response, "SERVICE_TYPE")
        assert hasattr(response, "status_code")
