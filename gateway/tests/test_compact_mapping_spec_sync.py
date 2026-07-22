"""The compact mapping SPEC and the compact CODEC must not drift apart.

R1-11 A-28, the item that matters most for the standard rather than for this
repo: `spec/compact-binary-mapping.md` is the artifact a third-party
implementer reads. Its Scope section carries the fail-closed MUSTs and its
"Declared representation normalizations" table is the exhaustive list of
differences between an input envelope and its decoded form that this mapping
calls *representation* rather than *loss*.

Nothing held the two together in EITHER direction. The only toolchain
reference to the file is the release manifest's checksum, which is a CURRENCY
pin: delete the section, regenerate the manifest, and the whole suite stays
green. So:

- a normalization implemented but NOT declared is silent laundering — a
  conforming implementer reading the spec would refuse an event this codec
  accepts, and the two nodes disagree about what the same bytes mean;
- a normalization declared but NOT implemented sends implementers chasing
  behaviour the reference codec does not have, and the reference refuses
  schema-valid events from conforming producers.

The join between the two sides is derived, not hand-maintained: each table
row states its verdict as a closing "Same <thing>." sentence, and the codec
declares each equivalence as a `_same_<thing>` predicate in the one arm of
`_semantic_difference` that returns "equivalent" for values that are not
equal. Adding a normalization therefore means adding both, or this fails.

What this file cannot see, stated so nobody mistakes it for total coverage:
the structural half reads `_semantic_difference` only, so a normalization
applied INSIDE the encoder or decoder - a field lowercased on the way out and
therefore equal on the way back - never reaches the comparator and is invisible
to it. The behavioural corpus below catches such a change only if it happens to
be one of the six shapes enumerated there. A generative round-trip differential
would close that gap and is deliberately not built here (gate 7); the shapes
that gap admits are all field-specific rather than value-class-wide, and the
per-field mapping is already pinned by the round-trip corpus in
`test_compact_fail_closed.py`.

Every check asserts a non-vacuity floor before it asserts anything else.
"""

import ast
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import zmeta_compact  # noqa: E402

MAPPING_SPEC = ROOT / "spec" / "compact-binary-mapping.md"
CODEC_PATH = ROOT / "zmeta_compact.py"


# --------------------------------------------------------------------------
# Doc side: the declared normalization table
# --------------------------------------------------------------------------

_TABLE_HEADING = "### Declared representation normalizations"
_SAME_CLAIM = re.compile(r"Same ([A-Za-z][A-Za-z0-9_]*)\.\s*$")


def declared_normalization_rows(text: str) -> list[tuple[str, str]]:
    """(name cell, verdict cell) for every row of the declared table.

    Anchored on the heading and terminated by the next blank line after the
    table body, so prose added under the section cannot be read as rows.
    """
    start = text.find(_TABLE_HEADING)
    assert start != -1, (
        f"{MAPPING_SPEC.name} no longer carries a "
        f"'{_TABLE_HEADING.lstrip('# ')}' section: the declared-normalization "
        "table is the exhaustive list of what this mapping calls representation "
        "rather than loss, and an implementer has nothing to read without it"
    )
    rows: list[tuple[str, str]] = []
    seen_table = False
    for line in text[start:].splitlines()[1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if seen_table:
                break
            continue
        seen_table = True
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 2:
            continue
        if cells[0] == "Normalization" or set(cells[0]) <= {"-", ":", " "}:
            continue
        rows.append((cells[0], cells[1]))
    return rows


def declared_equivalence_names(text: str) -> set[str]:
    """The `_same_<thing>` predicate each declared row commits the codec to."""
    names = set()
    for name_cell, verdict_cell in declared_normalization_rows(text):
        match = _SAME_CLAIM.search(verdict_cell)
        assert match, (
            f"declared normalization {name_cell!r} does not close with a "
            "'Same <thing>.' verdict. That sentence is what names the "
            "equivalence the codec must implement as `_same_<thing>`; without "
            "it the row states no checkable claim"
        )
        names.add(f"_same_{match.group(1).lower()}")
    return names


# --------------------------------------------------------------------------
# Code side: the equivalence arm of _semantic_difference
# --------------------------------------------------------------------------


def _semantic_difference_node() -> ast.FunctionDef:
    tree = ast.parse(CODEC_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_semantic_difference":
            return node
    raise AssertionError("zmeta_compact._semantic_difference not found")


def _equivalence_arms() -> list[ast.If]:
    """Every `if <test>: return None` inside _semantic_difference.

    These are exactly the places the comparison declares two values equivalent.
    There are two by construction: literal equality, and the declared
    normalizations. A third would be an undeclared equivalence.
    """
    return [
        node
        for node in ast.walk(_semantic_difference_node())
        if isinstance(node, ast.If)
        and len(node.body) == 1
        and isinstance(node.body[0], ast.Return)
        and isinstance(node.body[0].value, ast.Constant)
        and node.body[0].value.value is None
    ]


def _predicate_calls(test: ast.expr) -> list[ast.Call] | None:
    """The disjunct calls of an equivalence test, or None if it is not one."""
    if isinstance(test, ast.Call):
        return [test]
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or):
        if all(isinstance(value, ast.Call) for value in test.values):
            return list(test.values)
    return None


def implemented_equivalence_names() -> set[str]:
    arms = _equivalence_arms()
    assert len(arms) == 2, (
        "zmeta_compact._semantic_difference has "
        f"{len(arms)} `return None` arms, expected 2 (literal equality, and "
        "the declared normalizations). A third arm is an equivalence the "
        "mapping spec does not declare — which is the laundering this file "
        "exists to catch"
    )
    literal, declared = arms
    assert isinstance(literal.test, ast.Compare) and isinstance(
        literal.test.ops[0], ast.Eq
    ), "the first equivalence arm is no longer plain `original == restored`"

    calls = _predicate_calls(declared.test)
    assert calls is not None, (
        "the declared-normalization arm of _semantic_difference is no longer a "
        "disjunction of predicate calls. An equivalence spelled inline (say "
        "`original.lower() == restored.lower()`) cannot be matched against the "
        "spec's declared table, so it must be a named `_same_<thing>` predicate"
    )
    names = set()
    for call in calls:
        assert isinstance(call.func, ast.Name), (
            "an equivalence disjunct is not a plain named call: "
            f"{ast.dump(call.func)}"
        )
        assert call.func.id.startswith("_same_"), (
            f"equivalence predicate {call.func.id!r} does not follow the "
            "`_same_<thing>` naming that joins it to a declared table row"
        )
        assert [
            arg.id for arg in call.args if isinstance(arg, ast.Name)
        ] == ["original", "restored"], (
            f"{call.func.id} is not comparing the original against the restored "
            "value; an equivalence that compares something else is not the "
            "normalization the table declares"
        )
        names.add(call.func.id)
    return names


# --------------------------------------------------------------------------
# The two directions
# --------------------------------------------------------------------------


class DeclaredNormalizationSyncTest(unittest.TestCase):
    def setUp(self):
        self.text = MAPPING_SPEC.read_text(encoding="utf-8")

    def test_the_declared_table_is_not_empty(self):
        # Non-vacuity floor for everything below: an empty table would make
        # both set comparisons trivially satisfiable by an empty codec set.
        rows = declared_normalization_rows(self.text)
        self.assertGreaterEqual(
            len(rows),
            2,
            f"the declared normalization table has {len(rows)} rows; the "
            "mapping has always declared at least UUID hex case and "
            "millisecond timestamp formatting",
        )

    def test_every_implemented_normalization_is_declared_in_the_spec(self):
        """The laundering direction.

        A normalization the codec performs but the spec does not declare makes
        the reference implementation accept events a conforming implementer
        would refuse, on a wire whose whole premise is that the decoded
        envelope means the same thing.
        """
        declared = declared_equivalence_names(self.text)
        implemented = implemented_equivalence_names()
        undeclared = sorted(implemented - declared)
        self.assertEqual(
            [],
            undeclared,
            f"zmeta_compact treats {undeclared} as representation-only, but "
            f"{MAPPING_SPEC.name} declares only {sorted(declared)}. Add a table "
            "row closing with 'Same <thing>.' before shipping the behaviour",
        )

    def test_every_declared_normalization_is_implemented_by_the_codec(self):
        """The other direction: a promise the reference does not keep.

        A declared normalization the codec does not implement means the
        reference refuses schema-valid events from conforming producers, which
        the spec itself calls out as its own failure.
        """
        declared = declared_equivalence_names(self.text)
        implemented = implemented_equivalence_names()
        missing = sorted(declared - implemented)
        self.assertEqual(
            [],
            missing,
            f"{MAPPING_SPEC.name} declares {missing} as representation-only, "
            f"but _semantic_difference implements only {sorted(implemented)}",
        )

    def test_each_declared_predicate_exists_and_is_reachable(self):
        # Guard the guard: the AST walk reads names, not bindings. A row/arm
        # pair naming a predicate that does not exist would satisfy both set
        # comparisons above and fail only at runtime.
        for name in sorted(implemented_equivalence_names()):
            with self.subTest(predicate=name):
                self.assertTrue(
                    callable(getattr(zmeta_compact, name, None)),
                    f"{name} is called by _semantic_difference but is not a "
                    "callable in zmeta_compact",
                )


# --------------------------------------------------------------------------
# Behaviour: the declared normalizations really are accepted, and nothing else
# --------------------------------------------------------------------------


def _v1_0_event() -> dict:
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5d-4cd9-770e-b02d-55d71e516898",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:31:05Z",
        },
        "source": {
            "platform_id": "fusion-node-01",
            "node_role": "FUSION",
            "producer": "fusion-engine",
        },
        "payload": {
            "track_id": "trk-001",
            "geo": {"lat": 34.05, "lon": -118.24, "alt_m": 120.0},
        },
    }


class DeclaredNormalizationBehaviourTest(unittest.TestCase):
    """The declared rows are behaviour, not prose.

    Each runs through the real serialization boundary the Scope section
    requires (encode to bytes, decode, compare), and each is asserted to be a
    genuine normalization — the decoded string DIFFERS from the input — so a
    row cannot pass by being a no-op.
    """

    def _roundtrip(self, event):
        return zmeta_compact.loads(zmeta_compact.dumps(event))

    def test_uuid_hex_case_is_accepted_and_lowercased(self):
        event = _v1_0_event()
        event["event"]["event_id"] = event["event"]["event_id"].upper()
        restored = self._roundtrip(event)
        self.assertNotEqual(
            event["event"]["event_id"],
            restored["event"]["event_id"],
            "the UUID row is a no-op here, so it proves nothing",
        )
        self.assertEqual(
            event["event"]["event_id"].lower(), restored["event"]["event_id"]
        )

    def test_millisecond_timestamp_formatting_is_accepted(self):
        for original, expected in (
            ("2025-01-17T14:31:05.876Z", "2025-01-17T14:31:05.876000Z"),
            ("2025-01-17T14:31:05.000Z", "2025-01-17T14:31:05Z"),
        ):
            with self.subTest(ts=original):
                event = _v1_0_event()
                event["event"]["ts"] = original
                restored = self._roundtrip(event)
                self.assertNotEqual(original, restored["event"]["ts"])
                self.assertEqual(expected, restored["event"]["ts"])

    def test_the_spec_refusal_list_is_refused(self):
        """The bullets under "Everything else is loss and MUST be refused".

        Sub-millisecond truncation and non-finite floats are named there by
        example; both must raise rather than round-trip to something tidier.
        """
        sub_ms = _v1_0_event()
        sub_ms["event"]["ts"] = "2025-01-17T14:31:05.1234Z"
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
            zmeta_compact.dumps(sub_ms)

        for bad in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=repr(bad)):
                event = _v1_0_event()
                event["payload"]["geo"]["alt_m"] = bad
                with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
                    zmeta_compact.dumps(event)

    def test_no_undeclared_string_normalization_is_tolerated(self):
        """Plausible neighbours of the two declared rows, all of which are loss.

        Not exhaustive — no behavioural corpus can be — but each of these is a
        normalization a well-meaning implementer might add, and each changes
        what a consumer reads. The structural check above is what covers the
        cases this corpus cannot enumerate.
        """
        cases = {
            "trailing whitespace": ("trk-001", "trk-001 "),
            "case folding a non-UUID string": ("trk-001", "TRK-001"),
            "offset form instead of Z": (
                "2025-01-17T14:31:05Z",
                "2025-01-17T14:31:05+00:00",
            ),
            "a different instant": (
                "2025-01-17T14:31:05Z",
                "2025-01-17T14:31:06Z",
            ),
            "sub-millisecond truncation": (
                "2025-01-17T14:31:05.1234Z",
                "2025-01-17T14:31:05.123Z",
            ),
            "a different UUID": (
                "019c2b5d-4cd9-770e-b02d-55d71e516898",
                "019c2b5d-4cd9-770e-b02d-55d71e516899",
            ),
        }
        for label, (original, restored) in cases.items():
            with self.subTest(case=label):
                self.assertIsNotNone(
                    zmeta_compact._semantic_difference(original, restored),
                    f"{label} was treated as representation-only; it is loss and "
                    "is declared nowhere in the mapping spec",
                )
        # ...and the two that ARE declared still pass, so the corpus is not
        # simply asserting that everything is refused.
        self.assertIsNone(
            zmeta_compact._semantic_difference(
                "019C2B5D-4CD9-770E-B02D-55D71E516898",
                "019c2b5d-4cd9-770e-b02d-55d71e516898",
            )
        )
        self.assertIsNone(
            zmeta_compact._semantic_difference(
                "2025-01-17T14:31:05.876Z", "2025-01-17T14:31:05.876000Z"
            )
        )


# --------------------------------------------------------------------------
# The Scope MUSTs: stated in the spec AND kept by the codec
# --------------------------------------------------------------------------


class ScopeSectionMustsTest(unittest.TestCase):
    """Each normative MUST in the Scope section is pinned to its behaviour.

    A doc-only assertion would go stale as prose; a code-only assertion would
    let the normative sentence be deleted while the suite stays green. Both
    halves are asserted together so neither can move alone.
    """

    def setUp(self):
        self.text = MAPPING_SPEC.read_text(encoding="utf-8")
        start = self.text.find("## Scope:")
        self.assertNotEqual(
            -1,
            start,
            "compact-binary-mapping.md no longer has a Scope section; the "
            "fail-closed premise of the whole encoding is stated there",
        )
        self.scope = self.text[start : self.text.find("## Purpose")]

    def _normalize(self, text: str) -> str:
        return " ".join(text.split())

    def test_fail_closed_must_is_stated_and_kept(self):
        self.assertIn(
            "encoders MUST refuse any event that is not `zmeta_version \"1.0\"`",
            self._normalize(self.scope),
            "the Scope section no longer states the fail-closed refusal MUST",
        )
        experimental = _v1_0_event()
        experimental["zmeta_version"] = "1.1.0"
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
            zmeta_compact.verify_representable(experimental)
        self.assertIn("1.0", str(ctx.exception))

    def test_serialization_boundary_must_is_stated_and_kept(self):
        self.assertIn(
            "Verification MUST run through the real serialization boundary "
            "(encode to bytes, decode, compare)",
            self._normalize(self.scope),
            "the Scope section no longer states that verification must run "
            "through the real serialization boundary. That sentence is the "
            "reason an in-memory key-remap comparison is not sufficient: "
            "container equality short-circuits on identity, so a value that is "
            "not equal to itself (NaN) passes and reaches the wire",
        )
        # The behaviour: verification really does serialize. A value that only
        # a real encode/decode can expose must still be refused.
        event = _v1_0_event()
        event["payload"]["geo"]["alt_m"] = float("nan")
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError):
            zmeta_compact.verify_representable(event)

    def test_the_named_reference_symbols_exist(self):
        # The Scope section points implementers at two names. A rename that
        # left the prose behind would send them looking for nothing.
        for symbol in ("zmeta_compact.verify_representable", "CompactUnrepresentableError"):
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, self.scope)
        self.assertTrue(callable(zmeta_compact.verify_representable))
        self.assertTrue(issubclass(zmeta_compact.CompactUnrepresentableError, Exception))

    def test_the_declared_normalizations_do_not_launder_a_lossy_event(self):
        # Proportionality check on this whole file: the normalizations exist so
        # that conforming producers are not refused, NOT so that loss can be
        # waved through. An event carrying both a declared normalization and a
        # genuinely lossy field is still refused.
        event = _v1_0_event()
        event["event"]["event_id"] = event["event"]["event_id"].upper()
        event["payload"]["geo"]["error_ellipse_m"] = {
            "semi_major": 150.0,
            "semi_minor": 75.0,
        }
        with self.assertRaises(zmeta_compact.CompactUnrepresentableError) as ctx:
            zmeta_compact.dumps(event)
        self.assertIn("error_ellipse_m", str(ctx.exception))


class MatcherSelfTest(unittest.TestCase):
    """The doc-side parsers, exercised against doctored text.

    Both are regex/structure readers over prose, so they can silently stop
    matching and take the pins above down with them.
    """

    def test_table_reader_finds_rows_and_stops_at_the_table(self):
        doctored = (
            f"{_TABLE_HEADING}\n\nprose above\n\n"
            "| Normalization | Why it is not loss |\n"
            "| --- | --- |\n"
            "| Widget case | Widgets travel as bytes. Same widget. |\n"
            "| Gadget form | Gadgets are re-formatted. Same gadget. |\n"
            "\nprose below with a | pipe | in it\n"
        )
        rows = declared_normalization_rows(doctored)
        self.assertEqual(["Widget case", "Gadget form"], [row[0] for row in rows])
        self.assertEqual(
            {"_same_widget", "_same_gadget"}, declared_equivalence_names(doctored)
        )

    def test_a_row_without_a_verdict_sentence_is_rejected(self):
        doctored = (
            f"{_TABLE_HEADING}\n\n"
            "| Normalization | Why it is not loss |\n"
            "| --- | --- |\n"
            "| Widget case | Widgets travel as bytes, which is fine. |\n"
        )
        with self.assertRaises(AssertionError):
            declared_equivalence_names(doctored)

    def test_a_missing_section_is_an_error_not_an_empty_table(self):
        with self.assertRaises(AssertionError):
            declared_normalization_rows("# Some other document\n")


if __name__ == "__main__":
    unittest.main()
