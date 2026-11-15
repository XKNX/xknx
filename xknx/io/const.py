"""KNX Constants used within io."""

from typing import Final

from xknx.telegram.address import IndividualAddress

DEFAULT_INDIVIDUAL_ADDRESS: Final = IndividualAddress("15.15.250")
DEFAULT_MCAST_GRP: Final = "224.0.23.12"
DEFAULT_MCAST_PORT: Final = 3671

# Time to wait for a TCP connection to a KNXnet/IP server to be established.
TCP_CONNECT_TIMEOUT: Final = 10

# The client shall send a CONNECTIONSTATE_REQUEST regularly, i.e. every 60 seconds;
# the server shall answer within 10 seconds - KNX v01.06.02 - Core 03.08.02 - §5.4.
# ETS 6 sends one every 30 seconds (ETS 5: 60 seconds), which halves the time
# until a dead connection is noticed.
CONNECTIONSTATE_REQUEST_TIMEOUT: Final = 10
HEARTBEAT_RATE: Final = 30

# A DeviceConfigurationRequest that stays unacknowledged for this long is
# repeated this many times, after which the connection is terminated.
DEVICE_CONFIGURATION_REQUEST_TIMEOUT: Final = 10
DEVICE_CONFIGURATION_REQUEST_REPETITIONS: Final = 3

# Maximum time an authenticated secure session may remain unused (without
# any communication over this session) until the session will be dropped -
# KNX v01.01.02 - KNX IP Secure 03.08.09 - §2.2.3.5.2.1.1 timeoutSession.
SESSION_TIMEOUT: Final = 60
# The specification only requires the keepalive to be sent before the session
# timeout elapses. ETS sends one every 14 (ETS 5) / 15 (ETS 6) seconds of
# inactivity, leaving a wide margin for latency instead of 10 seconds.
SESSION_KEEPALIVE_RATE: Final = 15
XKNX_SERIAL_NUMBER: Final = bytes.fromhex("00 00 78 6b 6e 78")
