import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import zmeta_cbor
import zmeta_compact


def _load_events():
    path = ROOT / "examples" / "encoding-roundtrip.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    events = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        events.append(json.loads(line))
    return events


def test_cbor_roundtrip():
    for event in _load_events():
        encoded = zmeta_cbor.dumps(event)
        decoded = zmeta_cbor.loads(encoded)
        assert decoded == event


def test_compact_roundtrip():
    for event in _load_events():
        encoded = zmeta_compact.dumps(event)
        decoded = zmeta_compact.loads(encoded)
        assert decoded == event
