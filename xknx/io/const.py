"""KNX Constants used within io."""

from typing import Final

from xknx.telegram.address import IndividualAddress

DEFAULT_INDIVIDUAL_ADDRESS: Final = IndividualAddress("15.15.250")
DEFAULT_MCAST_GRP: Final = "224.0.23.12"
DEFAULT_MCAST_PORT: Final = 3671

# The client shall send a CONNECTIONSTATE_REQUEST every 60 seconds; the server
# shall answer within 10 seconds - KNX v01.06.02 - Core 03.08.02 - §5.4.
CONNECTIONSTATE_REQUEST_TIMEOUT: Final = 10
HEARTBEAT_RATE: Final = 60

# A DeviceConfigurationRequest that stays unacknowledged for this long is
# repeated this many times, after which the connection is terminated.
DEVICE_CONFIGURATION_REQUEST_TIMEOUT: Final = 10
DEVICE_CONFIGURATION_REQUEST_REPETITIONS: Final = 3

# Maximum time an authenticated secure session may remain unused (without
# any communication over this session) until the session will be dropped.
SESSION_TIMEOUT: Final = 60
SESSION_KEEPALIVE_RATE: Final = SESSION_TIMEOUT - 10
XKNX_SERIAL_NUMBER: Final = bytes.fromhex("00 00 78 6b 6e 78")
