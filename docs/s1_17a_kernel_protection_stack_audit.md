# S1-17A - Kernel Protection Stack Audit

Date: 2026-06-08

## Scope

This audit checked the current stack against the S1-16B kernel-protection
contract:

- locked semantics stay locked;
- tunable behavior remains policy/config behavior;
- advisory guidance does not become structural validity by accident;
- future/reserved/planned concepts remain `FUTURE_EXTENSION` material until
  versioned adoption;
- conformance protects the kernel without claiming exhaustive mission coverage.

The audit reviewed the tracked repository inventory with `git ls-files` and
targeted text searches for stale rule-class, future-vocabulary, release-target,
TAKEOFF, FORGE, and exhaustive-coverage drift.

Tracked inventory reviewed: 284 files.

## Changes Made

- Added a full kernel-protection conformance step to GitHub CI.
- Added `make validate-kernel` for the same local full conformance path.
- Updated `RELEASE_CHECKLIST.md` to require the full kernel-protection gate.
- Added the canonical full-kernel command to `conformance/README.md`.
- Updated `policy/README.md` to describe `LOCKED`, `TUNABLE`, `ADVISORY`, and
  `FUTURE_EXTENSION` boundaries.
- Updated `configs/policy-variants/README.md` to state that variants are
  tunable deployment overlays, not semantic exceptions.

No schemas, event vocabulary, gateway runtime behavior, adapters, encodings,
policy YAML semantics, examples, or conformance fixtures were changed.

## Folder Audit

| Surface | Files | Result |
|---|---:|---|
| `.github` | 1 | CI now runs both core strict conformance and full kernel-protection conformance. |
| Root docs/config | 11 | README already points to full conformance; Makefile and release checklist now expose the same gate. |
| `spec/` | 16 | Semantic contract, extension registry, conformance classes, profile/encoding specs, and release policy align with S1-16B. No new core semantics needed. |
| `schema/` | 5 | Exact v1.0/v1.1.0 version dispatch and subtype boundaries remain intact. No schema change needed. |
| `policy/` | 10 | Active YAML remains the tunable policy surface. README now states rule-class boundaries explicitly. |
| `configs/` | 8 | Configs remain deployment knobs. Policy variant README now clarifies that variants cannot bypass locked semantics or make future extensions valid. |
| `gateway/` | 31 | Validators and tests already enforce timing, lineage, producer authority, external promotion, risk labels, version dispatch, release hashes, bad-event corpus, and adapter harness. |
| `adapters/` | 52 | Ingress/egress docs and representative harness evidence preserve layer boundaries, UTC-Z normalization, lineage, and external promotion. Broader sensor-adapter certification remains planned rather than falsely claimed. |
| `conformance/` | 24 | Full optional guard path exists for projection, registry, classes, encoding-negative, precision, release, bad-events, and adapter harness. README now names this as the pre-release/CI-grade check. |
| `examples/` | 8 | Examples validate cleanly and do not introduce future/reserved vocabulary into v1.0. |
| `tools/` | 29 | Validation tools support the required kernel-protection checks. No tool logic change was needed beyond using existing validators in CI/Makefile. |
| `release/` | 53 | Live tracked release metadata is current for v1.1.5. Older tracked release notes/checksums/signatures are historical artifacts, not live drift. |
| `deploy/` | 3 | Docker deployment docs remain operational wrappers and do not redefine ZMeta semantics. |
| `docs/` | 29 | Audit trail is consistent; historical S1 notes preserve context and are not live semantic authority. |
| `source-docs/` | 2 | Legacy DOCX is explicitly non-normative; Markdown contract remains authoritative. |
| Encoding modules | 4 | CBOR, compact CBOR, protobuf, and UUID helpers remain projection/identity utilities and do not carry independent semantic authority. |

## Ignored Local Artifacts

`git status --short --ignored` shows local ignored state only:

- `LOCAL_NOTES.md` and `.gitconfig-local`;
- Python `__pycache__` trees;
- local release zips and generated release bundle/smoke folders;
- pytest cache/output folders.

Two ignored `pytest-cache-files-*` folders denied enumeration during the ignored
file count scan. They are ignored local cache folders and are not tracked,
release-governed, or semantically authoritative.

Ignored `release/bundles/` snapshots may contain older packaged files. They are
not tracked and are regenerated from the current tree by the release builders.
They should not be used as live semantic evidence.

## Findings

- No live schema, policy YAML, gateway runtime, adapter, encoding, example, or
  conformance-fixture drift was found.
- The main live gap was operational: CI and Makefile did not expose the complete
  kernel-protection conformance path as a first-class gate.
- Policy and policy-variant docs needed explicit locked-versus-tunable wording
  so operators know what they may tune without changing semantic truth.

## Verification

Verification for this slice:

```powershell
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
# projection conformance ok total=33
# extension registry ok entries=56
# conformance classes ok classes=34 claims=2
# encoding negative ok total=49
# profile precision policy ok total=32
# bad-event corpus ok total=9
# adapter conformance ok total=8
# conformance ok

python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
# release manifest ok groups=17 artifacts=59

python tools\validate_examples.py --strict --require-all
# overall total=40 passed=40 failed=0 warnings=0

python -m pytest -q
# 358 passed, 108 subtests passed

git diff --check
# passed with normal Windows CRLF conversion warnings
```
