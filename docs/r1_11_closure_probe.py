"""ZMeta R1-11 closure probe -- re-runs the ORIGINAL reproductions of the six
MAJOR audit findings A-01..A-06 against the CURRENT working tree.

Run from the repo root:   python closure_probe.py

This is a CURRENT-STATE probe, not a differential. It does not check out,
build, or compare against the pre-fix code, so it cannot prove that a given
fix commit is what changed the behaviour -- only what the tree in front of it
does today. Every probe prints the observed values BEFORE its verdict so the
verdict can be checked against the evidence rather than believed.

Read-only with respect to the repo: it writes nothing under the repository
tree. It creates temp directories (for the A-05 policy copies and the A-03
broken metrics sink) and removes them.

ASCII output only.
"""

import copy
import importlib.util
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import traceback
from pathlib import Path

VERDICTS = []  # list of (label, verdict_string)


# ---------------------------------------------------------------------------
# tiny helpers
# ---------------------------------------------------------------------------


def out(line=""):
    """Print one ASCII-safe line."""
    text = str(line)
    safe = text.encode("ascii", "backslashreplace").decode("ascii")
    print(safe, flush=True)


def header(title):
    out()
    out("=" * 72)
    out("=== " + title + " ===")
    out("=" * 72)


def verdict(label, state, why=""):
    if state == "CLOSED":
        line = "VERDICT %s: CLOSED" % label
    elif state == "STILL REPRODUCES":
        line = "VERDICT %s: STILL REPRODUCES" % label
    else:
        line = "VERDICT %s: INCONCLUSIVE - %s" % (label, why or "no reason given")
    VERDICTS.append((label, state))
    out(line)


def show_exc(exc, prefix="  "):
    out("%sEXCEPTION CLASS : %s.%s" % (prefix, type(exc).__module__, type(exc).__name__))
    out("%sEXCEPTION REPR  : %s" % (prefix, repr(exc)))


def section(name, title, fn):
    """Run one blocker section; a crash inside becomes evidence, not a stop."""
    header(title)
    try:
        fn()
    except BaseException as exc:  # noqa: BLE001 - the whole point is to report
        out("  SECTION CRASHED before all of its own verdicts were recorded.")
        show_exc(exc)
        out("  TRACEBACK:")
        for line in traceback.format_exc().splitlines():
            out("    " + line)
        # Make sure the section is represented in the tally even if it died
        # before recording anything.
        if not any(lbl.startswith(name + ".") for lbl, _ in VERDICTS):
            verdict(name + ".0", "INCONCLUSIVE", "section crashed: %r" % (exc,))


def run_with_watchdog(fn, timeout_sec, label):
    """Run fn() in a daemon thread. Returns (state, value, exc).

    state is one of "ok", "raised", "TIMEOUT". A hang is reported as a hang
    instead of hanging the caller's terminal.
    """
    box = {}

    def _target():
        try:
            box["value"] = fn()
            box["state"] = "ok"
        except BaseException as exc:  # noqa: BLE001
            box["exc"] = exc
            box["state"] = "raised"

    thread = threading.Thread(target=_target, name="watchdog-" + label, daemon=True)
    thread.start()
    thread.join(timeout_sec)
    if thread.is_alive():
        return ("TIMEOUT", None, None)
    return (box.get("state", "raised"), box.get("value"), box.get("exc"))


def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def nested(depth, leaf=None):
    """Build a `depth`-deep chain of dicts iteratively (no recursion)."""
    node = {"leaf": leaf} if leaf is not None else {"leaf": 1}
    for _ in range(depth):
        node = {"n": node}
    return node


# ---------------------------------------------------------------------------
# repo location + shared imports
# ---------------------------------------------------------------------------

ROOT = Path.cwd().resolve()
if not (ROOT / "schema" / "zmeta-event-1.0.schema.json").exists():
    # Tolerate being run from somewhere else if the repo is discoverable.
    here = Path(__file__).resolve()
    for cand in [ROOT] + list(ROOT.parents) + list(here.parents):
        if (cand / "schema" / "zmeta-event-1.0.schema.json").exists():
            ROOT = cand
            break

out("ZMeta R1-11 closure probe")
out("-------------------------")
out("SCOPE: this verifies the CURRENT state of the tree only. It re-runs each")
out("       finding's ORIGINAL reproduction as the audit recorded it and shows")
out("       what happens NOW. It is NOT a differential against the pre-fix")
out("       code: no old revision is checked out or executed, so a CLOSED")
out("       verdict means 'does not reproduce here today', not 'this specific")
out("       commit is what fixed it'.")
out("REPO ROOT : %s" % ROOT)
out("PYTHON    : %s" % sys.version.replace("\n", " "))
out("RECURSION LIMIT: %d" % sys.getrecursionlimit())
out("CWD       : %s" % Path.cwd())

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_IMPORT_ERRORS = {}


def _try(name, fn):
    try:
        return fn()
    except BaseException as exc:  # noqa: BLE001
        _IMPORT_ERRORS[name] = exc
        return None


validators = _try(
    "validators",
    lambda: load_module_from_path("zmeta_validators_probe", ROOT / "gateway" / "src" / "validators.py"),
)
gateway = _try(
    "gateway",
    lambda: load_module_from_path("zmeta_gateway_probe", ROOT / "gateway" / "src" / "gateway.py"),
)
zmeta_compact = _try("zmeta_compact", lambda: __import__("zmeta_compact"))
zmeta_to_cot_mod = _try(
    "zmeta_to_cot",
    lambda: load_module_from_path(
        "zmeta_to_cot_probe", ROOT / "adapters" / "egress" / "cot" / "zmeta_to_cot.py"
    ),
)

if _IMPORT_ERRORS:
    out()
    out("IMPORT PROBLEMS (each dependent probe reports INCONCLUSIVE below):")
    for name, exc in _IMPORT_ERRORS.items():
        out("  %-16s %r" % (name, exc))


SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
POLICY_DIR = ROOT / "policy"

_VALIDATOR = None
_POLICY = None


def kernel():
    """(validator, policy) loaded once; raises if unavailable."""
    global _VALIDATOR, _POLICY
    if _VALIDATOR is None:
        _VALIDATOR = validators.load_schema(SCHEMA_PATH)
    if _POLICY is None:
        _POLICY = validators.load_policy(POLICY_DIR)
    return _VALIDATOR, _POLICY


def shipped_profile_l_track_state():
    """The shipped Profile-L TRACK_STATE example, or None."""
    path = ROOT / "examples" / "zmeta-profile-L-examples.jsonl"
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        ev = obj.get("event", {})
        if ev.get("event_type") == "STATE_EVENT" and ev.get("event_subtype") == "TRACK_STATE":
            return obj
    return None


def describe_emitted(events):
    """Compact description of what process_message returned."""
    rows = []
    for ev in events or []:
        e = ev.get("event", {}) if isinstance(ev, dict) else {}
        row = "%s/%s" % (e.get("event_type"), e.get("event_subtype"))
        payload = ev.get("payload", {}) if isinstance(ev, dict) else {}
        if isinstance(payload, dict):
            if payload.get("state"):
                row += " state=%s" % payload.get("state")
            metrics = payload.get("metrics")
            if isinstance(metrics, dict) and metrics.get("reason_code"):
                row += " reason_code=%s" % metrics.get("reason_code")
        rows.append(row)
    return rows


# ===========================================================================
# A-01
# ===========================================================================


def probe_a01():
    if validators is None or gateway is None:
        verdict("A-01.1", "INCONCLUSIVE", "gateway/validators failed to import")
        verdict("A-01.2", "INCONCLUSIVE", "gateway/validators failed to import")
        verdict("A-01.3", "INCONCLUSIVE", "gateway/validators failed to import")
        return

    example = shipped_profile_l_track_state()
    if example is None:
        verdict("A-01.1", "INCONCLUSIVE", "no shipped Profile-L TRACK_STATE example found")
    else:
        _a01_1(example)

    _a01_2(example)
    _a01_3(example)


def _a01_1(example):
    out()
    out("-- A-01.1 : NaN / Infinity JSON TOKENS through gateway.process_message --")
    validator, policy = kernel()

    ev = copy.deepcopy(example)
    ev.setdefault("payload", {}).setdefault("geo", {})
    ev["payload"]["geo"]["lat"] = "__ZM_NAN__"
    ev["payload"]["geo"]["alt_m"] = "__ZM_INF__"
    raw_text = json.dumps(ev).replace('"__ZM_NAN__"', "NaN").replace('"__ZM_INF__"', "Infinity")
    raw = raw_text.encode("utf-8")

    out("  INPUT  : shipped Profile-L TRACK_STATE, event_id=%s" % example.get("event", {}).get("event_id"))
    out("  INPUT  : payload.geo.lat replaced with the literal token NaN in the JSON TEXT")
    out("  INPUT  : payload.geo.alt_m replaced with the literal token Infinity in the JSON TEXT")
    idx = raw_text.find('"geo"')
    out("  RAW JSON (geo slice): %s" % raw_text[idx:idx + 90] if idx >= 0 else "  RAW JSON: <no geo key>")

    # Show that stdlib json.loads accepts the tokens -- the premise of the finding.
    try:
        reparsed = json.loads(raw_text)
        out("  json.loads(raw) accepted the tokens: geo=%r" % (reparsed.get("payload", {}).get("geo"),))
    except BaseException as exc:  # noqa: BLE001
        out("  json.loads(raw) REFUSED the tokens:")
        show_exc(exc, "    ")

    try:
        emitted = gateway.process_message(
            raw, validator, policy, "L", {}, "json", strict_validation=True
        )
    except BaseException as exc:  # noqa: BLE001
        out("  process_message RAISED:")
        show_exc(exc, "    ")
        out("  OBSERVED: no event list produced.")
        verdict(
            "A-01.1",
            "INCONCLUSIVE",
            "process_message raised %s instead of returning a refusal" % type(exc).__name__,
        )
        return

    out("  OBSERVED emitted count : %d" % len(emitted))
    for row in describe_emitted(emitted):
        out("  OBSERVED emitted       : %s" % row)

    forwarded_track = [
        e
        for e in emitted
        if e.get("event", {}).get("event_type") == "STATE_EVENT"
    ]
    out("  OBSERVED forwarded STATE_EVENT count : %d" % len(forwarded_track))

    wire_has_nan = None
    wire_repr = ""
    if emitted:
        try:
            wire = gateway._encode_message(emitted[0], "json")
            blob = wire if isinstance(wire, bytes) else str(wire).encode("utf-8")
            wire_has_nan = (b"NaN" in blob) or (b"Infinity" in blob)
            out("  OBSERVED _encode_message(out[0],'json') length : %d bytes" % len(blob))
            out("  OBSERVED wire contains b'NaN' or b'Infinity'   : %s" % wire_has_nan)
            wire_repr = blob[:220].decode("ascii", "backslashreplace")
            out("  OBSERVED wire head : %s" % wire_repr)
        except BaseException as exc:  # noqa: BLE001
            out("  _encode_message RAISED:")
            show_exc(exc, "    ")
            wire_has_nan = None

    refused = (
        len(forwarded_track) == 0
        and len(emitted) >= 1
        and emitted[0].get("event", {}).get("event_type") == "SYSTEM_EVENT"
    )
    if refused and wire_has_nan is False:
        verdict("A-01.1", "CLOSED")
    elif forwarded_track or wire_has_nan:
        verdict("A-01.1", "STILL REPRODUCES")
    else:
        verdict(
            "A-01.1",
            "INCONCLUSIVE",
            "neither a clean refusal nor the original defect: emitted=%r wire_nan=%r"
            % (describe_emitted(emitted), wire_has_nan),
        )


def _a01_2(example):
    out()
    out("-- A-01.2 : zmeta_to_cot with a non-finite geo --")
    if zmeta_to_cot_mod is None:
        verdict("A-01.2", "INCONCLUSIVE", "adapters/egress/cot/zmeta_to_cot.py failed to import")
        return
    if example is None:
        verdict("A-01.2", "INCONCLUSIVE", "no shipped Profile-L TRACK_STATE example to mutate")
        return

    ev = copy.deepcopy(example)
    ev.setdefault("payload", {}).setdefault("geo", {})
    ev["payload"]["geo"]["lat"] = float("nan")
    ev["payload"]["geo"]["alt_m"] = float("inf")
    ev["payload"].setdefault("track_id", "track-l-001")
    out("  INPUT  : same shipped event, payload.geo.lat = nan (python float), alt_m = inf")
    out("  INPUT  : geo now = %r" % (ev["payload"]["geo"],))

    try:
        xml = zmeta_to_cot_mod.zmeta_to_cot(ev)
    except BaseException as exc:  # noqa: BLE001
        out("  zmeta_to_cot RAISED:")
        show_exc(exc, "    ")
        verdict("A-01.2", "INCONCLUSIVE", "zmeta_to_cot raised %s" % type(exc).__name__)
        return

    out("  OBSERVED return type : %s" % type(xml).__name__)
    if xml is None:
        out("  OBSERVED return value: None (adapter refused to convert)")
    else:
        text = str(xml)
        out("  OBSERVED XML length  : %d" % len(text))
        out("  OBSERVED XML         : %s" % text[:400])
        out("  OBSERVED contains 'nan' : %s" % ("nan" in text.lower()))
        out("  OBSERVED contains 'inf' : %s" % ("inf" in text.lower()))

    # Control: the same event with finite geo must still convert, otherwise a
    # None above would prove nothing about non-finite handling.
    control = copy.deepcopy(example)
    control.setdefault("payload", {}).setdefault("track_id", "track-l-001")
    try:
        control_xml = zmeta_to_cot_mod.zmeta_to_cot(control)
    except BaseException as exc:  # noqa: BLE001
        out("  CONTROL (finite geo) RAISED:")
        show_exc(exc, "    ")
        control_xml = None
    out("  CONTROL (finite geo) returns : %s" % ("None" if control_xml is None else "XML, %d chars" % len(str(control_xml))))

    if xml is None and control_xml is not None:
        verdict("A-01.2", "CLOSED")
    elif xml is not None and ("nan" in str(xml).lower() or "inf" in str(xml).lower()):
        verdict("A-01.2", "STILL REPRODUCES")
    elif xml is None and control_xml is None:
        verdict(
            "A-01.2",
            "INCONCLUSIVE",
            "adapter also refuses the untouched control event, so the refusal is not attributable to the non-finite value",
        )
    else:
        verdict("A-01.2", "INCONCLUSIVE", "XML produced but no nan/inf token found in it")


def _a01_3(example):
    out()
    out("-- A-01.3 : upstream clamp, NaN confidence with timing_freshness mode=degrade --")
    if example is None:
        verdict("A-01.3", "INCONCLUSIVE", "no shipped Profile-L TRACK_STATE example to mutate")
        return
    validator, policy = kernel()
    if "timing_freshness" not in policy:
        verdict("A-01.3", "INCONCLUSIVE", "policy has no timing_freshness block")
        return

    degrade_policy = copy.deepcopy(policy)
    degrade_policy["timing_freshness"] = copy.deepcopy(degrade_policy["timing_freshness"])
    degrade_policy["timing_freshness"]["mode"] = "degrade"

    ev = copy.deepcopy(example)
    ev["confidence"] = float("nan")
    out("  INPUT  : shipped Profile-L TRACK_STATE with confidence = nan")
    out("  INPUT  : policy['timing_freshness']['mode'] forced to 'degrade'")
    out("  BEFORE (recorded by the audit): min(1.0, nan) -> 1.0, event forwarded as")
    out("          TRACK_STATE at MAXIMUM confidence.")

    # (a) the clamp helper in isolation
    try:
        probe = copy.deepcopy(ev)
        violations = [{"code": "TIMING_STATUS_MISSING", "details": {"action": "degrade"}}]
        validators.apply_timing_freshness_degradation(
            probe, violations, degrade_policy["timing_freshness"]
        )
        out("  OBSERVED apply_timing_freshness_degradation -> confidence = %r" % (probe.get("confidence"),))
        clamped_to_one = probe.get("confidence") == 1.0
    except BaseException as exc:  # noqa: BLE001
        out("  apply_timing_freshness_degradation RAISED:")
        show_exc(exc, "    ")
        clamped_to_one = None

    # (b) end to end
    try:
        timing_state = gateway.ValidationState() if hasattr(gateway, "ValidationState") else None
        emitted = gateway.process_message(
            json.dumps(ev, allow_nan=True).encode("utf-8"),
            validator,
            degrade_policy,
            "L",
            {},
            "json",
            timing_state=timing_state,
            strict_validation=False,
        )
    except BaseException as exc:  # noqa: BLE001
        out("  process_message RAISED:")
        show_exc(exc, "    ")
        verdict("A-01.3", "INCONCLUSIVE", "process_message raised %s" % type(exc).__name__)
        return

    out("  OBSERVED emitted count : %d" % len(emitted))
    for ev_out in emitted:
        e = ev_out.get("event", {})
        out(
            "  OBSERVED emitted       : %s/%s confidence=%r"
            % (e.get("event_type"), e.get("event_subtype"), ev_out.get("confidence"))
        )

    forwarded_state = [e for e in emitted if e.get("event", {}).get("event_type") == "STATE_EVENT"]
    laundered = [
        e
        for e in forwarded_state
        if isinstance(e.get("confidence"), float) and e.get("confidence") == 1.0
    ]
    out("  OBSERVED forwarded STATE_EVENT count : %d" % len(forwarded_state))
    out("  OBSERVED forwarded with confidence==1.0 : %d" % len(laundered))
    out("  OBSERVED clamp helper rewrote nan to 1.0 : %r" % clamped_to_one)

    if laundered or clamped_to_one is True:
        verdict("A-01.3", "STILL REPRODUCES")
    elif not forwarded_state and emitted:
        verdict("A-01.3", "CLOSED")
    elif not emitted:
        verdict("A-01.3", "INCONCLUSIVE", "nothing emitted at all -- silent drop, neither refusal nor laundering")
    else:
        verdict(
            "A-01.3",
            "INCONCLUSIVE",
            "STATE_EVENT forwarded but not at confidence 1.0: %r"
            % ([e.get("confidence") for e in forwarded_state],),
        )


# ===========================================================================
# A-02
# ===========================================================================


def probe_a02():
    labels = ["A-02.1", "A-02.2", "A-02.3"]
    try:
        from adapters.ingress.sapient import test_sapient_ingress as helpers  # noqa: WPS433
        from adapters.ingress.sapient.sapient_to_zmeta import (  # noqa: WPS433
            SCHEMA_ID,
            translate,
            validate,
        )
    except BaseException as exc:  # noqa: BLE001
        out("  Could not import the SAPIENT module or its own test helpers:")
        show_exc(exc, "    ")
        for lbl in labels:
            verdict(lbl, "INCONCLUSIVE", "SAPIENT test helpers unavailable: %r" % (exc,))
        return

    for required in ("_detection_msg", "_store", "_rf_registration_msg"):
        if not hasattr(helpers, required):
            for lbl in labels:
                verdict(lbl, "INCONCLUSIVE", "test helper %s missing" % required)
            return

    _a02_1(helpers, SCHEMA_ID, translate, validate)
    _a02_2(helpers, SCHEMA_ID, translate, validate)
    _a02_3(helpers, SCHEMA_ID, translate, validate)


def _describe_sapient(events):
    rows = []
    for ev in events:
        e = ev.get("event", {})
        rows.append("%s/%s" % (e.get("event_type"), e.get("event_subtype")))
    return rows


def _rfc8259_check(obj, label):
    try:
        json.dumps(obj, allow_nan=False)
        out("  OBSERVED json.dumps(%s, allow_nan=False) : OK (RFC 8259 clean)" % label)
        return True
    except BaseException as exc:  # noqa: BLE001
        out("  OBSERVED json.dumps(%s, allow_nan=False) RAISED:" % label)
        show_exc(exc, "    ")
        return False


def _a02_1(helpers, SCHEMA_ID, translate, validate):
    out()
    out("-- A-02.1 : SAPIENT classification sub_class carrying a NaN confidence --")
    out("  BEFORE (recorded): NaN landed verbatim in canonical payload.claim.sub_class")
    out("                     and validate() returned pass.")
    def classification(conf):
        return [
            {
                "type": "UAV",
                "confidence": 0.9,
                "sub_class": [{"type": "quadcopter", "level": 1, "confidence": conf}],
            }
        ]

    out("  INPUT  : detection_report.classification[0].sub_class[0].confidence = nan")
    probe = _a02_run(
        helpers, SCHEMA_ID, translate, validate,
        helpers._detection_msg(classification=classification(float("nan"))),
        helpers._store(helpers._rf_registration_msg()),
        "probe/rf",
    )
    out("  CONTROL: the identical call with a FINITE sub_class confidence (0.7).")
    control = _a02_run(
        helpers, SCHEMA_ID, translate, validate,
        helpers._detection_msg(classification=classification(0.7)),
        helpers._store(helpers._rf_registration_msg()),
        "control/rf",
    )
    out("  OBSERVED probe emitted %d event(s); control emitted %d event(s)."
        % (len(probe["events"]), len(control["events"])))
    out("  OBSERVED any payload.claim carrying a sub_class in the probe run:")
    found = False
    for i, ev in enumerate(probe["events"]):
        claim = ev.get("payload", {}).get("claim")
        if isinstance(claim, dict) and "sub_class" in claim:
            found = True
            out("    event[%d] claim.sub_class = %r" % (i, claim.get("sub_class")))
    if not found:
        out("    <none: no probe event carries claim.sub_class>")

    _a02_verdict("A-02.1", probe, control)


def _a02_run(helpers, SCHEMA_ID, translate, validate, msg, registration, tag):
    """Translate one message, print everything observed, return a fact dict."""
    facts = {
        "events": [],
        "raised": None,
        "non_finite_canonical": False,
        "rfc8259_clean": True,
        "center_freq_hz": "<absent>",
        "bearing": [],
        "frames": [],
    }
    try:
        events = translate(msg, SCHEMA_ID, registration=registration)
    except BaseException as exc:  # noqa: BLE001
        out("  [%s] translate RAISED:" % tag)
        show_exc(exc, "    ")
        facts["raised"] = exc
        return facts

    facts["events"] = events
    out("  [%s] OBSERVED events emitted : %d %s" % (tag, len(events), _describe_sapient(events)))
    for i, ev in enumerate(events):
        payload = ev.get("payload", {}) if isinstance(ev, dict) else {}
        feats = payload.get("features")
        claim = payload.get("claim")
        bearing = payload.get("bearing")
        quality = payload.get("quality", {})
        frame = quality.get("bearing_frame") if isinstance(quality, dict) else None
        out("  [%s] OBSERVED event[%d] payload.features = %r" % (tag, i, feats))
        out("  [%s] OBSERVED event[%d] payload.claim    = %r" % (tag, i, claim))
        out("  [%s] OBSERVED event[%d] payload.bearing  = %r ; quality.bearing_frame = %r"
            % (tag, i, bearing, frame))
        if isinstance(feats, dict) and "center_freq_hz" in feats:
            facts["center_freq_hz"] = feats["center_freq_hz"]
        if bearing is not None:
            facts["bearing"].append(bearing)
        facts["frames"].append(frame)
        for name, node in (("features", feats), ("claim", claim), ("bearing", bearing),
                           ("quality", quality)):
            if node is not None and _contains_non_finite(node):
                facts["non_finite_canonical"] = True
                out("  [%s] OBSERVED NON-FINITE inside canonical payload.%s of event[%d]"
                    % (tag, name, i))
        try:
            status, violations = validate(ev)
            out("  [%s] OBSERVED validate() -> %r violations=%r" % (tag, status, violations))
        except BaseException as exc:  # noqa: BLE001
            out("  [%s] validate RAISED:" % tag)
            show_exc(exc, "    ")
        if not _rfc8259_check(ev, "%s event[%d]" % (tag, i)):
            facts["rfc8259_clean"] = False
    out("  [%s] OBSERVED features.center_freq_hz : %r" % (tag, facts["center_freq_hz"]))
    out("  [%s] OBSERVED non-finite in any canonical field : %s" % (tag, facts["non_finite_canonical"]))
    return facts


def _a02_verdict(label, probe_facts, control_facts, extra_facts=None):
    """Shared verdict logic for the two overflow cases.

    A run that emits nothing is only readable as a REFUSAL if the identical
    call with finite operands emits something. Otherwise the silence could be
    unrelated breakage, and that is reported as INCONCLUSIVE, not as closure.
    """
    all_facts = [probe_facts] + ([extra_facts] if extra_facts else [])
    reproduced = any(f["non_finite_canonical"] for f in all_facts)
    dirty_wire = any(not f["rfc8259_clean"] for f in all_facts)
    control_emitted = len(control_facts["events"]) > 0 and control_facts["raised"] is None
    probe_emitted = any(len(f["events"]) > 0 for f in all_facts)
    raised = [f["raised"] for f in all_facts if f["raised"] is not None]

    out("  DECISION INPUTS: non_finite_in_canonical=%r rfc8259_dirty=%r probe_emitted=%r control_emitted=%r translate_raised=%r"
        % (reproduced, dirty_wire, probe_emitted, control_emitted, [repr(e) for e in raised]))

    if reproduced or dirty_wire:
        verdict(label, "STILL REPRODUCES")
    elif raised:
        verdict(label, "INCONCLUSIVE", "translate raised %r on the probe input" % (raised[0],))
    elif not control_emitted:
        verdict(
            label,
            "INCONCLUSIVE",
            "the FINITE control emitted nothing either, so a refusal here is not attributable to the non-finite input",
        )
    else:
        verdict(label, "CLOSED")


def _a02_2(helpers, SCHEMA_ID, translate, validate):
    out()
    out("-- A-02.2 : SAPIENT signal frequencies at 1e308 (arithmetic overflow to inf) --")
    out("  BEFORE (recorded): payload.features.center_freq_hz == inf and validate() == pass")
    signal_bad = [
        {
            "amplitude": -57.0,
            "centre_frequency": 1e308,
            "start_frequency": -1e308,
            "stop_frequency": 1e308,
        }
    ]
    signal_ok = [
        {
            "amplitude": -57.0,
            "centre_frequency": 433.0,
            "start_frequency": 432.9,
            "stop_frequency": 433.1,
        }
    ]
    out("  INPUT  : signal[0] centre_frequency=1e308 start=-1e308 stop=1e308")
    out("  INPUT  : registration = _store(_rf_registration_msg())  [verbatim from the audit]")

    probe = _a02_run(
        helpers, SCHEMA_ID, translate, validate,
        helpers._detection_msg(signal=signal_bad),
        helpers._store(helpers._rf_registration_msg()),
        "probe/rf",
    )
    out("  CONTROL: the identical call with FINITE frequencies, same registration.")
    control = _a02_run(
        helpers, SCHEMA_ID, translate, validate,
        helpers._detection_msg(signal=signal_ok),
        helpers._store(helpers._rf_registration_msg()),
        "control/rf",
    )

    # Secondary: the repo's own tests note that with a PASSIVE_RF registration a
    # refused centre frequency also removes the node's only modality, so the
    # whole observation vanishes for an unrelated reason. A camera-signal
    # registration keeps the event alive so its features can actually be read.
    extra = None
    if hasattr(helpers, "_camera_signal_registration_msg"):
        out("  SECONDARY: same overflowing signal under _camera_signal_registration_msg(),")
        out("             which keeps the observation alive so features are observable.")
        extra = _a02_run(
            helpers, SCHEMA_ID, translate, validate,
            helpers._detection_msg(signal=signal_bad),
            helpers._store(helpers._camera_signal_registration_msg()),
            "probe/camera-signal",
        )
    else:
        out("  SECONDARY: helper _camera_signal_registration_msg not present; skipped.")

    _a02_verdict("A-02.2", probe, control, extra)


def _a02_3(helpers, SCHEMA_ID, translate, validate):
    out()
    out("-- A-02.3 : SAPIENT azimuth of 1e308 radians (TRUE datum) --")
    out("  BEFORE (recorded): payload.bearing.az_deg == nan while")
    out("                     quality.bearing_frame was still stamped TRUE_NORTH")

    def rb(azimuth):
        return {
            "azimuth": azimuth,
            "elevation": 0.0,
            "coordinate_system": "RANGE_BEARING_COORDINATE_SYSTEM_RADIANS_M",
            "datum": "RANGE_BEARING_DATUM_TRUE",
        }

    out("  INPUT  : detection_report.range_bearing.azimuth = 1e308 (RADIANS_M / DATUM_TRUE)")
    probe = _a02_run(
        helpers, SCHEMA_ID, translate, validate,
        helpers._detection_msg(signal=None, range_bearing=rb(1e308)),
        helpers._store(helpers._rf_registration_msg()),
        "probe/rf",
    )
    out("  CONTROL: the identical call with a FINITE azimuth (1.5708 rad), same registration.")
    control = _a02_run(
        helpers, SCHEMA_ID, translate, validate,
        helpers._detection_msg(signal=None, range_bearing=rb(math.radians(90.0))),
        helpers._store(helpers._rf_registration_msg()),
        "control/rf",
    )

    extra = None
    extra_control = None
    if hasattr(helpers, "_camera_registration_msg"):
        out("  SECONDARY: same overflowing azimuth under _camera_registration_msg(), the")
        out("             registration the repo's own overflow cases use, so the event")
        out("             survives and payload.bearing / quality.bearing_frame are readable.")
        extra = _a02_run(
            helpers, SCHEMA_ID, translate, validate,
            helpers._detection_msg(signal=None, range_bearing=rb(1e308)),
            helpers._store(helpers._camera_registration_msg()),
            "probe/camera",
        )
        extra_control = _a02_run(
            helpers, SCHEMA_ID, translate, validate,
            helpers._detection_msg(signal=None, range_bearing=rb(math.radians(90.0))),
            helpers._store(helpers._camera_registration_msg()),
            "control/camera",
        )
        stamped = [f for f in extra["frames"] if f == "TRUE_NORTH"]
        bearings = extra["bearing"]
        out("  OBSERVED (camera probe) payload.bearing values     : %r" % (bearings,))
        out("  OBSERVED (camera probe) bearing_frame == TRUE_NORTH : %d event(s)" % len(stamped))
        out("  OBSERVED (camera probe) a TRUE_NORTH stamp beside NO bearing at all : %s"
            % (bool(stamped) and not bearings))
    else:
        out("  SECONDARY: helper _camera_registration_msg not present; skipped.")

    # If the camera control emits and the camera probe does not (or emits a
    # clean event), that is the discriminating evidence; fold it in.
    if extra is not None and extra_control is not None and len(extra_control["events"]) > 0:
        control = extra_control
    _a02_verdict("A-02.3", probe, control, extra)


def _contains_non_finite(value, depth=0):
    """Iterative-ish non-finite search (bounded depth) for evidence printing."""
    if depth > 60:
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, dict):
        return any(_contains_non_finite(v, depth + 1) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_non_finite(v, depth + 1) for v in value)
    return False


# ===========================================================================
# A-03
# ===========================================================================


def probe_a03():
    if gateway is None:
        verdict("A-03.1", "INCONCLUSIVE", "gateway failed to import")
        verdict("A-03.2", "INCONCLUSIVE", "gateway failed to import")
        return

    out("  METHOD: driven IN PROCESS, not by spawning a real UDP gateway. The")
    out("          metrics sink is pointed at a path whose PARENT is a regular")
    out("          file so Path.mkdir raises, then the same calls the receive")
    out("          loop makes are invoked directly: metrics.record_violation /")
    out("          record_drop / maybe_log, and gateway._record_backstop_drop,")
    out("          which is the handler the audit found re-entering the sink.")

    tmpdir = tempfile.mkdtemp(prefix="zmeta_probe_a03_")
    try:
        blocker = Path(tmpdir) / "blocker"
        blocker.write_text("i am a regular file, not a directory\n", encoding="utf-8")
        log_path = blocker / "sub" / "metrics.jsonl"
        out()
        out("  INPUT  : metrics log path = %s" % log_path)
        out("  INPUT  : its parent chain contains the REGULAR FILE %s" % blocker)

        # Confirm the premise: mkdir on that parent really does raise.
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            out("  PREMISE CHECK: Path.mkdir did NOT raise -- the sink is not actually broken.")
            premise_ok = False
        except BaseException as exc:  # noqa: BLE001
            out("  PREMISE CHECK: Path.mkdir raises as required:")
            show_exc(exc, "    ")
            premise_ok = True

        if not premise_ok:
            verdict("A-03.1", "INCONCLUSIVE", "could not construct a failing metrics sink on this filesystem")
            verdict("A-03.2", "INCONCLUSIVE", "could not construct a failing metrics sink on this filesystem")
            return

        _a03_1(log_path)
        _a03_2(log_path)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        out("  CLEANUP: removed %s" % tmpdir)


def _a03_1(log_path):
    out()
    out("-- A-03.1 : the metrics sink itself under a broken parent --")
    if not hasattr(gateway, "MetricsLogger"):
        verdict("A-03.1", "INCONCLUSIVE", "gateway.MetricsLogger not found")
        return
    err_capture = io.StringIO()
    real_stderr = sys.stderr
    try:
        logger = gateway.MetricsLogger(log_path)
        sys.stderr = err_capture
        try:
            logger.write({"type": "probe", "n": 1})
            logger.write({"type": "probe", "n": 2})
            raised = None
        except BaseException as exc:  # noqa: BLE001
            raised = exc
        finally:
            sys.stderr = real_stderr
    except BaseException as exc:  # noqa: BLE001
        sys.stderr = real_stderr
        out("  MetricsLogger construction RAISED:")
        show_exc(exc, "    ")
        verdict("A-03.1", "INCONCLUSIVE", "MetricsLogger could not be constructed")
        return

    if raised is not None:
        out("  OBSERVED MetricsLogger.write RAISED:")
        show_exc(raised, "    ")
    else:
        out("  OBSERVED MetricsLogger.write returned normally on both calls (no raise)")
    out("  OBSERVED logger.write_failures : %r" % getattr(logger, "write_failures", "<absent>"))
    captured = err_capture.getvalue().strip()
    out("  OBSERVED stderr from the sink  : %s" % (captured.replace("\n", " | ")[:400] or "<none>"))

    if raised is None:
        verdict("A-03.1", "CLOSED")
    else:
        verdict("A-03.1", "STILL REPRODUCES")


def _a03_2(log_path):
    out()
    out("-- A-03.2 : the receive-loop backstop handler re-entering the failing sink --")
    out("  BEFORE (recorded): the backstop handler called back into the failing")
    out("                     sink and the IDENTICAL exception escaped uncaught,")
    out("                     terminating the process.")
    if not hasattr(gateway, "_record_backstop_drop"):
        verdict("A-03.2", "INCONCLUSIVE", "gateway._record_backstop_drop not found")
        return

    out("  NOTE: GatewayMetrics prints its periodic summary to STDOUT, so a few")
    out("        'metrics ...' lines below come from the gateway itself, not the probe.")
    err_capture = io.StringIO()
    real_stderr = sys.stderr
    escaped = None
    snapshot = {}
    try:
        logger = gateway.MetricsLogger(log_path)
        metrics = gateway.GatewayMetrics(emit=True, logger=logger)
        metrics.interval_sec = 0  # force maybe_log to actually do work
        sys.stderr = err_capture
        try:
            # 1. the violation path the audit walked (process_message ->
            #    metrics.record_violation -> MetricsLogger.write -> mkdir).
            metrics.record_violation("SCHEMA_INVALID")
            # 2. the backstop's own handler, with the sink already failing.
            #    record_drop bumps the counters, then maybe_log rolls the
            #    window - so the counters are snapshotted between the two.
            metrics.record_drop("INTERNAL_ERROR")
            window = getattr(metrics, "window", {}) or {}
            snapshot = {
                "drops": window.get("drops"),
                "drop_reasons": dict(window.get("drop_reasons") or {}),
                "violations": window.get("violations"),
                "violation_codes": dict(window.get("violation_codes") or {}),
            }
            gateway._record_backstop_drop(metrics, ValueError("synthetic datagram failure"))
        except BaseException as exc:  # noqa: BLE001
            escaped = exc
        finally:
            sys.stderr = real_stderr
    except BaseException as exc:  # noqa: BLE001
        sys.stderr = real_stderr
        out("  Setting up GatewayMetrics RAISED:")
        show_exc(exc, "    ")
        verdict("A-03.2", "INCONCLUSIVE", "could not construct GatewayMetrics with a failing sink")
        return

    if escaped is not None:
        out("  OBSERVED an exception ESCAPED the backstop handler:")
        show_exc(escaped, "    ")
    else:
        out("  OBSERVED no exception escaped record_violation, record_drop or _record_backstop_drop")

    out("  OBSERVED in-memory counters, snapshotted before maybe_log rolled the window:")
    out("    drops           = %r" % snapshot.get("drops"))
    out("    drop_reasons    = %r" % snapshot.get("drop_reasons"))
    out("    violations      = %r" % snapshot.get("violations"))
    out("    violation_codes = %r" % snapshot.get("violation_codes"))

    captured = err_capture.getvalue().strip()
    if captured:
        out("  OBSERVED stderr:")
        for line in captured.splitlines():
            out("    " + line[:300])
    else:
        out("  OBSERVED stderr: <none>")

    if escaped is None:
        verdict("A-03.2", "CLOSED")
    else:
        verdict("A-03.2", "STILL REPRODUCES")


# ===========================================================================
# A-04
# ===========================================================================


def _compact_event(payload_extension):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5c-c047-73ea-8f1a-302b9d9c0aa4",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T14:40:00Z",
        },
        "source": {
            "platform_id": "lora-node-01",
            "node_role": "GATEWAY",
            "producer": "sensorops",
        },
        "profile": "L",
        "payload": {
            "track_id": "track-l-001",
            "geo": {"lat": 34.0001, "lon": -118.0001, "alt_m": 100.0},
            "valid_for_ms": 1000,
            "extensions": {"vendor": payload_extension},
        },
        "confidence": 0.62,
        "lineage": {"based_on": ["019c2b5c-c047-73ea-8f1a-302e4b7b0aa4"]},
    }


def probe_a04():
    labels = ["A-04.1", "A-04.2", "A-04.3", "A-04.4"]
    if zmeta_compact is None:
        for lbl in labels:
            verdict(lbl, "INCONCLUSIVE", "zmeta_compact failed to import")
        return

    unrep = getattr(zmeta_compact, "CompactUnrepresentableError", None)
    out("  zmeta_compact.CompactUnrepresentableError present : %s" % (unrep is not None))
    out("  BEFORE (recorded): a raw RecursionError escaped the public API at ~1500 deep.")
    out("  NOTE: recursion thresholds are interpreter-specific; this run's limit is %d."
        % sys.getrecursionlimit())

    for label, depth in (("A-04.1", 1500), ("A-04.2", 300), ("A-04.3", 100000)):
        _a04_depth(label, depth, unrep)

    _a04_cycle(unrep)


def _a04_depth(label, depth, unrep):
    out()
    out("-- %s : zmeta_compact.dumps with payload.extensions.vendor nested %d deep --" % (label, depth))

    def _work():
        event = _compact_event(nested(depth))
        return zmeta_compact.dumps(event)

    state, value, exc = run_with_watchdog(_work, 120.0, label)

    if state == "TIMEOUT":
        out("  OBSERVED: TIMEOUT - dumps() did not return within 120s at depth %d" % depth)
        verdict(label, "INCONCLUSIVE", "TIMEOUT after 120s (hang, not a refusal and not a crash)")
        return

    if state == "ok":
        blob = value
        out("  OBSERVED: dumps() RETURNED normally, %d bytes" % (len(blob) if blob is not None else -1))
        out("  OBSERVED: no refusal raised at depth %d" % depth)
        verdict(
            label,
            "INCONCLUSIVE",
            "dumps() encoded a %d-deep nest instead of raising anything; not the recorded defect (RecursionError) and not a refusal"
            % depth,
        )
        return

    show_exc(exc, "  OBSERVED ")
    is_recursion = isinstance(exc, RecursionError)
    is_refusal = unrep is not None and isinstance(exc, unrep)
    out("  OBSERVED isinstance(exc, RecursionError)              : %s" % is_recursion)
    out("  OBSERVED isinstance(exc, CompactUnrepresentableError) : %s" % is_refusal)

    if is_recursion and not is_refusal:
        verdict(label, "STILL REPRODUCES")
    elif is_refusal:
        verdict(label, "CLOSED")
    else:
        verdict(
            label,
            "INCONCLUSIVE",
            "raised %s, which is neither RecursionError nor CompactUnrepresentableError"
            % type(exc).__name__,
        )


def _a04_cycle(unrep):
    out()
    out("-- A-04.4 : cyclic structure (d = {}; d['self'] = d) through zmeta_compact.dumps --")
    out("  WATCHDOG: 60s. A hang is reported as TIMEOUT rather than hanging the terminal.")

    def _work():
        d = {}
        d["self"] = d
        event = _compact_event(d)
        return zmeta_compact.dumps(event)

    state, value, exc = run_with_watchdog(_work, 60.0, "A-04.4")

    if state == "TIMEOUT":
        out("  OBSERVED: TIMEOUT - dumps() did not return within 60s on a self-referential dict.")
        out("  OBSERVED: the probe thread is a daemon and is abandoned; this process still exits.")
        verdict("A-04.4", "STILL REPRODUCES")
        return

    if state == "ok":
        out("  OBSERVED: dumps() RETURNED normally on a cyclic structure, %d bytes"
            % (len(value) if value is not None else -1))
        verdict(
            "A-04.4",
            "INCONCLUSIVE",
            "a cycle has no finite CBOR encoding, so a successful encode is neither the hang nor a refusal",
        )
        return

    show_exc(exc, "  OBSERVED ")
    is_recursion = isinstance(exc, RecursionError)
    is_refusal = unrep is not None and isinstance(exc, unrep)
    out("  OBSERVED isinstance(exc, RecursionError)              : %s" % is_recursion)
    out("  OBSERVED isinstance(exc, CompactUnrepresentableError) : %s" % is_refusal)
    if is_refusal:
        verdict("A-04.4", "CLOSED")
    elif is_recursion:
        verdict("A-04.4", "STILL REPRODUCES")
    else:
        verdict(
            "A-04.4",
            "INCONCLUSIVE",
            "raised %s, neither a refusal nor the recorded RecursionError" % type(exc).__name__,
        )


# ===========================================================================
# A-05
# ===========================================================================

_A05_STATE_EVENT = {
    "zmeta_version": "1.0",
    "event": {
        "event_id": "019c2b5c-c047-73ea-8f1a-302b9d9c0a05",
        "event_type": "STATE_EVENT",
        "event_subtype": "TRACK_STATE",
        "ts": "2025-01-17T14:40:00Z",
    },
    "source": {
        "platform_id": "unregistered-platform",
        "node_role": "GATEWAY",
        "producer": "totally-unregistered-node",
    },
    "profile": "L",
    "payload": {
        "track_id": "track-l-005",
        "geo": {"lat": 34.0001, "lon": -118.0001, "alt_m": 100.0},
        "valid_for_ms": 1000,
    },
    "confidence": 0.62,
    "lineage": {"based_on": ["019c2b5c-c047-73ea-8f1a-302e4b7b0aa4"]},
}


def probe_a05():
    labels = ["A-05.1", "A-05.2"]
    if validators is None:
        for lbl in labels:
            verdict(lbl, "INCONCLUSIVE", "validators failed to import")
        return
    lint_cli = ROOT / "tools" / "lint_policy_risk_modes.py"
    if not lint_cli.exists():
        for lbl in labels:
            verdict(lbl, "INCONCLUSIVE", "tools/lint_policy_risk_modes.py not found")
        return
    auth_file = POLICY_DIR / "producer-authority.yaml"
    if not auth_file.exists():
        for lbl in labels:
            verdict(lbl, "INCONCLUSIVE", "policy/producer-authority.yaml not found")
        return

    out("  The repo's own policy/ is NEVER touched: each case works on a copy in")
    out("  a temp directory, which is deleted afterwards.")

    # Sanity: schema-validity + the shipped-policy control.
    try:
        validator, policy = kernel()
        ok, viol = validators.validate_schema(
            _A05_STATE_EVENT, validator, policy.get("violation_severities")
        )
        out()
        out("  CONTROL: probe event is schema-valid : %s (%r)" % (ok, viol))
        ok2, viol2 = validators.validate_producer_authority(
            _A05_STATE_EVENT, policy["producer_authority"], policy["violation_severities"]
        )
        codes = [v.get("code") for v in (viol2 or [])]
        out("  CONTROL: shipped policy -> validate_producer_authority = (%r, codes=%r)" % (ok2, codes))
    except BaseException as exc:  # noqa: BLE001
        out("  CONTROL setup RAISED:")
        show_exc(exc, "    ")

    _a05_case(
        "A-05.1",
        "bare key with no list items",
        lint_cli,
        auth_file,
        mutate_bare_key,
    )
    _a05_case(
        "A-05.2",
        "scalar string STATE_EVENT",
        lint_cli,
        auth_file,
        mutate_scalar,
    )


def mutate_bare_key(text):
    """Strip the six list items, leaving `require_match_for_event_types:` bare."""
    lines = text.splitlines()
    result = []
    idx = 0
    found = False
    while idx < len(lines):
        line = lines[idx]
        result.append(line)
        if line.strip().startswith("require_match_for_event_types:"):
            found = True
            idx += 1
            # Drop the following "  - X" items belonging to this key.
            while idx < len(lines) and lines[idx].strip().startswith("- "):
                idx += 1
            continue
        idx += 1
    return ("\n".join(result) + "\n") if found else None


def mutate_scalar(text):
    """Replace the key's list with the scalar string STATE_EVENT."""
    lines = text.splitlines()
    result = []
    idx = 0
    found = False
    while idx < len(lines):
        line = lines[idx]
        if line.strip().startswith("require_match_for_event_types:"):
            found = True
            indent = line[: len(line) - len(line.lstrip())]
            result.append("%srequire_match_for_event_types: STATE_EVENT" % indent)
            idx += 1
            while idx < len(lines) and lines[idx].strip().startswith("- "):
                idx += 1
            continue
        result.append(line)
        idx += 1
    return ("\n".join(result) + "\n") if found else None


def _a05_case(label, description, lint_cli, auth_file, mutator):
    out()
    out("-- %s : require_match_for_event_types as a %s --" % (label, description))
    original = auth_file.read_text(encoding="utf-8")
    mutated = mutator(original)
    if mutated is None:
        verdict(label, "INCONCLUSIVE", "require_match_for_event_types key not found in policy/producer-authority.yaml")
        return

    tmpdir = tempfile.mkdtemp(prefix="zmeta_probe_a05_")
    try:
        copy_dir = Path(tmpdir) / "policy"
        shutil.copytree(POLICY_DIR, copy_dir)
        target = copy_dir / auth_file.name
        target.write_text(mutated, encoding="utf-8")

        # Show the exact mangled region.
        out("  INPUT  : copy of policy/ at %s" % copy_dir)
        out("  INPUT  : mangled region of producer-authority.yaml:")
        for line in mutated.splitlines()[:12]:
            out("      | " + line)

        # 1. the shipped lint CLI
        try:
            proc = subprocess.run(
                [sys.executable, str(lint_cli), "--policy-dir", str(copy_dir)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=180,
            )
            out("  OBSERVED lint exit code : %d" % proc.returncode)
            stdout = (proc.stdout or "").strip()
            stderr = (proc.stderr or "").strip()
            out("  OBSERVED lint stdout    :")
            for line in (stdout.splitlines() or ["<empty>"]):
                out("      " + line[:300])
            if stderr:
                out("  OBSERVED lint stderr    :")
                for line in stderr.splitlines()[:20]:
                    out("      " + line[:300])
            lint_rc = proc.returncode
        except BaseException as exc:  # noqa: BLE001
            out("  Running the lint CLI RAISED:")
            show_exc(exc, "    ")
            lint_rc = None

        # 2. validate_producer_authority against the mangled policy
        auth_result = None
        auth_exc = None
        try:
            mangled_policy = validators.load_policy(copy_dir)
            raw_key = mangled_policy.get("producer_authority", {})
            if isinstance(raw_key, dict):
                out("  OBSERVED loaded require_match_for_event_types = %r"
                    % (raw_key.get("require_match_for_event_types"),))
            else:
                out("  OBSERVED loaded producer_authority block = %r" % (raw_key,))
            severity = mangled_policy.get("violation_severities")
            auth_result = validators.validate_producer_authority(
                copy.deepcopy(_A05_STATE_EVENT), raw_key, severity
            )
            codes = [v.get("code") for v in (auth_result[1] or [])]
            out("  OBSERVED validate_producer_authority -> (ok=%r, codes=%r)" % (auth_result[0], codes))
            out("  OBSERVED full violations : %r" % (auth_result[1],))
        except BaseException as exc:  # noqa: BLE001
            auth_exc = exc
            out("  OBSERVED validate_producer_authority RAISED:")
            show_exc(exc, "    ")

        # Verdict. The recorded defect is TWO-part: lint exit 0 "ok" AND then
        # either a TypeError on every event (case a) or acceptance of the
        # unregistered producer (case b).
        lint_green = lint_rc == 0
        accepted = bool(auth_result and auth_result[0] is True)
        type_error = isinstance(auth_exc, TypeError)
        out("  OBSERVED summary : lint_exit=%r lint_green=%r accepted_unregistered=%r TypeError=%r"
            % (lint_rc, lint_green, accepted, type_error))

        if lint_rc is None:
            verdict(label, "INCONCLUSIVE", "the lint CLI could not be run")
        elif lint_green and (accepted or type_error):
            verdict(label, "STILL REPRODUCES")
        elif not lint_green:
            verdict(label, "CLOSED")
        elif lint_green and not accepted and not type_error:
            verdict(
                label,
                "INCONCLUSIVE",
                "lint still exits 0 on the mangled policy, but the mangle no longer bypasses or breaks authority (validate_producer_authority returned ok=%r)"
                % (auth_result[0] if auth_result else None),
            )
        else:
            verdict(label, "INCONCLUSIVE", "unclassified combination of results")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        out("  CLEANUP: removed %s" % tmpdir)


# ===========================================================================
# A-06
# ===========================================================================


def probe_a06():
    labels = ["A-06.1", "A-06.2", "A-06.3"]
    try:
        from adapters.ingress.mavlink.mavlink_to_zmeta_template import (  # noqa: WPS433
            translate_platform_state,
        )
    except BaseException as exc:  # noqa: BLE001
        out("  Could not import the MAVLink template:")
        show_exc(exc, "    ")
        for lbl in labels:
            verdict(lbl, "INCONCLUSIVE", "mavlink_to_zmeta_template import failed: %r" % (exc,))
        return

    base_kwargs = dict(
        platform_id="uav-1",
        producer="mavlink-adapter",
        ts="2025-01-17T15:20:00+00:00",
    )
    parent = "019c2b5c-c053-70e1-b6aa-340000000001"

    _a06_1(translate_platform_state, base_kwargs, parent)
    _a06_2(translate_platform_state, base_kwargs, parent)
    _a06_3(translate_platform_state, base_kwargs, parent)


def _a06_gates(event):
    """Run the shipped gates over an emitted MAVLink state event."""
    if event is None or validators is None:
        return
    try:
        validator, policy = kernel()
    except BaseException as exc:  # noqa: BLE001
        out("  Could not load the kernel for the gate run:")
        show_exc(exc, "    ")
        return
    severity = policy.get("violation_severities")
    for name, fn in (
        ("validate_schema", lambda: validators.validate_schema(event, validator, severity)),
        (
            "validate_producer_authority",
            lambda: validators.validate_producer_authority(event, policy["producer_authority"], severity),
        ),
        (
            "validate_semantics",
            lambda: validators.validate_semantics(event, policy["semantics"], severity),
        ),
    ):
        try:
            res = fn()
            if isinstance(res, tuple) and len(res) == 2:
                out("  OBSERVED %-28s -> (ok=%r, codes=%r)"
                    % (name, res[0], [v.get("code") for v in (res[1] or [])]))
            else:
                out("  OBSERVED %-28s -> %r" % (name, res))
        except BaseException as exc:  # noqa: BLE001
            out("  OBSERVED %s RAISED:" % name)
            show_exc(exc, "    ")


def _a06_1(translate_platform_state, base_kwargs, parent):
    out()
    out("-- A-06.1 : translate_platform_state with alt_m ABSENT --")
    out("  BEFORE (recorded): emitted payload.geo == {'lat':34.05,'lon':-118.24,'alt_m':0.0}")
    out("                     with geo_status AVAILABLE and confidence 0.8, passing")
    out("                     schema, validate_semantics and validate_producer_authority.")
    state = {
        "lat": 34.05,
        "lon": -118.24,
        "gps_fix_type": 3,
        "satellites_visible": 10,
        "heading_deg": 90.0,
        "speed_mps": 12.0,
        "source_event_uid": "mavlink:sysid-1:seq-1",
        "based_on": [parent],
        "loop_status": "CHECKED_NOT_REFLECTION",
    }
    out("  INPUT  : %r  (note: no 'alt_m' key)" % (state,))

    try:
        event = translate_platform_state(dict(state), **base_kwargs)
    except BaseException as exc:  # noqa: BLE001
        out("  translate_platform_state RAISED:")
        show_exc(exc, "    ")
        verdict("A-06.1", "INCONCLUSIVE", "translate raised %s" % type(exc).__name__)
        return

    out("  OBSERVED return : %s" % ("None (adapter refused to emit)" if event is None else "an event dict"))
    if event is not None:
        payload = event.get("payload", {})
        out("  OBSERVED payload.geo         : %r" % (payload.get("geo"),))
        quality = payload.get("quality", {})
        out("  OBSERVED payload.quality     : %r" % (quality,))
        out("  OBSERVED geo_status          : %r"
            % (payload.get("geo_status") or (quality.get("geo_status") if isinstance(quality, dict) else None),))
        out("  OBSERVED confidence          : %r" % (event.get("confidence"),))
        _a06_gates(event)

    # Control: with alt_m present the adapter must still emit, otherwise a None
    # above would not be attributable to the missing altitude.
    control_state = dict(state)
    control_state["alt_m"] = 120.0
    try:
        control = translate_platform_state(control_state, **base_kwargs)
    except BaseException as exc:  # noqa: BLE001
        out("  CONTROL (alt_m=120.0) RAISED:")
        show_exc(exc, "    ")
        control = None
    out("  CONTROL (alt_m=120.0) returns : %s"
        % ("None" if control is None else "event, geo=%r" % (control.get("payload", {}).get("geo"),)))

    if event is None and control is not None:
        verdict("A-06.1", "CLOSED")
    elif event is not None:
        geo = event.get("payload", {}).get("geo") or {}
        if isinstance(geo, dict) and geo.get("alt_m") == 0.0:
            verdict("A-06.1", "STILL REPRODUCES")
        elif isinstance(geo, dict) and "alt_m" not in geo:
            verdict(
                "A-06.1",
                "INCONCLUSIVE",
                "geo emitted without alt_m -- not the zero-fill, but contract 6.8 requires geo be omitted entirely: geo=%r" % (geo,),
            )
        else:
            verdict("A-06.1", "INCONCLUSIVE", "event emitted with geo=%r" % (geo,))
    else:
        verdict(
            "A-06.1",
            "INCONCLUSIVE",
            "adapter also refuses the control state that HAS alt_m, so the refusal is not attributable to the missing altitude",
        )


def _a06_2(translate_platform_state, base_kwargs, parent):
    out()
    out("-- A-06.2 : speed_mps default when speed is never reported --")
    out("  BEFORE (recorded): speed_mps defaulted to 0.0, asserting 'stationary'.")
    state = {
        "lat": 34.05,
        "lon": -118.24,
        "alt_m": 120.0,
        "gps_fix_type": 3,
        "satellites_visible": 10,
        "source_event_uid": "mavlink:sysid-1:seq-2",
        "based_on": [parent],
        "loop_status": "CHECKED_NOT_REFLECTION",
    }
    out("  INPUT  : %r  (note: no 'speed_mps' key)" % (state,))
    try:
        event = translate_platform_state(dict(state), **base_kwargs)
    except BaseException as exc:  # noqa: BLE001
        out("  translate_platform_state RAISED:")
        show_exc(exc, "    ")
        verdict("A-06.2", "INCONCLUSIVE", "translate raised %s" % type(exc).__name__)
        return

    if event is None:
        out("  OBSERVED return : None (nothing emitted)")
        verdict("A-06.2", "INCONCLUSIVE", "adapter emitted nothing for a state that has a full position")
        return

    payload = event.get("payload", {})
    present = "speed_mps" in payload
    out("  OBSERVED 'speed_mps' in payload : %s" % present)
    out("  OBSERVED payload.speed_mps      : %r" % (payload.get("speed_mps", "<absent>"),))
    out("  OBSERVED payload keys           : %r" % (sorted(payload.keys()),))

    if not present:
        verdict("A-06.2", "CLOSED")
    elif payload.get("speed_mps") == 0.0:
        verdict("A-06.2", "STILL REPRODUCES")
    else:
        verdict("A-06.2", "INCONCLUSIVE", "speed_mps present with value %r" % (payload.get("speed_mps"),))


def _a06_3(translate_platform_state, base_kwargs, parent):
    out()
    out("-- A-06.3 : satellites_visible = 255 (MAVLink UINT8_MAX 'unknown' sentinel) --")
    state = {
        "lat": 34.05,
        "lon": -118.24,
        "alt_m": 120.0,
        "gps_fix_type": 3,
        "satellites_visible": 255,
        "source_event_uid": "mavlink:sysid-1:seq-3",
        "based_on": [parent],
        "loop_status": "CHECKED_NOT_REFLECTION",
    }
    out("  INPUT  : %r" % (state,))
    try:
        event = translate_platform_state(dict(state), **base_kwargs)
    except BaseException as exc:  # noqa: BLE001
        out("  translate_platform_state RAISED:")
        show_exc(exc, "    ")
        verdict("A-06.3", "INCONCLUSIVE", "translate raised %s" % type(exc).__name__)
        return

    if event is None:
        out("  OBSERVED return : None (nothing emitted)")
        verdict("A-06.3", "INCONCLUSIVE", "adapter emitted nothing for a state that has a full position")
        return

    quality = event.get("payload", {}).get("quality", {})
    present = isinstance(quality, dict) and "satellites_visible" in quality
    out("  OBSERVED payload.quality : %r" % (quality,))
    out("  OBSERVED 'satellites_visible' in quality : %s" % present)

    # Control: a real count must still be carried, or "absent" proves nothing.
    control_state = dict(state)
    control_state["satellites_visible"] = 10
    try:
        control = translate_platform_state(control_state, **base_kwargs)
        control_quality = (control or {}).get("payload", {}).get("quality", {})
        out("  CONTROL (satellites_visible=10) quality : %r" % (control_quality,))
        control_present = isinstance(control_quality, dict) and "satellites_visible" in control_quality
    except BaseException as exc:  # noqa: BLE001
        out("  CONTROL RAISED:")
        show_exc(exc, "    ")
        control_present = None
    out("  CONTROL carries a real count : %r" % control_present)

    if not present and control_present is True:
        verdict("A-06.3", "CLOSED")
    elif present and quality.get("satellites_visible") == 255:
        verdict("A-06.3", "STILL REPRODUCES")
    elif not present and control_present is not True:
        verdict(
            "A-06.3",
            "INCONCLUSIVE",
            "the sentinel is dropped but so is a real count of 10, so the drop is not attributable to the sentinel",
        )
    else:
        verdict("A-06.3", "INCONCLUSIVE", "quality.satellites_visible = %r" % (quality.get("satellites_visible"),))


# ===========================================================================
# main
# ===========================================================================


def main():
    section("A-01", "A-01 non-finite laundering (validators.py / gateway.py / zmeta_to_cot.py)", probe_a01)
    section("A-02", "A-02 SAPIENT ingress non-finite into canonical claim / features / bearing", probe_a02)
    section("A-03", "A-03 metrics sink failure re-entered by the receive-loop backstop", probe_a03)
    section("A-04", "A-04 zmeta_compact raw RecursionError instead of a refusal", probe_a04)
    section("A-05", "A-05 require_match_for_event_types unlinted (bare key / scalar)", probe_a05)
    section("A-06", "A-06 MAVLink zero-filled altitude labelled AVAILABLE", probe_a06)

    header("SUMMARY")
    out("Reminder: this is a CURRENT-STATE probe. CLOSED means the recorded")
    out("reproduction does not reproduce against this tree right now; it is not")
    out("a differential against the pre-fix code.")
    out()
    counts = {"CLOSED": 0, "STILL REPRODUCES": 0, "INCONCLUSIVE": 0}
    for label, state in VERDICTS:
        counts[state] = counts.get(state, 0) + 1
        out("  %-8s %s" % (label, state))
    out()
    out("  CLOSED           : %d" % counts.get("CLOSED", 0))
    out("  STILL REPRODUCES : %d" % counts.get("STILL REPRODUCES", 0))
    out("  INCONCLUSIVE     : %d" % counts.get("INCONCLUSIVE", 0))
    out("  TOTAL VERDICTS   : %d" % len(VERDICTS))
    non_closed = len(VERDICTS) - counts.get("CLOSED", 0)
    out()
    out("PROBE EXIT: %d" % non_closed)
    sys.exit(non_closed)


if __name__ == "__main__":
    main()
