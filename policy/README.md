# Policy Pack

Policy-as-config rules used by the reference gateway for enforcement.

Files:
- `roles.yaml` allowed event types per node_role
- `profiles.yaml` allowed event types per profile
- `semantics.yaml` cross-field semantic constraints
- `routing.yaml` routing/source constraints
- `violation-codes.yaml` reason codes with severity tiers (advisory for reference implementations)

Normative compliance is defined by the semantic contract and schema; this policy pack
drives reference enforcement behavior.
