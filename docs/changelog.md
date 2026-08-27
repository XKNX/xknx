---
layout: default
title: Changelog
nav_order: 2
---

# Changelog

# Unreleased changes

### Breaking changes

- Rename `xknx.management.management.MANAGAMENT_ACK_TIMEOUT` and `MANAGAMENT_CONNECTION_TIMEOUT` to `MANAGEMENT_ACK_TIMEOUT` and `MANAGEMENT_CONNECTION_TIMEOUT` - they were misspelled.
- Drop support for Python 3.10. XKNX requires Python 3.11 or newer now.
- Remove `xknx.util`. Its only member was `asyncio_timeout` - a backport of `asyncio.timeout` for Python versions not providing it - so use `asyncio.timeout` directly.
- Remove `RemoteValue.__eq__()`. It compared `__dict__` attributes - a leftover of the YAML config handling removed in 1.0 - and raised `AttributeError` when compared to an object without a `__dict__`. Remote values compare by identity now, which also makes them hashable again, so they can be used in sets and as dict keys.
- All classes in `xknx.remote_value` define `__slots__` now. Setting an attribute that isn't declared by the class raises `AttributeError` instead of silently creating it.

  ```python
  rv_1 = RemoteValueSwitch(xknx, group_address="1/2/3")
  rv_2 = RemoteValueSwitch(xknx, group_address="1/2/3")

  rv_1 == rv_2  # before: True (equal attributes); now: False (distinct objects)
  hash(rv_1)  # before: TypeError: unhashable type; now: works
  rv_1.my_own_attribute = 1  # before: works; now: AttributeError
  ```
- Remove device lookup by name or index from `xknx.devices`. `xknx.devices["NameOfDevice"]` and `xknx.devices[0]` are gone - device names are never checked for uniqueness, so the lookup could return any one of several devices sharing a name. Keep a reference to the device object instead, or iterate `xknx.devices` to find it. `device in xknx.devices` takes the `Device` object now instead of its name.
- `Devices.async_add()` and `Devices.async_remove()` raise `ValueError` when the device object is already registered, or not registered at all. Adding a device twice had it receive every telegram twice and fire its callbacks twice; removing an unregistered one cancelled its tasks and unregistered its state updater before failing.
- Remove `Device.__eq__()` - same reasoning as `RemoteValue.__eq__()` above: it compared `__dict__` attributes and was a leftover of the YAML config handling removed in 1.0. Devices compare by identity now, which also makes `Device` hashable again, so devices can be used in sets and as dict keys. The same applies to `Light.red`, `.green`, `.blue` and `.white`.
- `RawValue` takes `payload_length` as its first argument after `xknx`, before `name` - `name` is optional now and Python doesn't allow a required argument after an optional one. `RawValue(xknx, "Name", 2, ...)` becomes `RawValue(xknx, 2, "Name", ...)`.
- `Sensor`, `NumericValue` and `ExposeSensor` take `value_type` as their first argument after `xknx`, before `name`, and require it - like `payload_length` of `RawValue` above. `Sensor(xknx, "Name", value_type="temperature")` becomes `Sensor(xknx, "temperature", "Name")`. `value_type` never had a usable default: passing `None` raised `ConversionError`. `Notification` keeps its optional `value_type`, now defaulting to `"string"` instead of `None`.
- `RemoteValueSensor`, `RemoteValueNumeric` and `RemoteValueString` take `value_type` as their first argument after `xknx` and require it. `RemoteValueString` no longer defaults to `DPTString`; pass `value_type="string"` explicitly.
- Every argument of a device after `xknx` is keyword-only now. `Switch(xknx, "Kitchen", "1/2/3")` becomes `Switch(xknx, name="Kitchen", group_address="1/2/3")`. Devices carry a lot of similar looking arguments - most of them group addresses - so a positional call was easy to get subtly wrong, and it pinned the argument order as public API. The argument order named in the entries above is therefore only about the signature; it doesn't affect how a device is constructed anymore.
- `Scene.scene_value` is a `RemoteValueSceneControl` (DPT 18.001) instead of a `RemoteValueSceneNumber` (DPT 17.001), so its value carries the learn bit next to the scene number. Telegrams on the wire are unchanged: DPT 18.001 encodes an activation to the same octet DPT 17.001 does, and decodes one back the same way. The device callback is called for received learn telegrams of the devices `scene_number` now, not only for activations - the new `Scene.learn_requested` tells both apart.
- Remove `ha_device_class` from `DPTBase` subclasses, `RemoteValueSensor`, `RemoteValueByLength`, `Sensor` and `NumericValue`. Home Assistant shall maintain this itself.

### Bugfixes

- Management: don't acknowledge a connected telegram from a device xknx has no open point-to-point connection with. The acknowledgement was sent before the connection was looked up, so a device that was not talking to us received a `T_Ack` and was then reported as "No active point-to-point connection for received telegram". KNX v01.02.03 - Transport Layer 03.03.04 - §5.4: no style of the connection oriented state machine acknowledges anything while CLOSED - including the styles that accept incoming connections.
- Management: only telegrams of a point-to-point connection are handled by an open connection to their sender. The sender address alone decided that before, so an unnumbered telegram from a device we happened to hold a connection with - a broadcast response for example - was acknowledged, never reached the broadcast context it was meant for, and could be mistaken for the response of a pending point-to-point request.
- Management: a repeated sequence number is acknowledged again instead of being acknowledged and dropped, and a sequence number that is neither the expected nor the previous one is answered with a negative acknowledgement instead of a positive one - Transport Layer 03.03.04 - §5.3 A3 and A4.

### Connection

- KNX IP Secure transports discard unencrypted frames instead of passing them to their callbacks. A secure session accepts a plain frame only for the handshake - `SessionRequest` outgoing, `SessionResponse` incoming - and raises `IPSecureError` when anything else is sent before the session is initialized. Secure routing keeps forwarding plain discovery and self description frames (`SearchRequest`, `SearchResponse`, `DescriptionRequest` and `DescriptionResponse`, extended variants included) since these services are never secured and share the multicast endpoint, but now drops every other plain frame - previously only `RoutingIndication` was dropped, so a plain `RoutingBusy` from any sender could still throttle outgoing telegrams. Frames that may not be encapsulated at all - a nested `SecureWrapper` and the Remote Configuration and Diagnosis service family - are discarded when received inside a `SecureWrapper`.

### Devices

- The `name` of a device is optional now and can be changed after instantiation. When no name is given it defaults to the class name of the device - `Sensor`, `NumericValue` and `ExposeSensor` append their value type, eg. `"Sensor temperature"`. Assigning `Device.name` passes the new name down to the devices `RemoteValue` instances, so log messages and exceptions use it too - previously the name was only copied to the remote values on instantiation and assigning a new one left them stale. Renaming a `Climate` renames its `mode` device as well.

  ```python
  light = Light(xknx, group_address_switch="1/2/3")
  light.name  # "Light"
  light.name = "light.kitchen_ceiling"  # eg. in Home Assistants `async_added_to_hass()`
  ```
- Scene: add `learn()` to send a telegram with the learn bit set, telling actuators to store their current state as this scene. Received learn telegrams are decoded instead of logging a "Can not process" warning, so a Scene can serve as scene actuator: restore its state from the device callback when `learn_requested` is `False`, store it when it is `True`.

### Internals

- `Devices` keeps a group address index of its registered devices instead of scanning every device on every incoming telegram. `Devices.devices_by_group_address()` is a dict lookup now - its result is unchanged, devices are still returned in registration order and a device carrying one group address on several of its `RemoteValue`s is still returned once. This relies on a devices group addresses being fixed when its `RemoteValue`s are created, which the library guarantees - assigning `RemoteValue.group_address` after `Devices.async_add()` was never supported and would now leave the index stale.
- `CEMILData.flags` is a `CEMIFlags` dataclass now instead of a 16 bit `int`, with a field per control field value: `priority` (new `CEMIPriority` enum), `repeat_on_error`, `system_broadcast` (both named for the positive meaning; inverted on the wire), `acknowledge_request`, `confirm_error`, `hop_count` - which replaces the removed `CEMILData.hops` property - and the received `frame_type` / `frame_format`. Frame Type and Address Type are derived when serializing, from the NPDU length and from the type of the destination address (`CEMILData.address_type`), so `flags` can no longer disagree with the frame that is put on the wire. `CEMILData(flags=...)` is optional now. The bit constants moved from `CEMIFlags` to `xknx.cemi.flags`.
- `xknx.secure.data_secure_asdu.block_0()`, `SecureData.init_from_plain_apdu()` and `SecureData.get_plain_apdu()` take `address_type: CEMIAddressType` and `frame_format: CEMIFrameFormat` instead of `frame_flags: int`. Only those two fields of Ctrl2 ever reached the CCM input; the value on the wire and the one fed to the MAC now come from the same place.
- `RequestResponse` is now generic over the response body it awaits, eg. `class Connect(RequestResponse[ConnectResponse])`. `start()` gives way to `request()`, which returns that response instead of leaving it on the instance, and raises the new `RequestResponseError` when none arrived or the server answered with an error status.
- `DescriptionQuery` and `SearchExtendedQuery` derive from `RequestResponse` now. Their `start()` and `gateway_descriptor` attribute are replaced by `request_gateway_descriptor()`.
- `Telegram` is now generic over its `payload` type (`Telegram[GroupValueWrite]`, etc.), defaulting to `Telegram` behaving exactly as before when left unparametrized - `payload` is `None` only for that default/unparametrized case (control telegrams like ACK/Disconnect); parametrized as `Telegram[SomeAPCI]`, `payload` is `SomeAPCI`, never `None`. `Device.process()` now hands `process_group_write()`/`process_group_response()`/`process_group_read()` a `Telegram` narrowed to the APCI type it already verified via `isinstance`, propagated through `RemoteValue.process()` and every device's `process_group_*` override. No behavior change - `RemoteValue.process()` keeps its own `isinstance` check since, unlike the management case below, nothing enforces the payload type before it's called directly.
- Add `APCIRequest` to `xknx.telegram.apci` - an `APCI` subclass carrying the KNX-spec-defined response type of a request service as its type argument, eg. `class MemoryRead(APCIRequest[MemoryResponse])`. `RESPONSE_TYPE` is derived from that argument. All 21 point-to-point request services with a spec-defined response were converted; group communication services (`GroupValueRead`, `GroupPropValueRead`) stay plain `APCI` since they are never sent via `P2PConnection.request()`. `request()` no longer takes an `expected=` argument - it infers and verifies the expected response from the payload's type and returns the correspondingly typed `Telegram[ResponseType]`, so procedures no longer need `assert isinstance(response.payload, ResponseType)` (or even a `None` check) to get a typed `.payload`.
- Add `APCIBroadcastRequest` to `xknx.telegram.apci` - the broadcast counterpart of `APCIRequest`, carrying its response type the same way. `IndividualAddressRead`, `IndividualAddressSerialRead`, `DomainAddressRead`, `DomainAddressSerialNumberRead`, `NetworkParameterRead` and `SystemNetworkParameterRead` derive from it. It is a sibling of `APCIRequest`, not a subclass, so a broadcast service can not be passed to `P2PConnection.request()` - it would be sent over a point-to-point connection and time out.
- Broadcast communication is encapsulated in a `Broadcast` class, reached as `xknx.management.broadcast`. `Management.send_broadcast()` becomes `xknx.management.broadcast.send()` and the `Management.broadcast()` context manager becomes `xknx.management.broadcast.context()`.
- Add `Broadcast.request()` - broadcasts a request service and yields the responses to it, eg. `async for telegram in xknx.management.broadcast.request(apci.IndividualAddressRead(), timeout=3)`. It replaces the context, `send()` and `receive()` trio for the common case, listening for the response type the payload declares and narrowing each telegram to it. Any number of devices may answer, so it yields until `timeout` elapses rather than returning a single telegram like `P2PConnection.request()`.
- `BroadcastContext.receive()` takes the APCI class to listen for, eg. `bc_context.receive(apci.IndividualAddressResponse, timeout=3)`, and yields only telegrams carrying it, narrowed to `Telegram[ThatAPCI]`, instead of everything on the broadcast channel. Called without an argument it behaves as before.
- `BroadcastContext.receive()`'s timeout is armed around the wait for the next telegram instead of around the whole iteration. Previously a caller leaving the loop early - after finding the response it was looking for - left the timeout armed on the abandoned generator, cancelling that caller once it elapsed. `timeout` still bounds the whole iteration.
- Dependencies are declared in `pyproject.toml` only - the library's own in `[project.dependencies]`, the development tooling in the `dev` group of `[dependency-groups]` - and pinned, including transitive ones, in `uv.lock`. The `requirements/` directory and `tox.ini` are removed; contributors need [uv](https://docs.astral.sh/uv/) now: `uv sync` to set up, `uv run pytest` to test.
- Git hooks are run by [prek](https://github.com/j178/prek) instead of pre-commit, from the same `.pre-commit-config.yaml`. Install them with `uv run prek install`, run them with `uv run prek run --all-files`. ruff, ruff format, mypy and pylint are local hooks executed via `uv run --frozen`, so their versions come from `uv.lock` alone - ruff is no longer pinned a second time in the hook config. `script/run-in-env.sh` is removed with them. The `check-json` hook is dropped - the repository tracks no JSON files.
- Releases are built with `uv build` and uploaded by `pypa/gh-action-pypi-publish` using [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) instead of `twine` with a stored username and password. Distributions now carry PEP 740 attestations.

# 3.20.0 DeviceManagement and Expose init 2026-08-16

### Devices

- Add `ExposeSensor.initialize_value()` to set a value without sending it to the KNX bus, eg. one restored from a previous run. Unlike assigning `sensor_value.value` directly, it also initializes the payload used for periodic sending and `skip_unchanged`. `None` clears the value.

### Features

- Add `UDPDeviceManagementConnection`, `TCPDeviceManagementConnection` and `SecureDeviceManagementConnection`, clients for a KNXnet/IP device management connection - the latter over a KNX IP Secure session. They read and write the Properties of a server's own Interface Objects via `read_property()`, `write_property()` or `request()` for any other cEMI frame, and report `M_PropInfo.ind` frames to an `indication_callback`. They are not an `Interface`: such a connection carries no telegrams, so it leaves `xknx.current_address` and the connection manager alone.
- Add `DeviceManagement` to acknowledge `DeviceConfigurationRequest` frames received over a device management connection - the counterpart to `DeviceConfiguration`, which covers the other direction.
- `DeviceConfiguration` now waits `DEVICE_CONFIGURATION_REQUEST_TIMEOUT` (10 seconds) for its acknowledgement instead of the one second inherited from `RequestResponse`, and takes a `timeout_in_seconds` argument to override it.
- Add `dmp_authorize_r_co(conn, key)`, `dmp_authorize2_r_co(conn, client_key)` and `dmp_connect_r_co(conn)` to `xknx.management.procedures`, running on an already-open `P2PConnection`. `dmp_authorize2_r_co` authorizes with `FREE_ACCESS_KEY` first, then `client_key`, and keeps whichever gives the better access level. `dmp_connect_r_co` reads Device Descriptor Type 0 to confirm the connection is live and returns the mask version.

### Internals

- Extract the connection heartbeat and the sequence counter handling for received frames into `ConnectionHeartbeat` and `IncomingSequenceCounter` in `xknx.io.data_connection`, shared by the tunnel and the device management connection instead of being duplicated. The mechanics are unchanged.

# 3.19.0 Covering CEMI errors 2026-08-10

### Bugfixes

- Fix the encoding of `SecurityALService.S_A_SYNC_REQ`: the S-A-Service field of the Security Control Field encodes an S-A_Sync_Req-PDU as `0b010`, not `0b001` - KNX v02.01.01 - Application Layer 03.03.07 - §5.1.1 Table 5. Incoming Data Secure sync requests were rejected with `CouldNotParseCEMI` "APDU invalid" instead of being parsed and then ignored as an unsupported S-AL service.

### Devices

- Cover: run device callbacks for every received current position telegram, even when the position doesn't change. Previously a GroupValueResponse or GroupValueWrite confirming the position a consumer already assumed - eg. one restored from a previous run - was swallowed, so the consumer never learned that its position is now confirmed by the bus. The periodic update task is still only started when the position actually changed.

### Protocol

- Be tolerant about property error codes the specification does not define: `CEMIMPropReadResponse.error_code` and `CEMIMPropWriteResponse` keep an octet outside `CEMIErrorCode` as a plain `int` instead of raising `ValueError` - from lazy resolution (and `__repr__`) on read, and from `from_knx` on write, where it made the whole frame unparsable. A `CEMIMPropWriteResponse` with the falsy `CEMI_ERROR_UNSPECIFIED` (`0x00`) error code no longer drops its error octet when serializing.
- Parse `M_PropInfo.ind` cEMI frames into a `CEMIMPropReadResponse` - its payload has the same layout as `M_PropRead.con`. A KNXnet/IP server sends these to announce a property changing on its own, e.g. the KNXnet/IP parameter object's device state when the KNX bus fails; they previously raised `UnsupportedCEMIMessage` and were counted as incoming errors. Serializing already worked.

### Internals

- Keep the underlying error message when a CEMI or APDU parse error is re-raised as a more generic exception so it no longer hides what was actually wrong with the frame.

# 3.18.0 Protocol Droid 2026-08-02

### Bugfixes

- Send frames with an APDU longer than 15 octets as L_Data_Extended frames. The Frame Type flag of Ctrl1 is now derived from the NPDU length when serializing a `CEMILData` instead of always being set to standard frame. This fixes sending telegrams over KNX Data Secure with a payload of 2 octets or more (eg. DPT 9.x or DPT 232.600) - Data Secure adds 12 octets to the plain APDU, which no longer fits in a standard frame. Sending an APDU longer than 254 octets now raises `ConversionError` instead of `OverflowError`.

### Features

- **Experimental.** Add `xknx.mcp`, a host-agnostic subpackage of async MCP tool functions for the KNX bus and data point types (`list_dpts`, `describe_dpt`, `encode_dpt_payload`, `decode_dpt_payload`, `get_connection_status`, `read_group_value`, `send_group_value_read`, `send_group_value_write`). Frozen, JSON-native dataclass I/O with per-field descriptions in `dataclasses.field` metadata; carries no MCP SDK, Home Assistant or web-framework dependency, so a consumer wraps the functions into its own MCP transport. This subpackage is experimental and its API may change in a future release.

### Protocol

- Reject incoming CEMI L_Data frames with a non-standard Extended Frame Format field with `UnsupportedCEMIMessage`. LTE-HEE frames use zone addressing, so their address fields can not be parsed as `GroupAddress`; reserved encodings are rejected too. The Frame Type flag is still not validated against the NPDU length when parsing - a receiver shall be tolerant towards the used frame format.
- `CEMIFlags.EXTENDED_FRAME_FORMAT` was removed; its value `0x0001` was reserved, not an "extended frame format" indicator - `0x0000` is used for standard frames as well as for long extended frames. The `CEMIFrameFormat` enum covers the field instead, resolving the whole `01xxb` range to `LTE_HEE`.
- The hop count is validated when serializing; a value outside `0..7` raises `ConversionError` instead of silently corrupting Ctrl2.
- Add explicit length checks to every remaining APCI `from_knx` (and the top-level `APCI.from_knx` dispatcher) as defense-in-depth on top of the broad `except (IndexError, struct.error, ValueError)` added in 3.17.0: each service now raises `ConversionError` with a specific "Invalid length for A_X in CEMI" message for a truncated, malformed or overlong frame instead of relying solely on the generic dispatcher-level catch.

### Deprecation notes

- `nm_invididual_address_write`, the typo'd alias for `nm_individual_address_write` in `xknx.management.procedures`, is deprecated and will be removed in v4. Use `nm_individual_address_write` instead.

### New Features

- Add `dm_restart_r_co(conn)` and `nm_individual_address_check_conn(conn)` to `xknx.management.procedures` — variants of `dm_restart`/`nm_individual_address_check` that operate on an already-open `P2PConnection` instead of opening and closing their own, for chaining several procedures over one connection. `dm_restart_r_co` is the actual KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.3 procedure name; the `_conn` suffix on the others is an xknx-only naming convention, not a KNX spec name. All existing top-level procedures (`dm_restart`, `nm_individual_address_check`, `nm_individual_address_write`, `nm_individual_address_read`, `nm_individual_address_serial_number_read`/`_write`) keep their `(xknx, ...)` signature unchanged.
- Add `P2PConnection.send_data(payload, wait_for_ack=True)` for sending a telegram, optionally without waiting for an ACK (used internally by `dm_restart`/`dm_restart_r_co` and `nm_individual_address_write` instead of open-coding the same `TDataConnected` construction in multiple procedures).

# 3.17.0 APCIs and DPTs 2026-07-25

### Deprecation notes

- Moved `ReturnCode` from `xknx.management.application_layer_enum` to `xknx.telegram.apci`. The old module still re-exports it for backwards compatibility but is deprecated and will be removed in a future release.

### Protocol

- Add A_DomainAddress_Write, A_DomainAddress_Read, A_DomainAddress_Response, A_DomainAddressSelective_Read, A_DomainAddressSerialNumber_Read, A_DomainAddressSerialNumber_Response and A_DomainAddressSerialNumber_Write APCI service parsing.
- Add A_FileStream_InfoReport APCI service parsing.
- Add A_FilterTable_Open, A_FilterTable_Read, A_FilterTable_Response and A_FilterTable_Write APCI service parsing.
- Add A_FunctionPropertyExtCommand, A_FunctionPropertyExtState_Read and A_FunctionPropertyExtState_Response APCI service parsing.
- Add A_GroupPropValue_Read, A_GroupPropValue_Response, A_GroupPropValue_Write and A_GroupPropValue_InfoReport APCI service parsing (KNX Logical Tag Extended specification).
- Add A_Key_Write and A_Key_Response APCI service parsing.
- Add A_Link_Read, A_Link_Response and A_Link_Write APCI service parsing.
- Add A_MemoryBit_Write and A_UserMemoryBit_Write APCI service parsing.
- Add A_NetworkParameter_Read, A_NetworkParameter_Response and A_NetworkParameter_Write APCI service parsing.
- Add A_PropertyExtValue_Read, A_PropertyExtValue_Response, A_PropertyExtValue_WriteCon, A_PropertyExtValue_WriteConRes, A_PropertyExtValue_WriteUnCon, A_PropertyExtValue_InfoReport, A_PropertyExtDescription_Read and A_PropertyExtDescription_Response APCI service parsing.
- Add A_RouterMemory_Read, A_RouterMemory_Response and A_RouterMemory_Write APCI service parsing. Recognize A_RouterStatus_Read/Response/Write APCI services; these are a legacy EIB/BCU1-era coupler status service with no PDU definition in the current Application Layer spec and are not planned for implementation - configure couplers via the Router Object properties (`A_PropertyValue_Read`/`A_PropertyValue_Write`) instead.
- Add A_SystemNetworkParameter_Read, A_SystemNetworkParameter_Response and A_SystemNetworkParameter_Write APCI service parsing.
- Fix A_Restart parsing to distinguish Basic Restart from Master Reset (restart_type bit was ignored, silently dropping erase_code/channel_number on relay). Add A_Restart_Response parsing for the Master Reset confirmation.
- Fix `APCI.from_knx` to raise `ConversionError` for malformed or truncated APDUs instead of leaking `IndexError`/`struct.error`/`ValueError`, which could crash the CEMI receive path. As a last-resort guard, any other unexpected error while parsing an incoming CEMI frame is now caught, logged with traceback and counted, so a single bad frame can never take down the connection. A malformed APDU of a recognized service is now logged as a warning (`CouldNotParseCEMI`), while a recognized-but-unimplemented service (new `UnsupportedAPCIService`) is logged as info (`UnsupportedCEMIMessage`), so the two are no longer conflated.

### Devices

- Notification: crop the message to the configured DPT's payload length instead of a hardcoded 14 characters (enables single-character DPT 4 notifications).

### DPT

- Add generic DPT 1 (`DPT1BitBoolean`, value_type `"1bit"`) and generic DPT 2 (`DPT2BitBoolean`, value_type `"2bit"`) as boolean fallbacks used when a value only resolves to the DPT 1 / DPT 2 main number (e.g. an ETS project without a specific 1.yyy / 2.yyy subtype). They behave like `DPTBool` / `DPTBoolControl`.
- Add DPT 2 definitions
- Add DPT 4 (`DPTCharacter` 4.001 ASCII, `DPTCharacterLatin1` 4.002 ISO 8859-1) for single characters
- Add DPT 243.600 (`DPT_Colour_Transition_xyY`)
- Add DPT 249.600 (`DPT_Brightness_Colour_Temperature_Transition`)
- Add DPT 250.600 (`DPT_Brightness_Colour_Temperature_Control`)
- Add DPT 252.600 (`DPT_Relative_Control_RGBW`)
- Add DPT 253.600 (`DPT_Relative_Control_xyY`)
- Add DPT 254.600 (`DPT_Relative_Control_RGB`)

# 3.16.0 Complex schema 2026-06-19

### DPT

- Add DPTComplex dict schema descriptions.

### Internals

- Split `xknx/management/procedures.py` into the `xknx/management/procedures/` package. Each procedure lives in its own file under a family subdirectory (`network/`, `device/`, etc.) with the KNX spec prefix in the filename. Public API and behaviour unchanged.
- Update Ruby and dependencies for building the website.
- Remove xknx.yaml Config-Converter from website.

# 3.15.0 Task improvements 2026-02-15

### Telegram

- Add `data_secure` flag to Telegram to indicate if it was sent or received as Data Secure.

### Devices

- ExposeSensor: `cooldown` is extended to wait for connection if not established.
- Weather: Add `invert_day_night` option to invert day/night value.

### Internals

- Replace `TaskRegistry.register()` with `TaskRegistry.start_task()` for better readability and easier handling.
- Rename `TaskRegistry.unregister()` to `TaskRegistry.remove_task()`.
- Allow TaskRegistry Tasks to call regular functions as well as async functions. Rename TaskRegistry.register and Task `async_func` attribute to `target`.
- Add TaskRegistry Task `wait_before_start` and `wait_for_connection` options to delay task start and wait for an established connection before running the target function.
- Add TaskRegistry Task `repeat_after` option to automatically restart the task periodically.
- Remove TaskRegistry.register `track_task` option. All tasks used this option before and it is now the default behaviour.

# 3.14.0 ExposeSensor improvements 2026-01-12

### Devices

- ExposeSensor: Add `skip_unchanged` argument to `set` method to skip sending when the encoded payload matches the last one.
- ExposeSensor: Add `periodic_send` argument to re-send value in a time interval (seconds). Disabled on `0` (default).

### Internal

- Add `__slots__` to various classes.
- Unsuccessful tunnel disconnects don't raise anymore.

# 3.13.0 Numeric metering 2025-12-18

### DPT

- Add numeric metering DPTs 13.1200, 13.1201, 14.1200, 14.1201

### Devices

- Fan: Fix turn_on default speed when step-mode is used.

# 3.12.0 Data Secure diagnostics 2025-12-03

### Data Secure

- Don't forward Data Secure frames in the CEMI handler when no keys are initialized.
- Add a callback for undecodable Data Secure telegrams for diagnostics/monitoring: `xknx.telegram_queue.register_data_secure_group_key_issue_cb`.
- Add a counter for undecodable Data Secure telegrams: `xknx.connection_manager.undecoded_data_secure`.

### Connection

- Tunnelling UDP: Cleanup reconnection task logic for invalid sequence number reconnect.

### Other

- `xknx.connection_manager.register_connection_state_changed_cb` now returns an unsubscribe callable instead of `None`.
- Make GroupAddress, IndividualAddress and InternalGroupAddress sortable and comparable.

# 3.11.0 Reconnect 2025-11-22

### Connection

- Tunnelling: Refactor reconnection logic. Immediate first reconnection attempt, prevent reconnect task leak.
- Tunnelling: Mitigate dropping frames while reconnecting.
- Tunnelling UDP: Schedule disconnect when receiving frames with invalid sequence numbers.

# 3.10.1 Fix cover auto-stop 2025-11-09

### Devices

- Cover: Fix race condition for cover auto-stopper.

# 3.10.0 Always callback Sensor and BinarySensor 2025-10-13

### Devices

- Sensor: Fire callback when `always_callback` is `True` for write as well as for response telegrams.
- BinarySensor: Add `always_callback` attribute to fire callbacks for every telegram.

### Internal

- Add support and test for Python 3.14

# 3.9.1 Fix Climate initialization 2025-10-10

### Devices

- Climate: Fix `supports_on_off` flag when empty list passed as group address.

# 3.9.0 Scene callbacks 2025-08-26

### Devices

- Scene: Fire device callback if scene number is activated (from xknx or bus).
- Add `group_addresses()` method to `Device` (and `RemoteValue`) to get all configured group addresses.

### Internal

- Use `repr()` for values in exceptions.

# 3.8.0 Valid energy 2025-05-12

### Connection

- Support passing a `Keyring` object to `SecureConfig` instead of a path to a keyring file

### DPT

- Fix flipped DPT 235.001 (Tariff and ActiveEnergy) data validity bits

# 3.7.0 Routing improvements 2025-04-17

### Routing

- Use separate socket for outgoing Multicast (Routing) datagrams. Source port will be different - this is used to filter loopback packets while still be able to have multiple instances of xknx on the same host communicating with each other via routing.
- Fix routing flow control wait time update on multiple RoutingBusy frames.

# 3.6.0 DPT helpers and timezone 2025-02-19

### Devices

- Datetime: Accept `datetime.tzinfo` for `timezone` argument to send time information for specific timezone. Boolean works like before: If `True` use system localtime. If `False` an arbitrary time can be sent.

### DPT

- Add `DPTBase.dpt_number_str` and `DPTBase.dpt_name` classmethods for human readable DPT number (eg. "9.001") and class name (eg. "DPTTemperature (9.001)").
- Add `DPTBase.get_dpt` classmethod to get a DPT class by its number, name or DPTBase type.

### Internal

- Collect group addresses with decoding errors at eager decoder in `xknx.group_address_dpt.ga_decoding_error` set.

# 3.5.0 Swing it 2025-01-28

### Devices

- Climate: Added swing and horizontal swing support to climate device

# 3.4.0 8 byte energy and 4 byte pressure 2024-11-20

### Devices

- Weather: Support either DPT 9.006 (2byte) or DPT 14.058 (4byte) for `group_address_air_pressure`

### DPT

- Add DPT 29 - 8byte signed definitions: generic, 29.010, 29.011, 20.012

### Management

- Add rate limit (in packets per second) option to P2PConnection.
- Fix typo in management procedure (`nm_invididual_address_write` was renamed to `nm_individual_address_write`)
- Fix TunnellingFeatureResponse missing `return_code`

# 3.3.0 Climate humidity 2024-10-20

### Devices

- Climate: Added humidity support

# 3.2.0 Climate Fan speed 2024-09-23

### Devices

- Climate: Added fan speed support

# 3.1.1 Fix Eberle status 2024-08-19

### Bugfixes

- Fix DPTHVACStatus inverted bit order

# 3.1.0 DPT 1 2024-08-13

### DPT

- Add DPT 1 definitions (as of KNX Specification 03_07_02 version 02.02.01)

### Devices

- ClimateMode: Restore `Climate.suppports_operation_mode` and `Climate.supports_controller_mode` to be `True` when read-only (like pre 3.0.0)
- ClimateMode: Filter custom controller / operation modes for available settable modes
- ClimateMode: For binary operation modes, only list configured modes and `Standby` in `operation_modes`

### Bugfixes

- Fix log message for DPT decoding errors in `GroupAddressDPT` parsing

# 3.0.0 Eager telegram decoding, DPTComplex and DPTEnum 2024-07-31

### Breaking changes

- Drop support for Python 3.9
- Change callback signatures from awaitable to callable in `XKNX.device_updated_cb`, TelegramQueue, Device, Devices, ConnectionManager and RemoteValue.
- Remove `async` from functions / methods (nothing has to be awaited there)
  - Tools:  `group_value_write`, `group_value_response` and `group_value_read`
  - ConnectionManager: `.connection_state_changed`
  - Device: `.process`, `.process_group_write`, `.process_group_read`, `.process_group_response`
  - Devices: `.process`
  - RemoteValue: `.set`, `.respond`, `.process` and `.update_value`
  - ValueReader: `.send_group_read`
- Rename DPT transcoder modules for schema `xknx.dpt.dpt_<main-number>.py`

### Bugfixes

- Fix value scaling for sensor types: time_period_100msec, time_period_10msec, delta_time_10ms, delta_time_100ms, percentV16

### Features

- Added eager telegram data decoding for GroupValueWrite / GroupValueResponse Telegrams. DPTs for group addresses can be set using `xknx.group_address_dpt.set()`. `Telegram` has a new attribute `decoded_data` which is set when a decoder was found.

### Devices

- A Device doesn't auto-add to `xknx.devices` anymore. It can be done via `xknx.devices.async_add()` now. `xknx.devices.async_remove` stops a device from processing telegrams, removes from StateUpdater and cancels its internal tasks. Removed devices can be added again.
- `Device.shutdown` method is removed
- Refactor `ClimateMode` device
- Rename `ClimateMode` argument `group_address_operation_mode_night` to `group_address_operation_mode_economy`
- Remove DPT 3 special handling `stepwise_*` and `startstop_*` from Sensor device
- Remove `DateTime` device in favour of `DateDevice`, `TimeDevice` and `DateTimeDevice` using `datetime` objects instead of `time.struct_time`

### DPT

- DPTComplex: Common interface for DPT transcoders with multi-value data. Resulting dataclasses can be converted to and from a dict with DPT specific properties to be JSON compatible.
- Added or refactored complex DPTs and dataclasses:
  - 3.007 - DPTControlDimming
  - 3.008 - DPTControlBlinds
  - 10.001 - DPTTime - KNXTime
  - 11.001 - DPTDate - KNXDate
  - 18.001 - DPTSceneControl
  - 19.001 - DPTDateTime - KNXDateTime
  - 232.600 - DPTColorRGB - RGBColor
  - 235.001 - DPTTariffActiveEnergy - TariffActiveEnergy
  - 242.600 - DPTColorXYY - XYYColor
  - 251.600 - DPTColorRGBW - RGBWColor
  - 20.60102 - DPTHVACStatus - HVACStatus (removed DPTControllerStatus in favour of this)
- DPTEnum: Common interface for DPT representing enumueration values. Transcoders accept Enum, string or raw integer values for encoding.
  - 1.007 - DPTStep
  - 1.008 - DPTUpDown
  - 1.100 - DPTHeatCool
  - 20.102 - DPTHVACMode - HVACOperationMode
    - rename "NIGHT" to "ECONOMY" and "FROST_PROTECTION" to "BUILDING_PROTECTION" according to KNX specifications
  - 20.105 - DPTHVACContrMode - HVACControllerMode
    - rename "DRY" to "DEHUMIDIFICATION" and add some values according to KNX specifications
- Change DPT number of Enthalpy from 9.999 to 9.60000 (manufacturer specific range)
- Support dict values with "main" and "sub" keys for `DPTBase.parse_transcoder()`
- Verify DPTBinary max payload bitsize when decoding by transcoders `payload_length`

### Address

- `InternalGroupAddress` attribute `address` is renamed to `raw` to be in line with `GroupAddress` (although still str). Its value has an "i-" prefix.

### Internal

- Use `slots` in addresses, Telegram, DPTBinary, DPTArray, TPCI, APCI, DPTComplexData
- Convert Telegram and APCI to dataclasses. `Telegram` is not hashable anymore.
- RemoteValue instances use pre-decoded data from Telegrams if available and `dpt_class` for is set - otherwise they decode the data themselves in `from_knx` like before.
- Remove RemoteValueControl and unused RemoteValue1Count class
- Add value argument to RemoteValue `after_update_cb` callback

# 2.12.2 Fix thread leak 2024-03-05

### Bugfixes

- Fix thread leak when initial connection attempt fails (on threaded connection mode).

# 2.12.1 Address error messages 2024-02-26

### Internal

- More detailed address parsing error messages.

# 2.12.0 Broadcasts 2024-02-05

### Bugfixes

- `None` is not a valid address parameter for GroupAddress and IndividualAddress anymore. It raises `CouldNotParseAddress`.
- `None` in a RemoteValue or Device group address list is now ignored instead of parsed as broadcast address.
- Broadcast address ("0/0/0") is now invalid for RemoteValue and Device group addresses and raises `CouldNotParseAddress`.

### Management

- Add handling mechanism and sending method for broadcast telegrams in the management class.
- Add new management procedures for device management: `nm_invididual_address_write`,  `nm_individual_address_read`, `nm_individual_address_serial_number_read` and `nm_individual_address_serial_number_write`.

### Secure

- Parse `project_name` from an ETS Keyring.

### Internal

- Use ruff format and more ruff linters. Remove black, isort, flake8 and pyupgrade from requirements.

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
    outlet = Outlet(xknx, name="TestOutlet", group_address="1/1/11")
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

