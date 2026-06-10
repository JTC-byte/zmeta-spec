# R1-03 v1.1.7 Stack Audit And Release

Date: 2026-06-10

## Scope

Audited the current ZMeta stack before the v1.1.7 patch release, with emphasis
on stale current-release references, ignored local build residue, tracked-source
secret risk, release manifest coverage, process-governance documentation, and
compatibility/default tooling.

## Audit Findings

- Active current-release surfaces were moved from v1.1.6 to v1.1.7:
  `README.md`, release command examples, compatibility checker defaults, CI
  compatibility checks, release builder defaults, release manifest metadata,
  release notes, validation report, changelog, worklog, and handoff notes.
- Historical release records for v1.1.5 and v1.1.6 remain intentionally
  preserved. Their release notes, validation reports, checksum files, audit
  docs, and worklog entries are historical evidence, not live drift.
- Ignored generated local release directories were confirmed untracked and
  removed before rebuilding: `release/bundles/`, `release/smoke-edge/`,
  `release/smoke-gateway/`, and `release/package-v1.1.6/`.
- Tracked files were scanned for secret-like filenames and common private key,
  token, credential, and password markers. No tracked source secret findings
  were identified.
- Tracked release files were scanned for checked-in generated ZIP/signature
  residue. No tracked release ZIP or `.asc` artifact residue was identified.
- The v1.1.7 release remains a patch release. It does not add event vocabulary,
  does not make future-extension concepts valid, does not change v1.0 schema
  semantics, and does not claim literal raw IQ support.

## Release Content

v1.1.7 publishes the post-v1.1.6 current-main hardening work:

- profile-projection preservation for `payload.extensions.risk_adjudication`;
- compact external-promotion evidence preservation for lower-profile exports;
- stricter extension registry metadata for projection, risk, preservation,
  security/privacy, and fixture coverage;
- formal human/AI agent change governance and release-process limits;
- downstream clone guidance that separates local integration freedom from
  compatibility-breaking private dialect/fork changes;
- current-release pointer and compatibility-target cleanup.

## Validation Summary

The release validation gate includes release manifest validation, release
package validation, strict examples, full kernel conformance, focused
projection/registry/class/encoding/precision/bad-event/adapter validators,
compatibility checks, gateway self-tests, risk-filter checks, full pytest,
artifact builds, checksum generation, checksum verification, and `git diff
--check`.

Detached signatures are not generated unless an approved external signing
identity is available. The release is integrity-verified with
`SHA256SUMS_v1.1.7.txt` and the structured release manifest.
