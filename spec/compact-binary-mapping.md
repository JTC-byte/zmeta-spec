# ZMeta Compact Binary Mapping (Profile L)

This document defines an optional **compact wire encoding** for Profile L links.
It preserves ZMeta semantics by expanding to the canonical JSON envelope before validation
and downstream translation (e.g., CoT/TAK).

## Scope: locked v1.0 events only, fail closed

The compact wire has **no `zmeta_version` key** and enumerated field tables;
decoding always yields a `zmeta_version: "1.0"` envelope. That stamp is honest
only because encoding is **fail closed**: encoders MUST refuse any event that
is not `zmeta_version "1.0"` or that would not expand back to a value-identical
canonical envelope (reference: `zmeta_compact.verify_representable`, raising
`CompactUnrepresentableError`). Silently dropping fields or relabeling a
versioned event to "1.0" is prohibited — it would launder experimental-branch
vocabulary into the locked namespace and destroy uncertainty labels (e.g.
`geo.error_ellipse_m`). Events outside compact's representable set MUST travel
on a version-preserving encoding (`json`, `cbor`, `proto`); the reference
gateway replaces an unrepresentable outgoing event with an
`ENCODING_UNSUPPORTED` SCHEMA_VIOLATION diagnostic rather than reducing it.

Verification MUST run through the real serialization boundary (encode to
bytes, decode, compare). An in-memory comparison of the key-remap alone is
not sufficient: it preserves object identity, and container equality
short-circuits on identity, so a value that is not equal to itself (`NaN`)
would pass verification and reach the wire.

### Declared representation normalizations

Two differences between the input envelope and the decoded envelope are
**declared by this mapping** and are therefore not loss — they change the
representation of a value, never the value:

| Normalization | Why it is not loss |
| --- | --- |
| UUID hex case (`019C2B5C-…` decodes as `019c2b5c-…`) | UUIDs travel as 16 raw bytes, so hex case is not carried; RFC 4122 defines UUIDs as case-insensitive and specifies the lowercase output form. Same UUID. |
| Timestamp formatting at millisecond resolution (`…:05.876Z` decodes as `…:05.876000Z`, `…:05.000Z` as `…:05Z`) | Timestamps travel as epoch milliseconds, so the decoded string is that same instant re-formatted. Same instant. |

Everything else is loss and MUST be refused, including:

- a **truncated sub-millisecond instant** (`…:05.1234Z` is not the same
  instant as `…:05.123Z`) — the epoch-ms mapping genuinely loses that
  precision, so such an event MUST travel on another encoding;
- **non-finite floats** (`NaN`, `Infinity`), which CBOR can carry but
  canonical JSON (RFC 8259) cannot represent, so they could never decode
  back to a valid canonical envelope;
- any dropped, added, or altered field.

Refusing the declared normalizations would be its own failure: it would
reject schema-valid events from conforming producers (the `uuid` pattern
admits uppercase hex, and `utcDateTime` admits fractional seconds) and
replace them with diagnostics.

## Purpose

Profile L links are bandwidth-constrained. The compact mapping reduces overhead by:
- Using CBOR with **integer keys** instead of string field names.
- Encoding UUIDv7 values as **16-byte binary** values.
- Encoding timestamps as **epoch milliseconds** (int64).
- Mapping common enums to small integers.

The gateway expands compact packets back into standard ZMeta JSON for enforcement and CoT emission.

## CBOR Determinism

ZMeta CBOR encoders SHOULD emit deterministic CBOR:
- Definite-length strings, byte strings, arrays, and maps only.
- No indefinite-length containers.
- Map keys sorted by canonical CBOR ordering.
- No semantic dependence on JSON object ordering or CBOR map ordering.

The reference fallback encoder (`zmeta_cbor.py`) uses deterministic map ordering.
When `cbor2` is available, the reference tools and gateway use canonical mode
for CBOR output.

## Encoding Rules (Compact v1)

Top-level map keys:
- `1`: `compact_version` (int; currently `1`)
- `2`: `event`
- `3`: `source`
- `4`: `payload`
- `5`: `confidence`
- `6`: `lineage`
- `7`: `profile`

Event map keys:
- `1`: `event_id` (UUID bytes)
- `2`: `event_type` (enum)
- `3`: `event_subtype` (enum or string)
- `4`: `ts` (epoch ms)
- `5`: `t_publish` (epoch ms, optional)
- `6`: `t_receive` (epoch ms, optional)

Source map keys:
- `1`: `platform_id`
- `2`: `node_role` (enum)
- `3`: `producer`
- `4`: `sensor_id` (optional)
- `5`: `sw_version` (optional)

Lineage map keys:
- `1`: `based_on` (array of UUID bytes)
- `2`: `transform` (optional)

## Payload Encoding (Profile L)

STATE_EVENT payload map keys:
- `1`: `track_id`
- `2`: `geo` (map)
- `3`: `valid_for_ms`
- `4`: `class` (optional)
- `5`: `source_summary` (optional)
- `6`: `heading_deg` (optional)
- `7`: `speed_mps` (optional)

Geo map keys:
- `1`: `lat`
- `2`: `lon`
- `3`: `alt_m`

COMMAND_EVENT payload map keys:
- `1`: `task_id`
- `2`: `task_type` (enum)
- `3`: `target_geo` (map)
- `4`: `geometry` (optional)
- `5`: `valid_from_ts` (epoch ms, optional)
- `6`: `valid_for_ms`
- `7`: `priority` (enum, optional)
- `8`: `requires_deconfliction` (optional; default true when expanded)

System event payload map keys:
- `1`: `system_type` (enum)
- `2`: `state` (enum or string)
- `3`: `metrics` (map)

## Enums (Compact v1)

Event types:
- `1` OBSERVATION_EVENT
- `2` INFERENCE_EVENT
- `3` FUSION_EVENT
- `4` STATE_EVENT
- `5` COMMAND_EVENT
- `6` SYSTEM_EVENT

Node roles:
- `1` EDGE
- `2` GATEWAY
- `3` APEX
- `4` DMZ
- `5` CLOUD

Profiles:
- `1` L
- `2` M
- `3` H

Event subtypes (common):
- `1` TRACK_STATE
- `2` GOTO
- `3` TASK_ACK
- `4` LINK_STATUS
- `5` TIME_STATUS
- `6` SCHEMA_VIOLATION
- `7` TRACK_FUSION
- `8` CLASSIFICATION
- `9` ASSOCIATION
- `10` ANOMALY
- `11` BEHAVIOR
- `12` RF
- `13` EO
- `14` IR
- `15` ACOUSTIC
- `16` NETWORK
- `17` ORBIT
- `18` HOLD
- `19` SEARCH_BOX

System types:
- `1` LINK_STATUS
- `2` TIME_STATUS
- `3` SCHEMA_VIOLATION
- `4` TASK_ACK

Task types:
- `1` GOTO
- `2` ORBIT
- `3` HOLD
- `4` SEARCH_BOX

Priorities:
- `1` LOW
- `2` MED
- `3` HIGH

Time source:
- `1` GPS_PPS
- `2` GPS_NMEA
- `3` NTP
- `4` PTP
- `5` MANUAL
- `6` UNKNOWN

Sync state:
- `1` LOCKED
- `2` HOLDOVER
- `3` UNSYNCED

TASK_ACK states:
- `1` RECEIVED
- `2` ACCEPTED
- `3` REJECTED
- `4` EXECUTING
- `5` COMPLETED
- `6` FAILED
- `7` CANCELLED
- `8` EXPIRED
- `9` DUPLICATE_IGNORED

LINK_STATUS states:
- `1` UP
- `2` DEGRADED
- `3` DOWN
- `4` UNKNOWN

Reason codes:
- Mapped to small integers by the reference implementation.
- Unknown reason codes may be transmitted as strings and are preserved.

## Unknown Integer Keys

For compact version 1, integer map keys are reserved for the tables defined in
this document. Decoders MUST reject any integer key that is not listed for the
specific compact map being decoded, including top-level, event, source,
lineage, payload, geo, target_geo, and metrics maps.

String keys are still allowed for canonical JSON fields and namespaced
extensions where the schema or policy permits them. Unknown integer keys MUST
NOT be converted to decimal string keys because that loses the distinction
between a future compact assignment such as key `99` and a producer that
intentionally sent the string key `"99"`.

## Value Model, Tags, and Expansion Bound (Fail Closed)

*(Normative. Doctrine entries R1-11-02, R1-11-03, and R1-11-18, adjudicated
2026-07-27.)*

The compact mapping accepts **only the canonical JSON value model**, carried
in the wire representations this document defines. Concretely, a compact
datagram expands to exactly: maps, arrays, UTF-8 text, byte strings (defined
by this mapping only as the transport form of UUID values), integers in the
CBOR 64-bit range `[-(2**64), 2**64 - 1]`, finite IEEE 754 floats, booleans,
and null. Map keys are integers (assigned by the tables in this document) or
text (canonical JSON fields and namespaced extensions). Anything else has no
canonical expansion and MUST be refused with an explicit diagnostic — on
encode (see Scope) and equally on decode. A decoder MUST NOT partially
interpret a construct this mapping does not define: repairing,
reinterpreting, or silently dropping wire content fabricates canonical
content the producer never sent. In particular, a non-text map key MUST NOT
be converted to a text key (the integer half of this rule is stated under
Unknown Integer Keys; it applies to every non-text key type).

### No tags

Compact v1 defines **no CBOR tags** (major type 6). A conforming decoder
MUST refuse any tagged item with an explicit diagnostic naming the tag —
never by discarding the tag and decoding the enclosed item, and never by
reading the tag's argument as a literal value. The CBOR value-sharing tags
28 (`shareable`) and 29 (`sharedref`) are the motivating case: the same
11-byte datagram `d81ca16473656c66d81d00` used to decode to `{"self": 0}` on
one conforming node (tag discarded, tag 29's argument read as an integer)
and to a self-referential map on another (sharing honoured) — one datagram,
two meanings, which is precisely the failure this format exists to prevent.

The reference fallback decoder (`zmeta_cbor.py`) enforces this at parse
time. A decoder built on a CBOR layer that interprets tags before handing
back the result (the `cbor2` fallback) cannot see every tag, so it MUST
refuse every tag footprint that survives interpretation:

- any container reachable more than once, including cycles — value sharing
  (tags 28/29); a tree decode can never produce one, so this refuses nothing
  honest;
- any integer outside the CBOR 64-bit range — bignum tags 2/3; this mapping
  defines no bignum tag;
- any non-finite float — in the wire model by type, outside it by value
  (RFC 8259 has no encoding for it);
- any value outside the wire value model above (tag-produced objects such as
  sets, timestamps, decimals, or tag wrappers).

The reference implementation of this scan is `zmeta_compact.decode_event`
(invoked by `zmeta_compact.loads` and by the gateway compact ingress), which
refuses with `CompactUnrepresentableError`. Known residual, stated so nobody
mistakes the fallback for full parse-time enforcement: a tag the underlying
CBOR layer collapses into an in-model value before the mapping can see it
(for example tag 2 wrapping a small integer) is undetectable
post-interpretation; the parse-time refusal in `zmeta_cbor.py` is the
conforming behavior, and the footprint scan is the strongest enforcement an
interpreting layer admits.

### Declared expansion bound

CBOR value sharing lets a few hundred wire bytes describe a structure whose
expansion is astronomically larger than the datagram. Refusing tags 28/29
closes that door, but a decoder MUST NOT rely on refusal alone: it MUST
enforce a declared expansion bound on the number of nodes a datagram expands
to (containers plus values, map keys uncounted), and beyond the bound it
MUST refuse with an explicit diagnostic naming the bound rather than
materializing the expansion.

- The declared default is **1,048,576 (2\*\*20) expanded nodes**
  (`zmeta_compact.DEFAULT_MAX_EXPANDED_NODES`), overridable per decode via
  the `max_expanded_nodes` keyword on `zmeta_compact.loads` and
  `zmeta_compact.decode_event`.
- The bound is computable in linear time even for a shared DAG: a memoized
  walk (expanded count per distinct container) never re-walks a shared
  subtree, so an implementation that stages sharing detection after
  expansion counting can still refuse cheaply. The reference decoder refuses
  sharing outright, so its count is the plain node count, and the count is
  checked before a container's children are traversed.
- The default is deliberately aligned with the fallback decoder's 1 MiB
  message limit (`zmeta_cbor.DEFAULT_MAX_MESSAGE_BYTES`): every decoded node
  costs at least one wire byte, so only value sharing (refused above) or an
  oversized datagram on a decode path without a byte limit (the `cbor2`
  fallback has none of its own) can reach the bound. It therefore refuses no
  honest event a conforming consumer could decode.

### Declared nesting maximum

The compact wire model is bounded at **64 nesting levels** (the datagram's
top-level map is depth 0), matching the fallback decoder's default
`max_depth`. A deeper datagram is not representable in compact v1 and MUST
be refused at decode with an explicit diagnostic. Before this was a mapping
rule, a 65–400 deep datagram encoded on a `cbor2`-only node and refused on
every `zmeta_cbor` consumer — representability depended on the local
install, which the Scope section forbids. Because encoders verify through
the real serialization boundary (encode, decode, compare — see Scope), this
decode-side rule also makes encoders refuse events that would exceed the
depth, on either backend.

## Compatibility

- The compact mapping is **wire-level only**.
- Gateways must expand compact packets into the canonical JSON schema before validation.
- Semantics are unchanged; only field names and primitive representations are
  compacted. This holds because encoding is fail closed (see Scope above):
  an event the mapping cannot represent losslessly is refused, never reduced.
- Profile projection preservation tests round-trip selected Profile L projected
  events through compact CBOR and compare the decoded JSON against the
  source/projected conformance fixture. Compact CBOR remains an encoding
  projection, not semantic authority.
- Encoding-negative fixtures in `conformance/encoding-negative/` exercise
  malformed compact input and schema-, policy-, projection-, gateway-, and
  CLI-invalid decoded JSON. These tests prove compact CBOR cannot bypass
  canonical validation.

## Size Optimization Tips (Profile L)

If you must drive STATE_EVENT packets under ~200 bytes, focus on optional fields and
omit them at the producer (gateway stripping does not reduce link size).

Common high-impact optional fields:
- `payload.data_ref` / `payload.data_refs`
- `payload.source_summary`
- `payload.heading_deg`
- `payload.speed_mps`
- `payload.class`

Do not strip required STATE_EVENT fields such as `confidence` or `lineage`.
Profile L may reference non-exported lineage parents, but the lineage field
itself remains required for STATE_EVENT.

Profile L precision reduction is governed by `spec/profile-precision-policy.md`
and the reference policy in `policy/profile-precision.yaml`, not by the compact
wire mapping. Packet-budget pressure may motivate policy-compliant
quantization, but it cannot authorize required semantic fields, source identity,
track identity, lineage, discriminator fields, confidence, or timing semantics
to be stripped. Compact packets must still expand to canonical JSON and pass
schema, policy, projection, encoding-negative, and precision-policy checks when
those conformance layers are invoked.

## Versioning

- `compact_version` (top-level key `1`) enables forward compatibility.
- Current version is `1`. Producers must set it to `1`.
- Decoders should reject unknown versions to avoid misinterpreting wire data.

## Profile L Payload Budget (Illustrative)

These are example sizes from `tools/measure_packet_size.py` using the current
Profile L examples. Actual sizes vary with field lengths and optional fields.
Generated via `python tools/measure_packet_size.py --file
examples/zmeta-profile-L-examples.jsonl --encodings json,cbor,compact`, taking
the first matching example per event type/subtype in that file's order.

| Event Type | JSON (bytes) | CBOR (bytes) | COMPACT (bytes) | Notes |
| --- | --- | --- | --- | --- |
| STATE_EVENT/TRACK_STATE | 458 | 395 | 150 | Tight budgets should drop optional payload fields such as `payload.data_ref`, `source_summary`, `heading_deg`, `speed_mps`, or `class`; keep `confidence` and `lineage`. |
| SYSTEM_EVENT/TIME_STATUS | 444 | 373 | 101 | Already within tight budgets. |
| COMMAND_EVENT/GOTO | 414 | 345 | 115 | Already within tight budgets. |
