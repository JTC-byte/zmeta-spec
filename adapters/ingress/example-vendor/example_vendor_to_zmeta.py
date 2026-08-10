"""Example-vendor RF JSON to ZMeta OBSERVATION_EVENT translator (worked exercise).

Implements the declarative mapping described by
``adapters/mapping-packs/example-vendor-pack`` as runnable adapter code. Per
``adapters/mapping-packs/README.md`` no runtime engine executes
``mapping.yaml`` — this module is the hand-written translation that pack
describes, written to the ``adapters/AUTHORING.md`` requirements so a new
author can diff a finished adapter against the guide.

Note the deliberate difference from the pack's minimal
``tests/expected.json``: the mapping file describes only the field mapping,
while the adapter also carries the semantic obligations the contract puts on
every producer — contract-required ``payload.timing_quality``, a UUIDv7
``event_id``, fail-closed refusal on missing semantics, all-or-nothing
canonical geo, and omit-or-refuse lineage.

Input format (schema_id ``vendor:example_rf:v1``):
  JSON object: {platform_id, sensor_id, ts, lat, lon, alt_hae_m,
                center_freq_hz, bandwidth_hz, power_dbm}

The vendor altitude key is datum-qualified by design: ``alt_hae_m`` is
declared WGS-84 Height Above Ellipsoid by the pack's ``units.yaml``, and
only a known-HAE value may occupy canonical ``payload.geo.alt_m``
(contract 6.2). A source field named plainly ``alt``/``altitude``/``alt_m``
carries no such guarantee — the MAVLink reference adapter now reads a bare
``alt_m`` input as MSL precisely because trusting it as HAE was a published
defect (the C1-01 altitude-datum class; see
``adapters/ingress/mavlink/mavlink_to_zmeta_template.py``). An adapter
whose source reports MSL, barometric, or AGL altitude must convert it or
omit canonical geo, never pass it through unlabeled.

``bandwidth_hz`` is required: the locked schema's RF minimum feature set
(contract 7.4) is center_freq_hz + bandwidth_hz + power_dbm, so a reading
missing any of them is refused rather than emitted schema-invalid. The
event carries no ``profile`` field — profile is gateway-added export
metadata (contract 3.4), and the production references never stamp it.
"""

import json
from pathlib import Path

from adapters.ingress.time_utils import coerce_timing_quality, normalize_utc_z
from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.0.0"
SCHEMA_ID = "vendor:example_rf:v1"

_SIGNATURE_KEYS = {
    "platform_id",
    "sensor_id",
    "ts",
    "center_freq_hz",
    "bandwidth_hz",
    "power_dbm",
}
_GEO_KEYS = ("lat", "lon", "alt_hae_m")

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "zmeta-event-1.0.schema.json"
_schema_cache = None


def detect(input_bytes):
    """Return the schema_id when the payload looks like example-vendor RF JSON."""
    if isinstance(input_bytes, (bytes, bytearray)):
        text = bytes(input_bytes).decode("utf-8", errors="replace")
    elif isinstance(input_bytes, str):
        text = input_bytes
    else:
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(obj, dict) and _SIGNATURE_KEYS.issubset(obj):
        return SCHEMA_ID
    return None


def translate(input_obj, schema_id, *, based_on=None, timing_quality=None):
    """Translate one example-vendor reading into ZMeta events.

    Returns a list with one OBSERVATION_EVENT, or an empty list when required
    semantic information is missing (fail closed; contract 3.4). The RF
    minimum feature set (contract 7.4) makes ``center_freq_hz``,
    ``bandwidth_hz``, and ``power_dbm`` all required — a reading missing any
    of them is refused, never emitted schema-invalid. Refusal covers missing
    and null values uniformly across the required keys — a null
    ``platform_id`` or ``sensor_id`` is refused, never coerced into a
    fabricated identity string. Identity and feature values pass through
    uncoerced; wrong value types (for example a string frequency or a
    numeric ``sensor_id``) are left to schema validation (ladder step 2) by
    design.

    ``based_on`` is caller-supplied real parent event ids. Lineage is never
    fabricated (contract 4.8): with no parents, ``lineage`` is omitted
    entirely. ``timing_quality`` should be source GPS/NTP/PTP metadata when
    the deployment has it; the ``coerce_timing_quality`` fallback is
    deliberately degraded (``UNKNOWN``/``UNSYNCED``) and stays visible.
    """
    if schema_id != SCHEMA_ID or not isinstance(input_obj, dict):
        return []
    if not _SIGNATURE_KEYS.issubset(input_obj):
        return []
    # A null under any required key is refused like a missing key: coercing a
    # null platform_id or sensor_id to text would fabricate identity.
    if any(input_obj.get(key) is None for key in _SIGNATURE_KEYS):
        return []
    ts = normalize_utc_z(input_obj.get("ts"))
    if ts is None:
        return []

    features = {
        "center_freq_hz": input_obj["center_freq_hz"],
        "bandwidth_hz": input_obj["bandwidth_hz"],
        "power_dbm": input_obj["power_dbm"],
    }

    payload = {
        "modality": "RF",
        "features": features,
        "timing_quality": coerce_timing_quality(timing_quality, event_ts=ts),
    }

    # Canonical geo is all-or-nothing (contract 6.8): omit it entirely rather
    # than zero-fill when any component is missing. The vertical crosses the
    # decode boundary under its datum-qualified name (contract 6.2): only the
    # declared-HAE alt_hae_m may become canonical alt_m.
    if all(input_obj.get(key) is not None for key in _GEO_KEYS):
        payload["geo"] = {
            "lat": float(input_obj["lat"]),
            "lon": float(input_obj["lon"]),
            "alt_m": float(input_obj["alt_hae_m"]),
        }

    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "RF",
            "ts": ts,
        },
        "source": {
            "platform_id": input_obj["platform_id"],
            "node_role": "EDGE",
            "producer": "example-vendor",
            "sensor_id": input_obj["sensor_id"],
        },
        "payload": payload,
    }
    if based_on:
        event["lineage"] = {
            "based_on": list(based_on),
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        }
    return [event]


def validate(zmeta_event):
    """Validate one event against the locked v1.0 schema.

    Returns ("pass", []) or ("fail", [violation strings]).
    """
    global _schema_cache
    import jsonschema

    if _schema_cache is None:
        _schema_cache = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(_schema_cache)
    violations = [
        f"{'/'.join(str(p) for p in error.absolute_path)}: {error.message}"
        for error in validator.iter_errors(zmeta_event)
    ]
    return ("pass", []) if not violations else ("fail", violations)
