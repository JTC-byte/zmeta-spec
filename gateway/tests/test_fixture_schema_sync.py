"""Pin the advisory fixture lint schema to the harness's actual fixture surface.

conformance/adapter-harness/fixture.schema.json declares additionalProperties
false at both the fixture and expect levels, so any key the harness learns to
read that is not added to the schema turns valid fixtures into false lint
failures for adapter authors. This test makes that drift a test failure at the
moment it is introduced instead of a surprise in someone else's ladder run.
"""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS_SOURCE = (ROOT / "tools" / "validate_adapter_conformance.py").read_text(encoding="utf-8")
SCHEMA = json.loads(
    (ROOT / "conformance" / "adapter-harness" / "fixture.schema.json").read_text(encoding="utf-8")
)

# Every string literal the harness reads off a fixture or expect mapping.
_GET_RE = re.compile(r"""(?:fixture|expect|indexed_expect)(?:\.get\(|\[)\s*["']([a-z_]+)["']""")

# Keys read from the fixture line itself (not inside expect).
FIXTURE_LEVEL_KEYS = {"module", "callable", "args", "kwargs", "result", "profile", "name", "expect"}


def _harness_keys() -> set[str]:
    return set(_GET_RE.findall(HARNESS_SOURCE))


def test_every_harness_fixture_key_is_in_the_lint_schema():
    fixture_props = set(SCHEMA["properties"])
    missing = (FIXTURE_LEVEL_KEYS & _harness_keys()) - fixture_props
    assert not missing, (
        f"harness reads fixture keys absent from fixture.schema.json properties: {sorted(missing)} "
        "(the schema uses additionalProperties: false, so these become false lint failures)"
    )


def test_every_harness_expect_key_is_in_the_lint_schema():
    expect_props = set(SCHEMA["$defs"]["expect"]["properties"])
    expect_keys = _harness_keys() - FIXTURE_LEVEL_KEYS
    missing = expect_keys - expect_props
    assert not missing, (
        f"harness reads expect keys absent from fixture.schema.json $defs/expect: {sorted(missing)} "
        "(the schema uses additionalProperties: false, so these become false lint failures)"
    )


def test_leaf_expect_does_not_lag_expect():
    # Per-index expectations reuse the same reader code paths, so every expect
    # key except the result-level ones must also be valid inside events[i].
    expect_props = set(SCHEMA["$defs"]["expect"]["properties"])
    leaf_props = set(SCHEMA["$defs"]["leaf_expect"]["properties"])
    result_level_only = {"events", "event_count"}
    missing = (expect_props - result_level_only) - leaf_props
    assert not missing, f"leaf_expect is missing expect keys: {sorted(missing)}"
