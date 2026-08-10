# Contributing To ZMeta

Status: current-main advisory governance.

ZMeta is a governed semantic standard and reference stack. Contributions are
welcome when they preserve interoperability, auditability, and the locked v1.0
kernel.

Before contributing, read:

- `AGENTS.md`
- `docs/zmeta_change_governance.md`
- `IP_POLICY.md`
- `CONFORMANCE.md`

## Contribution License

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in this repository is submitted under Apache License 2.0.

If a communication is not intended as a contribution, mark it conspicuously as
`Not a Contribution` before submitting it.

## Contributor Authority

By submitting a contribution, you represent that:

- you have the right to submit it under Apache License 2.0;
- it is not confidential, restricted, export-controlled, or proprietary
  material that you lack authority to contribute;
- it does not include third-party material unless that material is clearly
  identified and license-compatible;
- it does not include private keys, credentials, tokens, certificates with
  private material, or signing secrets.

If you are contributing on behalf of an employer or customer, confirm that you
have authority before submitting the work.

## Sign-Off

Use a DCO-style sign-off on commits when possible:

```text
Signed-off-by: Your Name <you@example.com>
```

The sign-off means you believe you have the authority to submit the
contribution under this repository's contribution terms.

## Change Process

Small docs and examples can be proposed directly. Governed surfaces require
matching validation and documentation updates. Follow the change classes in
`docs/zmeta_change_governance.md`.

At minimum, inspect state before editing:

```powershell
git status --short --branch
git log --oneline --decorate -n 10
```

For governed changes, expect to update the relevant docs, fixtures, tests,
release manifest, and example claim hashes together.

## Semantic Boundaries

Do not redefine these surfaces without explicit maintainer approval and a
versioned governance path:

- event type or subtype vocabulary;
- `zmeta_version` meaning or dispatch;
- required schema fields;
- units, geodesy, timing, lineage, confidence, TTL, or profile projection;
- risk labels, accepted-risk semantics, external-promotion evidence, or
  producer-authority semantics;
- command safety, command authority, or deconfliction semantics.

If a downstream implementation changes those surfaces locally, treat it as a
private dialect or fork rather than upstream-compatible ZMeta.

## Validation

Run the narrowest focused checks first. Before handoff for governed changes,
run:

```powershell
python tools\validate_conformance.py --kernel-gate
python -m pytest -q
git diff --check
```

Document any check you cannot run.

