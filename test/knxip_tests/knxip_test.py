"""Unit test for KNX/IP base class."""

from unittest.mock import patch

import pytest

from xknx.exceptions import CouldNotParseKNXIP, IncompleteKNXIPFrame
from xknx.knxip import KNXIPBody, KNXIPFrame, KNXIPHeader
from xknx.knxip.knxip import _BODY_CLASSES
from xknx.knxip.knxip_enum import KNXIPServiceType


class TestKNXIPFrame:
    """Test class for KNX/IP base class."""

    def test_wrong_init(self) -> None:
        """Testing init method with wrong service_type_ident."""
        header = KNXIPHeader()
        header.service_type_ident = KNXIPServiceType.REMOTE_DIAG_RESPONSE
        with pytest.raises(CouldNotParseKNXIP):
            # this is not yet implemented in xknx
            KNXIPFrame.from_knx(header.to_knx())

    @pytest.mark.parametrize("service_type", list(_BODY_CLASSES))
    def test_from_knx_service_type_dispatch(
        self, service_type: KNXIPServiceType
    ) -> None:
        """Test every implemented service type resolves to the body class declaring it."""
        body_class = _BODY_CLASSES[service_type]
        assert service_type == body_class.SERVICE_TYPE
        header = KNXIPHeader()
        header.service_type_ident = service_type
        header.total_length = KNXIPHeader.HEADERLENGTH + 2
        raw_body = bytes.fromhex("aa bb")
        with patch.object(body_class, "from_knx", return_value=2) as from_knx_mock:
            frame, rest = KNXIPFrame.from_knx(header.to_knx() + raw_body + b"\x00")
        from_knx_mock.assert_called_once_with(raw_body)
        assert frame.body.__class__ is body_class
        assert frame.header == header
        assert rest == b"\x00"

    @pytest.mark.parametrize(
        "service_type",
        [
            service_type
            for service_type in KNXIPServiceType
            if service_type not in _BODY_CLASSES
        ],
    )
    def test_from_knx_service_type_unsupported(
        self, service_type: KNXIPServiceType
    ) -> None:
        """Test service types without body class raise CouldNotParseKNXIP."""
        header = KNXIPHeader()
        header.service_type_ident = service_type
        header.total_length = KNXIPHeader.HEADERLENGTH
        with pytest.raises(
            CouldNotParseKNXIP,
            match=f"KNXIPServiceType not implemented: {service_type.name}",
        ):
            KNXIPFrame.from_knx(header.to_knx())

    def test_body_classes_complete(self) -> None:
        """Test every concrete KNXIPBody subclass is dispatched to."""

        def concrete_subclasses(cls: type[KNXIPBody]) -> set[type[KNXIPBody]]:
            result = set()
            for subclass in cls.__subclasses__():
                if subclass.SERVICE_TYPE is not None:
                    result.add(subclass)
                result |= concrete_subclasses(subclass)
            return result

        assert set(_BODY_CLASSES.values()) == concrete_subclasses(KNXIPBody)

    def test_double_frame(self) -> None:
        """Test parsing KNX/IP frame from streaming data containing two frames."""
        raw = bytes.fromhex(
            "06 10 04 20 00 15 04 02 51 00 29 00 bc e0 10 fa"
            "09 2d 01 00 80"
            "06 10 04 20 00 15 04 02 52 00 29 00 bc e0 10 1f"
            "08 2d 01 00 80"
        )  # both frames have length 21
        frame_1, rest_1 = KNXIPFrame.from_knx(raw)
        frame_2, _rest_2 = KNXIPFrame.from_knx(rest_1)
        assert frame_1.header.total_length == 21
        assert frame_2.header.total_length == 21

    def test_parsing_too_short_knxip(self) -> None:
        """Test parsing and streaming connection state request KNX/IP packet."""
        raw = bytes.fromhex("06 10 02 07 00 10 15 00 08 01 C0 A8 C8 0C C3")
        with pytest.raises(IncompleteKNXIPFrame):
            KNXIPFrame.from_knx(raw)
