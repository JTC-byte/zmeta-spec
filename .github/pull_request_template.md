<!-- See CONTRIBUTING.md and docs/zmeta_change_governance.md before opening. -->

## Change class

<!-- A: advisory docs/examples | B: governed baseline (contract/schema/policy/
     fixtures/validators/manifest) | C: runtime/reference (gateway/adapters/
     codecs/tools) | D: versioned semantic branch | E: release publication -->

## What and why


## Validation

<!-- Paste the commands you ran and their results. Minimum for governed (B/C+)
     changes: the full kernel gate, python -m pytest -q, git diff --check.
     Class A: git diff --check plus focused checks for any commands/paths the
     docs claim. -->

## Checklist

- [ ] No secrets, private keys, tokens, credentials, or private endpoints
- [ ] No release tags, published checksums, or release assets modified
- [ ] Locked v1.0 kernel untouched (no new vocabulary made valid)
- [ ] CHANGELOG / worklog / handoff updated where the change class requires it
- [ ] DCO-style sign-off on commits when possible (`Signed-off-by:`, per
      `CONTRIBUTING.md`)
