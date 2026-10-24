"""
Regression tests for malformed KNX/IP frames.

Every malformed frame must raise CouldNotParseKNXIP - never hang the event loop
(e.g. DIBs with structure length 0) or raise IndexError / ValueError from a body parser.
"""

import threading

import pytest

from xknx.exceptions import CouldNotParseKNXIP
from xknx.knxip import DIBGeneric, DescriptionResponse, KNXIPFrame

PARSE_TIMEOUT = 2  # seconds


def parse_guarded(raw: bytes) -> KNXIPFrame:
    """
    Parse `raw` in a daemon thread and return the frame or re-raise its exception.

    A parser that loops forever would hang the whole test run, so it fails
    the test after PARSE_TIMEOUT instead.
    """
    result: list[tuple[KNXIPFrame, bytes] | BaseException] = []

    def _parse() -> None:
        try:
            result.append(KNXIPFrame.from_knx(raw))
        except BaseException as err:  # pylint: disable=broad-exception-caught
            result.append(err)

    thread = threading.Thread(target=_parse, daemon=True)
    thread.start()
    thread.join(PARSE_TIMEOUT)
    if thread.is_alive():
        pytest.fail(f"KNXIPFrame.from_knx() did not return for {raw.hex()}")
    if isinstance(result[0], BaseException):
        raise result[0]
    return result[0][0]


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(
            bytes.fromhex("06 10 02 04 00 08 00 03"),
            id="description_response_dib_length_0",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 04 00 08 01 03"),
            id="description_response_dib_length_1",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 02 00 10 08 01 C0 A8 2A 0A 0E 57 00 02"),
            id="search_response_dib_length_0",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 02 00 10 08 01 C0 A8 2A 0A 0E 57 01 02"),
            id="search_response_dib_length_1",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 02 00 10 08 01 C0 A8 2A 0A 0E 57 10 02"),
            id="search_response_dib_longer_than_frame",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 0C 00 10 08 01 C0 A8 2A 0A 0E 57 00 07"),
            id="search_response_extended_tunneling_info_length_0",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 02 00 12 08 01 C0 A8 2A 0A 0E 57 04 02 EE 01"),
            id="search_response_unknown_service_family",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 04 00 08 36 01") + bytes(52),
            id="description_response_device_info_truncated",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 04 00 3C 36 01 03") + bytes(51),
            id="description_response_unknown_knx_medium",
        ),
        pytest.param(
            bytes.fromhex("06 10 05 30 00 00"),
            id="total_length_0",
        ),
        pytest.param(
            bytes.fromhex("06 10 05 30 00 00 06 10 05 30 00 11 29 00 bc e0 00 01 00 01 01 00 80"),
            id="total_length_0_with_trailing_frame",
        ),
        pytest.param(
            bytes.fromhex("06 10 05 30 00 05 00"),
            id="total_length_5",
        ),
        pytest.param(bytes.fromhex("06 10 04 20 00 06"), id="tunnelling_request_empty"),
        pytest.param(bytes.fromhex("06 10 04 21 00 06"), id="tunnelling_ack_empty"),
        pytest.param(
            bytes.fromhex("06 10 04 21 00 0A 04 2A 17 55"),
            id="tunnelling_ack_unknown_status",
        ),
        pytest.param(
            bytes.fromhex("06 10 03 10 00 06"), id="device_configuration_request_empty"
        ),
        pytest.param(
            bytes.fromhex("06 10 03 11 00 06"), id="device_configuration_ack_empty"
        ),
        pytest.param(bytes.fromhex("06 10 05 32 00 06"), id="routing_busy_empty"),
        pytest.param(
            bytes.fromhex("06 10 05 31 00 06"), id="routing_lost_message_empty"
        ),
        pytest.param(bytes.fromhex("06 10 02 06 00 06"), id="connect_response_empty"),
        pytest.param(
            bytes.fromhex("06 10 02 06 00 08 01 55"),
            id="connect_response_unknown_status",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 08 00 08 01 55"),
            id="connectionstate_response_unknown_status",
        ),
        pytest.param(
            bytes.fromhex("06 10 02 0A 00 08 01 55"),
            id="disconnect_response_unknown_status",
        ),
        pytest.param(
            bytes.fromhex("06 10 04 22 00 06"), id="tunnelling_feature_get_empty"
        ),
        pytest.param(
            bytes.fromhex("06 10 04 23 00 0e 04 01 17 55 03 00 01 00"),
            id="tunnelling_feature_response_unknown_status",
        ),
        pytest.param(
            bytes.fromhex("06 10 04 23 00 0e 04 01 17 00 EE 00 01 00"),
            id="tunnelling_feature_response_unknown_feature_type",
        ),
        pytest.param(
            bytes.fromhex("06 10 05 33 00 0a 00 00 00 00"),
            id="unknown_service_type",
        ),
    ],
)
def test_malformed_frame_raises(raw: bytes) -> None:
    """Test malformed KNX/IP frames raise CouldNotParseKNXIP and do not hang."""
    with pytest.raises(CouldNotParseKNXIP):
        parse_guarded(raw)


def test_unknown_dib_type_code_is_generic() -> None:
    """Test a DIB with an unknown (vendor) description type code is kept as DIBGeneric."""
    raw = bytes.fromhex("06 10 02 04 00 0A 04 80 AB CD")
    frame = parse_guarded(raw)
    assert isinstance(frame.body, DescriptionResponse)
    assert len(frame.body.dibs) == 1
    dib = frame.body.dibs[0]
    assert isinstance(dib, DIBGeneric)
    assert dib.dtc == 0x80
    assert dib.data == bytes.fromhex("AB CD")
