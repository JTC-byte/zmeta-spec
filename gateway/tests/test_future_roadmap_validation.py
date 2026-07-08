import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = ROOT / "pytest-work"
ROADMAP_PATH = ROOT / "spec" / "future-branch-roadmap.yaml"


def _workdir():
    path = TMP_ROOT / f"future-roadmap-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def _cleanup_workdir(path):
    shutil.rmtree(path, ignore_errors=True)
    try:
        TMP_ROOT.rmdir()
    except OSError:
        pass


def _run_validator(*args):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_future_roadmap.py"), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def _load_roadmap():
    return yaml.safe_load(ROADMAP_PATH.read_text(encoding="utf-8"))


def _write_roadmap(path, data):
    target = path / "future-branch-roadmap.yaml"
    target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return target


def test_reference_roadmap_validates():
    result = _run_validator()

    assert result.returncode == 0, result.stdout + result.stderr
    assert "future-branch roadmap ok" in result.stdout


def test_unknown_registry_reference_fails():
    tmp_path = _workdir()
    try:
        data = _load_roadmap()
        data["candidates"][0]["registry_refs"] = ["NOT_A_REAL_REGISTRY_NAME"]
        target = _write_roadmap(tmp_path, data)

        result = _run_validator("--roadmap", str(target))

        assert result.returncode == 1
        assert "ROADMAP_REGISTRY_REF_UNKNOWN" in result.stdout
    finally:
        _cleanup_workdir(tmp_path)


def test_missing_tripwires_fail():
    tmp_path = _workdir()
    try:
        data = _load_roadmap()
        data["candidates"][0]["tripwires"] = []
        target = _write_roadmap(tmp_path, data)

        result = _run_validator("--roadmap", str(target))

        assert result.returncode == 1
        assert "ROADMAP_TRIPWIRES_MISSING" in result.stdout
    finally:
        _cleanup_workdir(tmp_path)


def test_validity_asserting_status_requires_registry_support():
    tmp_path = _workdir()
    try:
        data = _load_roadmap()
        candidate = next(
            entry for entry in data["candidates"] if entry["id"] == "correlation-identity"
        )
        candidate["status"] = "experimental"
        target = _write_roadmap(tmp_path, data)

        result = _run_validator("--roadmap", str(target))

        assert result.returncode == 1
        assert "ROADMAP_STATUS_LEAK" in result.stdout
    finally:
        _cleanup_workdir(tmp_path)


def test_duplicate_candidate_id_fails():
    tmp_path = _workdir()
    try:
        data = _load_roadmap()
        data["candidates"].append(dict(data["candidates"][0]))
        target = _write_roadmap(tmp_path, data)

        result = _run_validator("--roadmap", str(target))

        assert result.returncode == 1
        assert "ROADMAP_DUPLICATE_ID" in result.stdout
    finally:
        _cleanup_workdir(tmp_path)


def test_unknown_dependency_fails():
    tmp_path = _workdir()
    try:
        data = _load_roadmap()
        data["candidates"][0]["depends_on"] = ["no-such-candidate"]
        target = _write_roadmap(tmp_path, data)

        result = _run_validator("--roadmap", str(target))

        assert result.returncode == 1
        assert "ROADMAP_DEPENDENCY_UNKNOWN" in result.stdout
    finally:
        _cleanup_workdir(tmp_path)
