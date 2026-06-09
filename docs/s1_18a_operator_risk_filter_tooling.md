# S1-18A - Operator Risk Filter Tooling

Date: 2026-06-08

## Scope

This slice added consumer-side filtering for accepted-risk ZMeta streams.

The goal is to let operators and engineers tune intake posture dynamically
without changing semantic truth:

- policy/gateway surfaces label risk;
- consumers filter by explicit labels;
- risky data is not rewritten to look clean;
- locked semantics and future-extension boundaries remain unchanged.

## Changes Made

- Added `tools/filter_risk.py`.
- Added presets:
  - `display`
  - `fusion`
  - `state`
  - `command`
  - `autonomy`
  - `aar`
  - `audit`
- Added focused tests in `gateway/tests/test_risk_filter_cli.py`.
- Documented filter usage in `tools/README.md`, `gateway/README.md`,
  `configs/README.md`, `conformance/README.md`, `README.md`, and
  `RELEASE_CHECKLIST.md`.
- Updated `ZMETA-RISK-FILTERING` conformance evidence to include the filter
  tool and focused tests.
- Added `tools/filter_risk.py` to the governed release manifest conformance
  tools group and rebuilt release/claim hashes.

## Filter Model

The filter reads JSONL events and evaluates existing labels:

- event-side `payload.extensions.risk_adjudication`;
- same-stream `SYSTEM_EVENT/SCHEMA_VIOLATION` metrics with risk fields.

It writes passing events unchanged. Dropped events can be written to a sidecar
with reasons using `--dropped-output`.

The filter can evaluate:

- maximum accepted risk level;
- required operational use;
- allowed or denied `policy_decision`;
- allowed or denied `risk_dimension`;
- whether diagnostics should be dropped;
- whether clean events or only risk-labeled events should pass.

## Preset Intent

| Preset | Default Posture |
|---|---|
| `display` | Allow explicitly display-usable data through quarantine. |
| `fusion` | Allow clean or warning-labeled data explicitly usable as `FUSION_INPUT`. |
| `state` | Allow clean or warning-labeled data explicitly usable as `STATE_UPDATE`. |
| `command` | Allow only clean data for `COMMAND_BASIS`. |
| `autonomy` | Allow only clean data for `AUTONOMY_TASKING`. |
| `aar` | Allow AAR-usable data through quarantine. |
| `audit` | Pass clean, accepted-risk, quarantine, and rejected diagnostic events for review. |

## Non-Changes

This work did not add schemas, event vocabulary, policy YAML semantics, gateway
runtime mutation, adapters, encodings, examples, or future-extension terms.

The filter is not semantic authority. It is a consumer posture tool over labels
already emitted by policy and gateway behavior.

## Verification

Verification for this slice:

```powershell
python -m pytest -q gateway\tests\test_risk_filter_cli.py
# 6 passed

python tools\validate_conformance_classes.py --manifest conformance\conformance_classes.yaml --claims conformance\claims\example-reference-gateway.yaml conformance\claims\example-core-producer.yaml
# conformance classes ok classes=34 claims=2

python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
# release manifest ok groups=17 artifacts=60

python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package --bad-events --adapter-harness
# projection conformance ok total=33
# extension registry ok entries=56
# conformance classes ok classes=34 claims=2
# encoding negative ok total=49
# profile precision policy ok total=32
# bad-event corpus ok total=9
# adapter conformance ok total=8
# conformance ok

python tools\validate_examples.py --strict --require-all
# overall total=40 passed=40 failed=0 warnings=0

python -m pytest -q
# 364 passed, 108 subtests passed

git diff --check
# passed with normal Windows CRLF conversion warnings
```
