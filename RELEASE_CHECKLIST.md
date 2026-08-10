# Release Checklist

Use this as the template for each release.

- [ ] `AGENTS.md` and `docs/zmeta_change_governance.md` reviewed for process requirements
- [ ] Change class identified and documented in handoff/worklog
- [ ] Semantic contract finalized for target version
- [ ] Contract hash recomputed
- [ ] **Governed baseline regenerated BEFORE the version bump**, from the
      manifest as it stands for the PREVIOUS release:
      `python tools/release_focus_facts.py --write-baseline --from-manifest release/zmeta-release-manifest.yaml`
      Order matters: run it before the release identity is bumped, or the
      baseline snapshots the new tree under the previous id and reports a
      governed change as clean. `gateway/tests/test_release_currency.py` pins that the baseline
      names the immediately previous published release.
- [ ] Release manifest built and validated
- [ ] Release package templates or generated package output validated
- [ ] Schema validates against examples
- [ ] Policy pack validation run locally
- [ ] Examples and conformance corpus validate locally:
      `python tools/validate_examples.py --strict --require-all`
- [ ] Full kernel-protection conformance passes:
      `python tools/validate_conformance.py --kernel-gate`
- [ ] Consumer risk-filter presets verified:
      `python -m pytest -q gateway/tests/test_risk_filter_cli.py`
- [ ] Gateway self-test passes locally
- [ ] Adapter and gateway pytest suite passes locally
- [ ] Profile L packet-size check passes locally
- [ ] Reference distribution bundle built
- [ ] Edge deployment bundle built
- [ ] Gateway deployment bundle built
- [ ] Formal release package metadata built in no-signature mode
      (`tools/build_release_package.py --release-notes
      release/RELEASE_NOTES_v<version>.md --release-state formal_release
      --no-signatures --allow-dirty --clean-output` during release prep;
      the `--release-state` flag is required because the builder defaults
      to `release_candidate`, and the v1.1.22 re-cut shipped a
      checksummed package self-describing `release_candidate` beside a
      `formal_release` manifest by omitting it; the
      `zmeta-release-package-<version>.zip` asset is built automatically
      from the package directory by `release/sign_release_artifacts.py
      --write-checksums`, never by hand, and the signer refuses a stale
      zip rather than checksumming it)
- [ ] Package ships the REAL release notes, not the template: pass
      `--release-notes release/RELEASE_NOTES_v<version>.md` to
      `tools/build_release_package.py`. Without it the template is copied
      verbatim and the package's `RELEASE_NOTES.md` reads "ZMeta Release
      Notes Template" with placeholder provenance beside metadata claiming
      `formal_release`. `validate_release_package` now fails this with
      `RELEASE_PACKAGE_NOTES_PLACEHOLDER`.
- [ ] No private keys, credentials, tokens, or signing secrets are present in release package paths
- [ ] Release notes updated
- [ ] Changelog updated
- [ ] `docs/zmeta_refinement_worklog.md` updated
- [ ] `docs/zmeta_refinement_handoff.md` updated
- [ ] Doc-currency pass: current-facing docs re-baselined to the new release
      (README current-release section and integration notes, installation
      guide, `docs/zmeta_professional_overview.md` release-context line,
      tools README examples, CI compatibility target and the
      compatibility CLI test, the release-manifest `release_id`/`release_date` pins in
      `gateway/tests/test_release_manifest.py`, the `VERSION` default in
      `release/sign_release_artifacts.py`, and `tools/check_compat.py`
      `TARGETS` extended with the new release id. `tools/check_adapter.py`
      derives its default compat target from the regenerated release
      manifest, so a manifest bump without a matching `TARGETS` entry breaks
      the wrapper for every adapter author).
      `gateway/tests/test_release_currency.py` machine-checks the enumerated
      current-facing surfaces (README, installation guide, professional
      overview, `release/README.md`, CHANGELOG first versioned heading,
      `check_compat` `TARGETS`) against the manifest `release_id` and fails
      pytest when any is stale; run it (or full pytest) after this pass
- [ ] Retention pass: worklog task sections completed before this release
      archived to `docs/zmeta_refinement_worklog_archive.md`; stale handoff
      content pruned
- [ ] SHA256SUMS generated for release assets
- [ ] SHA256SUMS verified
- [ ] Verifying a pre-v1.1.20 tag: check `docs/release_checksum_errata.md`
      first. Its published checksums for text assets are known wrong (no
      line-ending normalization before v1.1.20), and published files were
      never rewritten to match.
- [ ] Signing decision recorded: signed release, or checksums-only with the
      release notes stating that no detached signatures are attached
- [ ] *(signed releases only)* Detached signatures generated for SHA256SUMS
      and release assets
- [ ] *(signed releases only)* Detached signatures verified
- [ ] *(signed releases only)* Signing key fingerprint or Sigstore identity
      documented in release notes
- [ ] Release manifest and release package artifact attached or otherwise published
- [ ] GitHub Release body includes checksum/signature verification instructions
- [ ] GitHub CI passes for the release commit
- [ ] Gateway Docker build + run verified
- [ ] Tag created
- [ ] GitHub Release created with zips, SHA256SUMS, and signatures
