# Media attachments — `payload.media[]`

**Status:** Proposed for v1.2.0. Co-exists with v1.1 `data_ref` /
`data_refs` — see "Relationship to v1.1 `data_ref`" below.

## Purpose

ZMeta's three wire encodings (`zmeta_json`, `zmeta_cbor`, `zmeta_proto`)
do not all carry binary data with equal grace:

- `zmeta_json` requires base64 (~33% size inflation).
- `zmeta_cbor` has native byte strings.
- `zmeta_proto` delegates to JSON.

`payload.media[]` is a payload-level convention for attaching binaries
to any event type — image snippets, KLV bursts, camera frames,
screenshots, documents, raw signal slices — by reference, with an
optional inline preview. The schema definition lives in the v1.2.0
envelope schema under `$defs/MediaAttachment`.

This is a **payload-level convention**, not an envelope change.

## Relationship to v1.1 `data_ref`

v1.1 already defines a binary-attachment mechanism (`data_ref` /
`data_refs`) inside `ObservationPayload`. v1.2 introduces
`payload.media[]` as a generalized, MIME-typed alternative usable in
any event type. **Both mechanisms co-exist in v1.2**:

- `data_ref` / `data_refs` remain unchanged for OBSERVATION_EVENT
  payloads with their existing v1.1 semantics.
- `payload.media[]` is the alternative when the producer needs:
  - any event type other than OBSERVATION_EVENT,
  - RFC-6838 `content_type` (MIME) for client routing/rendering,
  - `valid_until` for transient references,
  - an inline `preview` for thumbnails or short excerpts,
  - free-form `metadata` for content-type-specific descriptors.
- A single event SHOULD use one mechanism, not both. Consumers SHOULD
  tolerate either.

Mechanism unification is intentionally deferred. A future minor revision
may add the v1.2-specific fields to `data_ref` and consolidate; we did
not propose that here because it would require moving `data_ref` from
inside `ObservationPayload` to envelope-level — a larger change than
v1.2 is scoped to make.

| Field equivalence | `media[].field` | `data_ref.field` |
|---|---|---|
| Location | `ref` (URL/URI/path) | `ref_id` + `store` (split) |
| MIME type | `content_type` | — (only `format`, untyped) |
| Cache key | `etag` (`sha256:HEX`) | `hash` (`sha256:HEX`) |
| Size | `size_bytes` | `size_bytes` |
| Expiry | `valid_until` | — |
| Inline preview | `preview` | — |
| Free-form metadata | `metadata` | — |

A bridge converting `media[]` → `data_ref` loses `content_type`,
`valid_until`, `preview`, and `metadata`.

## Shape

```json
"payload": {
  /* ...domain fields... */
  "media": [
    {
      "ref": "https://media.example.org/event/aor-1/t-1717000000.bin",
      "content_type": "application/x-rf-heatmap-v1",
      "size_bytes": 8192,
      "etag": "sha256:7e9f...",
      "valid_until": "2026-06-05T16:00:00Z",
      "preview": null,
      "metadata": { "bbox": [27.8, -82.5, 27.9, -82.4], "cell_size_m": 50 }
    }
  ]
}
```

### Field reference

| Field | Required | Type | Notes |
|---|---|---|---|
| `ref` | yes | string | URL, URI, or relative path. Consumers fetch lazily. Schemes: `https://`, `http://`, `mqtt-blob://` (custom for in-broker bulk transfer), `urn:`, relative paths. |
| `content_type` | yes | string | RFC-6838 media type or `application/x-*` for project-specific. |
| `size_bytes` | no | integer | Helpful for budget decisions; producers SHOULD set when known. |
| `etag` | no | string | Strong cache identifier. Recommended format: `sha256:HEX` or `xxh64:HEX`. |
| `valid_until` | no | ISO-8601 | If set, the `ref` is expected to expire at this time. Consumers SHOULD refetch only if needed. |
| `preview` | no | data URI \| null | Optional inline thumbnail/excerpt. **RECOMMENDED only when ≤ 4 KB.** |
| `metadata` | no | object | Free-form, content_type-specific (bbox, frame number, codec details). |

## Inline vs out-of-band guidance

| Encoded preview size | Recommendation |
|---|---|
| ≤ 4 KB | Inline as a data URI in `preview`. Useful for thumbnails or short text snippets. |
| > 4 KB | Out-of-band only via `ref`. Consumers fetch when they need the binary. |

Producers MAY omit `preview` even when small. Consumers MUST tolerate
its absence.

## Caching with `etag`

A `ref` returning the same `etag` over multiple events represents the
same content. Consumers SHOULD cache by `etag`. Producers that
intentionally rotate the binary (e.g., a new heatmap frame) MUST emit
a new `etag`.

## Multiple attachments

`media` is an array. A single event MAY carry multiple attachments —
for example, an FMV observation carrying both a KLV burst and a
thumbnail frame. Consumers select by `content_type`.

## Encoding-specific notes

| Encoding | Behavior |
|---|---|
| `zmeta_json` | `preview` data URI is base64-encoded by definition of the data URI scheme. |
| `zmeta_cbor` | `preview` MAY be a CBOR byte string instead of a data URI. Producers SHOULD pick one consistently per attachment. |
| `zmeta_proto` | `payload_json` carries the JSON form; CBOR-native byte-string `preview` is not available in this encoding. |

## Compatibility with v1.1

`payload.media[]` is optional. A v1.1 sender produces messages without
it; a v1.2 receiver handles those normally. A v1.2 sender producing
`media[]` to a v1.1 consumer: the consumer ignores the unknown field
(payload has `additionalProperties: true`). For OBSERVATION events,
producers writing to v1.1 consumers SHOULD use `data_ref`/`data_refs`
instead of (or alongside) `media[]`.

## Example

See `examples/zmeta-v1.2-examples.jsonl`, line 5
(`media-attachment-eo-frame`).
