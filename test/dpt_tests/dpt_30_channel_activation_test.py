"""Unit test for KNX DPT 30 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_30 import ChannelActivation24, DPTChannelActivation24
from xknx.exceptions import ConversionError, CouldNotParseTelegram

CHANNEL_FIELDS = tuple(f"channel_{n}" for n in range(1, 25))


class TestDPTChannelActivation24:
    """Test class for KNX DPTChannelActivation24 objects."""

    @pytest.mark.parametrize(
        ("field", "channel"), [(name, n) for n, name in enumerate(CHANNEL_FIELDS, 1)]
    )
    def test_single_channel(self, field: str, channel: int) -> None:
        """Test each channel of DPTChannelActivation24 (channel n is bit n-1)."""
        bit = 1 << (channel - 1)
        raw = (bit >> 16, bit >> 8 & 0xFF, bit & 0xFF)
        value = ChannelActivation24(**{field: True})
        assert DPTChannelActivation24.to_knx(value) == DPTArray(raw)
        assert DPTChannelActivation24.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (ChannelActivation24(), (0x00, 0x00, 0x00)),
            (ChannelActivation24(channel_1=True), (0x00, 0x00, 0x01)),
            (ChannelActivation24(channel_9=True), (0x00, 0x01, 0x00)),
            (ChannelActivation24(channel_17=True), (0x01, 0x00, 0x00)),
            (ChannelActivation24(channel_24=True), (0x80, 0x00, 0x00)),
            (
                ChannelActivation24(channel_1=True, channel_16=True, channel_24=True),
                (0x80, 0x80, 0x01),
            ),
            (
                ChannelActivation24(**dict.fromkeys(CHANNEL_FIELDS, True)),
                (0xFF, 0xFF, 0xFF),
            ),
        ],
    )
    def test_values(self, value: ChannelActivation24, raw: tuple[int, ...]) -> None:
        """Test DPTChannelActivation24 parsing and streaming."""
        assert DPTChannelActivation24.to_knx(value) == DPTArray(raw)
        assert DPTChannelActivation24.from_knx(DPTArray(raw)) == value

    def test_dict(self) -> None:
        """Test from_dict and as_dict methods."""
        assert ChannelActivation24.from_dict(
            {"channel_2": True, "channel_23": True, "channel_5": False}
        ) == ChannelActivation24(channel_2=True, channel_23=True)
        assert ChannelActivation24(channel_20=True).as_dict() == dict.fromkeys(
            CHANNEL_FIELDS, False
        ) | {"channel_20": True}
        assert DPTChannelActivation24.to_knx({"channel_18": True}) == DPTArray(
            (0x02, 0x00, 0x00)
        )

    @pytest.mark.parametrize(
        "data", [{"channel_1": "on"}, {"channel_24": 2}, {"channel_3": None}, []]
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            ChannelActivation24.from_dict(data)
        with pytest.raises(ConversionError):
            DPTChannelActivation24.to_knx(data)

    def test_to_knx_wrong_value(self) -> None:
        """Test serializing a field with a wrong value."""
        with pytest.raises(ConversionError):
            DPTChannelActivation24.to_knx(ChannelActivation24(channel_7="a"))  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "payload",
        [DPTArray((0x00, 0x00)), DPTArray((0x00, 0x00, 0x00, 0x00)), DPTBinary(1)],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing DPTChannelActivation24 with a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTChannelActivation24.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema of DPTChannelActivation24."""
        assert DPTChannelActivation24.get_dict_schema() == [
            {"name": name, "type": "boolean", "required": False, "default": False}
            for name in CHANNEL_FIELDS
        ]

    def test_lookup(self) -> None:
        """Test lookup of DPTChannelActivation24."""
        assert DPTBase.parse_transcoder("30.1010") is DPTChannelActivation24
        assert DPTBase.parse_transcoder("channel_activation_24") is (
            DPTChannelActivation24
        )
