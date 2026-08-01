## Ingress Adapter Template

Overview: see `adapters/README.md`.

Purpose: convert external payloads into ZMeta v1.0.

### Entry points

There is no single required function name. What every shipped adapter has in
common is one or more `translate_<subject>` functions, named for the shape of
input each accepts (`translate_aircraft`, `translate_message`,
`translate_stream`, `translate_csv_row`, `translate_bin_file`, and so on),
each taking one parsed input object (or an iterable, for a stream-shaped
entry point) and returning `list[dict]` of ZMeta events, or refusing with
`[]`/`None` when the input cannot honestly become one. Colocated tests
(`test_<adapter>_ingress.py`, next to the adapter module) are what pin each
entry point's emission and refusal behavior; see `adapters/AUTHORING.md`
section 9 for the one-refusal-fixture-per-required-field standard.

`detect(input_bytes) -> schema_id` is optional dispatch plumbing for a caller
that must identify the format from raw bytes before it can pick the right
entry point. Reference adapters whose caller already knows the schema
(`ingress/adsb/`, `ingress/ais/`) skip it entirely. A local
`validate(zmeta_event) -> (pass|fail, violations)` function is an optional
convenience some adapters ship; it is never the thing that makes an event
conformant. The canonical validator is
`python tools/validate.py --file <events>.jsonl --profile <profile> --strict`
against `schema/zmeta-event-1.0.schema.json` (`adapters/AUTHORING.md` ladder
step 2), and it is authoritative regardless of whether your adapter also
carries a local `validate()`.

### Required behavior

- Emitted events must be schema-valid against
  `schema/zmeta-event-1.0.schema.json`; run the canonical validator above
  before calling an adapter done.
- Building and emitting the `SYSTEM_EVENT`/`SCHEMA_VIOLATION` diagnostic for a
  refused input is caller-side (the gateway, a wrapping ingest script, or the
  harness), matching every reviewed adapter: a `translate_*` entry point's own
  fail-closed `[]`/`None` return is what signals the refusal, and the caller
  decides what diagnostic, if any, to build from it.
- Must emit `lineage` only when real parent ZMeta event ids exist (for
  example, caller-supplied `based_on`). When lineage is emitted, set
  `lineage.transform = "translate:<schema_id>@<adapter_version>"`. Never
  fabricate `lineage.based_on` values: an original observation with no ZMeta
  parent omits lineage entirely, and event families whose lineage is
  mandatory (INFERENCE/FUSION/STATE, contract 4.8) must refuse to emit
  rather than invent a parent id.
- Must apply Units & Geodesy rules (WGS-84, meters HAE, degrees, meters/sec).
- Must normalize timestamps with shared helpers such as
  `adapters.ingress.time_utils.normalize_utc_z()` or `epoch_ms_to_utc_z()`.
- Must expose timing quality per event or through periodic `TIME_STATUS`.
  `coerce_timing_quality()` provides a conservative `UNKNOWN`/`UNSYNCED`
  fallback, but that fallback is degraded timing and should be replaced by
  source-provided GPS/NTP/PTP metadata when available.

### Invocation style

Run adapters as importable modules from the repository root, or make the repo
root available on `PYTHONPATH`. Shared helpers use package imports such as
`from adapters.ingress.time_utils import ...`; direct execution from inside an
adapter subdirectory can fail because Python will not see the repository root.
