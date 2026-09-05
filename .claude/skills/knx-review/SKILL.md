---
name: knx-review
description: Review KNX code for protocol correctness - xknx itself and projects built on it (Home Assistant KNX integration, xknxproject, custom bindings). Use when reviewing a PR, diff, issue report or file that touches DPT transcoders, telegrams, group addresses, APCI, cEMI, KNXnet-IP frames, tunnelling/routing, KNX Data Secure, management procedures, or xknx devices and remote values.
---

# Reviewing KNX code

A KNX bug is not like an ordinary bug. The code runs against physical
actuators in someone's house, over a bus that has no schema, no negotiation
and no error correction at the application layer. A wrong byte is not a
crash - it is a blind that closes at 3 a.m., a valve that opens to 100 %, or
a heating setpoint of -20.48 °C instead of 0 °C. Nothing in the type system,
the linters or the test suite catches "the bytes are wrong but well-formed",
so that is the part a review has to catch.

Reviewing KNX code well means being able to answer, for every changed line
that touches the wire: *what exact octets does this put on the bus, and is
that what the KNX Standard says those octets mean?*

This document is self-contained: it carries the KNX domain knowledge needed
to do that, then the xknx-specific contracts, then the procedure and the
checklists. It is written for an agent reviewing a diff, but works as a
human reference too.

**Using it elsewhere.** Copy this file to
`.claude/skills/knx-review/SKILL.md` in any repo to have it load on demand,
paste it into `AGENTS.md` / `CLAUDE.md` to have it always in context, or
hand it to an agent as a prompt prefix before a review. §0-§2 (spec access,
KNX domain knowledge, procedure) and §5-§7 (tests, citations, reporting)
apply to any KNX codebase; §3 (layer contracts), §4 (compatibility) and §8
(checklists) are xknx-specific and are the parts to adapt for a different
code base. In xknx itself, `AGENTS.md` carries the contributor conventions
this document assumes (spec citation format, changelog rules, tooling).

---

## 0. First: ask for the specification

**Ask the user, at the start of any review that touches the wire format,
whether they can give you access to the official KNX Standard documents.**
Do it before reading the diff - knowing you have the spec changes how you
review, and asking afterwards wastes a pass.

The KNX Standard is the only authority for byte layouts, state machines,
timeouts and procedure steps. Without it you are reviewing plausibility;
with it you are reviewing correctness. Almost every finding in this
document's top severity band is only *provable* against the spec.

Ask concretely, e.g.:

> Do you have the KNX Standard documents available locally? If you point me
> at the folder (or the specific PDFs for Application Layer 03.03.07 /
> Management Procedures 03.05.02 / …), I can check this PR's byte layout and
> the spec citations against the real text instead of inferring them. I
> won't copy them into the repo or into any PR comment.

**Licensing - treat the documents as confidential input, not content.**
The KNX Standard is copyrighted and licensed to the person who obtained it.
Therefore:

- **Never commit spec files to the repository**, never attach them to a PR,
  never upload them anywhere, and never paste long passages into a public
  comment, issue or commit message.
- Keep them outside the working tree, or - if they must live inside it -
  behind a local `.gitignore` entry that is *not* committed
  (`.git/info/exclude` is the right place for a personal path).
- In public review comments, **cite and paraphrase**; quote at most the one
  sentence a finding turns on, the way the existing code comments in this
  repo do. A citation plus a one-line paraphrase is both safer and more
  useful than a wall of quoted text.
- The user's local copy is theirs. Do not "helpfully" copy it into the
  repo, a scratch directory that is committed, or a gist.

**Working with them once you have them**

- PDFs: read them directly, or convert with `pdftotext -layout` into a
  scratch directory outside the repo when you need to grep across a
  document.
- Take the **version from the document's own title page / revision block**,
  not from a neighbouring citation and not from memory. That is exactly the
  version that goes into the code's citation.
- Map claim → document with the volume/chapter scheme (`03.03.07` = Volume
  3, chapter 3, subchapter 7). `AGENTS.md` lists the documents xknx cites
  and their confirmed versions - use it to know *which* file to ask for.
- If the user has a persistent location, suggest they record it locally
  (a `KNX_SPEC_DIR` env var, or a line in a personal `CLAUDE.md` /
  `.claude/settings.local.json`) so future sessions don't have to ask again.

**If the spec is not available** - which is the normal case - say so, and
review accordingly:

- Fall back on the ordering in §2 Step 2: sibling implementations in the
  repo, known-good captures from ETS or real devices, the issue report.
- Mark every wire-format conclusion as unverified in your review, explicitly:
  "not checked against the standard".
- **Do not fill the gap with recalled paragraph numbers or versions.** See
  §6 - a fabricated citation is worse than an admitted gap.

---

## 1. KNX in the amount of detail a reviewer needs

### 1.1 Group communication

KNX devices exchange **telegrams**. The kind that carries application data is
addressed to a **group address** (GA) - a logical channel, not a device. Many
devices can send to and listen on the same GA. There is no handshake, no
schema exchange, no reply-with-error: a sender emits octets and every
listener interprets them with whatever DPT it was configured with in ETS.

Consequences that matter in review:

- **Nothing on the bus tells you the type.** A 1-byte payload is a
  percentage, a scene, an enum or a counter depending only on ETS
  configuration. Code that guesses a type from payload length is guessing.
- **A misinterpretation is silent.** No exception, no NACK - just a wrong
  value acted on by real hardware.
- **Being "lenient" is dangerous, not friendly.** Widening an accepted range
  or clamping instead of raising means writing a value the actuator will
  happily execute.

Three application services carry group values:

| Service | Meaning |
|---|---|
| `GroupValueRead` | "Whoever holds this value, send it" - no payload |
| `GroupValueResponse` | The answer to a read |
| `GroupValueWrite` | "This is the new value" - unsolicited |

A response and a write carry the same payload and, in almost all client
code, mean the same thing. Read requests are answered only by devices that
own the value.

### 1.2 Addresses

- **Group address**: 16 bit. 3-level `main/middle/sub` = 5/3/8 bits
  (0-31 / 0-7 / 0-255); 2-level `main/sub` = 5/11 bits; free level = raw
  0-65535. Raw `0` is the **broadcast address**, never a normal GA.
- **Individual address (IA)**: 16 bit, `area.line.device` = 4/4/8 bits.
  `x.y.0` is a line coupler, `0.0.0` means "unset" in xknx and is filled in
  with the interface's own address when sending.
- Same 16 bits, different meaning - a function that takes "an address" and
  does not distinguish GA from IA is a bug waiting to happen.

### 1.3 Payload packing - the 6-bit rule

The APCI field is 10 bits; its lowest 6 bits are either **the data itself**
(for payloads of 6 bits or less) or zero, with the data in the octets that
follow.

That is the whole reason xknx has two payload classes:

- `DPTBinary(value)` - **small payload**, value packed into those 6 bits
  (`0x00`-`0x3F`). Used by DPT 1 (1 bit), DPT 2 (2 bit), DPT 3 (4 bit).
- `DPTArray(bytes)` - **appended octets**, one or more full bytes. Used by
  everything from DPT 4 / 5 (1 byte) upwards.

They are *different encodings on the wire*, not two spellings of the same
thing. `DPTBinary(1)` and `DPTArray((1,))` are different telegrams. Getting
this wrong is one of the most common defects in new DPT code and in code
that constructs telegrams by hand.

### 1.4 DPTs

A datapoint type is written `main.sub` (e.g. `9.001`). **Main** fixes the
encoding and length; **sub** fixes range, unit and semantics. `5.001`
(0-100 %) and `5.010` (0-255 counter) are the same octet with different
meanings - a value of `200` is valid for one and out of range for the other.

The majors you will meet, with the traps each one carries:

| DPT | Encoding | Trap |
|---|---|---|
| 1.yyy | 1 bit (`DPTBinary`) | Sub-type decides the *words* (on/off, up/down, open/close), never the bit. Don't invert semantics for convenience. |
| 2.yyy | 2 bit: control + value | Control bit = "is this command binding" - dropping it loses meaning. |
| 3.yyy | 4 bit: direction + 3-bit step code | `step_code == 0` means **break/stop**, not "step of zero". Range is subdivided into `2**(step_code-1)`. |
| 4.yyy | 1 byte character | ASCII (4.001) vs ISO-8859-1 (4.002). |
| 5.yyy | 1 byte unsigned | 5.001 scales 0-255 to 0-100 %: `round(raw/255*100)`. Rounding must be symmetric so a round trip is stable. 5.003 is 0-360°, 5.004 is 0-255 %. |
| 6.yyy | 1 byte signed (two's complement) | 6.020 is a status *bit field*, not a number. |
| 7/8.yyy | 2 byte unsigned / signed | Big-endian. Many sub-types have a resolution factor (e.g. 7.002 ms, 7.012 mA). |
| 9.yyy | 2 byte float: sign, 4-bit exponent, 11-bit mantissa; `value = 0.01 * M * 2**E` | Not IEEE 754. Resolution degrades with magnitude - `to_knx(from_knx(x))` is stable, `from_knx(to_knx(x))` is *not* exact. Values near zero are special-cased (see §3.1). |
| 10.yyy | 3 byte time | Top 3 bits of octet 0 are day-of-week (0 = "no day"). |
| 11.yyy | 3 byte date | 2-digit year: `>= 90` → 1990-1999, `< 90` → 2000-2089. |
| 12/13.yyy | 4 byte unsigned / signed | 13.010 etc. are energy counters - overflow and sign matter. |
| 14.yyy | 4 byte IEEE 754 float | The *only* IEEE float in KNX. Don't confuse with DPT 9. |
| 16.yyy | 14 byte string, zero-padded | Fixed 14 octets, always. ASCII (16.000) vs Latin-1 (16.001); un-encodable characters must not be silently mangled. |
| 17.001 | 1 byte scene number | Raw `0`-`63` maps to scene **1-64**. Off-by-one is the default bug here. |
| 18.001 | 1 byte scene control | Bit 7 = learn, bits 0-5 = scene number (same +1 offset). |
| 19.001 | 8 byte date+time | Carries a flags octet: quality, DST, working day, "field valid" bits. Dropping the flags loses information the sender meant to convey. |
| 20.yyy | 1 byte enum | Unknown raw values must raise, not fall back to a default. |
| 232/251/242… | multi-byte structs | RGBW (251.600) has a **validity nibble** in the last octet: a channel with its bit clear is *unset*, not zero. Reserved octets must be sent as `0x00` and ignored on receive. |

### 1.5 Transport: how a telegram reaches the bus

- **Tunnelling (KNXnet-IP, UDP/TCP)**: point-to-point to one interface.
  Frames carry an 8-bit **sequence counter** that wraps at `0xFF`, and every
  request must be ACKed. A repeated frame with the same counter is a
  retransmission; a gap means frames were lost and the connection has to be
  torn down. Heartbeat (`CONNECTIONSTATE_REQUEST`) keeps it alive.
- **Routing (multicast)**: no ACKs, no sequence numbers, no delivery
  guarantee. Flow control is `ROUTING_BUSY` / `ROUTING_LOST_MESSAGE` - a
  router telling senders to back off. Ignoring busy means flooding the
  installation.
- **cEMI** is the frame format wrapping the telegram inside either
  transport. An outgoing `L_Data.req` is answered by an `L_Data.con`
  confirmation from the local stack - this only confirms the *interface*
  accepted it, never that a device received it.
- **KNX Secure**: *IP Secure* encrypts the IP tunnel; *Data Secure* protects
  individual telegrams end-to-end with a per-GA key, a monotonic sequence
  number and an MAC. Replay protection depends on that counter never going
  backwards.

### 1.6 Management: point-to-point, broadcast, procedures

Everything above is group communication - anonymous, connectionless,
fire-and-forget. **Management** is the opposite: addressed to one device by
**individual address**, connection-oriented, sequenced and acknowledged.
It is how ETS reads a device's properties, assigns addresses, downloads
applications and restarts hardware. Review it conservatively: a group-value
bug sets a wrong brightness, a management bug can leave a physical device
unreachable until someone walks to it and presses the programming button.

**Three communication modes**, distinguished by TPCI, not by payload:

| Mode | TPCI | Used for |
|---|---|---|
| Connection-oriented (P2P) | `T_Connect`, `T_DataConnected(seq)`, `T_Ack(seq)`, `T_Nak(seq)`, `T_Disconnect` | Property/memory access, restart, authorize - anything needing reliability |
| Broadcast | `T_DataBroadcast` to GA `0/0/0` | Finding devices in programming mode, address assignment - *any number* of devices may answer |
| Connectionless (point-to-point) | `T_DataIndividual` | Simple addressed requests without a connection |

**The connection-oriented state machine** (Transport Layer 03.03.04) is
where the subtle bugs live:

- A 4-bit sequence number per direction, wrapping at `0xF` - **not** the
  8-bit KNXnet-IP tunnelling counter; they are different fields at different
  layers, and confusing them is a classic mistake.
- Each numbered telegram must be acknowledged. Receiving the **expected**
  sequence number → ACK and advance. Receiving the **previous** one → the
  peer missed our ACK, so ACK again and *do not process the payload twice*.
  Anything else → NAK.
- Acknowledging is a **transport-layer duty**: it does not depend on whether
  the application layer is waiting for something. ACK first, dispatch after.
- While CLOSED, nothing is acknowledged - including telegrams from a device
  you were previously talking to.
- Connections are half-open-prone: the peer can send `T_Disconnect` at any
  time, and every pending wait has to be resolved when it does.

**The application layer on top** (Application Layer 03.03.07) provides the
`A_*` services: `A_PropertyValue_Read/Write`, `A_PropertyDescription_Read`,
`A_Memory_Read/Write`, `A_DeviceDescriptor_Read`, `A_Restart`,
`A_Authorize_Request`, `A_IndividualAddress_Read/Write`. Two properties of
these matter constantly in review:

- **APDU length is tiny.** A standard frame carries at most 15 octets after
  the TPCI octet. A device's real capacity is its `PID_MAX_APDU_LENGTH`
  property; until you have read it, 15 is the only safe assumption.
  Anything longer must be chunked, and the chunking is the code's job.
- **Property access is `(object_index, property_id, count, start_index)`**
  where `count` is 4 bits (max 15 elements) and `start_index` is 12 bits
  (max 4095). Element index `0` is special: reading it returns the
  property's *current element count*, not element data; writing `0` elements
  to it resets the array. A response with `nr_of_elem == 0` is the device
  reporting **an error** (unknown object/property, missing access rights) -
  not an empty result.

**Procedures** (Management Procedures 03.05.02) are the scripted sequences
built from those services: `NM_*` for network management (individual
address read/write/check, serial-number based addressing), `DM_*` and
`DMP_*` for device management (connect, authorize, restart, property
read/write/scan/verify), `FTP_*` for file transfer. The spec prescribes the
*steps and their order*, and that order usually exists for a safety reason -
checking whether an address is already occupied before writing it, verifying
a device answers before restarting it. A procedure that "simplifies" the
spec's step sequence is a finding, not an optimization.

---

## 2. Review procedure

### Step 1 - Classify the change

Before reading the diff line by line, answer:

1. **Which layer?** DPT transcoder / RemoteValue / Device / telegram-APCI /
   cEMI / KNXnet-IP frame / io-connection / management / secure.
2. **Does it change bytes on the wire, or only Python-side behavior?**
   Wire changes need byte-level proof; everything else needs API-compat
   thinking.
3. **Blast radius.** A fix in `DPTBase`, `RemoteValue`, `Telegram` or
   `CEMIHandler` touches every device and every downstream consumer. A new
   `DPT` subclass touches only users of that DPT. Calibrate scrutiny to
   this, not to diff size.

### Step 2 - Establish ground truth before judging

Do not review a wire-format change against the diff's own reasoning. Get an
independent reference for what the octets should be:

- The KNX Standard document - **read the cited paragraph, don't take the
  citation's word for it**. If you don't have the documents, ask (§0);
  for a protocol or management change it is worth asking even mid-review.
- Existing sibling implementations in the repo (the other DPT 9 subclasses,
  the other KNXIP bodies) - consistency with them is evidence.
- Known-good captures: values from ETS, from a real device, from the issue
  report that triggered the PR.

If you cannot establish ground truth, say so in the review instead of
approving on plausibility. "I could not verify the byte layout for DPT
x.yyy; please add a reference" is a legitimate review outcome.

### Step 3 - Read the diff against the layer contract

§3 lists the contract for each layer. Work through the applicable one.

### Step 4 - Read the tests as evidence, not decoration

See §5. The key question: **would these tests fail if the encoding were
wrong?** A test that only round-trips the implementation against itself
proves nothing.

### Step 5 - Compatibility, changelog, citations

See §4 and §6.

### Step 6 - Report

See §7.

---

## 3. Layer contracts (xknx)

### 3.1 DPT transcoders (`xknx/dpt/`)

Every transcoder is a `DPTBase` subclass with `from_knx()` / `to_knx()`
classmethods. Check:

**Class attributes**

- `payload_type` is `DPTArray` or `DPTBinary` per §1.3 - not "whatever the
  parent had".
- `payload_length` is **bytes for `DPTArray`, bits for `DPTBinary`**. This
  double meaning is a real source of bugs; verify against the DPT's actual
  size.
- `dpt_main_number` / `dpt_sub_number` match the spec. `dpt_sub_number =
  None` marks the *generic* main-number transcoder (the ETS fallback when a
  project resolves only to "DPT 9"); there must be at most one per main
  number.
- `value_type` is a unique, stable, snake_case string. **It is public API** -
  Home Assistant configuration and xknxproject mappings reference it. Renaming
  one is a breaking change; a typo in one is forever.
- `unit` and, for `DPTNumeric`, `value_min` / `value_max` / `resolution`
  describe the *DPT's* range, not the encoding's. `DPTTemperature` (9.001) is
  -273..670760, even though the 2-byte float encoding reaches lower.

**`from_knx()`**

- **Calls `cls.validate_payload(payload)` first** and indexes only its
  return value. Indexing `payload.value` directly skips type and length
  checking - a malformed telegram from any device on the bus then raises
  `IndexError` instead of `CouldNotParseTelegram`, which propagates out of
  the receive path.
- Masks reserved bits instead of trusting them zero. Devices in the field
  do send garbage in reserved bits.
- Raises `CouldNotParseTelegram` for structural problems (wrong type/length)
  and `ConversionError` for values that cannot be interpreted. Never returns
  `None`, never returns a partly-decoded value.
- Out-of-range raw values raise - they are not clamped to `value_min`.

**`to_knx()`**

- Accepts the documented input types and rejects everything else with
  `ConversionError` (not `ValueError`, not `TypeError` leaking through).
- Range check happens **before** encoding, against `value_min`/`value_max`.
- Reserved bits are written as `0`.
- No silent clamping and no silent rounding of a value the caller will
  believe was sent verbatim.

**Round-trip properties** - state these explicitly in the review when they
are not obviously held:

- For every raw payload the DPT accepts: `to_knx(from_knx(raw)) == raw`.
  This must hold *exactly*; if it can't (lossy encodings), the PR needs to
  say why.
- `from_knx(to_knx(value))` is only approximately `value` for lossy DPTs
  (9.yyy, scaled 5.yyy). Tests asserting exact equality there are wrong
  even when they currently pass.
- DPT 9 has a deliberate near-zero deviation from ETS in xknx: any value
  whose raw hundredths round to `0` (roughly `|value| <= 0.005`) encodes to
  `0x0000`, including small negatives, where ETS would emit `0x8000` -
  which decodes to -20.48. Don't "fix" that without reading the comment.

**Enum DPTs** (`DPTEnum` + `DPTEnumData`): member *values* are the raw KNX
integers - changing one changes the wire. Member *names* are public API too
(they are parsed from strings and used as translation keys). Unknown raw
values must raise `ConversionError`, not map to a fallback member.

**Complex DPTs** (`DPTComplex` + `DPTComplexData`): `from_dict()` /
`as_dict()` must round-trip, the dataclass fields carry `value_min` /
`value_max` metadata used to generate the schema, and `None` fields mean
"not valid / not set" where the DPT has validity bits - not zero.

**Registration**: a new DPT class must be exported from `xknx/dpt/__init__.py`
and added to the lookup table in `test/dpt_tests/dpt_lookup_test.py`. The
meta-tests in `test/dpt_tests/dpt_test.py` already enforce unique
`value_type`s, unique `(main, sub)` pairs and presence of required
attributes - if the PR doesn't run them, run them.

### 3.2 RemoteValue (`xknx/remote_value/`)

A `RemoteValue` binds one DPT to group addresses and holds the last known
value. Contract points reviewers miss:

- **`set()` must not assign `self._value`.** It sends a telegram; the value
  is set when that outgoing telegram comes back through `process()`. Code
  that sets the value directly makes the local state diverge from what was
  actually put on the bus, and suppresses the callback.
- `process()` returns `bool` (was this telegram mine?) and must return
  `False` - not raise - for addresses it doesn't own.
- The de-duplication (`self._value != decoded_payload`) is deliberate:
  repeated identical values don't re-fire callbacks unless
  `always_callback` is set. Changing that changes behavior for every
  consumer.
- `group_addresses()` must yield **all** addresses including passive ones -
  it drives telegram routing and the state updater.
- `readable` means a state address exists; `writable` means a writable
  address exists. Sending on a non-writable RV logs a warning and returns;
  it must not raise.
- New attributes need a `__slots__` entry - all remote values define
  `__slots__`, so a stray assignment raises `AttributeError`.

### 3.3 Devices (`xknx/devices/`)

- **`_iter_remote_values()` must yield every RemoteValue the device owns.**
  A forgotten one silently loses state updates, group-address registration
  and device-name propagation. This is the single most common device bug;
  check it against the `__init__` on every device PR.
- `process_group_write()` / `process_group_response()` /
  `process_group_read()` - the default is that devices ignore reads;
  responses are treated like writes. A device that answers reads must be
  deliberate about it.
- `after_update()` swallows exceptions from consumer callbacks by design -
  don't "clean that up".
- Background work goes through `xknx.task_registry`, not a bare
  `asyncio.create_task()`; untracked tasks get garbage-collected mid-flight
  and don't restart after a reconnect.
- Device attributes and callback timing are public API - see §4.

### 3.4 Telegram, APCI, addresses (`xknx/telegram/`)

- `Telegram` is a dataclass compared by value; `decoded_data` and
  `data_secure` are `compare=False` on purpose (they are context, not
  identity).
- TPCI is inferred in `__post_init__` from the destination address type -
  GA `0` gets `TDataBroadcast`, other GAs `TDataGroup`, IAs
  `TDataIndividual`. Code that constructs telegrams with an explicit TPCI
  should have a reason.
- `InternalGroupAddress` never goes to the bus. Any new code path that
  serializes a destination address must handle it - usually by refusing.
- APCI parsing operates on attacker-controlled bytes: length and octet
  counts must be validated before slicing.

### 3.5 cEMI and KNXnet-IP frames (`xknx/cemi/`, `xknx/knxip/`)

Everything here parses **remote input**. Rules:

- `from_knx(raw)` returns the number of octets consumed; callers rely on it
  to advance. An implementation that returns the wrong count corrupts every
  following field.
- Length fields in the frame are *claims*, not facts. Compare declared
  length against actual buffer length before slicing; `raw[a:b]` on a short
  buffer silently returns fewer bytes rather than raising.
- Every parse failure must surface as `CouldNotParseKNXIP` /
  `CouldNotParseCEMI` / `UnsupportedCEMIMessage`. `struct.error`,
  `IndexError`, `ValueError` or `KeyError` escaping into the receive loop is
  a defect - the loop must survive any malformed frame from the network.
- `calculated_length()` must agree with `len(to_knx())`. Mismatches produce
  frames a gateway rejects with no useful error.
- Unknown service types / message codes are logged and dropped, never
  raised into the loop.

### 3.6 Connection layer (`xknx/io/`)

- **Sequence counters**: 8-bit, wrap `& 0xFF`. Check the wrap, check that a
  repeated counter is treated as a retransmission and a gap triggers
  reconnect, and that the counter resets on reconnect.
- **Timeouts** use `asyncio.timeout`; every request that awaits a response
  needs one. A missing timeout is a permanent hang, not a slow path.
- **Reconnect** must restore state: sequence numbers, tunnel address,
  registered tasks, state-updater subscriptions. Review what is *not* reset
  as carefully as what is.
- **Never block the event loop.** No `time.sleep`, no synchronous socket
  I/O, no blocking file or crypto calls in a callback.
- Callbacks fired from the receive path are synchronous and must not raise;
  an exception there kills the reader task and the connection with it.
- **Secure**: no key material, session key, device authentication code or
  password in log output, `__str__`, `__repr__` or exception messages -
  check this explicitly on any diff under `secure/` or `ip_secure`.
  Sequence numbers must be verified monotonic; accepting a lower one
  re-opens replay attacks.

### 3.7 Management transport (`xknx/management/management.py`)

`Management` owns the open `P2PConnection`s and the `Broadcast` channel and
dispatches incoming telegrams between them. Review points:

**Dispatch**

- Only connection-oriented TPCIs (`TDataConnected`, `TAck`, `TNak`,
  `TDisconnect`) belong to a `P2PConnection`. The **sender address alone is
  not enough**: a device you hold a connection with can also answer a
  broadcast, and that telegram must reach the broadcast context, not the
  connection. Any new dispatch logic that keys only on `source_address` is
  reintroducing a fixed bug.
- Nothing is acknowledged without a matching open connection. A `T_Ack` sent
  from the CLOSED state tells an uninvolved device it is in a connection it
  never opened.
- Incoming `TConnect` is refused with `TDisconnect` - xknx is a client, not
  a management server. A change accepting inbound connections is a design
  change, not a bugfix.

**`P2PConnection` sequence handling**

- Two independent counters: the outgoing generator and
  `_expected_sequence_number` for incoming, both `& 0xF`. Check every new
  wrap arithmetic against 4 bits - `& 0xFF` here is the tunnelling counter
  leaking into the wrong layer.
- The three incoming cases must all be present: expected → ACK + advance;
  `expected - 1 & 0xF` → ACK again and **return without processing** (it is
  a retransmission); anything else → NAK and drop. Losing the repeat case
  means duplicate processing; losing the NAK means silent desync.
- ACK handling: a `TNak` is an error, and an ACK whose sequence number does
  not match the request must raise rather than be accepted.
- `send_data()` resends **once** after `MANAGEMENT_ACK_TIMEOUT`, then raises
  `ManagementConnectionTimeout`. Unbounded retries are a finding.
- `wait_for_ack=False` is only correct for commands the device does not
  answer - `A_Restart` being the canonical one, because the device is gone
  before it could ACK.
- The rate limit (default 20 telegrams/s) exists because devices are slow
  and drop what they cannot process. Removing or raising it needs a reason.
- Futures (`_ack_waiter`, `_response_waiter`) must be re-created for the
  next request and resolved - with `ManagementConnectionRefused` - when the
  peer disconnects. A pending waiter left unresolved on disconnect is a
  hang, not an error.

**`Broadcast`**

- The receive context is opened **before** the request is sent; a device
  answering immediately must not be missed. A refactor that sends first is a
  race.
- A broadcast request yields *any number* of responses (or none) until the
  timeout - it is not request/response. Code treating the first answer as
  "the" answer must justify it, and code that needs uniqueness must check it
  explicitly (as `nm_individual_address_read(raise_if_multiple=True)` does).
- The timeout is armed around the wait for the next telegram only, never
  across a `yield`. A timeout spanning the `yield` stays armed on an
  abandoned generator and later cancels whoever entered it - check this in
  any change to a receive loop.

### 3.8 Management procedures (`xknx/management/procedures/`)

**Structure and naming** - the package docstring in
`procedures/__init__.py` is canonical; check new procedures against it:

- One public `async def` per file, `procedures/<family>/<spec_name>.py`,
  `network/` for `NM_*`, `device/` for `DM_*`/`DMP_*`, `ftp/` for `FTP_*`.
- The two forms: `<spec_name>(xknx, ...)` opens and closes its own
  connection or broadcast; `<spec_name>_conn(conn, ...)` runs on an
  already-open connection for chaining. `_conn` is an xknx convention;
  `dm_restart_r_co` is the exception, because `RCo` is the real KNX name.
- Module docstring carries the spec name and a full citation; the procedure
  docstring documents parameters, return value **and every exception**.
- Re-exported from the family `__init__.py` and the package `__init__.py`.
- Mirrored test at `test/management_tests/procedures/<family>/test_<name>.py`.

**Correctness against the spec**

- The step sequence matches the procedure's spec paragraph, in order. Where
  the implementation deliberately deviates (or skips an optional step), a
  comment must say why, with the citation - as the `DMP_InterfaceObject*`
  procedures do for the optional `A_PropertyDescription_Read` step.
- Preconditions are enforced, not assumed: `DM_Connect` before property
  access, exactly one device in programming mode before an address write,
  a check that the target address is not already occupied.
- Post-conditions too: `nm_individual_address_write` verifies the device
  answers at its new address and restarts it to leave programming mode -
  dropping that leaves the installation in a half-programmed state.

**Chunking and bounds** - the most defect-prone part of the property
procedures:

- **Validate the whole transfer up front**, not per chunk. A `count` that
  pushes a later chunk's `start_index` past `0xFFF` must fail *before* the
  first chunk is written, otherwise the device is left partly written.
- `count` ≤ 15 (4 bits), `start_index` ≤ 4095 (12 bits), `object_index`
  0-255, `property_id` 1-255.
- Chunk size is derived from `max_apdu_length` minus the fixed PDU header
  octets, and defaults to the spec's 15-octet fallback unless the device's
  real `PID_MAX_APDU_LENGTH` was read. A procedure that assumes a larger
  APDU without having read it is a finding.
- Element size is not on the wire. Reads that don't know it must learn it
  from a single-element first request before widening - not guess.
- `nr_of_elem == 0` in a response → raise `ManagementConnectionError`
  (device-side error), never return empty data. An element count that does
  not match the request is equally an error.
- `start_index == 0` means "how many elements are there" on read (and
  requires `count == 1`), and "reset the array" on write. A procedure
  treating index 0 as ordinary data is wrong in both directions.

**Safety**

- Every path closes its connection - use `async with
  xknx.management.connection(addr)`, not manual connect/disconnect.
- Destructive procedures (address write, restart, memory/property write,
  authorize) need spec citations and tests; they change physical devices.
  Review them as you would a migration script, and be explicit in your
  findings about what a mistake costs.
- Secrets: authorization keys must not reach logs or exception messages.

**Tests** for procedures assert the exact telegram sequence, including the
TPCI and sequence numbers:

```python
xknx.cemi_handler = AsyncMock()
async with xknx.management.connection(individual_address) as conn:
    await dm_restart_r_co(conn)
assert xknx.cemi_handler.send_telegram.call_args_list == [
    call(connect), call(restart), call(disconnect)
]
```

A procedure test that only asserts "no exception raised" proves nothing -
the whole content of a procedure *is* the telegram sequence. Device
responses must be simulated for both the success and the error return
codes.

### 3.9 Async and callbacks (all layers)

- Fire-and-forget tasks must be tracked (`TaskRegistry`) or awaited.
- `xknx.telegrams` is an `asyncio.Queue` filled with `put_nowait()` -
  outgoing telegram creation is sync on purpose.
- Tests must not `asyncio.sleep()` to wait for behavior - the `time_travel`
  fixture advances the loop clock deterministically.

---

## 4. Compatibility - the part that bites downstream

xknx is consumed by the Home Assistant KNX integration. Treat the following
as **breaking**, even when no signature changes:

- The Python type or value a decoded DPT returns (`int` → `float`, raw int →
  enum member, scalar → dataclass).
- A `value_type` string, DPT class name, enum member name, or device
  attribute name.
- **When** a callback fires - adding, removing or reordering callbacks for a
  given telegram, or changing the de-duplication behavior.
- Default values, argument order (all device arguments are keyword-only),
  or exception types raised.
- Anything that changes the bytes sent for the same API call.

Every user-facing change belongs in `docs/changelog.md` under
`# Unreleased changes`, in the matching `### Category` section. Breaking
changes need a before/after snippet, not prose. Match the existing entries'
style: they explain *why*, not just *what*, and cite the spec where behavior
follows from it. A PR that changes wire behavior with no changelog entry is
incomplete - say so.

---

## 5. Reviewing the tests

**What a good xknx test looks like**

- Byte vectors on both sides, from an external source (spec example, ETS,
  a real device capture), asserted in both directions:
  ```python
  assert DPT2ByteFloat.to_knx(-30.00) == DPTArray((0x8A, 0x24))
  assert DPT2ByteFloat.from_knx(DPTArray((0x8A, 0x24))) == -30.00
  ```
- Boundaries: `value_min`, `value_max`, one step outside each,
  `payload_length ± 1`, and the wrong payload class
  (`DPTBinary` where `DPTArray` is expected).
- Error paths asserted by type:
  `pytest.raises(ConversionError)` / `pytest.raises(CouldNotParseTelegram)`.
- Device tests assert the **telegram queue contents**, not internal state:
  ```python
  assert xknx.telegrams.qsize() == 1
  assert xknx.telegrams.get_nowait() == Telegram(
      destination_address=GroupAddress("1/2/3"),
      payload=GroupValueWrite(DPTBinary(1)),
  )
  ```
- Callbacks verified with `Mock` (called / not called / call args), timing
  with the `time_travel` fixture.
- New `__str__` implementations covered in `test/str_test.py`.

**Red flags**

- Round-tripping the implementation against itself
  (`from_knx(to_knx(x)) == x`) with no independent byte vector - passes
  even when the encoding is completely wrong.
- Only happy paths; no malformed-payload test on a parser.
- `asyncio.sleep()` in tests.
- Asserting exact float equality on a lossy DPT.
- A bugfix PR with no test that fails without the fix. Ask for one; if the
  fix is real it is usually two lines of test.

Run them - don't infer:

```
uv sync
uv run pytest                       # full suite
uv run pytest test/dpt_tests -q     # focused
uv run prek run --all-files         # ruff, format, mypy, pylint, codespell
```

Formatting and typing are enforced by tooling - don't spend review comments
on what `ruff` and `mypy` already catch.

---

## 6. Spec citations

The repo cites the KNX Standard in the form
`KNX v<version> - <Title> <document number> - §<paragraph>`, e.g.
`KNX v01.02.02 - Transport Layer 03.03.04 - §2 TPDU`. Documents carry
*different, independent* version numbers; `AGENTS.md` holds the table of
confirmed versions.

As a reviewer:

- A citation without a version is incomplete - flag it.
- **Never accept a version that was inferred** from a neighbouring citation
  "for consistency". If the author can't confirm it, the citation should say
  less rather than guess.
- If you have the document (§0), verify the paragraph says what the code
  claims, and take the version from that document's own revision block. If
  you don't have it, ask for it - and until you do, say that you couldn't
  verify the citation rather than approving it.
- Protocol behavior asserted without a source ("devices expect this") is a
  question for the review, not a fact.

The same rule applies to your own review comments: **do not invent spec
paragraph numbers.** Say "this contradicts how the other DPT 9 subclasses
encode, and I couldn't find a spec basis for it" - that is a useful finding.
A fabricated citation is worse than no citation, because it will be trusted
and propagated.

---

## 7. Writing the review

Rank findings by what they do to a real installation, not by how clever they
are to spot:

1. **Damage to a physical installation** - a management procedure that
   writes a wrong individual address, restarts or reprograms the wrong
   device, or leaves one half-programmed. Recovery means someone standing in
   front of the hardware.
2. **Wrong bytes on the bus** - wrong encoding, wrong DPT, wrong payload
   class, off-by-one in a scene or scaling. Real devices act on these.
3. **Crash or hang in the receive/connection path** - unhandled parse error,
   missing timeout, blocked event loop, untracked task. Takes the whole
   connection down.
4. **Silent data loss** - swallowed exception, dropped reserved/validity
   bits, missing RemoteValue in `_iter_remote_values()`, callback that never
   fires.
5. **Unflagged breaking change** - API or behavior change with no changelog
   entry.
6. **Missing/weak test** for the behavior the PR claims to fix.
7. Style, naming, docs - lowest, and skip whatever the linters own.

For each finding, give: **the file and line**, **the concrete failure**
(input → wrong output, with actual octets where it is an encoding issue),
and **why the spec or the surrounding code says otherwise**. Prefer a
one-line reproduction over a paragraph of prose:

> `dpt_17.py:44` - `to_knx(64)` would encode to `DPTArray((0x40,))`, one
> octet past the scene range: raw `0x00`-`0x3F` maps to scenes 1-64, so the
> boundary check has to run on the *raw* value after the `-1`, not on the
> input. Round trip breaks: `from_knx(to_knx(64))` returns 65.

(That is an illustration of the shape, not a live finding - check the real
boundary logic before reporting it.)

Say plainly when you could not verify something. On a KNX PR, "I can't
confirm this byte layout" is a more useful review than a confident guess.

---

## 8. Checklists

### New DPT transcoder

- [ ] `payload_type` / `payload_length` correct (bytes for array, bits for binary)
- [ ] `dpt_main_number` / `dpt_sub_number` match the spec; no duplicate pair
- [ ] `value_type` unique, snake_case, stable; `unit` set where applicable
- [ ] `value_min` / `value_max` / `resolution` are the DPT's range, not the encoding's
- [ ] `from_knx()` calls `validate_payload()` first; masks reserved bits
- [ ] `to_knx()` range-checks before encoding; writes reserved bits as 0
- [ ] Raises `ConversionError` / `CouldNotParseTelegram`, nothing else escapes
- [ ] Exact round trip `to_knx(from_knx(raw)) == raw` for all valid raw
- [ ] Exported in `xknx/dpt/__init__.py`
- [ ] Added to `test/dpt_tests/dpt_lookup_test.py`
- [ ] Tests with external byte vectors, boundaries, and error cases
- [ ] Changelog entry under `### DPT`

### New / changed device

- [ ] Every RemoteValue yielded by `_iter_remote_values()`
- [ ] Group read / write / response handling deliberate
- [ ] Tests assert telegram queue contents, not internals
- [ ] Callbacks fire when expected and not when not
- [ ] Tasks registered with `TaskRegistry`; removed in `async_remove_tasks()`
- [ ] `__str__` covered in `test/str_test.py`
- [ ] Docs page under `docs/` updated
- [ ] Changelog entry under `### Devices`

### Protocol / frame change

- [ ] Byte layout verified against a cited spec paragraph (with version)
- [ ] `from_knx()` returns the correct consumed length
- [ ] Declared lengths validated against actual buffer length
- [ ] `calculated_length()` == `len(to_knx())`
- [ ] Malformed input raises only the `CouldNotParse*` family
- [ ] Unknown types logged and dropped, not raised
- [ ] Tests feed raw bytes, including truncated and oversized frames

### Connection / io change

- [ ] Sequence counter wrap, retransmission and gap handling
- [ ] Every await that can hang has a timeout
- [ ] Reconnect restores sequence numbers, tasks and subscriptions
- [ ] No blocking calls in the event loop
- [ ] Callbacks in the receive path cannot raise
- [ ] No secrets in logs, `__str__` or exception messages
- [ ] Tests use `time_travel`, not `asyncio.sleep`

### Management procedure

- [ ] File layout, naming and the two forms match `procedures/__init__.py`
- [ ] Module docstring names the procedure and cites spec + version
- [ ] Step sequence matches the spec paragraph; deviations justified in a comment
- [ ] Preconditions enforced (connection open, one device in programming mode, address free)
- [ ] Post-conditions completed (verify reachable, restart to leave programming mode)
- [ ] `count` ≤ 15, `start_index` ≤ 4095, whole transfer bounds-checked before the first chunk
- [ ] Chunk size derived from `max_apdu_length`; 15-octet fallback unless `PID_MAX_APDU_LENGTH` was read
- [ ] `nr_of_elem == 0` and mismatched element counts raise, never return empty
- [ ] `start_index == 0` handled as element-count query (read) / array reset (write)
- [ ] 4-bit sequence arithmetic (`& 0xF`), not the 8-bit tunnelling counter
- [ ] Connection closed on every path, including errors (`async with ... connection()`)
- [ ] `wait_for_ack=False` only where the device genuinely does not answer
- [ ] Authorization keys absent from logs and exception messages
- [ ] Test asserts the exact telegram sequence incl. TPCI, and covers device error codes
- [ ] Re-exported from both `__init__.py` files
- [ ] Changelog entry

### Any PR

- [ ] `uv run pytest` green
- [ ] `uv run prek run --all-files` green
- [ ] Changelog entry present for user-facing changes; breaking changes have before/after
- [ ] Spec citations carry a version and were not guessed
- [ ] The test suite would fail without the fix
