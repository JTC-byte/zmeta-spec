import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FILTER_PATH = ROOT / "tools" / "filter_risk.py"

spec = importlib.util.spec_from_file_location("zmeta_filter_risk", FILTER_PATH)
filter_risk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filter_risk)


def _state_event(event_id, risk=None):
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": event_id,
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-01-17T15:05:00Z",
        },
        "source": {
            "platform_id": "fusion-node-01",
            "node_role": "GATEWAY",
            "producer": "fusion-engine",
        },
        "profile": "L",
        "payload": {
            "track_id": "track-1",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 1000,
        },
        "confidence": 0.8,
        "lineage": {"based_on": ["019c2b5c-c051-70e1-b6aa-34bf14c8b201"]},
    }
    if risk:
        event["payload"]["extensions"] = {"risk_adjudication": [risk]}
    return event


def _risk(decision, allowed, prohibited, dimension="timing"):
    mode = {
        "WARN_ACCEPT": "warn",
        "DEGRADED_ACCEPT": "degrade",
        "QUARANTINE_ACCEPT": "quarantine",
        "REJECTED": "reject",
    }.get(decision, decision.lower())
    return {
        "risk_dimension": dimension,
        "reason_code": "TIMING_STATUS_STALE",
        "policy_mode": mode,
        "policy_decision": decision,
        "allowed_uses": allowed,
        "prohibited_uses": prohibited,
    }


def _diagnostic(decision, allowed, prohibited):
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": "019c2b5c-c051-70e1-b6aa-34bf14c8b399",
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "SCHEMA_VIOLATION",
            "ts": "2025-01-17T15:05:01Z",
        },
        "source": {
            "platform_id": "zmeta-gateway",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "profile": "H",
        "payload": {
            "system_type": "SCHEMA_VIOLATION",
            "state": "WARNING",
            "metrics": {
                "reason_code": "TIMING_STATUS_STALE",
                "original_event_id": "019c2b5c-c051-70e1-b6aa-34bf14c8b200",
                "risk_dimension": "timing",
                "policy_mode": "degrade",
                "policy_decision": decision,
                "allowed_uses": allowed,
                "prohibited_uses": prohibited,
            },
        },
    }


def _write_jsonl(path, events):
    path.write_text(
        "".join(json.dumps(event, separators=(",", ":")) + "\n" for event in events),
        encoding="utf-8",
    )


def _run_filter(*args):
    return subprocess.run(
        [sys.executable, str(FILTER_PATH), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_display_preset_allows_quarantine_display_label():
    event = _state_event(
        "019c2b5c-c051-70e1-b6aa-34bf14c8b301",
        _risk(
            "QUARANTINE_ACCEPT",
            ["DISPLAY", "AAR_ONLY", "DEBUG_ONLY"],
            ["FUSION_INPUT", "STATE_UPDATE", "COMMAND_BASIS"],
            dimension="external_promotion",
        ),
    )

    result = filter_risk.evaluate_event(
        event,
        max_risk="quarantine",
        require_uses=["DISPLAY"],
    )

    assert result["passed"] is True


def test_command_preset_drops_degraded_or_quarantined_data(tmp_path):
    clean = _state_event("019c2b5c-c051-70e1-b6aa-34bf14c8b302")
    degraded = _state_event(
        "019c2b5c-c051-70e1-b6aa-34bf14c8b303",
        _risk(
            "DEGRADED_ACCEPT",
            ["DISPLAY", "LOCAL_AWARENESS", "ALERTING"],
            ["FUSION_INPUT", "STATE_UPDATE", "COMMAND_BASIS", "AUTONOMY_TASKING"],
        ),
    )
    source = tmp_path / "events.jsonl"
    dropped = tmp_path / "dropped.jsonl"
    _write_jsonl(source, [clean, degraded])

    result = _run_filter(
        "--input",
        str(source),
        "--preset",
        "command",
        "--dropped-output",
        str(dropped),
        "--fail-on-drop",
    )

    assert result.returncode == 1
    passed = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert [event["event"]["event_id"] for event in passed] == [clean["event"]["event_id"]]
    dropped_items = [json.loads(line) for line in dropped.read_text(encoding="utf-8").splitlines()]
    assert len(dropped_items) == 1
    assert any("risk_exceeds_clean" in reason for reason in dropped_items[0]["reasons"])
    assert any("use_prohibited:COMMAND_BASIS" in reason for reason in dropped_items[0]["reasons"])


def test_fusion_preset_accepts_warning_but_rejects_degraded_fusion_input(tmp_path):
    warning = _state_event(
        "019c2b5c-c051-70e1-b6aa-34bf14c8b304",
        _risk(
            "WARN_ACCEPT",
            ["DISPLAY", "LOCAL_AWARENESS", "ALERTING", "FUSION_INPUT", "STATE_UPDATE"],
            ["COMMAND_BASIS", "AUTONOMY_TASKING"],
        ),
    )
    degraded = _state_event(
        "019c2b5c-c051-70e1-b6aa-34bf14c8b305",
        _risk(
            "DEGRADED_ACCEPT",
            ["DISPLAY", "LOCAL_AWARENESS", "ALERTING"],
            ["FUSION_INPUT", "STATE_UPDATE", "COMMAND_BASIS", "AUTONOMY_TASKING"],
        ),
    )
    source = tmp_path / "events.jsonl"
    _write_jsonl(source, [warning, degraded])

    result = _run_filter("--input", str(source), "--preset", "fusion")

    assert result.returncode == 0
    passed = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert [event["event"]["event_id"] for event in passed] == [warning["event"]["event_id"]]
    assert "dropped=1" in result.stderr


def test_diagnostic_metrics_filter_by_required_use():
    diagnostic = _diagnostic(
        "DEGRADED_ACCEPT",
        ["DISPLAY", "LOCAL_AWARENESS", "ALERTING"],
        ["FUSION_INPUT", "STATE_UPDATE", "COMMAND_BASIS", "AUTONOMY_TASKING"],
    )

    result = filter_risk.evaluate_event(
        diagnostic,
        max_risk="degrade",
        require_uses=["COMMAND_BASIS"],
    )

    assert result["passed"] is False
    assert any("use_prohibited:COMMAND_BASIS" in reason for reason in result["reasons"])
    assert result["risk_records"][0]["source"] == "diagnostic"


def test_list_presets_cli():
    result = _run_filter("--list-presets")

    assert result.returncode == 0
    assert "command: max_risk=clean" in result.stdout
    assert "display: max_risk=quarantine" in result.stdout


def test_filter_rejects_overlapping_input_and_output_paths(tmp_path):
    event = _state_event("019c2b5c-c051-70e1-b6aa-34bf14c8b306")
    source = tmp_path / "events.jsonl"
    _write_jsonl(source, [event])
    original = source.read_text(encoding="utf-8")

    result = _run_filter("--input", str(source), "--output", str(source))

    assert result.returncode == 1
    assert "output path must differ from input path" in result.stderr
    assert source.read_text(encoding="utf-8") == original
