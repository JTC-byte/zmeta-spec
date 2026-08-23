# CLAUDE.md: Working Guide for the ZMeta Repo

Orientation for any Claude Code session working in this repository. This file is
**advisory** (Docs/advisory change class) and **non-normative**. It captures the
*intent* and *decision gates* that keep work aligned. It does not define
compliance and does not replace `AGENTS.md`.

**Authority order.** When this file conflicts with a governed source, defer to:
1. `spec/semantics-contract.md` (v1.0 Locked, normative)
2. `schema/zmeta-event.schema.json`, `schema/zmeta-event-1.0.schema.json`, `policy/*.yaml`
3. `AGENTS.md` and `docs/zmeta_change_governance.md` (change process, authority order, release limits)

Read `AGENTS.md` before touching any governed artifact.

## North Star

ZMeta is a **free, open, generatively-complete semantic alphabet for resilient
ISR**: a transport-agnostic translation layer that normalizes heterogeneous
sensor and tactical formats into one honest canonical event model, running as a
lightweight container at or near the sensor, so systems interoperate at scale
**without N×N point-to-point bridges**. Adapt once to ZMeta and inherit
interoperability with everything else ZMeta maps.

Solve interoperability first, at the standardize rung, so that automation,
modernization, and innovation can follow. You can't innovate until you
modernize, can't modernize until you automate, can't automate until you
standardize.

The semantic kernel is **locked and immutable**. Freedom lives above it: in
labels, policy, profiles, filters, and namespaced extensions. Growing the event
vocabulary to solve a local need defeats the entire purpose: it creates a
private dialect and silently breaks the interoperability guarantee for everyone
downstream. The governance, conformance, and hashing apparatus is not
bureaucracy. It is the enforcement mechanism of the "instant interoperability"
promise.

## Design Gates: apply to every change

1. **Alphabet, not dictionary.** ZMeta ships composable primitives, not a symbol
   for every idea (Legos, not pre-built castles). Before adding anything to the
   core, ask: *is this an essential primitive that cannot be composed from what
   already exists AND cannot live in a namespaced extension or mapping pack?* If
   it can be composed or extended, it does not go in the kernel. New brick only
   when there is a shape of connection no existing brick can make.

2. **Consumer-sufficiency, not producer-completeness.** Include a field because a
   downstream consumer needs it to *responsibly infer or act* ("the minimum
   an operator needs to know what the X on the map is"), not because a sensor
   happens to emit it. "Responsibly" means the honest uncertainty label travels
   with the data.

3. **Honesty end-to-end / no laundering.** Never make degraded, stale,
   low-confidence, or externally-promoted data look clean. Uncertainty,
   provenance, lineage, and timing quality stay explicit and filterable. The
   *consumer* adjudicates truth, never a black box.

4. **ZMeta is the source of truth; egress is projection.** The canonical ZMeta
   event is the authoritative semantic summary, linked back to the raw artifact
   via lineage / `data_ref`. Projections out (CoT/JREAP/KLV/MAVLink) are lossy
   and one-directional in authority; a re-imported projection is never equal to
   the original.

5. **Structure is authoritative; free-text is a human projection.** Semantically
   load-bearing data lives in structured, parseable fields (e.g. CoT `<detail>`
   sub-elements), never *only* in free-text (`remarks`). Render human-readable
   text *from* the structured source. Both channels are welcome, but structure
   is the source and remarks is the projection.

6. **Prefer the outer rings.** Solve needs via policy → config → profiles →
   adapter mappings → namespaced extensions *before* touching schema or core
   semantics. Escalate any schema, semantic, event-vocabulary, command-safety, or
   release-publication change to the maintainer before treating it as ready.

7. **Essentials-complete, not endlessly optimized.** Stop at generative
   completeness. Do not trap the standard in an indefinite optimization loop. A
   small, honest, stable kernel that others build on is the goal.

## How we work here

- **Align before acting.** Confirm intent on anything touching meaning; the
  standard's integrity outranks speed or cleverness.
- When auditing, ignore the duplicate snapshot trees: `.tmp/`,
  `release/bundles/`, `release/dist/`, `pytest-cache-files-*/`, `__pycache__/`.
  The canonical stack is the top-level tree.
- Before proposing governed changes as done, run the kernel gates:
  `python tools/validate_conformance.py --kernel-gate`,
  `python tools/validate_examples.py --strict --require-all`,
  and `python tools/validate_future_roadmap.py`,
  then `python -m pytest -q` (the same command block in `AGENTS.md` adds
  `git diff --check` as the final step).
- Never create tags, push branches, upload releases, generate signatures, or
  rewrite published checksums unless explicitly asked (see `AGENTS.md` release
  limits).
- **Windows tooling hygiene.** Two failure modes bit during the v1.1.13
  cycle: never round-trip repo text through Windows PowerShell
  `Get-Content`/`Set-Content`, which silently mojibakes UTF-8 (edit prose with
  the file tools or Python), and pass multi-line commit messages via
  `git commit -F <file>`, never inline `-m` (embedded quotes get mangled
  into pathspecs).
- **Documentation voice.** Repo documentation reads as flat, declarative
  technical prose: simple, clean, upfront and detailed, professional without
  sounding like a sales pitch. An outside reader called the README
  machine-written in July 2026, and the whole current-facing doc set was
  rewritten to fix it. Keep new writing to that standard rather than
  re-earning it later. Specifically, avoid: em dashes as a connector (use a
  comma, colon, semicolon, or a second sentence); inversion for emphasis
  ("X is not Y, it is Z"); sentence fragments or mid-sentence bolding used for
  rhythm, with bold reserved for genuine scanning aids such as a bullet's
  leading label; sentences opening with And, But or So to carry cadence; and
  metaphor standing in for a checkable statement. Do not over-correct into
  passive voice, hedging, or padding. A voice pass should leave word count
  flat or slightly higher, never compress. Two exceptions: quotations are
  copied exactly, tics included, and process records are never restyled,
  because rewriting them falsifies what was true when they were written.
  This standard also applies to commit subjects, tag annotations, and
  release titles (maintainer direction, 2026-08-03): describe the change
  in plain terms, with no aphorisms or taglines. Earlier commit history
  uses an aphoristic subject style; do not imitate it in new commits.
- **Commit attribution is human-only.** Attribute commits and PRs to the human
  maintainer alone. Do **not** add `Co-Authored-By` trailers naming Claude, and
  do not list the agent as a contributor. Every contributor in the stack works
  through Claude, so the repo's history tracks *people*, not the tool. This
  applies to commits and PRs, not to agent-guidance files like this one.
