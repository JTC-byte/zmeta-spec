# Policy Variants

Optional deployment policy snippets. Copy the selected file into a deployment
`policy/` directory using the active filename expected by the gateway.

- `producer-authority.strict.yaml`: copy to `policy/producer-authority.yaml`
  after replacing the example producer IDs with local authenticated identities.
- `timing-freshness-profile-L-degrade.yaml`: copy to
  `policy/timing-freshness.yaml` when Profile L should degrade stale/missing
  timing while M/H remain fail-closed.

These files are outside the reference `policy/` directory so they do not change
the reference policy hash until explicitly adopted by a deployment.

Policy variants are tunable deployment overlays, not semantic exceptions. They
may adjust bounded responses such as reject, warn, degrade, quarantine,
freshness thresholds, producer allowlists, routing gates, confidence caps, TTL
caps, and degraded-link tolerance. They must not redefine event vocabulary,
semantic layers, units/geodesy, confidence semantics, lineage requirements,
profile behavior, command safety, adapter/gateway obligations, or
`FUTURE_EXTENSION` validity.

Once a variant is copied into the active deployment `policy/` directory, it is
part of that deployment's policy hash. Recompute hashes with
`python tools/compute_contract_hash.py` against the active policy directory and
update any configured `require_policy_hash` or `require_contract_hash` startup
gate for that deployment. Keeping a variant as an external overlay preserves the
reference release hash; adopting it as active policy intentionally creates a
deployment-local hash.
