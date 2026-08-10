import json
from pathlib import Path

from adapters.ingress.time_utils import utc_now_z
from zmeta_uuid import uuid7

import yaml
from jsonschema import Draft202012Validator


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
    Emit lineage only when real parent ZMeta event ids exist: set
    lineage.based_on to those ids and
    lineage.transform = f"translate:{schema_id}@{ADAPTER_VERSION}".
    Otherwise omit the lineage block entirely; never fabricate based_on.
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
            "event_id": str(uuid7()),
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
    # No format_checker is installed here on purpose. `date-time` is the only
    # `format` assertion in the ZMeta schemas, and jsonschema registers no
    # `date-time` checker without an RFC 3339 checker library, which this stack
    # does not depend on. The `utcDateTime` `pattern` is the real gate on
    # timestamps; `format` is annotation-only here. Passing a bare
    # FormatChecker() would validate nothing and would imply otherwise.
    return Draft202012Validator(schema)


def _utc_now():
    return utc_now_z()
