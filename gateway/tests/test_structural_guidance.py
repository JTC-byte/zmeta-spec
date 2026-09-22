"""The structural guidance rules and their lane gates.

tools/explain.py applies the `structural_rules` in tools/validation_guidance.yaml
to the shape of an event. The 2026-09-10 acoustic evidence build found the
acoustic rule firing on a v1.0 event, where no ACOUSTIC feature contract
exists; the detect grammar gained lane gates, and nothing tested the rules at
all. These pins fail against that explain.py: the gate keys were ignored, so
the v1.0 case fired, and HANDLED_DETECT_KEYS did not exist.
"""

import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _explain():
    spec = importlib.util.spec_from_file_location("zmeta_explain", ROOT / "tools" / "explain.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rules():
    data = yaml.safe_load((ROOT / "tools" / "validation_guidance.yaml").read_text(encoding="utf-8"))
    return {rule["id"]: rule for rule in data["structural_rules"]}


def _fired(event):
    explain = _explain()
    return {rule_id for rule_id, rule in _rules().items() if explain.matches(rule, event)}


def _acoustic(version, features, timing=None):
    event = {
        "event": {"event_type": "OBSERVATION_EVENT", "event_subtype": "ACOUSTIC"},
        "payload": {"modality": "ACOUSTIC", "features": dict(features)},
    }
    if version is not None:
        event["zmeta_version"] = version
    if timing is not None:
        event["payload"]["timing_quality"] = dict(timing)
    return event


FULL_TIMING = {"time_source": "UNKNOWN", "sync_state": "UNSYNCED", "est_error_ms": 60000, "last_sync_ts": "2026-09-10T00:00:00Z"}


def test_the_required_features_rule_stays_silent_on_the_locked_lane():
    assert "acoustic-missing-required-features" not in _fired(_acoustic("1.0", {}, FULL_TIMING))
    assert "acoustic-missing-required-features" in _fired(_acoustic("1.1.0", {}, FULL_TIMING))


def test_the_required_features_rule_fires_on_undeclared_dialect_input():
    assert "acoustic-missing-required-features" in _fired(_acoustic(None, {}, FULL_TIMING))
    assert "acoustic-missing-required-features" in _fired(_acoustic("1.2.0", {}, FULL_TIMING))


def test_a_level_without_a_reference_is_flagged_and_a_declared_one_is_not():
    bare = {"center_freq_hz": 140.6, "spl_db": -29.4}
    declared = dict(bare, level_reference="DBFS")
    assert "acoustic-level-without-reference" in _fired(_acoustic("1.1.0", bare, FULL_TIMING))
    assert "acoustic-level-without-reference" not in _fired(_acoustic("1.1.0", declared, FULL_TIMING))
    assert "acoustic-level-without-reference" not in _fired(_acoustic("1.0", bare, FULL_TIMING))


def test_a_missing_level_is_flagged_and_either_carrier_silences_it():
    freq_only = {"center_freq_hz": 3.2}
    assert "acoustic-missing-level" in _fired(_acoustic("1.1.0", freq_only, FULL_TIMING))
    assert "acoustic-missing-level" not in _fired(_acoustic("1.1.0", dict(freq_only, spl_db=-29.4, level_reference="DBFS"), FULL_TIMING))
    assert "acoustic-missing-level" not in _fired(_acoustic("1.1.0", dict(freq_only, pressure_pa=0.0142, pressure_statistic="RMS"), FULL_TIMING))
    assert "acoustic-missing-level" not in _fired(_acoustic("1.0", freq_only, FULL_TIMING))


def test_a_pascals_level_does_not_trip_the_required_features_rule():
    # The rule used to demand spl_db; a pascals producer is a compliant 1.1.0 form now.
    pa = {"center_freq_hz": 3.2, "pressure_pa": 0.0142, "pressure_statistic": "RMS"}
    assert "acoustic-missing-required-features" not in _fired(_acoustic("1.1.0", pa, FULL_TIMING))


def test_a_pressure_without_its_statistic_is_flagged():
    pa_only = {"center_freq_hz": 3.2, "pressure_pa": 0.0142}
    assert "acoustic-pressure-without-statistic" in _fired(_acoustic("1.1.0", pa_only, FULL_TIMING))
    assert "acoustic-pressure-without-statistic" not in _fired(_acoustic("1.1.0", dict(pa_only, pressure_statistic="RMS"), FULL_TIMING))
    assert "acoustic-pressure-without-statistic" not in _fired(_acoustic("1.0", pa_only, FULL_TIMING))


def test_a_statistic_without_its_pressure_is_flagged():
    stat_only = {"center_freq_hz": 2500.0, "spl_db": 72.3, "pressure_statistic": "RMS"}
    assert "acoustic-statistic-without-pressure" in _fired(_acoustic("1.1.0", stat_only, FULL_TIMING))
    assert "acoustic-statistic-without-pressure" not in _fired(_acoustic("1.1.0", dict(stat_only, pressure_pa=0.0142), FULL_TIMING))
    assert "acoustic-statistic-without-pressure" not in _fired(_acoustic("1.0", stat_only, FULL_TIMING))


def test_the_locked_lane_gets_its_own_level_advice():
    bare = {"center_freq_hz": 140.6, "spl_db": -29.4}
    assert "acoustic-level-on-locked-lane" in _fired(_acoustic("1.0", bare, FULL_TIMING))
    assert "acoustic-level-on-locked-lane" not in _fired(_acoustic("1.1.0", bare, FULL_TIMING))


def test_a_partial_timing_quality_is_flagged_and_a_complete_one_is_not():
    partial = {"time_source": "UNKNOWN", "sync_state": "UNSYNCED", "last_sync_ts": "2026-09-10T00:00:00Z"}
    features = {"center_freq_hz": 140.6, "level_dbfs": -29.4}
    assert "timing-quality-incomplete" in _fired(_acoustic("1.0", features, partial))
    assert "timing-quality-incomplete" not in _fired(_acoustic("1.0", features, FULL_TIMING))
    assert "timing-quality-incomplete" not in _fired(_acoustic("1.0", features, None))


def test_every_detect_key_in_the_file_is_one_the_matcher_handles():
    explain = _explain()
    used = {key for rule in _rules().values() for key in (rule.get("detect") or {})}
    assert used <= explain.HANDLED_DETECT_KEYS, sorted(used - explain.HANDLED_DETECT_KEYS)
