# ZMeta Future-Branch Roadmap

The future-branch roadmap is the machine-readable companion to the D-003
versioned semantic branch plan
(`docs/s1_11_future_versioned_semantic_branch_roadmap_plan.md`). It records,
per future-branch candidate: status, priority, dependencies, required
implementation surfaces, recorded field evidence, promotion tripwires, and
rejection/defer decisions.

It exists so that future semantic work is tracked in one governed place and
so that promotion decisions are made against recorded evidence instead of
memory or re-litigated debate.

## Authority

The roadmap is a planning and governance artifact. It is **not** a vocabulary
source.

Required rule:

> The roadmap does not make any concept valid. Name governance stays in
> `spec/extension-registry.yaml`; semantic authority stays in
> `spec/semantics-contract.md`. Reserved and proposed concepts remain invalid
> until an approved version branch adds schema, policy, adapter/gateway,
> encoding, documentation, fixture, conformance, release, and audit coverage.

Roadmap candidate status describes the maturity of a *branch concept*. The
extension registry status of each referenced name governs that *name*. When
they disagree, the registry is authoritative for validity.

## Machine-Readable Roadmap

The machine-readable roadmap is:

```text
spec/future-branch-roadmap.yaml
```

Validate it with:

```bash
python tools/validate_future_roadmap.py --roadmap spec/future-branch-roadmap.yaml
```

Validation is standalone and opt-in, matching the original opt-in posture of
registry validation. It checks structure, status/priority vocabulary, unique
candidate ids, dependency resolution, registry cross-references, tripwire
coverage, and status leakage (a roadmap candidate cannot claim experimental
or adopted standing while its registry names remain reserved/proposed).

## Candidate Fields

- `id`: stable kebab-case candidate identifier.
- `display_name`: human-readable name.
- `status`: branch-concept lifecycle status (S1-11A Section D vocabulary).
- `priority`: `near_term`, `mid_term`, `long_term`, or `evidence_gated`.
  `evidence_gated` marks candidates whose sequencing is driven purely by the
  promotion evidence bar rather than roadmap ordering.
- `purpose` / `affected_events`: what the branch would define and where.
- `registry_refs`: extension-registry entry names governed by this candidate.
- `depends_on`: other candidate ids that should precede this branch.
- `required_surfaces`: `default` (the full S1-11A adoption gate list in
  `default_required_surfaces`) or an explicit list.
- `promotion_evidence`: recorded field evidence to date. Each entry should
  state the date, the source, and how many independent implementations it
  represents. An empty list means no evidence recorded.
- `tripwires`: the concrete conditions that would justify promotion. Every
  candidate must have at least one tripwire; the default tripwire is the
  promotion evidence bar in `spec/extension-registry.md` (two or more
  independent implementations plus a documented semantic-contract Section
  2.6 failure condition).
- `recommendation` / `notes`: advisory maintainer guidance.

`rejected_or_deferred` records decisions made against concepts so they are
durable and not re-litigated. Registry `rejected` entries remain the
authoritative rejection record for names.

## How To Use The Roadmap

1. When field evidence arrives (external PRs, deployment reports, audits),
   append it to the matching candidate's `promotion_evidence` — external
   contributions are field telemetry, not patches.
2. When a tripwire fires, the candidate becomes eligible for an `Sx-A Plan
   Only` document per the S1-11A implementation pattern. Nothing is
   implemented from the roadmap directly.
3. When a concept is declined, record the decision in
   `rejected_or_deferred` (and as a `rejected` registry entry when a name
   was proposed).
4. Keep `last_updated` current and re-run the validator after every edit.

The roadmap does not replace the extension registry, the change governance
process, or maintainer approval. It feeds them.
