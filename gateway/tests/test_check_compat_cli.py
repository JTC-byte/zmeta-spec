import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = ROOT / "pytest-work"


def _sample_event():
    path = ROOT / "examples" / "encoding-roundtrip.jsonl"
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def _workdir():
    path = TMP_ROOT / f"check-compat-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def _cleanup_workdir(path):
    shutil.rmtree(path, ignore_errors=True)
    try:
        TMP_ROOT.rmdir()
    except OSError:
        pass


def _run_check(path, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_compat.py"), str(path), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def test_check_compat_reports_migration_buckets():
    tmp_path = _workdir()
    try:
        event = _sample_event()
        event["event"]["ts"] = "2025-02-01T12:00:00+00:00"
        event["event"]["event_subtype"] = "PLATFORM_POSITION"
        event["source"]["producer"] = "edge-comms"
        event["payload"].pop("timing_quality", None)
        event["payload"].pop("track_id", None)

        path = tmp_path / "bad.jsonl"
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")

        result = _run_check(path)

        assert result.returncode == 1
        assert "timestamp_format" in result.stdout
        assert "subtype_vocabulary" in result.stdout
        assert "timing_quality" in result.stdout
        assert "producer_authority" in result.stdout
        assert "cot_projection" in result.stdout
        assert "suggestion=2025-02-01T12:00:00Z" in result.stdout
    finally:
        _cleanup_workdir(tmp_path)


def test_check_compat_reports_v11_only_vocabulary_version_mismatch():
    tmp_path = _workdir()
    try:
        event = _sample_event()
        event["profile"] = "H"
        event["event"]["event_type"] = "SYSTEM_EVENT"
        event["event"]["event_subtype"] = "PLATFORM_STATUS"
        event["payload"] = {
            "system_type": "PLATFORM_STATUS",
            "state": "ACTIVE",
            "metrics": {"power": {"state": "NOMINAL"}},
        }
        event["source"]["producer"] = "zmeta-gateway"
        event.pop("confidence", None)
        event.pop("lineage", None)

        path = tmp_path / "platform-status.json"
        path.write_text(json.dumps(event), encoding="utf-8")

        result = _run_check(path)

        assert result.returncode == 1
        assert "version_vocabulary" in result.stdout
        assert "PLATFORM_STATUS requires zmeta_version 1.1.0" in result.stdout
    finally:
        _cleanup_workdir(tmp_path)


def test_check_compat_warns_on_explicit_unknown_unsynced_timing():
    tmp_path = _workdir()
    try:
        event = _sample_event()
        event["payload"]["timing_quality"] = {
            "time_source": "UNKNOWN",
            "sync_state": "UNSYNCED",
            "est_error_ms": 60000,
            "last_sync_ts": "2025-02-01T12:00:00Z",
        }

        path = tmp_path / "fallback.json"
        path.write_text(json.dumps(event), encoding="utf-8")

        result = _run_check(path)

        assert result.returncode == 0
        assert "WARN timing_quality_fallback" in result.stdout
    finally:
        _cleanup_workdir(tmp_path)


def test_check_compat_accepts_current_release_target():
    tmp_path = _workdir()
    try:
        event = _sample_event()
        path = tmp_path / "event.json"
        path.write_text(json.dumps(event), encoding="utf-8")

        result = _run_check(path, "--target", "v1.1.12")

        assert result.returncode == 0
        assert "issues=0" in result.stdout
    finally:
        _cleanup_workdir(tmp_path)
