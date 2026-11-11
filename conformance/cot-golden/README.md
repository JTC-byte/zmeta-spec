# Golden CoT Outputs

`golden.jsonl` holds what the reference CoT projection
(`adapters/egress/cot/zmeta_to_cot.py`) gives for every STATE_EVENT the
repository ships in `examples/`, under each of its two profiles, `standard`
and `cds`: the CoT XML it writes, or the reason it refuses. It is a
conformance artifact of the `ZMETA-COT-PROJECTION` class
(`conformance/conformance_classes.yaml`).

Each line is one case:

- `name`: the example file's stem, its line number and the profile.
- `description`: one sentence naming the source and the profile.
- `source`: the example file and line the event comes from.
- `event`: that STATE_EVENT, as the example file holds it.
- `cot_config`: the projection config. The `standard` cases use the default
  config. The `cds` cases set `profile` to `cds` and `how` to `m-f`, a
  deployment's claim that the `cds` profile requires.
- `now`: the projection instant, the event's `ts` plus 500 ms. The `cds`
  profile reads it for its stale ceiling and its age rule; the `standard`
  profile does not read it.
- `expect`: either `cot_xml`, the string the reference projection returns, or
  `refusal`, the reason it reports when it returns nothing.

One case is a refusal: the round-trip example asserts an affiliation in its
class (`a-f-G-U-C`), which the `cds` profile refuses as `AFFILIATION_ASSERTED`.

`tools/validate_cot_golden.py` projects every case again with the reference
projection and compares the result byte for byte. A case line that repeats a
member name is refused (contract 3.5), and so is a case that is not well
formed, each with a FAIL line. `gateway/tests/test_cot_golden.py` holds the
corpus to the examples: every example STATE_EVENT has a case under both
profiles, and each case carries its example's event unchanged, number types
included, so a change to an example fails the test until the corpus is
rebuilt. The corpus is not a sub-check of the kernel gate
(`tools/validate_conformance.py --kernel-gate`); the class's required
command runs it, and so does the repository's test battery.

What the strings are. They are the reference implementation's output, and a
byte comparison holds only for it. Another implementation compares its own
output with them by their elements and attributes; this repository ships no
tool for that. Under the `standard` profile the reference writes a number in
Python's float text, which can take an exponent form for a value near zero,
so a different number formatting is not by itself a difference in meaning.
The `cds` profile writes the point attributes in plain decimal notation; a
confidence in its remarks keeps Python's float text. No example's validity
window is long enough to reach the `cds` profile's stale cap (120 s by
default), so the corpus does not pin that ceiling.

What is not here. The TAK Protocol Version 1 bytes are not part of this
artifact: that adapter is not among the required surfaces of the
`ZMETA-COT-PROJECTION` class, and its known-answer bytes stay in its own tests
(`adapters/egress/tak_protocol/`).
