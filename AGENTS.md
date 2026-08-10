# ZMeta Agent And Maintainer Guide

This repository is the ZMeta semantic standard and reference stack. Treat it as
a governed specification, not as an application codebase where any local need
can directly redefine the data model.

For the full change process, read:

```text
docs/zmeta_change_governance.md
```

For contribution, conformance, name-use, and industry-sharing posture, also
read:

```text
IP_POLICY.md
CONTRIBUTING.md
CONFORMANCE.md
TRADEMARK.md
docs/zmeta_defensive_publication.md
```

## Operating Model

- Preserve the semantic kernel: event identity, version dispatch, event-family
  separation, units/geodesy, confidence rules, lineage, timing quality,
  profile projection, producer authority, and command safety.
- Keep v1.0 locked. Do not make v1.1.0 or future registry concepts valid under
  `zmeta_version: "1.0"`.
- Prefer policy, config, adapter mappings, profile projection, or extension
  registry governance before changing schemas or core semantics.
- Accepted risk must remain explicit, policy-adjudicated, auditable, and
  filterable. Do not make degraded or externally promoted data look clean.
- Future concepts may be documented or reserved, but they are not valid event
  vocabulary until a versioned branch adds schema, policy, adapter/encoding,
  conformance, release, and audit coverage.
- Share only public release, conformance, and defensive-publication material in
  industry circles unless unpublished material is covered by an appropriate
  agreement or has explicit maintainer approval.

## Downstream Clone Users

These rules are interoperability boundaries, not permission barriers. If you
cloned this repository without maintainer or collaborator access, you can still
use the stack freely for local integration:

- pin to a tagged release and validate ZMeta events locally;
- build adapters, deployment policy, filters, dashboards, and application
  mappings around the released contract;
- keep private notes, local patches, and deployment-specific configuration;
- run the reference gateway, tools, conformance checks, and tests in your own
  environment.

If you expect to interoperate with upstream ZMeta or other ZMeta ecosystems, do
not locally redefine:

- event type or subtype vocabulary;
- `zmeta_version` meaning or version dispatch;
- required schema fields;
- units, geodesy, timing quality, lineage, confidence, TTL, or profile
  projection rules;
- risk labels, accepted-risk semantics, external-promotion evidence, or
  producer-authority policy semantics;
- command safety, command authority, or deconfliction semantics.

If you change those surfaces locally, treat the result as a private fork or
dialect. Do not claim upstream compatibility unless the change has versioning,
documentation, conformance evidence, and release governance. Prefer adapters,
policy/config, profiles, and namespaced extensions over changing core schema or
semantic meaning.

## Change Classes

- **Docs/advisory**: README, examples, deployment notes, handoff/worklog, and
  explanatory docs that do not change validation or governed artifacts.
- **Governed baseline**: semantic contract, schemas, policy YAML, extension
  registry, conformance classes, projection/precision/encoding fixtures,
  validators, release manifest, release tooling, and claims.
- **Runtime/reference**: gateway, adapters, codecs, and tools that implement or
  demonstrate the governed baseline.
- **Release/publication**: release notes, validation report, checksums,
  package metadata, tags, signatures, and uploaded assets.

Escalate schema, semantic-contract, event-vocabulary, profile, command-safety,
or release-publication changes to a human maintainer before treating them as
ready to publish.

## Required Local Workflow

Before editing, inspect current state:

```powershell
git status --short --branch
git log --oneline --decorate -n 10
```

When changing governed artifacts, update the matching docs and validation
surfaces in the same change. At minimum consider:

- `CHANGELOG.md`
- `docs/zmeta_refinement_worklog.md`
- `docs/zmeta_refinement_handoff.md`
- relevant `spec/`, `policy/`, `conformance/`, `release/`, or `tools/` docs
- `release/zmeta-release-manifest.yaml` and example claim hashes when governed
  manifest artifacts changed

Downstream application integrations that only consume a pinned ZMeta release do
not need to update upstream worklogs, changelogs, or release manifests. Update
those process artifacts when proposing an upstream change, maintaining a forked
ZMeta baseline, or publishing a derived dialect.

Run the narrowest focused checks first, then the kernel gate:

```powershell
python tools\validate_conformance.py --kernel-gate
python tools\validate_examples.py --strict --require-all
python -m pytest -q
git diff --check
```

If you cannot run a required check, document the reason in the final handoff.

## Release Limits

- Do not create tags, push branches, upload GitHub releases, generate detached
  signatures, or change published checksum files unless explicitly asked by the
  release authority.
- Do not commit private keys, tokens, credentials, certificates with private
  material, signing secrets, or generated local cache/package output.
- `release/SHA256SUMS_<version>.txt` represents published assets for that
  version. Do not rewrite it for post-release current-main guidance changes.
- A post-release main commit that regenerates the release manifest under the
  published identity makes current main diverge from the published
  `SHA256SUMS_<version>.txt` manifest pin. Record that divergence explicitly
  in the worklog entry for the commit (published checksums are immutable;
  resolution is the next release cut) — an unexplained mismatch must never be
  the downstream verifier's first notice.

## Handoff Standard

A completed change should leave the next maintainer able to answer:

- what changed and why;
- whether it changed semantics, schema, policy, runtime, docs, or release
  packaging;
- what validation ran and what passed;
- whether the public release baseline or only current `main` changed;
- what remains open or intentionally deferred.
