"""KNX Constants used within io."""

DEFAULT_MCAST_GRP = "224.0.23.12"
DEFAULT_MCAST_PORT = 3671

CONNECTION_ALIVE_TIME = 120
CONNECTIONSTATE_REQUEST_TIMEOUT = 10
HEARTBEAT_RATE = CONNECTION_ALIVE_TIME - (CONNECTIONSTATE_REQUEST_TIMEOUT * 5)

# Maximum time an authenticated secure session may remain unused (without
# any communication over this session) until the session will be dropped.
SESSION_TIMEOUT = 60
SESSION_KEEPALIVE_RATE = SESSION_TIMEOUT - 10
XKNX_SERIAL_NUMBER = bytes.fromhex("00 00 78 6b 6e 78")
