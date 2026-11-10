## ZMeta to TAK Protocol Version 1 Egress Adapter (Reference)

Overview: see `adapters/README.md`.

TAK Protocol Version 1 is the binary wire form of Cursor-on-Target that TAK
clients and servers exchange on mesh (multicast UDP) and stream (TCP, TLS)
connections: the CoT event as a protobuf `TakMessage`, with the typed parts of
`<detail>` in typed fields and the rest of `<detail>` as XML text in
`xmlDetail`. This adapter encodes the CoT XML that the CoT egress projection
(`adapters/egress/cot/`) produces, under either of its profiles, and frames it
for mesh or stream. It is a wire step over that projection: the semantics,
every refusal and both profiles are the CoT adapter's, and this module adds
the encoding, the framing, and a refusal of whatever the encoding cannot carry
without loss.

Input: ZMeta `STATE_EVENT`/`TRACK_STATE` (through `zmeta_to_cot`), or CoT 2.0
XML directly.
Output: TAK Protocol Version 1 bytes, mesh framed by default.

Status: Reference. The encoding was checked byte for byte against the
MIT-licensed `takproto` package (3.0.1) for the known-answer event, and
`takproto` parses the adapter's output of a declared 2-D vessel with no field
mismatch; the recce of 2026-11-03 parsed the same shape back for 809 events of
the producers' run 7 and 1,680 live ADS-B events. No TAK Server or client has been driven with the
bytes from this repository, and the adapter does not open connections. An
independent review of 2026-11-10 read the adapter against the published
`.proto` files and protocol text; the required items, the typed route and
the sender's steps below follow from that reading. The
adapter is not among the required surfaces of the `ZMETA-COT-PROJECTION`
conformance class, whose surfaces are the CoT XML projection and ingress.

### Usage

```python
from adapters.egress.tak_protocol.zmeta_to_tak_protocol import (
    zmeta_to_tak_protocol, cot_xml_to_tak_message, frame_mesh, frame_stream,
    tak_control_message, read_tak_message, validate_framing,
)

cot_config = {"how": "m-f"}                       # the CoT adapter's configuration, passed through; `how` is required here
frame = zmeta_to_tak_protocol(state_event, cot_config=cot_config)                    # mesh: bf 01 bf + message
frame = zmeta_to_tak_protocol(state_event, cot_config=cot_config, framing="stream") # bf + varint length + message
message = zmeta_to_tak_protocol(state_event, cot_config=cot_config, framing="none") # the bare TakMessage

message = cot_xml_to_tak_message(cot_xml)         # encode CoT XML from any source, unframed
announce = frame_mesh(tak_control_message("my-contact-uid"))  # the mesh announcement; see "What a sender does"
fields = read_tak_message(frame)                  # a dict of the fields present, for inspection
```

`how` must be set. The published schema requires it, and the CoT projection
writes it only when the deployment sets `how` in `cot_config`, since the event
model carries no position pedigree for the adapter to assert. An event whose
projection has no `how` is refused.

`validate_framing(framing)` returns the name or raises `ValueError`; a gateway
that adopts this adapter calls it when it reads its configuration, as the
reference gateway calls `validate_cot_config` (the reference gateway does not
yet use this adapter). `zmeta_to_tak_protocol` returns `None` for an unknown framing, for every
refusal of the CoT projection, and for an encoding refusal; a caller that
passes a `refusal` dict reads the CoT adapter's `cds` reasons there,
`TAK_PROTOCOL_HOW_REQUIRED` when a missing `how` is the one thing the
encoding refuses, and `TAK_PROTOCOL_UNREPRESENTABLE` for any other refusal of
the encoding. An event with no `how` that would be refused anyway reads the
second, since setting `how` would not clear it.

No protobuf package is used. The encoder is written against the schema below
in the canonical proto3 form: fields in field-number order, a scalar equal to
its default (an empty string, 0, 0.0) written as absent; the test for 0.0 is
on the bits, so `-0.0` is written, as protobuf's serializers write it.

### The schema this adapter encodes

From the TAK Protocol Version 1 `.proto` files published in the ATAK-CIV
repository; the field numbers were checked against the `takproto` package's
descriptors on 2026-11-09, and the required and optional items against the
files' own comments on 2026-11-10. Those comments mark every item required
unless noted. They note as optional `access`, `qos`, `opex` and `detail` on
`CotEvent`, and `endpoint` on `Contact`.

| Message | Fields |
|---|---|
| `TakMessage` | `takControl` 1 (written only by `tak_control_message`), `cotEvent` 2 |
| `TakControl` | `minProtoVersion` 1, `maxProtoVersion` 2 (uint32); `contactUid` 3 (string) |
| `CotEvent` | `type` 1, `access` 2, `qos` 3, `opex` 4, `uid` 5 (strings); `sendTime` 6, `startTime` 7, `staleTime` 8 (uint64, milliseconds since the epoch); `how` 9 (string); `lat` 10, `lon` 11, `hae` 12, `ce` 13, `le` 14 (doubles); `detail` 15 |
| `Detail` | `xmlDetail` 1 (string); `contact` 2; `group` 3; `precisionLocation` 4; `status` 5; `takv` 6; `track` 7 |
| `Contact` | `endpoint` 1 (optional), `callsign` 2 |
| `Group` | `name` 1, `role` 2 (the CoT element is `__group`) |
| `PrecisionLocation` | `geopointsrc` 1, `altsrc` 2 |
| `Status` | `battery` 1 (uint32) |
| `Takv` | `device` 1, `platform` 2, `os` 3, `version` 4 |
| `Track` | `speed` 1, `course` 2 (doubles) |

Framing: `mesh` is the three bytes `bf 01 bf` then the message; `stream` is
`bf`, the message length as a base-128 varint, then the message; `none` is
the bare message.

### What a sender does

The adapter produces bytes and opens no connection. A sender that puts them
on a network follows the published protocol text, the `README.md` beside the
`.proto` files. The steps below restate that text as it was read on
2026-11-10. Where they differ from it, the published text governs. No TAK
Server or client has been driven from this repository, so the steps are
unconfirmed here.

Mesh (UDP datagrams, or one message per directed TCP connection):

- Send one framed message per datagram: `frame_mesh(message)`.
- Broadcast the announcement at least once every 60 seconds, and again at
  once whenever the version the sender uses changes:
  `frame_mesh(tak_control_message(contact_uid))`. It states the lowest and
  the highest version the sending device can decode. The minimum is always
  1, since a sender of version 1 frames decodes version 1; `max_version`
  raises the maximum where the receiving side decodes a later version. The
  published rules allow no version of 0 in it.
- Track the version range of every known contact. A contact heard for the
  first time takes the version of the message that revealed it, which is
  version 0 for a contact first heard in XML. An announcement from the
  contact replaces that. A contact that has sent no announcement for two
  minutes falls back to the version of its most recent message.
- Send the highest version that all known contacts support, the sender
  included. Where no version above 0 is common to all of them, because one
  contact supports only version 0 or because two contacts' ranges do not
  meet, send the CoT projection's XML and not this adapter's bytes. A sender
  that does not listen cannot make that choice, and it reaches version 1
  clients only.

Stream (TCP or TLS to a TAK Server):

- A stream starts in XML. Where the server requires authentication, the
  authentication message goes first.
- Wait for the server's offer, a CoT XML event of type `t-x-takp-v`, which
  lists the versions the server supports. Send no request before it arrives.
- Request one of the versions the offer lists, with a CoT XML event of type
  `t-x-takp-q`. This adapter encodes version 1, so request version 1 when the
  offer lists it, and stay in XML when it does not. Send no more XML after
  the request.
- Wait at least one minute for the response, a CoT XML event of type
  `t-x-takp-r`. On a true status, send only `frame_stream(message)` frames
  with nothing between them. On a false status, carry on in XML. With no
  response, disconnect.

A sender that writes a frame at connect, without the negotiation, sends
protobuf to a peer that is reading XML. The three negotiation events are XML
and are not written by this adapter. The protobuf `takControl` field is the
mesh announcement and plays no part in a stream's negotiation.

### Mapping

| CoT XML | TAK Protocol field | Notes |
|---|---|---|
| `event@version` | none | Must be `2.0`, the CoT this schema encodes; any other value, or no version, refuses |
| `event@type`, `@uid`, `@how` | `type`, `uid`, `how` | Required, as the published schema requires them; a missing or empty value refuses. The CoT projection writes `how` only when `cot_config` sets it |
| `event@access`, `@qos`, `@opex` | `access`, `qos`, `opex` | Carried when present; the published schema notes them as optional. An empty value refuses: proto3 writes no field for an empty string, so it would read back as absent, and a claim that cannot be told from no claim is not sent |
| `event@time`, `@start`, `@stale` | `sendTime`, `startTime`, `staleTime` | Milliseconds since the epoch, floored; see "What the encoding changes" |
| `point@lat`, `@lon`, `@hae`, `@ce`, `@le` | `lat`, `lon`, `hae`, `ce`, `le` | All five required, as CoT requires them; each must be a finite decimal; `9999999.0`, the CoT unknown-value convention the CoT adapter writes, passes through as that number |
| `detail/contact`, `__group`, `precisionlocation`, `status`, `takv`, `track` | the typed field, or `xmlDetail` | Typed only when the typed message carries the element whole; see the next table |
| every other `detail` child | `xmlDetail` | Serialized as XML text, in document order, concatenated without whitespace |
| any other attribute of `event` or `point`, any other child of `event` | none | Refused; the schema has no field, and the adapter drops nothing in silence |

The typed route. A typed child goes to its typed field only when the typed
message can carry the element whole and the published message takes it:
every attribute has a typed field, no attribute is empty, every item of the
message is present except the contact's `endpoint`, and the element has no
text and no child elements. Otherwise the element travels whole in
`xmlDetail`, like every other child, so a reader that rebuilds `<detail>`
from `xmlDetail` sees it as it was written. The published messages mark
every item required unless noted, and a missing item on send falls back to
the XML form; `endpoint` is the one item noted as optional, so `<contact
callsign="…" />` is typed and `<__group name="…" />` without a `role` is
not. An absent number would also read back as 0, a value, so `<track
course="…" />` without a `speed` could not be told from a speed of 0.

Two more cases follow the published sender rule (`detail.proto`, rule 1):
when a child appears more times than its message field holds, or mapping it
to the message fails, the element stays in the XML and the field is not
populated. So two elements of one typed kind both travel in `xmlDetail` and
neither is typed, and a typed element whose numeric attribute is not a number
travels in `xmlDetail` as it was written. The event is sent in both cases.
The published receiver rule ignores a typed field whose element is also in
`xmlDetail`, which is why one of two is never typed.

The whole-element rule exists because the CoT projection writes
`<precisionlocation geopointsrc="…" ellipse_major="…" ellipse_minor="…"
ellipse_angle="…" />` when a position source is configured and the event
carries an ellipse with a `semi_major`, and the typed `PrecisionLocation`
message holds `geopointsrc` and `altsrc` only. A typed carrier would drop the
ellipse, the one structured place the projection carries the uncertainty's
shape rather than its circular bound (the standard profile's `remarks` also
carry it as text). A consumer that reads only the typed `precisionLocation`
field sees nothing for such an event; a consumer that reads `xmlDetail` sees
the element whole. The `takproto` package types the element and drops the
ellipse attributes; this adapter does not follow it there.

| Element as the CoT projection writes it | Carrier |
|---|---|
| `<contact callsign="…" />` | typed `contact.callsign` |
| `<__group name="…" role="…" />` (friendly types) | typed `group` |
| `<track course="…" speed="…" />` | typed `track`; `course`, `speed` as doubles |
| `<precisionlocation geopointsrc="…" altsrc="…" />` (no ellipse; CoT XML from another source, since the projection writes the element only with an ellipse) | typed `precisionLocation` |
| `<precisionlocation geopointsrc="…" ellipse_major="…" … />` | `xmlDetail`, whole |
| `<remarks>…</remarks>`, `<labels_on …/>`, `<usericon …/>`, `<geo_dimensionality …/>`; `<circle …/>` from `zmeta_to_cot_uncertainty_circle` when a caller encodes that output | `xmlDetail` |
| a typed element with an attribute the message lacks (`<contact callsign="…" phone="…" />`), an empty attribute, an item left out (`<track course="…" />`, `<__group name="…" />`, a `contact` with no `callsign`), text, or children | `xmlDetail`, whole |
| a typed element whose numeric attribute is not a number (`course="east"`, `battery="-1"`, `battery` above 2^32 - 1) | `xmlDetail`, whole, as it was written; the event is sent |
| two elements of one typed kind, whether or not each would qualify alone | both in `xmlDetail`, neither typed; the event is sent |

### Refusals (`None`): fail closed, never substitute, never drop in silence

| Condition | Disposition |
|---|---|
| Not a `STATE_EVENT`, or anything the CoT projection refuses (missing geo or `track_id`, a non-finite number, a lapsed `cds` validity, and the rest of its table) | refused; inherited |
| Unknown `framing` | refused; `validate_framing` raises at configuration time |
| XML that does not parse, an empty string, a value that is neither text nor UTF-8 bytes | refused |
| A root element other than `event`; a `version` other than `2.0` | refused |
| A comment, a document type declaration or a processing instruction anywhere in the document, inside or outside the root element (the XML declaration that may open the document is not one) | refused rather than dropped: the text is scanned for them before parsing, since the parser would drop one outside the root in silence and expand a declaration's entities into content the event never carried |
| An attribute of `event` or `point` the schema has no field for; a child of `event` other than `point` and `detail` | refused |
| Text directly inside `event` or `detail`, other than whitespace | refused; the schema has no carrier for it |
| A missing `point`, a missing point attribute, a point value that is not a finite decimal (`nan`, `inf`, `north`) | refused |
| A missing or unparseable `time`, `start` or `stale`; an instant without an offset; an instant before 1970 (no uint64) | refused |
| A missing or empty `type`, `uid` or `how` | refused; see the mapping table. A missing `how` is reported as `TAK_PROTOCOL_HOW_REQUIRED` when it is the one thing refused |
| An empty `access`, `qos` or `opex` | refused; see the mapping table |

### What the encoding changes

| Change | Why it is accepted |
|---|---|
| Times are milliseconds. The CoT projection writes microseconds; the microseconds are dropped, never rounded up | `stale` is never later than the event's claim (contract 4.2: a projection may lower a validity, never raise it); `time` and `start` move by less than one millisecond and never forward |
| `lat`, `lon`, `hae`, `ce`, `le`, `course`, `speed` become float64 | A decimal with more digits than a double holds is rounded to the nearest double; the XML carried the text. The CoT projection writes Python floats, which round-trip exactly |
| A typed integer is carried as its value (`battery="007"` reads back as 7) | `Status.battery` is a uint32; the text form of the number is not carried |
| A scalar equal to its default is absent on the wire (a coordinate of exactly 0.0, a time at the epoch, a battery of 0) | proto3 defines absent as the default, so a reader recovers the same value; the adapter requires the five point attributes and both `track` attributes, so absence never means "not sent" for a number |
| The whitespace between detail children is dropped | Formatting, not content |
| The typed children lose their position among the other children | A reader rebuilds `<detail>` from the typed fields and `xmlDetail` separately; CoT gives the children no order |
| `event@version` is not carried | The schema is CoT 2.0; the adapter requires that value |
| An event message carries no `takControl` | The announcement is its own message. `tak_control_message` writes it for mesh, and a stream's negotiation does not use it; see "What a sender does" |

Everything the CoT projection itself loses or changes (confidence in
`remarks`, lineage and timing quality absent, the ellipse reduced to `ce` on
the point and to text in `remarks` unless a position source is configured) is
the CoT adapter's register, unchanged by this encoding.

### The reader

`read_tak_message(data)` reads a mesh frame, a stream frame or a bare message
into a dict of the fields present, nested as the schema nests them
(`{"cotEvent": {"type": …, "detail": {"xmlDetail": …, "contact": {…}}}}`). It
raises `ValueError` for a frame or message the schema does not describe: an
empty input, a truncated or oversized stream frame, trailing bytes after one,
a stream length beyond 2^63 - 1 (the published range of the header varint),
an unknown field number, a known field with the wrong wire type, a repeated
field, a truncated field, a varint wider than 64 bits, a string that is not
UTF-8. The three bytes `bf 01 bf` alone read as an empty mesh frame (an empty
`TakMessage`, `{}`); as a stream frame they would carry a one-byte message,
which no `TakMessage` is. That is the rule the repository's
own decoders apply (`DECODE_AMBIGUOUS`, 2026-11-02): a decode that would have
to choose is not a decode. The reader is for tests and inspection; it is not
the proof of the encoder.

### Verification

The tests (`test_tak_protocol_egress.py`) were written before the module
(the build's private record holds the run that failed at collection with no
module); after the module they pass. What they prove and how:

- Two known-answer tests hold the expected bytes for two CoT events, computed
  in the test file from the field numbers and an independent varint writer,
  so the encoder's own tables are not the oracle: one small event (type,
  uid, times, how, the point, a contact, a track, a remark in `xmlDetail`),
  and one that sets every field of every typed message with `access`, `qos`
  and `opex`, so a wrong field number anywhere in the tables changes the
  bytes. Three mutants of the encoder were each run against the suite on
  2026-11-09 and each failed it: the `uid` field number moved (3 failures),
  the times rounded instead of floored (1), the typed route's attribute check
  removed (2). A fourth mutant that moved and swapped field numbers of the
  typed messages passed the suite as it then stood (a refuter's finding of
  the same day); the second known answer was added for it.
- The reader round-trips the known message on both framings, and has its own
  negative controls, each seen raising: an unknown field, a wrong wire type,
  a repeated field, a truncated stream frame, trailing bytes after one, a
  string that is not UTF-8, a varint wider than 64 bits, an empty input, a
  stream length beyond the published range.
- The change of 2026-11-10 was built the same way, in two rounds (the
  build's private record holds both first runs). Seven new or changed tests
  failed against the module as it stood; two more, written for an
  independent reviewer's findings, failed against the first change. One more
  pins behaviour the adapter already had and no test covered, a missing or
  empty `type`, `uid` or `how` refused. The tests of the change pin: a missing `how` refused, and named as the reason only when
  setting it would clear the refusal; a typed child with a required item
  left out; two elements of one typed kind; a typed attribute that is not a
  number; an empty `endpoint`; a typed integer carried as its value; the
  announcement's known-answer bytes, its fixed minimum and its refusals; a
  stream length beyond the published range. Fifteen mutants were each run
  against the suite on 2026-11-10 and each failed it. Thirteen are mutants
  of the change: `how`
  optional again, a string item left out of a typed element, the `endpoint`
  required too, one of two elements typed, a bad number refusing the event,
  the announcement's version fields swapped, a maximum of 0 accepted, the
  stream length unbounded, a missing `how` reported as unrepresentable,
  every refusal reported as a missing `how`, a missing `how` named before
  the other checks, the announced minimum following the maximum, and the
  contact uid left out. Two are mutants of the required-attribute checks:
  `type` and `uid` no longer required, and an empty attribute no longer
  refused.
- The `refusal` dict is exercised: a 1969 instant passes the CoT projection
  and is refused here with `TAK_PROTOCOL_UNREPRESENTABLE`; a clean event
  leaves the dict empty.
- Two tests cross-check against `takproto` and run only when the environment
  variable `TAK_PROTO_SITE` names a directory holding `takproto` and
  `google.protobuf`: the mesh and stream bytes for the known event, the mesh
  bytes for the all-typed event and for a `-0.0` latitude are identical to
  `takproto.xml2proto`'s, and `takproto.parse_mesh` reads the adapter's
  output of a declared 2-D vessel with every checked field equal. The
  repository vendors neither package; without the variable the two tests are
  skipped and say so.
- The shared adapter harness (`tools/validate_adapter_conformance.py`) checks
  emitted ZMeta events, so it does not apply to an egress that emits bytes;
  the colocated tests are the adapter's fixtures, as for the other egress
  adapters.

```
python -m pytest -q adapters/egress/tak_protocol
TAK_PROTO_SITE=<dir holding takproto> python -m pytest -q adapters/egress/tak_protocol
```

### Source

The TAK Protocol Version 1 schema: the `.proto` files in the ATAK-CIV
repository (`commoncommo/core/impl/protobuf/`, and the copies under
`takproto/`, which are the ones read on 2026-11-10). The protocol text for
mesh and stream use, and for the negotiation: the `README.md` under
`takproto/`. The CoT projection it encodes:
`adapters/egress/cot/`. The recce that ranked this adapter first among the
egress candidates and measured the round trips: the repository's private
session record of 2026-11-03.
