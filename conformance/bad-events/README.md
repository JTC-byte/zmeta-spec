# Bad-Event Corpus

This suite contains intentionally dishonest or semantically unsafe ZMeta events.
It is narrower than `conformance/must-fail.jsonl`: each case documents a
contract failure pattern that an implementation must not treat as clean data.

Use:

```powershell
python tools\validate_bad_events.py --must-fail conformance\bad-events\must-fail.jsonl
python tools\validate_conformance.py --strict --bad-events
```

The corpus allows expected warning cases when the fixture declares
`expect_severity: warn`. This preserves the reject/warn/quarantine/degrade
policy model while still proving degraded or risky data is explicitly labeled.
