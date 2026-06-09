# S1-13A - Stack Conformance And Stale File Audit

Date: 2026-06-08

## Scope

This audit reviewed the current ZMeta stack for semantic-contract conformance,
release/version drift, stale tracked files, rogue generated artifacts, and
deferred issue state.

The audit did not change the semantic contract, JSON schemas, policy packs,
extension registry, conformance class manifest, adapters, encodings, release
manifest, or event vocabulary.

## Findings

- The tracked worktree had no untracked non-ignored files.
- Ignored local artifacts were expected local state: `LOCAL_NOTES.md`,
  `.gitconfig-local`, Python `__pycache__/`, generated release zip files,
  `release/bundles/`, `release/dist/`, and smoke extraction directories.
- Active README/release surfaces identify `v1.1.5` as the current release.
- `tools/check_compat.py` and CI still targeted `v1.1.4`; this was stale live
  tooling drift and was corrected to `v1.1.5`.
- Historical `v1.1.4`, `TAKEOFF`, and FORGE references remain only as release
  history, invalidity guards, or audit history.
- D-009 had enough implied coverage in existing tests, but lacked explicit
  boundary tests proving that generic v1.0 observation extension permissiveness
  does not adopt v1.1.0 formal feature, quality, or data-reference contracts.

## Changes Made

- Updated `tools/check_compat.py` to accept and default to `--target v1.1.5`.
- Updated `.github/workflows/ci.yml` migration compatibility checks to target
  `v1.1.5`.
- Added a regression test proving `tools/check_compat.py --target v1.1.5`
  accepts current examples.
- Added explicit D-009 boundary tests:
  - v1.0 generic EO/ACOUSTIC observation extension shapes can be structurally
    valid without becoming v1.1.0 formal feature contracts.
  - v1.0 generic quality and data-reference shapes can be structurally valid
    without becoming v1.1.0 structured quality or formal data-reference
    contracts.

## Deferred Issue State

- D-009 is closed. The stack now has explicit tests for the v1.0/v1.1.0
  observation extension boundary.
- D-003 remains `OPEN - ROADMAP PLANNED` for future versioned semantic branches.

## Verification

Verification completed during this audit:

```powershell
python tools\check_compat.py examples\zmeta-command-examples.jsonl --target v1.1.5
python -m pytest -q gateway\tests\test_check_compat_cli.py
python -m pytest -q gateway\tests\test_schema_version_discrimination.py
python tools\validate_examples.py --strict --require-all
python tools\validate_conformance.py --strict --profile-projection --extension-registry --conformance-classes --encoding-negative --precision-policy --release-manifest --release-package
python tools\validate_release_manifest.py --manifest release\zmeta-release-manifest.yaml
python tools\validate_release_package.py --manifest release\zmeta-release-manifest.yaml --templates-only
python gateway\src\gateway.py --profile H --self-test
python -m pytest
git diff --check
```

Results:

- Compatibility check: `issues=0 failed=0 warnings=0`.
- Compatibility CLI tests: `4 passed`.
- Schema version-discrimination tests: `118 passed`.
- Strict example validation: `40 passed`.
- Full opt-in conformance: passed.
- Release manifest validation: `release manifest ok groups=15 artifacts=55`.
- Release package template validation: passed.
- Gateway self-test: `self-test: ok`.
- v1.1.5 checksum verification: passed.
- Full pytest: `336 passed`.
- Whitespace diff check: passed with CRLF conversion warnings only.
