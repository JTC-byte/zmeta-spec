# ZMeta v1.1.25 Release Notes

## Summary

This release mints `RF_ZERO_FILL_SUSPECTED`, the first governed vocabulary
change since v1.1.21 and the first minted directly from external field
evidence. A field verification pass (credit: Barrett Downs, Torch) measured
the gap on real line-of-bearing traffic: a naive mapping zero-filled
`bandwidth_hz` and `power_dbm` its source records never carried, and
fifteen such events passed reference validation with no RF-shaped signal.
Policy had the geospatial form of the same laundering
(`GEO_ZERO_FILL_SUSPECTED`) and no RF analogue. It now has one, at warn
severity, with the event staying accepted: the consumer adjudicates.

The locked kernel's anchored surfaces do not move: the semantic contract
file and the v1.0 schema are byte-identical to every release since the
lock, both pinned by their own guards. The governed delta, relative to
v1.1.24: `conformance/bad-events/must-fail.jsonl`, `policy/semantics.yaml`,
`policy/violation-codes.yaml`, and `schema/zmeta-event-1.1.0.schema.json`.

## The check

- **The trigger is the pair, and only the pair.** `bandwidth_hz` and
  `power_dbm` both exactly 0.0 in a feature block draws the warning. The
  documented receiver-class sentinel (`bandwidth_hz` 0.0 beside a measured
  power, emitted by five adapter families and sanctioned in the authoring
  guide) does not trigger it, and neither does a legitimate one-milliwatt
  reading beside a real bandwidth. The pair is inherently RF-family, so no
  modality gate is needed.
- **Three containers.** The check walks `payload.features`,
  `payload.claim.features`, and `payload.estimated_state.features`, the
  same three containers as its geo analogue.
- **Warn is the ceiling by construction.** The locked contract states the
  zero-fill prohibition for geospatial data only (6.8), so policy labels
  and never rejects. Strict mode escalates, as it does for every warn.
- **On the v1.0 wire** the code rides the documented post-lock fallback
  (`reason_code: GEO_ZERO_FILL_SUSPECTED`, the same zero-fill class at the
  same severity) with the exact code in `metrics.diagnostic_code` and the
  offending block in `metrics.path`. The 1.1.0 lane carries the native
  code.

## The adjudication record

Doctrine pressure log X2-04 records the three maintainer adjudications:
mint-now as completion of the zero-fill class rather than holding a single
field instance against the occurrence rule; the paired predicate,
re-adjudicated after the pre-cut verification pass measured the
first-draft bandwidth-alone trigger failing the documented sentinel on
five adapter families; and the v1.0 fallback with its cross-family
overload recorded deliberately. The generalized contract clause (missing
measurements MUST be omitted, never zero-filled, across field families,
with declared sentinels defined) is recorded as versioned-semantic-branch
material.

Two apparatus notes from the mint itself: the v1.0 byte-anchor guard
rejected a first draft that touched the locked lane's enum, forcing the
documented post-lock path in real time, and this cut is the first to run
the runtime-harness checklist step re-wired at v1.1.24 (both harnesses
pass, and the containerized gateway demonstrated the new diagnostic end
to end).

## Compatibility

No v1.0 wire changes: every event that validated before validates now.
The change is additive and warn-severity only. Consumers filtering
zero-fill suspicion on the v1.0 lane see the fallback pair; filter on
`metrics.diagnostic_code` when the field family matters. The bad-event
corpus grows by two warn vectors, its first. `tools/check_compat.py`
accepts `--target v1.1.25`.

## Signing

Signed release. The release authority, Justin Carr (Incept.IO), directed
this signed cut on 2026-08-13 with the Incept.IO ZMeta release signing key
`A3B150AF2A0E1CA413C4B7F112BE81F54654B96E`. Verify the assets against
`SHA256SUMS_v1.1.25.txt` and its detached signature:

```
sha256sum -c SHA256SUMS_v1.1.25.txt
gpg --import ZMETA_RELEASE_SIGNING_KEY_v1.1.25.asc
gpg --verify SHA256SUMS_v1.1.25.txt.asc SHA256SUMS_v1.1.25.txt
```

The public key ships in the repository as
`release/ZMETA_RELEASE_SIGNING_KEY_v1.1.2.asc` (same key, v1.1.2 through
v1.1.4 and v1.1.23 onward).
