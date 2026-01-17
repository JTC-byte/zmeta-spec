import json
from datetime import datetime, timezone
from pathlib import Path
import uuid

import yaml
from jsonschema import Draft202012Validator, FormatChecker


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "zmeta-event-1.0.schema.json"
MAPPING_PACKS_DIR = Path(__file__).resolve().parents[2] / "mapping-packs"
ADAPTER_VERSION = "0.1.0"


def detect(input_bytes):
    """
    Inspect raw input and return a schema identifier string.
    """
    raise NotImplementedError("detect() must be implemented per source format")


def translate(input_obj, schema_id):
    """
    Translate a parsed input object into a list of ZMeta events.
    Must set lineage.transform = f\"translate:{schema_id}@{ADAPTER_VERSION}\".
    """
    raise NotImplementedError("translate() must be implemented per source format")


def validate(zmeta_event):
    """
    Validate against the ZMeta schema.
    Return (\"pass\"|\"warn\"|\"fail\", violations)
    """
    validator = _load_schema_validator()
    errors = sorted(validator.iter_errors(zmeta_event), key=lambda e: e.path)
    if errors:
        violations = [
            {
                "code": "SCHEMA_INVALID",
                "severity": "fail",
                "message": errors[0].message,
                "details": {"path": "/".join(str(p) for p in errors[0].path)},
            }
        ]
        return "fail", violations
    return "pass", []


def emit_schema_violation(original_event_id, source_platform_id, producer, details):
    """
    Build a SYSTEM_EVENT/SCHEMA_VIOLATION for deterministic failures.
    """
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid.uuid4()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "SCHEMA_VIOLATION",
            "ts": _utc_now(),
        },
        "source": {
            "platform_id": source_platform_id or "unknown",
            "node_role": "EDGE",
            "producer": producer or "adapter",
        },
        "payload": {
            "system_type": "SCHEMA_VIOLATION",
            "state": "REJECTED",
            "metrics": {
                "reason_code": "SCHEMA_INVALID",
                "original_event_id": original_event_id,
                **(details or {}),
            },
        },
    }


def load_mapping_pack(schema_id):
    """
    Placeholder for loading a mapping pack from adapters/mapping-packs/.
    """
    path = MAPPING_PACKS_DIR / f"{schema_id}.yaml"
    if not path.is_file():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_schema_validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
