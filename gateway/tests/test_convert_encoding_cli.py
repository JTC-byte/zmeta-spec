import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import zmeta_cbor


ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = ROOT / "pytest-work"

# Hostile compact-decode datagrams (audit-named): an unknown top-level
# integer key, a CBOR tag this profile refuses (28/29, the value-sharing
# pair), and truncated bytes. Tag bytes are the minimal single-byte-argument
# encoding (major type 6, one-byte tag number, then a zero argument); the
# truncated case reuses the vetted minimal example from
# gateway/tests/test_compact_negative_decode.py's decoder-level test.
_HOSTILE_COMPACT_INPUTS = {
    "unknown_integer_key": zmeta_cbor.dumps({99: "x"}),
    "shared_reference_tag_28": bytes.fromhex("d81c00"),
    "shared_reference_tag_29": bytes.fromhex("d81d00"),
    "truncated_bytes": bytes.fromhex("45616263"),
}


def _sample_event():
    path = ROOT / "examples" / "encoding-roundtrip.jsonl"
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def _workdir():
    path = TMP_ROOT / f"convert-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def _cleanup_workdir(path):
    shutil.rmtree(path, ignore_errors=True)
    try:
        TMP_ROOT.rmdir()
    except OSError:
        pass


def test_convert_json_proto_json():
    tmp_path = _workdir()
    try:
        _run_convert_json_proto_json(tmp_path)
    finally:
        _cleanup_workdir(tmp_path)


def _run_convert_json_proto_json(tmp_path):
    event = _sample_event()
    json_path = tmp_path / "event.json"
    proto_path = tmp_path / "event.pb"
    roundtrip_path = tmp_path / "event.roundtrip.json"

    json_path.write_text(json.dumps(event), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "convert_encoding.py"),
            "--from",
            "json",
            "--to",
            "proto",
            "--input",
            str(json_path),
            "--output",
            str(proto_path),
        ],
        cwd=str(ROOT),
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "convert_encoding.py"),
            "--from",
            "proto",
            "--to",
            "json",
            "--input",
            str(proto_path),
            "--output",
            str(roundtrip_path),
        ],
        cwd=str(ROOT),
        check=True,
    )

    assert json.loads(roundtrip_path.read_text(encoding="utf-8")) == event


def test_convert_json_compact_auto_json():
    tmp_path = _workdir()
    try:
        _run_convert_json_compact_auto_json(tmp_path)
    finally:
        _cleanup_workdir(tmp_path)


def _run_convert_json_compact_auto_json(tmp_path):
    event = _sample_event()
    json_path = tmp_path / "event.json"
    compact_path = tmp_path / "event.zmc"
    roundtrip_path = tmp_path / "event.roundtrip.json"

    json_path.write_text(json.dumps(event), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "convert_encoding.py"),
            "--from",
            "json",
            "--to",
            "compact",
            "--input",
            str(json_path),
            "--output",
            str(compact_path),
        ],
        cwd=str(ROOT),
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "convert_encoding.py"),
            "--from",
            "auto",
            "--to",
            "json",
            "--input",
            str(compact_path),
            "--output",
            str(roundtrip_path),
        ],
        cwd=str(ROOT),
        check=True,
    )

    assert json.loads(roundtrip_path.read_text(encoding="utf-8")) == event


def _run_hostile_compact_decode(data):
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "convert_encoding.py"),
            "--from",
            "compact",
            "--to",
            "json",
        ],
        input=data,
        cwd=str(ROOT),
        capture_output=True,
    )


def test_convert_compact_unknown_integer_key_refuses_without_traceback():
    result = _run_hostile_compact_decode(_HOSTILE_COMPACT_INPUTS["unknown_integer_key"])
    assert result.returncode != 0
    assert b"Traceback" not in result.stderr
    assert b"decode refused:" in result.stderr


def test_convert_compact_shared_reference_tag_28_refuses_without_traceback():
    result = _run_hostile_compact_decode(_HOSTILE_COMPACT_INPUTS["shared_reference_tag_28"])
    assert result.returncode != 0
    assert b"Traceback" not in result.stderr
    assert b"decode refused:" in result.stderr


def test_convert_compact_shared_reference_tag_29_refuses_without_traceback():
    result = _run_hostile_compact_decode(_HOSTILE_COMPACT_INPUTS["shared_reference_tag_29"])
    assert result.returncode != 0
    assert b"Traceback" not in result.stderr
    assert b"decode refused:" in result.stderr


def test_convert_compact_truncated_bytes_refuses_without_traceback():
    result = _run_hostile_compact_decode(_HOSTILE_COMPACT_INPUTS["truncated_bytes"])
    assert result.returncode != 0
    assert b"Traceback" not in result.stderr
    assert b"decode refused:" in result.stderr
