"""The README launcher forwards --schema-path to the gateway.

The reference gateway accepted --schema-path (gateway/src/gateway.py) while
tools/run_gateway.py, the launcher the README recommends, did not expose it,
so the documented ten-minute path could only run the locked v1.0 lane and
refused every v1.1.0 event (execution review 2026-09-08, D1-01). Against that
launcher the first test fails: argparse rejects the flag and exits 2.
"""

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "tools" / "run_gateway.py"


def _load_launcher():
    spec = importlib.util.spec_from_file_location("run_gateway_launcher", LAUNCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(monkeypatch, argv):
    module = _load_launcher()
    captured = {}

    def fake_call(cmd):
        captured["cmd"] = list(cmd)
        return 0

    monkeypatch.setattr(module.subprocess, "call", fake_call)
    monkeypatch.setattr(sys, "argv", ["run_gateway.py", *argv])
    with pytest.raises(SystemExit) as exc:
        module.main()
    assert exc.value.code == 0
    return captured["cmd"]


def test_launcher_forwards_schema_path(monkeypatch):
    cmd = _run(monkeypatch, ["--profile", "H", "--schema-path", "schema/zmeta-event-1.1.0.schema.json"])
    index = cmd.index("--schema-path")
    assert cmd[index + 1] == "schema/zmeta-event-1.1.0.schema.json"


def test_launcher_omits_schema_path_when_not_given(monkeypatch):
    cmd = _run(monkeypatch, ["--profile", "H"])
    assert "--schema-path" not in cmd
