"""TIME_STATUS payload.state Class B enum pins (doctrine R1-11-15, B-04).

Before this wave the v1.1.0 SystemPayload TIME_STATUS branch constrained
`metrics` only, so `payload.state: "NOMINAL"` over `metrics.sync_state:
"UNSYNCED"` passed the kernel clean - the operator-facing verdict could
launder over the metrics block that contradicted it. The 2026-07-27
adjudication (doctrine review log, R1-11-15 DECIDED) approved constraining
`state` to a declared vocabulary matching the sibling branches, v1.1.0 ONLY.

The vocabulary is derived from the tree, not from taste:

- ``LOCKED`` / ``HOLDOVER`` / ``UNSYNCED`` - the sync-state trio the examples
  corpus and conformance must-pass corpus publish as payload.state, the trio
  the gateway test corpus teaches (state mirrors metrics.sync_state), and the
  vocabulary the locked semantics contract names for timing loss.
- ``UP`` / ``DEGRADED`` / ``DOWN`` - the mavlink template's declared
  ``_TIME_STATUS_STATE_SEVERITY`` ordering, the health verdicts that adapter
  actually emits. Its "SYNCED" spelling is an input synonym normalised to UP
  before emission, so it is deliberately NOT a kernel enum member.

The v1.0 schema is LOCKED and stays byte-identical: the same NOMINAL event
must still pass under zmeta_version 1.0 (the semantic layer backstops it),
and that divergence is pinned here so nobody "fixes" the locked schema.
"""

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012
from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schema"
VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validators)


# The locked v1.0 schema, byte-for-byte. This wave (and every future one)
# must not touch it: the TIME_STATUS state enum is v1.1.0 ONLY.
# Digest of the LF-normalized bytes: git stores the schema with LF line
# endings, but a Windows checkout under autocrlf materializes CRLF, so a
# raw-bytes pin holds on exactly one platform (post-release CI catch,
# 2026-07-27). Normalizing CRLF to LF before hashing makes the pin hold on
# every checkout while still detecting any real edit.
# Pinned at the adjudicated lock baseline. The 2026-08-02 session moved this
# anchor believing the subtype consistency block a post-lock narrowing; the
# 2026-08-03 adjudication reversed that: the 2026-05-07 lockdown audit
# (contract section 7.3) is the lock's true baseline and the block is lawful
# enforcement of it. Moving this hash requires a maintainer adjudication on
# the record.
V1_0_SCHEMA_SHA256 = "1d2d84164b3a8986874e932c0e9369be3bf392a483a8ff261d464f34bd16d7b5"

# The derived vocabulary, in declared order: the sync-state trio in the
# metrics.sync_state enum's own order, then the mavlink template's health
# trio in its declared severity order (least degraded first, matching how
# the sibling LINK_STATUS enum is ordered).
TIME_STATUS_STATE_ENUM = ["LOCKED", "HOLDOVER", "UNSYNCED", "UP", "DEGRADED", "DOWN"]


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_unified_validator():
    schema_v1_0 = load_json(SCHEMA_DIR / "zmeta-event-1.0.schema.json")
    schema_v1_1_0 = load_json(SCHEMA_DIR / "zmeta-event-1.1.0.schema.json")
    unified_schema = load_json(SCHEMA_DIR / "zmeta-event.schema.json")

    registry = Registry().with_resources(
        [
            (
                schema_v1_0["$id"],
                Resource.from_contents(schema_v1_0, default_specification=DRAFT202012),
            ),
            (
                schema_v1_1_0["$id"],
                Resource.from_contents(schema_v1_1_0, default_specification=DRAFT202012),
            ),
        ]
    )
    return Draft202012Validator(
        unified_schema,
        registry=registry,
        format_checker=FormatChecker(),
    )


def time_status_event(state, *, version="1.1.0", sync_state="LOCKED"):
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TIME_STATUS",
            "ts": "2026-07-27T10:00:00Z",
        },
        "source": {
            "platform_id": "edge-node-01",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "profile": "L",
        "payload": {
            "system_type": "TIME_STATUS",
            "state": state,
            "metrics": {
                "time_source": "GPS_PPS",
                "sync_state": sync_state,
                "est_error_ms": 1,
                "last_sync_ts": "2026-07-27T09:59:59Z",
            },
        },
    }


def leaf_errors(validator, event):
    """Flatten jsonschema's composite errors to their leaves.

    The unified dispatcher wraps version dispatch in a combinator, so the
    top-level message is the useless "is not valid under any of the given
    schemas" - the honest diagnostic (the enum refusal) is a context leaf.
    """
    out = []

    def descend(err):
        if err.context:
            for child in err.context:
                descend(child)
        else:
            out.append(err)

    for err in validator.iter_errors(event):
        descend(err)
    return out


def resolve_time_status_state_schema(schema):
    """Walk to the TIME_STATUS branch's `state` subschema, sibling-style."""
    branches = schema["$defs"]["SystemPayload"]["allOf"]
    matches = [
        branch
        for branch in branches
        if set(branch.get("if", {}).get("properties", {})) == {"system_type"}
        and branch["if"]["properties"]["system_type"].get("const") == "TIME_STATUS"
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one TIME_STATUS type branch, found {len(matches)}"
        )
    return matches[0]["then"]["properties"].get("state")


class TimeStatusStateEnumTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_unified_validator()

    def test_v1_1_declared_enum_matches_derived_vocabulary(self):
        """The v1.1.0 branch constrains state exactly like its siblings."""
        state_schema = resolve_time_status_state_schema(
            load_json(SCHEMA_DIR / "zmeta-event-1.1.0.schema.json")
        )
        self.assertIsNotNone(
            state_schema,
            "v1.1.0 TIME_STATUS branch does not constrain payload.state",
        )
        self.assertEqual(state_schema.get("type"), "string")
        self.assertEqual(state_schema.get("enum"), TIME_STATUS_STATE_ENUM)

    def test_v1_1_out_of_vocabulary_state_refused(self):
        """B-04's exact laundering shape: NOMINAL over an UNSYNCED metrics
        block must be schema-refused under 1.1.0 with the enum diagnostic."""
        event = time_status_event("NOMINAL", sync_state="UNSYNCED")
        ok, violations = validators.validate_schema(event, self.schema)
        self.assertFalse(ok, "v1.1.0 accepted TIME_STATUS state 'NOMINAL'")
        self.assertTrue(violations)
        self.assertEqual(violations[0]["code"], "SCHEMA_INVALID")

        expected_message = (
            "'NOMINAL' is not one of ['LOCKED', 'HOLDOVER', 'UNSYNCED', "
            "'UP', 'DEGRADED', 'DOWN']"
        )
        leaves = leaf_errors(self.schema, event)
        messages = [err.message for err in leaves]
        self.assertIn(
            expected_message,
            messages,
            f"expected the enum refusal diagnostic, got: {messages}",
        )
        enum_error = leaves[messages.index(expected_message)]
        self.assertEqual(list(enum_error.absolute_path), ["payload", "state"])

    def test_v1_1_synced_spelling_is_not_a_kernel_member(self):
        """SYNCED is the mavlink-side input spelling, normalised to UP before
        emission - the kernel enum must not admit it."""
        event = time_status_event("SYNCED", sync_state="LOCKED")
        ok, _violations = validators.validate_schema(event, self.schema)
        self.assertFalse(ok, "v1.1.0 accepted TIME_STATUS state 'SYNCED'")
        expected_message = (
            "'SYNCED' is not one of ['LOCKED', 'HOLDOVER', 'UNSYNCED', "
            "'UP', 'DEGRADED', 'DOWN']"
        )
        self.assertIn(
            expected_message,
            [err.message for err in leaf_errors(self.schema, event)],
        )

    def test_every_vocabulary_member_validates(self):
        """All six derived members stay schema-valid under 1.1.0."""
        for state in TIME_STATUS_STATE_ENUM:
            with self.subTest(state=state):
                ok, violations = validators.validate_schema(
                    time_status_event(state), self.schema
                )
                self.assertTrue(
                    ok,
                    f"vocabulary member {state!r} no longer validates: "
                    f"{[item['message'] for item in violations]}",
                )

    def test_v1_0_schema_byte_identical(self):
        """The locked v1.0 schema is untouched by this wave (EOL-agnostic)."""
        raw = (SCHEMA_DIR / "zmeta-event-1.0.schema.json").read_bytes()
        digest = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        self.assertEqual(digest, V1_0_SCHEMA_SHA256)

    def test_v1_0_state_stays_unconstrained(self):
        """Version discrimination: the same NOMINAL event passes the locked
        v1.0 schema (its TIME_STATUS branch constrains metrics only). This
        pins the divergence so nobody 'aligns' the locked schema."""
        event = time_status_event("NOMINAL", version="1.0", sync_state="UNSYNCED")
        ok, violations = validators.validate_schema(event, self.schema)
        self.assertTrue(
            ok,
            "locked v1.0 schema behavior changed: "
            f"{[item['message'] for item in violations]}",
        )


if __name__ == "__main__":
    unittest.main()
