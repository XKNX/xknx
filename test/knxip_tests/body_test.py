"""Unit test for KNX/IP Body base class."""

from unittest.mock import patch

from xknx.knxip import KNXIPBody, KNXIPBodyResponse


class TestKNXIPBody:
    """Test base class for KNX/IP bodys."""

    @patch.multiple(KNXIPBody, __abstractmethods__=set())
    def test_body_attributes(self) -> None:
        """Test attributes of KNXIPBody base class."""
        body = KNXIPBody()
        assert hasattr(body, "SERVICE_TYPE")

    @patch.multiple(KNXIPBodyResponse, __abstractmethods__=set())
    def test_response_attributes(self) -> None:
        """Test attributes of KNXIPBodyResponse base class."""
        response = KNXIPBodyResponse()
        assert hasattr(response, "SERVICE_TYPE")
        assert hasattr(response, "status_code")
