# Policy Variants

Optional deployment policy snippets. Copy the selected file into a deployment
`policy/` directory using the active filename expected by the gateway.

- `producer-authority.strict.yaml`: copy to `policy/producer-authority.yaml`
  after replacing the example producer IDs with local authenticated identities.
- `timing-freshness-profile-L-degrade.yaml`: copy to
  `policy/timing-freshness.yaml` when Profile L should degrade stale/missing
  timing while M/H remain fail-closed.
- `command-evidence.strict.yaml`: copy to `policy/command-evidence.yaml` when
  every COMMAND_EVENT must cite its evidence. It sets `require_evidence: true`
  for every task type and `unresolved_parent_mode: reject`, and changes
  nothing else. A human operator's direct command is not exempt: the
  operator cites the STATE_EVENT, INFERENCE_EVENT or FUSION_EVENT the command
  acts on.
- `routing.command-origin.yaml`: copy to `policy/routing.yaml` when an
  automation may originate only the closed set of non-movement commands,
  SCAN_RF and CHANGE_SENSOR_MODE. The two automation producers,
  `retasking-engine` and `comms-deconfliction-*`, carry that set plus every
  SYSTEM_EVENT subtype; the human-origin producer, `sensorops`, keeps every
  task type. Origin is declared by producer name, which does not prove who
  issued a command.

The last two together are the strict command posture: every command cites
its evidence, and platform movement is originated by the human-origin
producer only. `gateway/tests/test_command_policy_variants.py` pins each to
the reference file it replaces and runs the pair through the gateway.

`tools/assemble_policy_dir.py` builds a deployment policy directory from the
reference `policy/` directory plus the selected variants, runs the policy
lints, and prints the hashes to pin:

```
python tools/assemble_policy_dir.py --out <deployment>/policy \
    configs/policy-variants/command-evidence.strict.yaml \
    configs/policy-variants/routing.command-origin.yaml
```

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
