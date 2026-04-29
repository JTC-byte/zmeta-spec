"""
Compact binary mapping for ZMeta (CBOR + integer keys).

This module provides a lossless compact wire format intended for Profile L links.
It preserves semantics by expanding back to the canonical JSON envelope.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

try:
    import cbor2
except ImportError:  # pragma: no cover - optional dependency
    cbor2 = None

try:
    import zmeta_cbor
except ImportError:  # pragma: no cover - optional dependency
    zmeta_cbor = None


COMPACT_VERSION = 1

TOP_KEYS = {
    "compact_version": 1,
    "event": 2,
    "source": 3,
    "payload": 4,
    "confidence": 5,
    "lineage": 6,
    "profile": 7,
}

EVENT_KEYS = {
    "event_id": 1,
    "event_type": 2,
    "event_subtype": 3,
    "ts": 4,
    "t_publish": 5,
    "t_receive": 6,
}

SOURCE_KEYS = {
    "platform_id": 1,
    "node_role": 2,
    "producer": 3,
    "sensor_id": 4,
    "sw_version": 5,
}

LINEAGE_KEYS = {
    "based_on": 1,
    "transform": 2,
}

STATE_PAYLOAD_KEYS = {
    "track_id": 1,
    "geo": 2,
    "valid_for_ms": 3,
    "class": 4,
    "source_summary": 5,
    "heading_deg": 6,
    "speed_mps": 7,
}

COMMAND_PAYLOAD_KEYS = {
    "task_id": 1,
    "task_type": 2,
    "target_geo": 3,
    "geometry": 4,
    "valid_from_ts": 5,
    "valid_for_ms": 6,
    "priority": 7,
    "requires_deconfliction": 8,
}

SYSTEM_PAYLOAD_KEYS = {
    "system_type": 1,
    "state": 2,
    "metrics": 3,
}

GEO_KEYS = {
    "lat": 1,
    "lon": 2,
    "alt_m": 3,
}

GEO2D_KEYS = {
    "lat": 1,
    "lon": 2,
}

TASK_ACK_METRICS_KEYS = {
    "task_id": 1,
    "original_event_id": 2,
    "reason_code": 3,
}

LINK_STATUS_METRICS_KEYS = {
    "link_id": 1,
    "latency_ms": 2,
    "packet_loss_pct": 3,
    "throughput_bps": 4,
    "rssi_dbm": 5,
    "snr_db": 6,
    "jitter_ms": 7,
    "reason_code": 8,
    "interface": 9,
}

TIME_STATUS_METRICS_KEYS = {
    "time_source": 1,
    "sync_state": 2,
    "est_error_ms": 3,
    "last_sync_ts": 4,
}

SCHEMA_VIOLATION_METRICS_KEYS = {
    "reason_code": 1,
    "original_event_id": 2,
    "path": 3,
    "error": 4,
}

EVENT_TYPE_MAP = {
    "OBSERVATION_EVENT": 1,
    "INFERENCE_EVENT": 2,
    "FUSION_EVENT": 3,
    "STATE_EVENT": 4,
    "COMMAND_EVENT": 5,
    "SYSTEM_EVENT": 6,
}

NODE_ROLE_MAP = {
    "EDGE": 1,
    "GATEWAY": 2,
    "APEX": 3,
    "DMZ": 4,
    "CLOUD": 5,
}

PROFILE_MAP = {"L": 1, "M": 2, "H": 3}

EVENT_SUBTYPE_MAP = {
    "TRACK_STATE": 1,
    "GOTO": 2,
    "TASK_ACK": 3,
    "LINK_STATUS": 4,
    "TIME_STATUS": 5,
    "SCHEMA_VIOLATION": 6,
    "TRACK_FUSION": 7,
    "CLASSIFICATION": 8,
    "ASSOCIATION": 9,
    "ANOMALY": 10,
    "BEHAVIOR": 11,
    "RF": 12,
    "EO": 13,
    "IR": 14,
    "ACOUSTIC": 15,
    "NETWORK": 16,
    "ORBIT": 17,
    "HOLD": 18,
    "SEARCH_BOX": 19,
}

SYSTEM_TYPE_MAP = {
    "LINK_STATUS": 1,
    "TIME_STATUS": 2,
    "SCHEMA_VIOLATION": 3,
    "TASK_ACK": 4,
}

TASK_TYPE_MAP = {
    "GOTO": 1,
    "ORBIT": 2,
    "HOLD": 3,
    "SEARCH_BOX": 4,
}

PRIORITY_MAP = {
    "LOW": 1,
    "MED": 2,
    "HIGH": 3,
}

TIME_SOURCE_MAP = {
    "GPS_PPS": 1,
    "GPS_NMEA": 2,
    "NTP": 3,
    "PTP": 4,
    "MANUAL": 5,
    "UNKNOWN": 6,
}

SYNC_STATE_MAP = {
    "LOCKED": 1,
    "HOLDOVER": 2,
    "UNSYNCED": 3,
}

TASK_ACK_STATE_MAP = {
    "RECEIVED": 1,
    "ACCEPTED": 2,
    "REJECTED": 3,
    "EXECUTING": 4,
    "COMPLETED": 5,
    "FAILED": 6,
    "CANCELLED": 7,
    "EXPIRED": 8,
    "DUPLICATE_IGNORED": 9,
}

LINK_STATUS_STATE_MAP = {
    "UP": 1,
    "DEGRADED": 2,
    "DOWN": 3,
    "UNKNOWN": 4,
}

REASON_CODE_MAP = {
    "SCHEMA_INVALID": 1,
    "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE": 2,
    "EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE": 3,
    "COMMAND_NOT_DECONFLICTED": 4,
    "COMMAND_HAS_ALTITUDE": 5,
    "OBSERVATION_HAS_IDENTITY": 6,
    "INFERENCE_HAS_TRACK_ID": 7,
    "STATE_HAS_RAW_FEATURES": 8,
    "SCHEMA_VIOLATION_MISSING_REASON_CODE": 9,
    "SCHEMA_VIOLATION_MISSING_ORIGINAL_EVENT_ID": 10,
    "SCHEMA_VIOLATION_INVALID_REASON_CODE": 11,
    "TASK_ACK_MISSING_TASK_ID": 12,
    "TASK_ACK_MISSING_REQUIRED_FIELD": 13,
    "TASK_ACK_MISSING_ORIGINAL_EVENT_ID": 14,
    "TASK_ACK_MISSING_REASON_CODE": 15,
    "TASK_ACK_INVALID_STATE": 16,
    "TASK_ACK_INVALID_REASON_CODE": 17,
    "LINK_STATUS_MISSING_REQUIRED_FIELD": 18,
    "LINK_STATUS_INVALID_STATE": 19,
    "LINK_STATUS_MISSING_REASON_CODE": 20,
    "LINK_STATUS_INVALID_REASON_CODE": 21,
    "PRODUCER_NOT_ALLOWED": 22,
    "TASK_DUPLICATE": 23,
    "TASK_EXPIRED": 24,
    "TASK_CANCELLED": 25,
    "TASK_FAILED": 26,
    "TASK_ABORTED": 27,
    "TASK_REJECTED": 28,
    "LINK_LOSS": 29,
    "LOW_RSSI": 30,
    "HIGH_LATENCY": 31,
    "HIGH_PACKET_LOSS": 32,
    "LOW_THROUGHPUT": 33,
    "INTERFERENCE": 34,
    "JAMMED": 35,
    "BACKHAUL_DOWN": 36,
    "NO_ROUTE": 37,
    "CONFIG_ERROR": 38,
    "POWER_SAVE": 39,
    "UNKNOWN_CAUSE": 40,
}


def _reverse_map(mapping: Dict[str, int]) -> Dict[int, str]:
    return {value: key for key, value in mapping.items()}


EVENT_TYPE_REV = _reverse_map(EVENT_TYPE_MAP)
NODE_ROLE_REV = _reverse_map(NODE_ROLE_MAP)
PROFILE_REV = _reverse_map(PROFILE_MAP)
EVENT_SUBTYPE_REV = _reverse_map(EVENT_SUBTYPE_MAP)
SYSTEM_TYPE_REV = _reverse_map(SYSTEM_TYPE_MAP)
TASK_TYPE_REV = _reverse_map(TASK_TYPE_MAP)
PRIORITY_REV = _reverse_map(PRIORITY_MAP)
TIME_SOURCE_REV = _reverse_map(TIME_SOURCE_MAP)
SYNC_STATE_REV = _reverse_map(SYNC_STATE_MAP)
TASK_ACK_STATE_REV = _reverse_map(TASK_ACK_STATE_MAP)
LINK_STATUS_STATE_REV = _reverse_map(LINK_STATUS_STATE_MAP)
REASON_CODE_REV = _reverse_map(REASON_CODE_MAP)


def _require_cbor():
    if cbor2 is None and zmeta_cbor is None:
        raise SystemExit("CBOR support requires cbor2 or zmeta_cbor.")


def dumps(event: Dict[str, Any]) -> bytes:
    compact = encode_event(event)
    _require_cbor()
    if zmeta_cbor is not None:
        return zmeta_cbor.dumps(compact)
    return cbor2.dumps(compact, canonical=True)


def loads(data: bytes, **decode_limits) -> Dict[str, Any]:
    compact = _decode_cbor(data, **decode_limits)
    return decode_event(compact)


def is_compact(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    return any(isinstance(key, int) for key in obj.keys())


def encode_event(event: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    out[TOP_KEYS["compact_version"]] = COMPACT_VERSION

    event_block = event.get("event", {})
    source = event.get("source", {})
    payload = event.get("payload", {})

    if event_block:
        out[TOP_KEYS["event"]] = _encode_event_block(event_block)
    if source:
        out[TOP_KEYS["source"]] = _encode_source(source)
    if payload is not None:
        out[TOP_KEYS["payload"]] = _encode_payload(payload, event_block.get("event_type"))

    if "confidence" in event:
        out[TOP_KEYS["confidence"]] = event.get("confidence")
    if "lineage" in event:
        out[TOP_KEYS["lineage"]] = _encode_lineage(event.get("lineage", {}))
    if "profile" in event:
        out[TOP_KEYS["profile"]] = _map_enum(event.get("profile"), PROFILE_MAP)

    return out


def decode_event(compact: Dict[int, Any]) -> Dict[str, Any]:
    event: Dict[str, Any] = {"zmeta_version": "1.0"}

    if TOP_KEYS["compact_version"] in compact:
        version = compact.get(TOP_KEYS["compact_version"])
        if version != COMPACT_VERSION:
            raise ValueError(f"Unsupported compact_version: {version}")

    event_block = compact.get(TOP_KEYS["event"])
    if isinstance(event_block, dict):
        event["event"] = _decode_event_block(event_block)

    source = compact.get(TOP_KEYS["source"])
    if isinstance(source, dict):
        event["source"] = _decode_source(source)

    payload = compact.get(TOP_KEYS["payload"])
    if payload is not None and "event" in event:
        event_type = event["event"].get("event_type")
        event["payload"] = _decode_payload(payload, event_type)
    elif payload is not None:
        event["payload"] = payload

    if TOP_KEYS["confidence"] in compact:
        event["confidence"] = compact.get(TOP_KEYS["confidence"])
    if TOP_KEYS["lineage"] in compact:
        event["lineage"] = _decode_lineage(compact.get(TOP_KEYS["lineage"]))
    if TOP_KEYS["profile"] in compact:
        event["profile"] = _unmap_enum(compact.get(TOP_KEYS["profile"]), PROFILE_REV)

    return event


def _decode_cbor(data: bytes, **decode_limits) -> Any:
    _require_cbor()
    if zmeta_cbor is not None:
        return zmeta_cbor.loads(data, **decode_limits)
    if decode_limits:
        raise ValueError("compact decode limits require zmeta_cbor")
    return cbor2.loads(data)


def _encode_event_block(block: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    event_id = block.get("event_id")
    if event_id is not None:
        out[EVENT_KEYS["event_id"]] = _uuid_to_bytes(event_id)
    event_type = block.get("event_type")
    if event_type is not None:
        out[EVENT_KEYS["event_type"]] = _map_enum(event_type, EVENT_TYPE_MAP)
    event_subtype = block.get("event_subtype")
    if event_subtype is not None:
        out[EVENT_KEYS["event_subtype"]] = _map_enum(event_subtype, EVENT_SUBTYPE_MAP)
    ts = block.get("ts")
    if ts is not None:
        out[EVENT_KEYS["ts"]] = _parse_ts(ts)
    t_publish = block.get("t_publish")
    if t_publish is not None:
        out[EVENT_KEYS["t_publish"]] = _parse_ts(t_publish)
    t_receive = block.get("t_receive")
    if t_receive is not None:
        out[EVENT_KEYS["t_receive"]] = _parse_ts(t_receive)
    return out


def _decode_event_block(block: Dict[int, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if EVENT_KEYS["event_id"] in block:
        out["event_id"] = _uuid_from_bytes(block.get(EVENT_KEYS["event_id"]))
    if EVENT_KEYS["event_type"] in block:
        out["event_type"] = _unmap_enum(block.get(EVENT_KEYS["event_type"]), EVENT_TYPE_REV)
    if EVENT_KEYS["event_subtype"] in block:
        out["event_subtype"] = _unmap_enum(block.get(EVENT_KEYS["event_subtype"]), EVENT_SUBTYPE_REV)
    if EVENT_KEYS["ts"] in block:
        out["ts"] = _format_ts(block.get(EVENT_KEYS["ts"]))
    if EVENT_KEYS["t_publish"] in block:
        out["t_publish"] = _format_ts(block.get(EVENT_KEYS["t_publish"]))
    if EVENT_KEYS["t_receive"] in block:
        out["t_receive"] = _format_ts(block.get(EVENT_KEYS["t_receive"]))
    return out


def _encode_source(source: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    if source.get("platform_id") is not None:
        out[SOURCE_KEYS["platform_id"]] = source.get("platform_id")
    if source.get("node_role") is not None:
        out[SOURCE_KEYS["node_role"]] = _map_enum(source.get("node_role"), NODE_ROLE_MAP)
    if source.get("producer") is not None:
        out[SOURCE_KEYS["producer"]] = source.get("producer")
    if source.get("sensor_id") is not None:
        out[SOURCE_KEYS["sensor_id"]] = source.get("sensor_id")
    if source.get("sw_version") is not None:
        out[SOURCE_KEYS["sw_version"]] = source.get("sw_version")
    return out


def _decode_source(source: Dict[int, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if SOURCE_KEYS["platform_id"] in source:
        out["platform_id"] = source.get(SOURCE_KEYS["platform_id"])
    if SOURCE_KEYS["node_role"] in source:
        out["node_role"] = _unmap_enum(source.get(SOURCE_KEYS["node_role"]), NODE_ROLE_REV)
    if SOURCE_KEYS["producer"] in source:
        out["producer"] = source.get(SOURCE_KEYS["producer"])
    if SOURCE_KEYS["sensor_id"] in source:
        out["sensor_id"] = source.get(SOURCE_KEYS["sensor_id"])
    if SOURCE_KEYS["sw_version"] in source:
        out["sw_version"] = source.get(SOURCE_KEYS["sw_version"])
    return out


def _encode_lineage(lineage: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    based_on = lineage.get("based_on")
    if based_on is not None:
        out[LINEAGE_KEYS["based_on"]] = [_uuid_to_bytes(value) for value in based_on]
    if lineage.get("transform") is not None:
        out[LINEAGE_KEYS["transform"]] = lineage.get("transform")
    return out


def _decode_lineage(lineage: Any) -> Any:
    if not isinstance(lineage, dict):
        return lineage
    out: Dict[str, Any] = {}
    if LINEAGE_KEYS["based_on"] in lineage:
        values = lineage.get(LINEAGE_KEYS["based_on"], [])
        out["based_on"] = [_uuid_from_bytes(value) for value in values]
    if LINEAGE_KEYS["transform"] in lineage:
        out["transform"] = lineage.get(LINEAGE_KEYS["transform"])
    return out


def _encode_payload(payload: Any, event_type: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    event_type_str = _unmap_enum(event_type, EVENT_TYPE_REV) if isinstance(event_type, int) else event_type
    if event_type_str == "STATE_EVENT":
        return _encode_state_payload(payload)
    if event_type_str == "COMMAND_EVENT":
        return _encode_command_payload(payload)
    if event_type_str == "SYSTEM_EVENT":
        return _encode_system_payload(payload)
    return payload


def _decode_payload(payload: Any, event_type: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    if event_type == "STATE_EVENT":
        return _decode_state_payload(payload)
    if event_type == "COMMAND_EVENT":
        return _decode_command_payload(payload)
    if event_type == "SYSTEM_EVENT":
        return _decode_system_payload(payload)
    return payload


def _encode_state_payload(payload: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in STATE_PAYLOAD_KEYS.items():
        if key not in payload:
            continue
        value = payload[key]
        if key == "geo" and isinstance(value, dict):
            out[idx] = _encode_geo(value)
        else:
            out[idx] = value
    for key, value in payload.items():
        if key not in STATE_PAYLOAD_KEYS:
            out[key] = value
    return out


def _decode_state_payload(payload: Dict[int, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, idx in STATE_PAYLOAD_KEYS.items():
        if idx not in payload:
            continue
        value = payload[idx]
        if key == "geo" and isinstance(value, dict):
            out[key] = _decode_geo(value)
        else:
            out[key] = value
    for key, value in payload.items():
        if key not in STATE_PAYLOAD_KEYS.values():
            out[str(key)] = value
    return out


def _encode_command_payload(payload: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in COMMAND_PAYLOAD_KEYS.items():
        if key not in payload:
            continue
        value = payload[key]
        if key == "task_type":
            out[idx] = _map_enum(value, TASK_TYPE_MAP)
        elif key == "priority":
            out[idx] = _map_enum(value, PRIORITY_MAP)
        elif key == "valid_from_ts":
            out[idx] = _parse_ts(value)
        elif key == "target_geo" and isinstance(value, dict):
            out[idx] = _encode_geo2d(value)
        else:
            out[idx] = value
    for key, value in payload.items():
        if key not in COMMAND_PAYLOAD_KEYS:
            out[key] = value
    return out


def _decode_command_payload(payload: Dict[int, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, idx in COMMAND_PAYLOAD_KEYS.items():
        if idx not in payload:
            continue
        value = payload[idx]
        if key == "task_type":
            out[key] = _unmap_enum(value, TASK_TYPE_REV)
        elif key == "priority":
            out[key] = _unmap_enum(value, PRIORITY_REV)
        elif key == "valid_from_ts":
            out[key] = _format_ts(value)
        elif key == "target_geo" and isinstance(value, dict):
            out[key] = _decode_geo2d(value)
        else:
            out[key] = value
    for key, value in payload.items():
        if key not in COMMAND_PAYLOAD_KEYS.values():
            out[str(key)] = value
    out.setdefault("requires_deconfliction", True)
    return out


def _encode_system_payload(payload: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    system_type = payload.get("system_type")
    if system_type is not None:
        out[SYSTEM_PAYLOAD_KEYS["system_type"]] = _map_enum(system_type, SYSTEM_TYPE_MAP)
    state = payload.get("state")
    if state is not None:
        out[SYSTEM_PAYLOAD_KEYS["state"]] = _encode_system_state(system_type, state)
    metrics = payload.get("metrics")
    if metrics is not None:
        out[SYSTEM_PAYLOAD_KEYS["metrics"]] = _encode_metrics(system_type, metrics)
    for key, value in payload.items():
        if key not in SYSTEM_PAYLOAD_KEYS:
            out[key] = value
    return out


def _decode_system_payload(payload: Dict[int, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    system_type = None
    if SYSTEM_PAYLOAD_KEYS["system_type"] in payload:
        system_type = _unmap_enum(payload.get(SYSTEM_PAYLOAD_KEYS["system_type"]), SYSTEM_TYPE_REV)
        out["system_type"] = system_type
    if SYSTEM_PAYLOAD_KEYS["state"] in payload:
        out["state"] = _decode_system_state(system_type, payload.get(SYSTEM_PAYLOAD_KEYS["state"]))
    if SYSTEM_PAYLOAD_KEYS["metrics"] in payload:
        out["metrics"] = _decode_metrics(system_type, payload.get(SYSTEM_PAYLOAD_KEYS["metrics"]))
    for key, value in payload.items():
        if key not in SYSTEM_PAYLOAD_KEYS.values():
            out[str(key)] = value
    return out


def _encode_geo(geo: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in GEO_KEYS.items():
        if key in geo:
            out[idx] = geo[key]
    return out


def _decode_geo(geo: Dict[int, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, idx in GEO_KEYS.items():
        if idx in geo:
            out[key] = geo[idx]
    return out


def _encode_geo2d(geo: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in GEO2D_KEYS.items():
        if key in geo:
            out[idx] = geo[key]
    return out


def _decode_geo2d(geo: Dict[int, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, idx in GEO2D_KEYS.items():
        if idx in geo:
            out[key] = geo[idx]
    return out


def _encode_metrics(system_type: Any, metrics: Any) -> Any:
    if not isinstance(metrics, dict):
        return metrics
    system_type_str = (
        _unmap_enum(system_type, SYSTEM_TYPE_REV) if isinstance(system_type, int) else system_type
    )
    if system_type_str == "TASK_ACK":
        return _encode_metrics_with_keys(metrics, TASK_ACK_METRICS_KEYS, uuid_keys={"original_event_id"})
    if system_type_str == "LINK_STATUS":
        return _encode_metrics_with_keys(metrics, LINK_STATUS_METRICS_KEYS)
    if system_type_str == "TIME_STATUS":
        return _encode_time_status_metrics(metrics)
    if system_type_str == "SCHEMA_VIOLATION":
        return _encode_metrics_with_keys(
            metrics, SCHEMA_VIOLATION_METRICS_KEYS, uuid_keys={"original_event_id"}
        )
    return metrics


def _decode_metrics(system_type: Any, metrics: Any) -> Any:
    if not isinstance(metrics, dict):
        return metrics
    system_type_str = (
        _unmap_enum(system_type, SYSTEM_TYPE_REV) if isinstance(system_type, int) else system_type
    )
    if system_type_str == "TASK_ACK":
        return _decode_metrics_with_keys(metrics, TASK_ACK_METRICS_KEYS, uuid_keys={"original_event_id"})
    if system_type_str == "LINK_STATUS":
        return _decode_metrics_with_keys(metrics, LINK_STATUS_METRICS_KEYS)
    if system_type_str == "TIME_STATUS":
        return _decode_time_status_metrics(metrics)
    if system_type_str == "SCHEMA_VIOLATION":
        return _decode_metrics_with_keys(
            metrics, SCHEMA_VIOLATION_METRICS_KEYS, uuid_keys={"original_event_id"}
        )
    return metrics


def _encode_metrics_with_keys(
    metrics: Dict[str, Any],
    key_map: Dict[str, int],
    uuid_keys: set[str] | None = None,
) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    uuid_keys = uuid_keys or set()
    for key, value in metrics.items():
        if key in key_map:
            idx = key_map[key]
            if key in uuid_keys:
                out[idx] = _uuid_to_bytes(value)
            elif key == "reason_code":
                out[idx] = _map_enum(value, REASON_CODE_MAP)
            else:
                out[idx] = value
        else:
            out[key] = value
    return out


def _decode_metrics_with_keys(
    metrics: Dict[int, Any],
    key_map: Dict[str, int],
    uuid_keys: set[str] | None = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    uuid_keys = uuid_keys or set()
    reverse = _reverse_map(key_map)
    for key, value in metrics.items():
        if key in reverse:
            name = reverse[key]
            if name in uuid_keys:
                out[name] = _uuid_from_bytes(value)
            elif name == "reason_code":
                out[name] = _unmap_enum(value, REASON_CODE_REV)
            else:
                out[name] = value
        else:
            out[str(key)] = value
    return out


def _encode_time_status_metrics(metrics: Dict[str, Any]) -> Dict[int, Any]:
    out: Dict[int, Any] = {}
    for key, idx in TIME_STATUS_METRICS_KEYS.items():
        if key not in metrics:
            continue
        value = metrics[key]
        if key == "time_source":
            out[idx] = _map_enum(value, TIME_SOURCE_MAP)
        elif key == "sync_state":
            out[idx] = _map_enum(value, SYNC_STATE_MAP)
        elif key == "last_sync_ts":
            out[idx] = _parse_ts(value)
        else:
            out[idx] = value
    for key, value in metrics.items():
        if key not in TIME_STATUS_METRICS_KEYS:
            out[key] = value
    return out


def _decode_time_status_metrics(metrics: Dict[int, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, idx in TIME_STATUS_METRICS_KEYS.items():
        if idx not in metrics:
            continue
        value = metrics[idx]
        if key == "time_source":
            out[key] = _unmap_enum(value, TIME_SOURCE_REV)
        elif key == "sync_state":
            out[key] = _unmap_enum(value, SYNC_STATE_REV)
        elif key == "last_sync_ts":
            out[key] = _format_ts(value)
        else:
            out[key] = value
    for key, value in metrics.items():
        if key not in TIME_STATUS_METRICS_KEYS.values():
            out[str(key)] = value
    return out


def _encode_system_state(system_type: Any, state: Any) -> Any:
    system_type_str = (
        _unmap_enum(system_type, SYSTEM_TYPE_REV) if isinstance(system_type, int) else system_type
    )
    if system_type_str == "TASK_ACK":
        return _map_enum(state, TASK_ACK_STATE_MAP)
    if system_type_str == "LINK_STATUS":
        return _map_enum(state, LINK_STATUS_STATE_MAP)
    return state


def _decode_system_state(system_type: Any, state: Any) -> Any:
    if system_type == "TASK_ACK":
        return _unmap_enum(state, TASK_ACK_STATE_REV)
    if system_type == "LINK_STATUS":
        return _unmap_enum(state, LINK_STATUS_STATE_REV)
    return state


def _map_enum(value: Any, mapping: Dict[str, int]) -> Any:
    if isinstance(value, str) and value in mapping:
        return mapping[value]
    return value


def _unmap_enum(value: Any, mapping: Dict[int, str]) -> Any:
    if isinstance(value, int) and value in mapping:
        return mapping[value]
    return value


def _uuid_to_bytes(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)) and len(value) == 16:
        return bytes(value)
    if isinstance(value, str):
        try:
            return uuid.UUID(value).bytes
        except (ValueError, AttributeError):
            return value
    return value


def _uuid_from_bytes(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)) and len(value) == 16:
        try:
            return str(uuid.UUID(bytes=bytes(value)))
        except (ValueError, AttributeError):
            return value
    return value


def _parse_ts(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        ts = value.strip()
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            return value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    return value


def _format_ts(value: Any) -> Any:
    if isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    return value
