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
