---
layout: default
title: Changelog
nav_order: 2
---

# Changelog

# Unreleased changes

### Secure

- Parse `project_name` from an ETS Keyring.

### Internal

- Use ruff isort plugin, remove isort from requirements.

# 2.11.2 DPT 9 small negative fix 2023-07-24

### Bugfixes

- Fix DPT 9 handling of values < `0` and >= `-0.005`. These are now rounded to `0` instead of being sent as `-20.48`.

# 2.11.1 DateTime fix 2023-06-26

### Bugfixes

- Fix processing custom time data in DateTime devices.

# 2.11.0 DateTime state 2023-06-25

### Devices

- Add group_address_state, respond_to_read and sync_state arguments to DateTime devices.
- Add DPT 9 support for Light color temperature.

### Internals

- Remove pydocstyle and flake8 plugins, add pytest-icdiff to testing requirements.

# 2.10.0 Tunnelling Feature 2023-05-08

### Protocol

- Support Tunnelling Feature service messages.

# 2.9.0 Spring cleanup 2023-04-22

### Dependencies

- For Python <3.11 dependency `async_timeout` is added as backport for `asyncio.timeout`.

### Internals

- Replace `asyncio.wait_for` with `asyncio.timeout`.
- Add Ruff to pre-commit and tox.
- Use pyproject.toml for specifying project metadata.

# 2.8.0 Hostnames 2023-04-12

### Connection

- Resolve IP addresses from hostname or adapter name for `gateway_ip` or `local_ip`.

### Bugfixes

- Handle empty list for group addresses in RemoteValue.

### Internals

- Refactor DPTBase transcoder classes
  - Accept `DPTArray` or `DPTBinary` in `DPTBase.from_knx()` instead of raw `tuple[int]`.
  - Return `DPTArray` or `DPTBinary` from `DPTBase.to_knx()` instead of `tuple[int, ...]`.
  - Remove payload_valid() from RemoteValue and remove payload type form its generics parameters.

# 2.7.0 IP Device Management 2023-03-15

### Protocol

- Add support for Device Management Configuration service.
- Support CEMI M_Prop messages.
- Don't ignore CEMIFrames with source address equal to `xknx.current_address`.

### Internals

- Use CEMILData instead of CEMIFrame in DataSecure.
- Move `init_from_telegram()` from CEMIFrame to CEMILData. `telegram()` is now a method of CEMILData instead of a property of CEMIFrame.

# 2.6.0 Connection information 2023-02-27

### Connection

- When `ConnectionConfig.individual_address` is set and a Keyring is given `ConnectionType.AUTOMATIC` will try to connect to the host of this address. If not found (in keyfile or discovery) it will raise.
- Add CEMIFrame counters connection type and timestamp of connection start.

### Internals

- Lower log levels for unsupported Telegrams and add more information.
- Move CEMIFrame parsing from Interface to CEMIHandler.

# 2.5.0 Request IA 2023-02-14

### Connection

- Use only Interfaces listed in Keyring when `ConnectionType.AUTOMATIC` is used and a Keyring is configured.
- Request specific tunnel by individual address for TCP connections when `ConnectionConfig.individual_address` is set.

### Bugfixes

- Parse Data Secure credentials form Keyring from non-IP-Secure interfaces.
- Parse Data Secure credentials from Keyrings exported for specific interfaces.
- Fix callback for Cover target position when called with same value consecutively.
- Fix Windows TCP transport bug when using IP Secure Tunnelling.
- Don't create unreferenced asyncio Tasks. `xknx.task_registry.background()` can now be used to create background tasks.

### Protocol

- Support Extended Connection Request Information (CRI) for requesting a specific individual address on Tunnelling v2.
- Add Core v2 Error Code definitions.

### Cleanups

- Accept `str | os.PathLike` for Keyring path. Previously only `str`.
- Rename `_load_keyring` to `sync_load_keyring` to make it public e.g. when it should be used from an executor.
- Update CI. Use `codespell` and `flake8-print`.

# 2.4.0 Data Secure 2023-02-05

### Data Secure

- Support KNX Data Secure for group communication. Keys are sourced from an ETS keyring file.

### Bugfixes

- Fix wrong string length in keyfile signature verification for multi-byte UTF-8 encoded attribute values.

### Internals

- `destination_address` in `Telegram` init is no longer optional.
- `timestamp` attribute in `Telegram` is removed.
- Rename `xknx.secure.ip_secure` to `xknx.secure.security_primitives`.
- Return `bytes` from `BaseAddress.to_knx()` instead of `tuple[int, int]`. This is used in `IndividualAddress` and `GroupAddress`.
- Add `BaseAddress.from_knx()` to instantiate from `bytes`, remove instantiation form `tuple[int, int]`.
- Refactor APCI to return complete Subclass `APCI.from_knx()` and removed `APCI.resolve_apci()`.

# 2.3.0 Routing security, DPTs and CEMI-Refactoring 2023-01-10

### DPTs

- Add definitions for DPTs
  - 7.010 "prop_data_type"
  - 8.012 "length_m"
  - 9.009 "air_flow"
  - 9.029 "absolute_humidity"
  - 9.030 "concentration_ugm3"
  - 12.001 "pulse_4_ucount"
  - 12.100 "long_time_period_sec"
  - 12.101 "long_time_period_min"
  - 12.102 "long_time_period_hrs"
  - 13.016 "active_energy_mwh"
  - 14.080 "apparent_power"

### IP Secure

- SecureRouting: verify MAC of received TimerNotify frames.
- SecureRouting: verify and handle timer value of received SecureWrapper frames after verification of MAC.
- SecureRouting: Discard received unencrypted RoutingIndication frames.

### Internals

- Move `CEMIFrame`, `CEMIFlags` and `CEMIMessageCode` to xknx.cemi package.
- Remove `CEMIFrame.telegram` setter in favour of `init_from_telegram()` staticmethod; convert `from_knx()` and `from_knx_data_link_layer()` to staticmethods returning a CEMIFrame.
- Remove default values for `CEMIFrame` constructor.
- Parse T_Data_Broadcast TPCI. Forward these telegrams to the Management class.
- KNXIPHeader total_length is 2 bytes long. There are no reserved bytes.
- Revert handling L_Data.req frames for incoming device management requests.
- Decouple CEMIFrame handling from IP interface
  - Add CEMIHandler class. This class handles incoming CEMIFrames and dispatches them to the upper layers as Telegram objects and creates CEMIFrames from Telegram objects to be sent to the network.
  - Use `CEMIFrame` instead of `Telegram` in KNXIPInterface.

# 2.2.0 Expose cooldown 2022-12-27

### Devices

- ExposeSensor: Add `cooldown` option to allow rate-limiting of sent telegrams.
- ExposeSensor: Add `respond_to_read` option.

### Connection

- Disconnect when tunnelling sequence number (UDP) gets out of sync.

### Internals

- Add `task.done()` to TaskRegistry tasks.
- Decouple KNXIPFrame parsing from CEMIFrame parsing. TunnellingRequest and RoutingIndication now carry the raw cemi frame payload as bytes. This allows decoupled CEMIFrame parsing at a later time (in Interface class rather than in KNXIPTransport class) for better error handling and upcoming features.
- Make KNXIPFrame body non-optional. Return KNXIPFrame object and remaining bytes from `KNXIPFrame.from_knx()` staticmethod.
- Add new logger `xknx.cemi` for incoming and outgoing CEMIFrames.
- Remove timestamp and line break in knx and raw logger.

# 2.1.0 Enhance notification device 2022-11-29

### Devices

- Notification: Add `respond_to_read` option.
- Notification: Rename `self._message` to `self.remote_value`.

# 2.0.0 Find and Connect 2022-11-25

### Interface changes

- Removed `own_address` from `XKNX` class. `ConnectionConfig` `individual_address` can be used to set a source address for routing instead.
  If set for a secure tunnelling connection, a tunnel with this IA will be read from the knxkeys file.
- Disable TelegramQueue rate limiting by default.
- Separate discovery multicast group from routing group. Add `multicast_group` and `multicast_port` `ConnectionConfig` parameters.

### Connection and Discovery

- Use manually configured IP secure tunnel password over loading it from keyring.
- GatewayScanFilter now also matches secure enabled gateways by default. The `secure` argument as been replaced by `secure_tunnelling` and `secure_routing` arguments. When multiple methods are `True` a gateway is matched if one of them is supported. Non-secure methods don't match if secure is required for that gateway.
- Self description queries more information from Core v2 devices via SearchRequestExtended.

### Features

- Add support for python 3.11
- Add methods to Keyring to get interfaces by individual address (host or tunnel).

### Internal

- Remove `InterfaceWithUserIdNotFound` and `InvalidSignature` errors in favor of `InvalidSecureConfiguration`.
- Keyring: rename `load_key_ring` to `load_keyring` and make it a coroutine.

### Management

- Fix APCI service parsing for 10bit control fields.
- Set reasonable default count values for APCI classes.
- Set xknx.current_address for routing connections so management frames received over Routing are handled properly.
- Fix wrong length of AuthorizeRequest.
- Raise sane error messages in Management.

# Bugfixes

- No mutable default arguments. Fixes unexpected behaviour like GatewayScanner not finding all interfaces.

# 1.2.1 Hotfix release 2022-11-20

### Bugfixes

- Fix Latency parsing in .knxkeys keyring files

# 1.2.0 Secure Routing 2022-10-10

### Features

- We now support KNXnet/IP Secure multicast communication (secure routing) in addition to tunnelling!
  Thanks to Weinzierl for providing us a router for testing purposes!
- Parse `latency` from a .knxkeys keyring files `Backbone` tag.
- Use `multicast_group` from a .knxkeys keyring files `MulticastAddress` tag (Routing).
- Support InternalGroupAddress in xknx.tools package.

### Protocol

- Add TimerNotify frame parser

## 1.1.0 Routing flow control 2022-09-26

### Added

- Convenience functions for KNX group communication (`xknx.tools`)

### Routing

- Support flow control for routing

### Protocol

- Add RoutingBusy frame parser
- Add RoutingLostMessage frame parser

## 1.0.2 Route-back reconnect 2022-08-31

### Bugfixes

- Fix expected sequence counter reset for UDP Tunnelling connections with route_back enabled.

## 1.0.1 Handle UDP hickups 2022-08-24

### Bugfixes

- Correctly retry sending a TunnellingRequest if no TunnellingAck was received for the first time for UDP tunnelling connections.
- Ignore repeated TunnellingRequests received from UDP tunnelling connections.
- Properly log repeated heartbeat errors

## 1.0.0 Support for lukewarm temperatures 2022-08-13

### Internal

- Fix DPT2ByteFloat numeric range issues
- Fix keyring parsing
- We can now correctly parse 20,48 °C thus xknx is now a stable library

## 0.22.1 Wrong delivery 2022-07-29

### Management

- Ignore received telegrams addressed to individual addresses other than XKNXs current address

## 0.22.0 Management 2022-07-26

### Management

- Add support for creating point-to-point connections to do device management
- Add `nm_individual_address_check` procedure to check if an individual address is in use on the network
- Add `dm_restart` procedure to request a basic restart of a device
- Remove PayloadReader class. Management procedure functions should be used to request data from individual devices.

### Internals

- Optionally return a list of Telegrams to be sent to an incoming request as reply. This is used for incoming device management requests. Callbacks for incoming requests (in Interface subclasses) are now handled in an asyncio Task.
- Incoming L_DATA.req frames are confirmed (L_DATA.con) and replies / acks are sent as L_DATA.ind

## 0.21.5 Secure discovery bugfix 2022-06-28

### Bugfix

- Fix GatewayDescriptor parsing when SearchResponseExtended DIBs are in unexpected order

## 0.21.4 Fan out 2022-06-07

### Devices

- Fan: Add support for dedicated on/off switch GA
- Sensor: Set `unit_of_measurement` for DPTString to `None`

### Internals

- Lock sending telegrams via a Tunnel until a confirmation is received
- Use device subclass for `device_updated_cb` callback argument type hint
- Fix CEMI Frame Ack-request flag set wrongly

## 0.21.3 Cover updates 2022-05-17

### Devices

- Cover: call `device_updated_cb` periodically when cover is moving
- Cover: auto-send a stop for covers not supporting setting position
- Cover: add `invert_updown` option to decouple updown from position
- Cover: fix travel time prediction when receiving updates from bus while moving

### Protocol

- Parse and encode different TPCI in a CEMIFrame or Telegram
- Set priority "System" flag for point-to-point CEMI frames initialized by a Telegram

## 0.21.2 IP Secure Bug fixes 2022-05-04

### Bugfixes

- IP Secure: Fix MAC calculation for 22-byte payloads
- IP Secure: Fix Keyring loading

### Internals

- Rename TaskRegistry.register and Task `task` attribute to `async_func` to avoid confusion; return Task from `start()`

## 0.21.1 Fix Task Registry 2022-05-01

### Bugfixes

- Fix exposure of datetime, time and date objects to the Bus again

### Internals

- TaskRegistry takes functions returning coroutines instead of coroutines directly

## 0.21.0 Search and connect 2022-04-30

### Discovery

- Use unicast discovery endpoint to receive SearchRespones frames
- Send SearchRequest and SearchRequestExtended simultaneously when using GatewayScanner
- Skip SearchResponse results for Core-V2 devices - wait for SearchResponseExtended
- Identify interfaces having KNX IP Secure Tunneling required and skip if using Automatic connection mode
- Only send SearchRequests from one interface for each `scan()` call
- Connect to next found interface in case of unsuccessful initial connection when using "automatic" mode

### Internals

- Use `ifaddr` instead of `netifaces`
- make HPAI hashable and add `addr_tuple` convenice property

## 0.20.4 Fix exposure of time and date 2022-04-20

### Bugfixes

- Fix exposure of datetime, time and date objects to the Bus

### Protocol

- Add DIBSecuredServiceFamilies and DIBTunnelingInfo parser

### Internal

- Include base class in `DPTBase.parse_transcoder()` lookup
- Move `levels` instance attribute form `GroupAddress` to `address_format` class variable
- Remove xknx form every class in the knxip package: CEMIFrame, KNXIPFrame and KNXIPBody (and subclasses)
- Remove xknx form every class in the io.request_response package
- Remove xknx form io.transport package and io.secure_session and io.self_description modules

## 0.20.3 Threading fixes 2022-04-15

### Devices

- Notification: add `value_type` argument to set "string" or "latin_1" text encoding

### Bug fixes

- Fix call from wrong thread in ConnectionManager
- Fix thread leak when restarting XKNX

### Internal

- Change RemoteValueString to _RemoteValueGeneric subclass

## 0.20.2 Handle shutdown properly 2022-04-11

### Bug fixes

- Properly shutdown climate mode if climate.shutdown() is called and ClimateMode exists

## 0.20.1 Add support for DPT 16.001 and SearchRequestExtended 2022-04-05

### Features

- Add support for SearchRequestExtended to find interfaces that allow IP Secure
- Use XKNX `state_updater` argument to set default method for StateUpdater. StateUpdater is always started - Device / RemoteValue can always opt in to use it, even if default is `False`.
- Add support for DPT 16.001 (DPT_String_8859_1) as `DPTLatin1` with value_type "latin_1".

### Bug fixes

- Stop SecureSession keepalive_task when session is stopped (and don't restart it from sending STATUS_CLOSE)
- Fix encoding invalid characters for DPTString (value_type "string")

## 0.20.0 IP Secure 2022-03-29

### Features

- We now support IP Secure!
  Thanks to MDT for providing us an interface for testing purposes!
- Add support for requesting tunnel interface information

### Protocol

- add SessionRequest, SessionResponse, SessionAuthenticate, SessionStatus, SecureWrapper Frame parser

### Internals

- Drop support for Python 3.8 to follow Home Assistant changes
- Return `bytes` from to_knx() in knxip package instead of `list[int]`
- Add a callback for `connection_lost` of TCP transports to Tunnel

## 0.19.2 TCP Heartbeat 2022-02-06

### Connection

- Do a ConnectionStateRequest heartbeat on TCP tunnel connections too

### Devices

- Handle invalid payloads per RemoteValue, log a readable warning

## 0.19.1 Bugfix for route_back 2022-01-31

### Connection

- Tunneling: Fix route_back connections sending to invalid address

### Protocol

- add DescriptionRequest and DescriptionResponse Frame parser

## 0.19.0 Tunneling connection protocol 2022-01-18

### Devices

- Handle ConversionError in RemoteValue, log a readable warning

### Connection

- Raise if an initial connection can not be established, auto-reconnect only when the connection was successful once
- Add support for TCP tunnel connections
- Optionally run KNXIPInterface in separate thread
- Handle separate Tunneling control and data endpoints
- Fix rate limiter wait time: don't add time waiting for ACK or L_DATA.con frames to the rate_limit

## Internals

- Some refactoring and code movement in the io module - especially in KNXIPInterface; renamed UDPClient to UDPTransport
- Cleanup some list generating code in the knxip module

## 0.18.15 Come back almighty Gateway Scanner 2021-12-22

### Internals

- Fix Gateway Scanner on Linux

## 0.18.14 Tunnelling flow control 2021-12-20

### Internals

- Tunnel: Implement flow control according to KNX spec recommendations: wait for L_DATA.con frame before sending next L_DATA.req with 3 second timeout
- Logging: Some changes to loggers like `knx` now includes the source/destination HPAI and a timestamp
- Fix a rare race-condition in the gateway scanner where a non-existing interface was queried

## 0.18.13 Hold your colour 2021-11-13

### Internals

- Fix GatewayScanner on MacOS and Windows and only return one instance of a gateway

### Devices

- Light: Only send to global switch or brightness address if individual colors are configured to not overwrite actuator colors
- Light: Debounce individual colors callback to mitigate color flicker in visualizations

## 0.18.12 Add always callback to NumericValue and RawValue 2021-11-01

### Internals

- Gatewayscanner now also reports the individual address of the gateway
- Outgoing telegrams will now have the correct source_address if tunneling is used

### Devices

- Added `always_callback` option to NumericValue and RawValue

## 0.18.11 Task Registry 2021-10-16

### Internals

- Stop state updater if connection is lost and restart if restored
- Add central task registry to keep track of tasks spawned in devices

## 0.18.10 Connection Manager 2021-10-13

### Internals

- DPTString: replace invalid characters with question marks in `to_knx`
- Catch and log exceptions raised in callbacks to not stall the TelegramQueue
- Handle callbacks in separate asyncio Tasks
- GatewayScanFilter: Ignore non-gateway KNX/IP devices
- Introduce connection state change handler

### Home Assistant Plugin

- Properly handle disconnected state in the UI.

## 0.18.9 HS-color 2021-07-26

### Devices

- Light: Support for HS-color (DPT 5.003 hue and 5.001 saturation)

## 0.18.8 Position-only cover 2021-06-30

### Devices

- Cover: enable `set_up` and `set_down` with `group_address_position` only (without `group_address_long`).

## 0.18.7 RawValue 2021-06-18

### Devices

- Add RawValue device.
- Remove unused HA-specific attributes (unique_id, device_class, create_sensors).
- Climate: add `group_address_active_state`, `group_address_command_value_state` and a `is_active` property.
- Configurable `sync_state` in all devices.

## 0.18.6 NumericValue 2021-06-11

### Devices

- Add `respond_to_read` option to Switch. If `True` GroupValueRead telegrams addressed to the `group_address` are answered.
- Add NumericValue device.

### Internals

- Add RemoteValueNumeric for values of type `float | int`.
- Fix DPTBase classmethod return types

## 0.18.5 DPTNumeric 2021-06-08

### Internals

- `DPTBase.parse_transcoder` is now a classmethod to allow parsing only subclasses.
- Add `DPTNumeric` as base class for DPTs representing numeric values.

## 0.18.4 ClimateMode bugfix 2021-06-04

### Bugfix

- ClimateMode: Fix telegram processing when operation_mode and controller_mode (heat/cool) are both used

## 0.18.3 XYY colors 2021-05-30

### Devices

- Light: Support for xyY-color (DPT 242.600)

## 0.18.2 Climate and Light improvements 2021-05-11

### Devices

- Climate: Make `setpoint_shift_mode` optional. When `None` assign its DPT from the first incoming payload.
- Light: Support individual color lights without switch object

## 0.18.1 Internal group addresses 2021-04-23

### Devices

- Add InternalGroupAddress for communication between Devices without sending to the bus.

### Internals

- RemoteValue.value changed to a settable property. It is used to create payloads for outgoing telegrams.
- RemoteValue.update_value (async) sets a new value and awaits the callbacks without sending to the bus.
- Round DPT 14 values to precision of 7 digits

## 0.18.0

## Devices

- Add support for cover lock
- ExposeSensor values can now be read from other xknx devices that share a group address
- Add more information to sensors and binary sensors in the HA integration

### Breaking Changes

- Remove configuration handling from core library (use https://xknx.io/config-converter)

### Internals

- Drop support for python 3.7
- use pytest tests instead of unittest TestCase
- Move RequestResponse and subclasses to xknx.io.request_response.*
- Move ConnectionConfig to xknx.io.connection
- Store last Telegram and decoded value in RemoteValue
- Improve CI to use Codecov instead of Coveralls for code coverage reports

## 0.17.5 Add support for unique ids 2021-03-30

### HA integration

- Add experimental (opt-in) support for unique ids

### Internals

- Remove unfinished config v2

## 0.17.4 Bugfix for ValueReader 2021-03-26

### Internals

- Comparing GroupAddress or IndividualAddress to other types don't raise TypeError anymore
- Specify some type annotations

## 0.17.3 Passive addresses 2021-03-16

### Devices

- Accept lists of group addresses using the heads for group_address / group_address_state and the tails for passive_group_addresses in every Device (and RemoteValue)
- Sensor: Don't allow floats in DPTBase value_type parser

## 0.17.2 Value templates 2021-03-10

### Devices

- BinarySensor, Sensor: add `ha_value_template` attribute to store HomeAssistant value templates

### Internals

- Distribute type annotations

## 0.17.1 Cover up 2021-02-23

### Devices

- Cover: Use correct step direction when stopping

### Internals

- Convert all Enums to upper case to satisfy pylint

## 0.17.0 Route back 2021-02-19

### New Features

- Add new optional config `route_back` for connections to be able to work behind NAT.
- Read env vars after reading config file to allow dynamic config.

### HA integration

- knx_event: fire also for outgoing telegrams

### Devices

- BinarySensor: return `None` for `BinarySensor.counter` when context timeout is not used (and don't calculate it)
- Climate: Add `create_temperature_sensors` option to create dedicated sensors for current and target temperature.
- Weather (breaking change!): Renamed `expose_sensors` to `create_sensors` to prevent confusion with the XKNX `expose_sensor` device type.
- Weather: Added wind bearing attribute that accepts a value in degrees (0-360) for determining wind direction.

### Internals

- RemoteValue is Generic now accepting DPTArray or DPTBinary
- split RemoteValueClimateMode into RemoteValueControllerMode and RemoteValueOperationMode
- return the payload (or None) in RemoteValue.payload_valid(payload) instead of bool
- Light colors are represented as `Tuple[Tuple[int,int,int], int]` instead of `Tuple[List[int], int]` now
- DPT 3 payloads/values are not invertable anymore.
- Tunnel: Interface changed - gateway_ip, gateway_port before local_ip, local_port added with default `0`.
- Tunnel: default `auto_reconnect`to True

## 0.16.3 Fan contributions 2021-02-06

### Devices

- Fan: Add `max_step` attribute which defines the maximum amount of steps. If set, the fan is controlled by steps instead of percentage.
- Fan: Add `group_address_oscillation` and `group_address_oscillation_state` attributes to control the oscillation of a fan.

## 0.16.2 Bugfix for YAML loader 2021-01-24

### Internals

- fix conflict with HA YAML loader

## 0.16.1 HA register services 2021-01-16

### HA integration

- knx_event: renamed `fire_event_filter` to `event_filter` and deprecated `fire_event` config option. A callback is now always registered for HA to be able to modify its `group_addresses` filter from a service.
- added `knx.event_register` service allowing to add and remove group addresses to trigger knx_event without having to change configuration.
- added `knx.exposure_register` service allowing to add and remove ExposeSensor instances at runtime

### Internals

- remove DPTComparator: DPTBinary and DPTArray are not equal, even if their .value is, and are never equal to `None`.
- add Device.shutdown() method (used eg. when removing ExposeSensor)
- TelegramQueue.Callback: add `group_addresses` attribute to store a list of GroupAddress triggering the callback (additionally to `address_filters`).
- add a lot of type annotations

## 0.16.0 APCI possibilities considerably increased 2021-01-01

### Devices

- Sensor: add DPT-3 datatypes "stepwise_dimming", "stepwise_blinds", "startstop_dimming", "startstop_blinds"
- Light: It is now possible to control lights using individual group addresses for red, green, blue and white

### HA integration

- knx_event: renamed `address` to `destination` and added `source`, `telegramtype`, `direction` attributes.

### Internals

- Tunnel connections process DisconnectRequest now and closes/reconnects the tunnel when the other side closes gracefully
- XKNX.connected Event can be used in future to await for a working connection or stop/relaunch tasks if the connection is lost
- Lower heartbeat rate from every 15sec to every 70 sec and raise ConnectionstateRequest timeout from 1 to 10sec (3/8/1 KNXip Overview §5.8 Timeout Constants)
- clean up Tunnel class
- refactored timeout handling in GatewayScanner, RequestResponse and ValueReader.
- renamed "PhysicalAddress" to "IndividualAddress"
- Telegram: `group_address` renamed to `destination_address`, to prepare support for other APCI services and add `source_address`
- Telegram: remove `Telegram.telegramtype` and replace with payload object derived from `xknx.telegram.apci.APCI`.
- CEMIFrame: remove `CEMIFrame.cmd`, which can be derived from `CEMIFrame.payload`.
- APCI: extend APCI services (e.g. `MemoryRead/Write/Response`, `PropertyRead/Write/Response`, etc).
- Farewell Travis CI; Welcome Github Actions!
- StateUpdater allow float values for `register_remote_value(tracker_options)` attribute.
- Handle exceptions from received unsupported or not implemented KNXIP Service Type identifiers

## 0.15.6 Bugfix for StateUpater 2020-11-26

### Bugfixes

- StateUpdater: shield from cancellation so update_received() don't cancel ongoing RemoteValue.read_state()

## 0.15.5 A Telegram for everyone 2020-11-25

### Internals

- process every incoming Telegram in all Devices, regardless if a callback for the GA is registered (eg. StateUpdater) or not.

### Bugfixes

- StateUpdater: always close the update task before starting a new in StateTracker
- Cover: separate target and state position RemoteValue to fix position update from RemoteValue and call `after_update()`

## 0.15.4 Bugfix for switch 2020-11-22

### Devices

- Light, Switch: initialize state with `None` instead of `False` to account for unknown state.
- Cover: `device_class` may be used to store the type of cover for Home-Assistant.
- HA-Entity Light, Switch, Cover: initialize with `assumed_state = True` until we have received a state.

### Bugfixes

- Switch.after_update was not called from RemoteValueSwitch.read_state (StateUpdater). Moved Switch.state to RemoteValue again.
- StateUpdater: query less aggressive - 2 parallel reads with 2 seconds timeout (instead of 3 - 1).

## 0.15.3 Opposite day! 2020-10-29

### Devices

- BinarySensor: added option to invert payloads
- BinarySensor: `ignore_internal_state` and counter are only applied to GroupValueWrite telegrams, not GroupValueRespond.
- BinarySensor: if `context_timeout` is set `ignore_internal_state` is set to True.
- Switch: added option to invert payloads

### Bugfixes

- HA Switch entity: keep state without state_address
- Cover: fix `set_position` without writable position / auto_stop_if_necessary
- handle unsupported CEMI Messages without losing tunnel connection

## 0.15.2 Winter is coming

### Devices

- ClimateMode: Refactor climate modes in operation_mode and controller_mode, also fixes a bug for binary operation modes where the mode would be set to AWAY no matter what value was sent to the bus.
- Sensor: Add `always_callback` option
- Switch: Allow resetting switches after x seconds with the new `reset_after` option.

### Internals

- StateUpdater: Only request 3 GAs at a time.
- RemoteValue: Add support for passive group addresses

## 0.15.1 bugfix for binary sensors

### Devices

- BinarySensor: `reset_after` expects seconds, instead of ms now (to use same unit as `context_timeout`)
- Binary Sensor: Change the default setting `context_timeout` for binary sensor from 1.0 to 0.0 and fixes a bug that would result in the update callback being executed twice thus executing certain automations in HA twice for binary sensor from 1.0 to 0.0 and fixes a bug that would result in the update callback being executed twice thus executing certain automations in HA twice.

## 0.15.0 Spring cleaning and quality of life changes

### Logging

- An additional `log_directory` parameter has been introduced that allows you to log your KNX logs to a dedicated file. We will likely silence more logs over the time but this option will help you and us to triage issues easier in the future. It is disabled by default.

### Internals

- The heartbeat task, that is used to monitor the state of the tunnel and trigger reconnects if it doesn't respond, is now properly stopped once we receive the first reconnect request
- `XKNX.start()` no longer takes arguments. They are now passed directly to the constructor when instantiating `XKNX()`
- Support for python 3.6 has been dropped
- XKNX can now be used as an asynchronous context manager
- Internal refactorings
- Improve test coverage

## 0.14.4 Bugfix release

### Devices

- Don't set standby operation mode if telegram was not processed by any RemoteValue
- Allow covers to be inverted again
- Correctly process outgoing telegrams in our own devices

## 0.14.3 Bugfix release

### Internals

- Make connectivity less noisy on connection errors.

## 0.14.2 Bugfix release

### Bugfixes

- Correctly reset the counter of the binary sensor after a trigger.

## 0.14.1 Bugfix release

### Bugfixes

- Use correct DPT 9.006 for the air pressure attribute of weather devices
- Reset binary sensor counters after the context has been timed out in order to be able to use state change events within HA
- Code cleanups

## 0.14.0 New sensor types and refactoring of binary sensor automations

### Breaking changes

- Binary sensor automations within the home assistant integration have been refactored to use the HA built in events as automation source instead of having the automation schema directly attached to the sensors. (Migration Guide: https://xknx.io/migration_ha_0116.html)

### New Features

- Add support for new sensor types DPT 12.1200 (DPT_VolumeLiquid_Litre) and DPT 12.1201 (DPTVolumeM3).
- Weather devices now have an additional `brightness_north` GA to measure the brightness. Additionally, all sensor values are now part of the HA device state attributes for a given weather device.

### Bugfixes

- Fix hourly broadcasting of localtime

### Internals

- Allow to pass GroupAddress and PhysicalAddress objects to wherever an address is acceptable.
- Stop heartbeat and reconnect tasks before disconnecting

## 0.13.0 New weather device and bugfixes for HA integration

### Deprecation notes

- Python 3.5 is no longer supported

### New Features

- Adds support for a weather station via a dedicated weather device
- support for configuring the previously hard-coded multicast address (@jochembroekhoff #312)

### Internals

- GatewayScanner: Passing None or an integer <= 0 to the `stop_on_found` parameter now causes the scanner to only stop once the timeout is reached (@jochembroekhoff #311)
- Devices are now added automatically to the xknx.devices list after initialization
- Device.sync() method now again has a `wait_for_result` parameter that allows the user to wait for the telegrams
- The default timeout of the `ValueReader` has been extended from 1 second to 2 seconds

### Bugfixes

- Device: Fixes a bug (#339) introduced in 0.12.0 so that it is again possible to have multiple devices with the same name in the HA integration

## 0.12.0 New StateUpdater, improvements to the HA integrations and bug fixes 2020-08-14

### Breaking changes

- Climate: `setpoint_shift_step` renamed for `temperature_step`. This attribute can be applied to all temperature modes. Default is `0.1`
- Removed significant_bit attribute in BinarySensor
- DateTime devices are initialized with string for broadcast_type: "time", "date" or "datetime" instead of an Enum value
- Removed `bind_to_multicast` option in ConnectionConfig and UDPClient

### New Features

- Cover: add optional `group_address_stop` for manual stopping
- Cover: start travel calculator when up/down telegram from bus is received
- HA integration: `knx.send` service takes `type` attribute to allow sending DPT encoded values like `sensor`
- HA integration: `sensor` and `expose` accept int and float values for `type` (parsed as DPT numbers)
- new StateUpdater: Devices `sync_state` can be set to `init` to just initialize state on startup, `expire [minutes]` to read the state from the KNX bus when it was not updated for [minutes] or `every [minutes]` to update it regularly every [minutes]
- Sensor and ExposeSensor now also accepts `value_type` of int (generic DPT) or float (specific DPT) if implemented.
- Added config option ignore_internal_state in binary sensors (@andreasnanko #267)
- Add support for 2byte float type (DPT 9.002) to climate shiftpoint
- ClimateMode: add `group_address_operation_mode_standby` as binary operation mode
- ClimateMode: add `group_address_heat_cool` and `group_address_heat_cool_state for switching heating mode / cooling mode with DPT1

### Bugfixes

- Tunneling: don't process incoming L_Data.con confirmation frames. This avoids processing every outgoing telegram twice.
- enable multicast on macOS and fix a bug where unknown cemi frames raise a TypeError on routing connections
- BinarySensor: reset_after is now implemented as asyncio.Task to prevent blocking the loop
- ClimateMode: binary climate modes should be fully functional now (sending, receiving and syncing)
- Cover: position update from bus does update current position, but not target position (when moving)

### Internals

- Cover travelcalculator doesn't start from 0% but is initialized by first movement or status telegram
- Cover uses 0% for open cover and 100% for closed cover now
- DPT classes can now be searched via value_type string or dpt number from any parent class (DPTBase for all) to be used in Sensor
- Use RemoteValue class in BinarySensor, DateTime and ClimateMode device
- use time.struct_time for internal time and date representation
- use a regular Bool type for BinarySensor state representation
- RemoteValue.process has always_callback attribute to run the callbacks on every process even if the payload didn't change
- Separate incoming and outgoing telegram queues; apply rate limit only for outgoing telegrams
- Automatically publish packages to pypi (@Julius2342 #277)
- keep xknx version in `xknx/__version__.py` (@farmio #278)
- add raw_socket logger (@farmio #299)

## 0.11.3 Sensor types galore! 2020-04-28

### New Features

- added a lot of DPTs now usable as sensor type (@eXtenZy #255)

### Bugfixes

- DPT_Step correction (used in Cover) (@recMartin #260)
- prevent reconnects on unknown CEMI Messages (@farmio #271)
- fix the parsing of operation mode strings to HVACOperationMode (@FredericMa #266)
- corrected binding to multicast address in Windows (Routing) (@FredericMa #256)
- finish tasks when stopping xknx (@farmio #264, #274)

### Internals

- some code cleanup (dpt, telegram and remote_value module) (@farmio #232)
- refactor Notification device (@farmio #245)

## 0.11.2 Add invert for climate on_off; fixed RGBW lights and stability improvements 2019-09-29

### New Features

- Sensor: add DPT 9.006 as pressure_2byte #223 (@michelde)
- Climate: add new attribute on_off_invert #225 (@tombbo)

### Bugfixes

- Light: Fix for wrong structure of RGBW DPT 251.600 #231 (@dstrigl)
- Core: Correct handling of E_NO_MORE_CONNECTIONS within ConnectResponses #217 (@Julius2342)
- Core: Fix exceptions #234 (@elupus)
- Core: Avoid leaking ValueError exception on unknown APCI command #235 (@elupus)
- add tests for Climate on_off_invert (#233) @farmio
- merge HA plugin from upstream 0.97.2 (#224) @farmio
- Small adjustments to the sensor documentation and example (#219) @biggestj
- merge HA plugin from upstream @farmio

## 0.11.1 Bugfix release 2019-07-08

- Optionally disable reading (GroupValueRead) for sensor and binary_sensor #216 @farmio

## 0.11.0 Added new sensor types and fixed a couple of bugs 2019-06-12

### Features

- Auto detection of local ip: #184 (@farmio )
- Added new sensor types and fix existing: #189 (@farmio ) - binary mapped to RemoteValueSwitch - angle DPT 5.003 - percentU8DPT 5.004 (1 byte unscaled) - percentV8 DPT 6.001 (1 byte signed unscaled) - counter*pulses DPT 6.010 - DPT 8.\*\*\* types (percentV16, delta_time*\*, rotation_angle, 2byte_signed and DPT-8) - luminous_flux DPT 14.042 - pressure DPT 14.058 - string DPT 16.000 - scene_number DPT 17.001
- Binary values are now exposable
- Add support for RGBW lights - DPT 251.600: #191 #206 (@phbaer )
- Bump PyYAML to latest version (5.1): #204 (@Julius2342 )
- Add DPT-8 support for Sensors and HA Sensors: #208 (@farmio )

### Breaking changes

- Scene: scene_number is now 1 indexed according to KNX standards
- Replaced group_address in BinarySensor with group_address_state (not for Home Assistant component)

### Bugfixes

- Fix pulse sensor type: #187 (@farmio )
- Fix climate device using setpoint_shift: #190 (@farmio )
- Read binary sensors on startup: #199 (@farmio )
- Updated YAML to use safe mode: #196 (@farmio )
- Update README.md #195 (thanks @amp-man)
- Code refactoring: #200 (@farmio )
- Fix #194, #193, #129, #116, #114
- Fix #183 and #148 through #190 (@farmio )

## 0.10.0 Bugfix release 2019-02-22

- Connection config can now be configured in xknx.yml (#179 @farmio )
- (breaking change) Introduced target_temperature_state for climate devices (#175 @marvin-w )
- Introduce a configurable rate limit (#178 @marvin-w)
- updated HA plugin (#174 @marvin-w)
- Migrate documentation in main project (#168 @marvin-w)
- documentation updates (@farmio & @marvin-w)

## 0.9.4 - Release 2019-01-01

- updated hass plugin (@marvin-w #162)
- tunable white and color temperature for lights (@farmio #154)

## 0.9.3 - Release 2018-12-23

- updated requirements (added flake8-isort)
- some more unit tests
- Breaking Change:
  ClimateMode is now a member of Climate (the hass plugin
  needs this kind of dependency. Please note the updated xknx.yml)

## 0.9.2 - Release 2018-12-22

- Min and max values for Climate device
- split up Climate in Climate and ClimateMode
- added **contains** method for Devices class.
- fixed KeyError when action refers to a non existing device.

## 0.9.1 - Release 2018-10-28

- state_addresses of binary_sesor should return empty value if no
  state address is set.
- state_address for notification device

## 0.9.0 - Release 2018-09-23

- Updated requirements
- Feature: Added new DPTs for DPTEnthalpy, DPTPartsPerMillion, DPTVoltage. Thanks @magenbrot #146
- Breaking Change: Only read explicit state addresses #140
- Minor: Fixed some comments, @magenbrot #145
- Minor: lowered loglevel from INFO to DEBUG for 'correct answer from KNX bus' @magenbrot #144
- Feature: Add fan device, @itineric #139
- Bugfix: Tunnel: Use the bus address assigned by the server, @M-o-a-T #141
- Bugfix: Adde:wd a check for windows because windows does not support add_signal @pulse-mind #135
- Bugfix: correct testing if xknx exists within self @FireFrei #131
- Feature: Implement support to automatically reconnect KNX/IP tunnel, @rnixx #125
- Feature: Adjusted to Home Assistant's changes to light colors @oliverblaha #128
- Feature: Scan multiple gateways @DrMurx #111
- Bugfix: Pylint errors @rnixx #132
- Typo: @itineric #124
- Feature: Add support for KNX DPT 20.105 @cian #122

## 0.8.5 -Release 2018-03-10

- Bugfix: fixed string representation of GroupAddress https://github.com/home-assistant/home-assistant/issues/13049

## 0.8.4 -Release 2018-03-04

- Bugfix: invert scaling value #114
- Minor: current_brightness and current_color are now properties
- Feature: Added DPT 5.010 DPTValue1Ucount @andreasnanko #109

## 0.8.3 - Release 2018-02-05

- Color support for HASS plugin
- Bugfixes (esp problem with unhashable exceptions)
- Refactoring: split up remote_value.py
- Better test coverage

## 0.8.1 - Release 2018-02-03

- Basic support for colored lights
- Better unit test coverage

## 0.8.0 - Release 2018-01-27

- New example for MQTT forwarder (thanks @JohanElmis)
- split up Address into GroupAddress and PhysicalAddress (thanks @encbladexp)
- Time object was renamed to Datetime and does now support different broadcast types "time", "date" and "datetime" (thanks @Roemer)
- Many new DTP datapoints esp for physical values (thanks @Straeng and @JohanElmis)
- new asyncio `await` syntax
- new device "ExposeSensor" to read a local value from KNX bus or to expose a local value to KNX bus.
- Support for KNX-scenes
- better test coverage
- Fixed versions for dependencies (@encbladexp)

And many more smaller improvements :-)

## 0.7.7-0.7.18 - Release 2017-11-05

- Many iterations and bugfixes to get climate support with setpoint shift working.
- Support for invert-position and invert-angle within cover.
- State updater may be switched of within home assistant plugin

## 0.7.6 - Release 2017-08-09

Introduced KNX HVAC/Climate support with operation modes (Frost protection, night, comfort).

## 0.7.0 - Released 2017-07-30

### More asyncio:

More intense usage of asyncio. All device operations and callback functions are now async.

E.g. to switch on a light you have to do:

```python
await light.set_on()
```

See updated [examples](https://github.com/XKNX/xknx/tree/main/examples) for details.

### Renaming of several objects:

The naming of some device were changed in order to get the nomenclature closer to several other automation projects and to avoid confusion. The device objects were also moved into `xknx.devices`.

#### Climate

Renamed class `Thermostat` to `Climate` . Please rename the section within configuration:

```yaml
groups:
  climate:
    Cellar.Thermostat: { group_address_temperature: "6/2/0" }
```

#### Cover

Renamed class `Shutter` to `Cover`. Please rename the section within configuration:

```yaml
groups:
  cover:
    Livingroom.Shutter_1:
      {
        group_address_long: "1/4/1",
        group_address_short: "1/4/2",
        group_address_position_feedback: "1/4/3",
        group_address_position: "1/4/4",
        travel_time_down: 50,
        travel_time_up: 60,
      }
```

#### Binary Sensor

Renamed class `Switch` to `BinarySensor`. Please rename the section within configuration:

```yaml
groups:
  binary_sensor:
    Kitchen.3Switch1:
      group_address: "5/0/0"
```

Sensors with `value_type=binary` are now integrated into the `BinarySensor` class:

```yaml
groups:
  binary_sensor:
    SleepingRoom.Motion.Sensor:
      { group_address: "6/0/0", device_class: "motion" }
    ExtraRoom.Motion.Sensor: { group_address: "6/0/1", device_class: "motion" }
```

The attribute `significant_bit` is now only possible within `binary_sensors`:

```yaml
groups:
  binary_sensor_motion_dection:
    Kitchen.Thermostat.Presence:
      { group_address: "3/0/2", device_class: "motion", significant_bit: 2 }
```

#### Switch

Renamed `Outlet` to `Switch` (Sorry for the confusion...). The configuration now looks like:

```yaml
groups:
  switch:
    Livingroom.Outlet_1: { group_address: "1/3/1" }
    Livingroom.Outlet_2: { group_address: "1/3/2" }
```

Within `Light` class i introduced an attribute `group_address_brightness_state`. The attribute `group_address_state` was renamed to `group_address_switch_state`. I also removed the attribute `group_address_dimm` (which did not have any implemented logic).

## Version 0.6.2 - Released 2017-07-24

XKNX Tunnel now does hartbeat - and reopens connections which are no longer valid.

## Version 0.6.0 - Released 2017-07-23

Using `asyncio` interface, XKNX has now to be stated and stopped asynchronously:

```python
import asyncio
from xknx import XKNX, Outlet

async def main():
    xknx = XKNX()
    await xknx.start()
    outlet = Outlet(xknx,
                    name='TestOutlet',
                    group_address='1/1/11')
    outlet.set_on()
    await asyncio.sleep(2)
    outlet.set_off()
    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

`sync_state` was renamed to `sync`:

````python
await sensor2.sync()
```
````

