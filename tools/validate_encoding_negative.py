from __future__ import annotations

import argparse
import base64
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
validators_spec = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(validators_spec)
validators_spec.loader.exec_module(validators)

GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
gateway_spec = importlib.util.spec_from_file_location("zmeta_gateway", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(gateway_spec)
gateway_spec.loader.exec_module(gateway)

PROJECTION_PATH = ROOT / "tools" / "validate_projection.py"
projection_spec = importlib.util.spec_from_file_location("zmeta_validate_projection", PROJECTION_PATH)
validate_projection = importlib.util.module_from_spec(projection_spec)
projection_spec.loader.exec_module(validate_projection)

CONVERT_PATH = ROOT / "tools" / "convert_encoding.py"
convert_spec = importlib.util.spec_from_file_location("zmeta_convert_encoding", CONVERT_PATH)
convert_encoding = importlib.util.module_from_spec(convert_spec)
convert_spec.loader.exec_module(convert_encoding)

import zmeta_cbor
import zmeta_compact
import zmeta_proto


FAILURE_CODES = (
    "ENCODE_NEGATIVE_MALFORMED_CBOR",
    "ENCODE_NEGATIVE_MALFORMED_COMPACT",
    "ENCODE_NEGATIVE_UNSUPPORTED_COMPACT_VERSION",
    "ENCODE_NEGATIVE_INVALID_COMPACT_SHAPE",
    "ENCODE_NEGATIVE_INVALID_COMPACT_ENUM",
    "ENCODE_NEGATIVE_INVALID_UUID_BYTES",
    "ENCODE_NEGATIVE_MALFORMED_PROTOBUF",
    "ENCODE_NEGATIVE_UNSUPPORTED_PROTOBUF_WIRE_TYPE",
    "ENCODE_NEGATIVE_INVALID_PROTOBUF_FIELD",
    "ENCODE_NEGATIVE_PROTOBUF_OVERSIZE",
    "ENCODE_NEGATIVE_PAYLOAD_JSON_OVERSIZE",
    "ENCODE_NEGATIVE_PAYLOAD_JSON_TOO_DEEP",
    "ENCODE_NEGATIVE_INVALID_UTF8",
    "ENCODE_NEGATIVE_PAYLOAD_NOT_OBJECT",
    "ENCODE_NEGATIVE_SCHEMA_INVALID_DECODED",
    "ENCODE_NEGATIVE_POLICY_INVALID_DECODED",
    "ENCODE_NEGATIVE_PROJECTION_INVALID_DECODED",
    "ENCODE_NEGATIVE_RESERVED_VOCAB_LEAK",
    "ENCODE_NEGATIVE_V1_1_LEAK_TO_V1_0",
    "ENCODE_NEGATIVE_GATEWAY_ACCEPTED_INVALID",
    "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID",
)

RESERVED_VOCAB = {
    "RADAR",
    "LIDAR",
    "MAGNETIC",
    "SEISMIC",
    "CYBER",
    "SIGINT",
    "PNT_STATUS",
    "MODEL_STATUS",
    "TRUST_STATUS",
    "UAS_IDENTITY",
    "BEHAVIORAL_IDENTITY",
    "RELEASE_LABEL",
    "EMERGENCY_L0_PROFILE",
    "TAKEOFF",
}
V1_1_ONLY_VOCAB = {
    "SENSOR_STATUS",
    "PLATFORM_STATUS",
    "RETURN_TO_BASE",
    "LAND",
    "LOITER",
    "SCAN_RF",
    "TRACK_TARGET",
    "CHANGE_SENSOR_MODE",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ZMeta encoding-negative fixtures.")
    parser.add_argument(
        "--fixtures",
        help="Directory containing compact-must-fail.jsonl, protobuf-must-fail.jsonl, and gateway-must-fail.jsonl.",
    )
    parser.add_argument(
        "--compact",
        help="Compact CBOR must-fail JSONL fixture file.",
    )
    parser.add_argument(
        "--protobuf",
        help="Protobuf must-fail JSONL fixture file.",
    )
    parser.add_argument(
        "--gateway",
        help="Gateway/CLI must-fail JSONL fixture file.",
    )
    parser.add_argument(
        "--context",
        help="Optional encoding-negative context JSONL file.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print failures and final summary.")
    return parser.parse_args()


def iter_jsonl(path: Path | str):
    fixture_path = Path(path)
    if not fixture_path.exists():
        raise FileNotFoundError(f"encoding-negative fixture file not found: {fixture_path}")
    for line_no, line in enumerate(fixture_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        yield line_no, json.loads(line)


def _result(stage: str, code: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"stage": stage, "code": code, "message": message, "details": details or {}}


def _event_id(event: Any) -> str | None:
    if not isinstance(event, dict):
        return None
    event_block = event.get("event", {})
    if not isinstance(event_block, dict):
        return None
    value = event_block.get("event_id")
    return str(value) if value is not None else None


def _event_type(event: Any) -> str | None:
    if not isinstance(event, dict):
        return None
    block = event.get("event", {})
    return str(block.get("event_type")) if isinstance(block, dict) and block.get("event_type") else None


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def _contains_vocab(event: Any, vocab: set[str]) -> bool:
    return any(value in vocab for value in _walk_strings(event))


def _is_event_like(value: Any) -> bool:
    return isinstance(value, dict) and {"event", "source", "payload"}.issubset(value)


def _decode_limits(fixture: dict[str, Any]) -> dict[str, Any]:
    limits = fixture.get("decode_limits", {})
    return dict(limits) if isinstance(limits, dict) else {}


def _map_compact_decode_error(exc: BaseException) -> dict[str, Any]:
    message = str(exc)
    if isinstance(exc, UnicodeDecodeError):
        return _result("decode", "ENCODE_NEGATIVE_MALFORMED_CBOR", message)
    if "Unsupported compact_version" in message:
        return _result("decode", "ENCODE_NEGATIVE_UNSUPPORTED_COMPACT_VERSION", message)
    if "has no attribute" in message or "not subscriptable" in message or "compact shape" in message:
        return _result("decode", "ENCODE_NEGATIVE_INVALID_COMPACT_SHAPE", message)
    if "CBOR" in message or "unexpected end" in message or "indefinite lengths" in message:
        return _result("decode", "ENCODE_NEGATIVE_MALFORMED_CBOR", message)
    return _result("decode", "ENCODE_NEGATIVE_MALFORMED_COMPACT", message)


def _map_proto_decode_error(exc: BaseException) -> dict[str, Any]:
    message = str(exc)
    if isinstance(exc, UnicodeDecodeError):
        return _result("decode", "ENCODE_NEGATIVE_INVALID_UTF8", message)
    if "unsupported protobuf wire type" in message:
        return _result("decode", "ENCODE_NEGATIVE_UNSUPPORTED_PROTOBUF_WIRE_TYPE", message)
    if "field numbers" in message:
        return _result("decode", "ENCODE_NEGATIVE_INVALID_PROTOBUF_FIELD", message)
    if "max_bytes" in message:
        return _result("decode", "ENCODE_NEGATIVE_PROTOBUF_OVERSIZE", message)
    if "max_payload_bytes" in message:
        return _result("decode", "ENCODE_NEGATIVE_PAYLOAD_JSON_OVERSIZE", message)
    if "max_json_depth" in message:
        return _result("decode", "ENCODE_NEGATIVE_PAYLOAD_JSON_TOO_DEEP", message)
    return _result("decode", "ENCODE_NEGATIVE_MALFORMED_PROTOBUF", message)


def decode_bytes(data: bytes, encoding: str, fixture: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    limits = _decode_limits(fixture)
    try:
        if encoding == "compact":
            return zmeta_compact.loads(data, **limits), None
        if encoding in {"proto", "protobuf"}:
            return zmeta_proto.loads(data, **limits), None
        if encoding == "cbor":
            decoded = zmeta_cbor.loads(data, **limits)
            if not _is_event_like(decoded):
                return None, _result(
                    "decode",
                    "ENCODE_NEGATIVE_INVALID_COMPACT_SHAPE",
                    "CBOR input did not decode to a ZMeta event",
                )
            return decoded, None
        if encoding == "auto":
            return convert_encoding.decode_event(data, "auto"), None
    except Exception as exc:
        if encoding == "compact":
            return None, _map_compact_decode_error(exc)
        if encoding in {"proto", "protobuf"}:
            return None, _map_proto_decode_error(exc)
        return None, _result("decode", "ENCODE_NEGATIVE_MALFORMED_CBOR", str(exc))
    return None, _result("decode", "ENCODE_NEGATIVE_MALFORMED_COMPACT", f"unsupported encoding: {encoding}")


def encode_event(event: dict[str, Any], encoding: str) -> bytes:
    if encoding == "compact":
        return zmeta_compact.dumps(event)
    if encoding in {"proto", "protobuf"}:
        return zmeta_proto.dumps(event)
    if encoding == "json":
        return json.dumps(event, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    raise ValueError(f"unsupported generated event encoding: {encoding}")


def _compact_map_for_case(name: str) -> Any:
    v = zmeta_compact
    if name == "compact_unsupported_version":
        return {v.TOP_KEYS["compact_version"]: 99}
    if name == "compact_invalid_shape":
        return [1, 2, 3]
    if name == "compact_invalid_event_type_enum":
        return {
            v.TOP_KEYS["compact_version"]: 1,
            v.TOP_KEYS["event"]: {
                v.EVENT_KEYS["event_id"]: bytes.fromhex("019c2b5cc05270e1b6aa34bf14c8d501"),
                v.EVENT_KEYS["event_type"]: 99,
                v.EVENT_KEYS["event_subtype"]: v.EVENT_SUBTYPE_MAP["TRACK_STATE"],
                v.EVENT_KEYS["ts"]: 1738584000000,
            },
            v.TOP_KEYS["source"]: {
                v.SOURCE_KEYS["platform_id"]: "fusion-node-01",
                v.SOURCE_KEYS["node_role"]: v.NODE_ROLE_MAP["GATEWAY"],
                v.SOURCE_KEYS["producer"]: "fusion-engine",
            },
            v.TOP_KEYS["payload"]: {
                v.STATE_PAYLOAD_KEYS["track_id"]: "TRACK-NEG-501",
                v.STATE_PAYLOAD_KEYS["geo"]: {1: 34.0, 2: -118.0, 3: 100.0},
                v.STATE_PAYLOAD_KEYS["valid_for_ms"]: 1000,
            },
            v.TOP_KEYS["confidence"]: 0.7,
            v.TOP_KEYS["lineage"]: {v.LINEAGE_KEYS["based_on"]: [bytes.fromhex("019c2b5cc05270e1b6aa34bf14c8c501")]},
            v.TOP_KEYS["profile"]: v.PROFILE_MAP["L"],
        }
    if name == "compact_invalid_event_subtype_enum":
        event = _base_state_event("019c2b5c-c052-70e1-b6aa-34bf14c8d502")
        compact = zmeta_compact.encode_event(event)
        compact[v.TOP_KEYS["event"]][v.EVENT_KEYS["event_subtype"]] = 99
        return compact
    if name == "compact_invalid_profile_enum":
        event = _base_state_event("019c2b5c-c052-70e1-b6aa-34bf14c8d503")
        compact = zmeta_compact.encode_event(event)
        compact[v.TOP_KEYS["profile"]] = 99
        return compact
    if name == "compact_invalid_uuid_bytes":
        event = _base_state_event("019c2b5c-c052-70e1-b6aa-34bf14c8d504")
        compact = zmeta_compact.encode_event(event)
        compact[v.TOP_KEYS["event"]][v.EVENT_KEYS["event_id"]] = b"short"
        return compact
    if name == "compact_missing_top_level_maps":
        return {v.TOP_KEYS["compact_version"]: 1, v.TOP_KEYS["profile"]: v.PROFILE_MAP["L"]}
    if name == "compact_non_utc_timestamp":
        event = _base_state_event("019c2b5c-c052-70e1-b6aa-34bf14c8d505")
        compact = zmeta_compact.encode_event(event)
        compact[v.TOP_KEYS["event"]][v.EVENT_KEYS["ts"]] = "2025-02-03T12:00:00"
        return compact
    raise ValueError(f"unknown compact generated case: {name}")


def _proto_bytes_for_case(name: str, fixture: dict[str, Any]) -> bytes:
    if name == "proto_payload_only":
        return b"\x22\x02{}"
    if name == "proto_invalid_utf8_payload":
        return b"\x22\x01\xff"
    if name == "proto_payload_not_object":
        event = copy.deepcopy(fixture["event"])
        return zmeta_proto.dumps(event)
    if name == "proto_oversized_payload":
        event = copy.deepcopy(fixture["event"])
        return zmeta_proto.dumps(event)
    if name == "proto_deep_payload":
        event = copy.deepcopy(fixture["event"])
        return zmeta_proto.dumps(event)
    raise ValueError(f"unknown protobuf generated case: {name}")


def generated_bytes(fixture: dict[str, Any]) -> bytes:
    encoding = fixture.get("encoding")
    name = str(fixture.get("generated_case") or fixture.get("name") or "")
    if encoding == "compact":
        return zmeta_cbor.dumps(_compact_map_for_case(name))
    if encoding in {"proto", "protobuf"}:
        return _proto_bytes_for_case(name, fixture)
    raise ValueError(f"generated input not supported for encoding: {encoding}")


def materialize_bytes(fixture: dict[str, Any]) -> bytes:
    input_kind = fixture.get("input_kind")
    material_encoding = str(fixture.get("actual_encoding") or fixture.get("encoding"))
    if input_kind == "hex":
        return bytes.fromhex(str(fixture.get("bytes_hex", "")))
    if input_kind == "base64":
        return base64.b64decode(str(fixture.get("bytes_b64", "")))
    if input_kind == "event_json":
        return encode_event(copy.deepcopy(fixture["event"]), material_encoding)
    if input_kind == "generated":
        return generated_bytes(fixture)
    raise ValueError(f"unsupported input_kind for bytes: {input_kind}")


def _base_state_event(event_id: str) -> dict[str, Any]:
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": event_id,
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2025-02-03T12:00:00Z",
        },
        "source": {
            "platform_id": "fusion-node-01",
            "node_role": "GATEWAY",
            "producer": "fusion-engine",
        },
        "profile": "L",
        "payload": {
            "track_id": "TRACK-NEG",
            "geo": {"lat": 34.0, "lon": -118.0, "alt_m": 100.0},
            "valid_for_ms": 1000,
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2025-02-03T11:59:59Z",
            },
        },
        "confidence": 0.7,
        "lineage": {"based_on": ["019c2b5c-c052-70e1-b6aa-34bf14c8c501"]},
    }


def _context_events(fixture: dict[str, Any], contexts: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    context = fixture.get("context")
    if context is None:
        return []
    if isinstance(context, str):
        return list(contexts.get(context, []))
    if isinstance(context, dict):
        preload = context.get("preload")
        if isinstance(preload, list):
            return [item for item in preload if isinstance(item, dict)]
        return [context]
    if isinstance(context, list):
        return [item for item in context if isinstance(item, dict)]
    return []


def load_contexts(path: Path | None) -> dict[str, list[dict[str, Any]]]:
    if path is None or not path.exists():
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for _line_no, item in iter_jsonl(path):
        name = item.get("name")
        if not name:
            continue
        preload = item.get("preload", [])
        out[str(name)] = [event for event in preload if isinstance(event, dict)]
    return out


def _schema_specific_code(event: dict[str, Any], encoding: str) -> str:
    event_id = event.get("event", {}).get("event_id") if isinstance(event.get("event"), dict) else None
    if isinstance(event_id, (bytes, bytearray)):
        return "ENCODE_NEGATIVE_INVALID_UUID_BYTES"
    if encoding == "compact":
        event_block = event.get("event", {}) if isinstance(event, dict) else {}
        if any(isinstance(event_block.get(key), int) for key in ("event_type", "event_subtype")):
            return "ENCODE_NEGATIVE_INVALID_COMPACT_ENUM"
        if isinstance(event.get("profile"), int):
            return "ENCODE_NEGATIVE_INVALID_COMPACT_ENUM"
    if "payload" in event and not isinstance(event.get("payload"), dict):
        return "ENCODE_NEGATIVE_PAYLOAD_NOT_OBJECT"
    if str(event.get("zmeta_version")) == "1.0" and _contains_vocab(event, V1_1_ONLY_VOCAB):
        return "ENCODE_NEGATIVE_V1_1_LEAK_TO_V1_0"
    if _contains_vocab(event, RESERVED_VOCAB):
        return "ENCODE_NEGATIVE_RESERVED_VOCAB_LEAK"
    return "ENCODE_NEGATIVE_SCHEMA_INVALID_DECODED"


def _schema_profile_issue(
    event: dict[str, Any],
    encoding: str,
    schema_validator: Any,
    policy: dict[str, Any],
    fixture: dict[str, Any],
) -> dict[str, Any] | None:
    severity_map = policy.get("violation_severities", {})
    ok, violations = validators.validate_schema(event, schema_validator, severity_map)
    if not ok:
        first = violations[0]
        return _result(
            "schema",
            _schema_specific_code(event, encoding),
            f"decoded event failed schema validation: {first.get('message')}",
            details={"original_code": first.get("code"), "original_details": first.get("details", {})},
        )
    profile = str(fixture.get("profile") or event.get("profile") or "H")
    ok, violations = validators.validate_profile(event, profile, policy["profiles"], severity_map)
    if not ok:
        first = violations[0]
        return _result(
            "schema",
            _schema_specific_code(event, encoding),
            f"decoded event failed profile validation: {first.get('code')}",
            details={"original_code": first.get("code"), "profile": profile},
        )
    return None


def _policy_issue(
    event: dict[str, Any],
    schema_validator: Any,
    policy: dict[str, Any],
    fixture: dict[str, Any],
    contexts: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    schema_issue = _schema_profile_issue(event, str(fixture.get("encoding")), schema_validator, policy, fixture)
    if schema_issue:
        return schema_issue

    severity_map = policy.get("violation_severities", {})
    profile = str(fixture.get("profile") or event.get("profile") or "H")
    state = validators.ValidationState()
    for seed in _context_events(fixture, contexts):
        state.record(seed)

    checks = [
        validators.validate_role(event, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map),
        validators.validate_timing_quality(
            event,
            policy["semantics"],
            state=state,
            severity_map=severity_map,
            timing_freshness_policy=policy.get("timing_freshness", {}),
            profile=profile,
        ),
        validators.validate_semantics(event, policy["semantics"], severity_map),
        validators.validate_lineage(
            event,
            policy.get("lineage", {}),
            state=state,
            profile=profile,
            severity_map=severity_map,
        ),
        validators.validate_producer_authority(event, policy.get("producer_authority", {}), severity_map),
        validators.validate_routing(event, policy["routing"], severity_map),
    ]
    for _ok, violations in checks:
        hard = [item for item in violations if item.get("severity") != "warn"]
        if hard:
            first = hard[0]
            return _result(
                "policy",
                "ENCODE_NEGATIVE_POLICY_INVALID_DECODED",
                f"decoded event failed policy validation: {first.get('code')}",
                details={"original_code": first.get("code"), "original_details": first.get("details", {})},
            )
    return _result("accepted", "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID", "decoded event unexpectedly passed policy validation")


def _decode_event_fixture(fixture: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    data = materialize_bytes(fixture)
    return decode_bytes(data, str(fixture.get("encoding")), fixture)


def _evaluate_decoded_fixture(
    fixture: dict[str, Any],
    schema_validator: Any,
    policy: dict[str, Any],
    contexts: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    encoding = str(fixture.get("encoding"))
    event, decode_issue = _decode_event_fixture(fixture)
    if decode_issue:
        return decode_issue
    if event is None:
        return _result("decode", "ENCODE_NEGATIVE_MALFORMED_COMPACT", "decoder returned no event")

    category = fixture.get("category")
    if category == "decode_invalid":
        return _result("accepted", "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID", "decode-invalid fixture unexpectedly decoded")
    if category == "schema_invalid_after_decode":
        issue = _schema_profile_issue(event, encoding, schema_validator, policy, fixture)
        if issue:
            return issue
        return _result("accepted", "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID", "schema-invalid fixture unexpectedly passed validation")
    if category == "policy_invalid_after_decode":
        return _policy_issue(event, schema_validator, policy, fixture, contexts) or _result(
            "accepted",
            "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID",
            "policy-invalid fixture unexpectedly passed validation",
        )
    return _result("accepted", "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID", f"unsupported decoded category: {category}")


def _decode_projection_event(event: dict[str, Any], encoding: str) -> dict[str, Any]:
    return decode_bytes(encode_event(copy.deepcopy(event), encoding), encoding, {})[0]  # type: ignore[index]


def _evaluate_projection_fixture(
    fixture: dict[str, Any],
    schema_validator: Any,
    policy: dict[str, Any],
) -> dict[str, Any]:
    encoding = str(fixture.get("encoding"))
    source = _decode_projection_event(fixture["source"], encoding)
    projected = _decode_projection_event(fixture["projected"], encoding)
    projection_fixture = copy.deepcopy(fixture)
    projection_fixture["source"] = source
    projection_fixture["projected"] = projected
    projection_fixture["roundtrip"] = []
    catalog = validate_projection.load_catalog(ROOT / "conformance" / "profile_projection_field_catalog.yaml")
    issues = validate_projection.compare_projection(projection_fixture, catalog, policy, schema_validator)
    expected = fixture.get("expect_code")
    selected = next((issue for issue in issues if issue.get("code") == expected), issues[0] if issues else None)
    if selected:
        return _result(
            "projection",
            "ENCODE_NEGATIVE_PROJECTION_INVALID_DECODED",
            f"decoded projection pair failed projection validation: {selected.get('code')}",
            details={"original_code": selected.get("code"), "original_details": selected.get("details", {})},
        )
    return _result("accepted", "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID", "projection-invalid fixture unexpectedly passed")


def _gateway_rejected(outputs: list[dict[str, Any]], original_event: dict[str, Any] | None) -> bool:
    original_id = _event_id(original_event)
    if not outputs:
        return True
    first = outputs[0]
    first_type = _event_type(first)
    if first_type == "SYSTEM_EVENT":
        return True
    if original_id and _event_id(first) == original_id:
        return False
    return first_type != _event_type(original_event)


def _evaluate_gateway_fixture(
    fixture: dict[str, Any],
    schema_validator: Any,
    policy: dict[str, Any],
    contexts: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    path = fixture.get("path", "gateway")
    encoding = str(fixture.get("encoding"))
    data = materialize_bytes(fixture)
    decoded, decode_issue = decode_bytes(data, encoding if encoding != "auto" else str(fixture.get("actual_encoding", "auto")), fixture)
    if decode_issue:
        semantic_issue = decode_issue
    else:
        assert decoded is not None
        semantic_issue = _schema_profile_issue(decoded, str(fixture.get("actual_encoding") or encoding), schema_validator, policy, fixture)
        if semantic_issue is None and fixture.get("semantic_stage") == "policy":
            semantic_issue = _policy_issue(decoded, schema_validator, policy, fixture, contexts)
        if semantic_issue is None:
            semantic_issue = _result("accepted", "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID", "decoded fixture unexpectedly passed validation")

    if path == "gateway":
        try:
            outputs = gateway.process_message(
                data,
                schema_validator,
                policy,
                str(fixture.get("profile") or (decoded or {}).get("profile") or "H"),
                gateway.TaskDedupeCache(),
                encoding,
                event_dedupe_cache=gateway.EventDedupeCache(),
                task_ack_dedupe_cache=gateway.TaskAckDedupeCache(),
                timing_state=validators.ValidationState(),
                strict_validation=True,
            )
        except Exception as exc:
            return _result("gateway_cli", semantic_issue["code"], f"gateway rejected invalid input with exception: {exc}")
        if not _gateway_rejected(outputs, decoded):
            return _result(
                "gateway_cli",
                "ENCODE_NEGATIVE_GATEWAY_ACCEPTED_INVALID",
                "gateway accepted invalid decoded input",
                details={"event_id": _event_id(decoded), "outputs": outputs},
            )
        return _result("gateway_cli", semantic_issue["code"], f"gateway rejected invalid input: {semantic_issue['message']}", details=semantic_issue.get("details", {}))

    if path == "convert_validate":
        try:
            converted = convert_encoding.decode_event(data, encoding)
        except Exception as exc:
            if semantic_issue["stage"] == "decode":
                return _result("gateway_cli", semantic_issue["code"], f"convert rejected invalid input: {exc}")
            return _result("gateway_cli", "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID", f"convert failed before expected semantic validation: {exc}")
        issue = _schema_profile_issue(converted, encoding, schema_validator, policy, fixture)
        if issue is None and fixture.get("semantic_stage") == "policy":
            issue = _policy_issue(converted, schema_validator, policy, fixture, contexts)
        if issue is None:
            return _result(
                "gateway_cli",
                "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID",
                "convert path emitted decoded event that passed canonical validation unexpectedly",
            )
        return _result("gateway_cli", issue["code"], f"convert output was rejected by canonical validation: {issue['message']}", details=issue.get("details", {}))

    return _result("gateway_cli", "ENCODE_NEGATIVE_CONVERT_ACCEPTED_INVALID", f"unsupported gateway/CLI path: {path}")


def evaluate_fixture(
    fixture: dict[str, Any],
    schema_validator: Any,
    policy: dict[str, Any],
    contexts: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    category = fixture.get("category")
    if category == "projection_invalid_after_decode":
        return _evaluate_projection_fixture(fixture, schema_validator, policy)
    if category == "gateway_cli_invalid_after_decode":
        return _evaluate_gateway_fixture(fixture, schema_validator, policy, contexts)
    return _evaluate_decoded_fixture(fixture, schema_validator, policy, contexts)


def _case_label(item: dict[str, Any], line_no: int) -> str:
    return str(item.get("name") or f"line-{line_no}")


def _fixture_paths(args: argparse.Namespace) -> tuple[list[Path], Path | None]:
    fixture_paths: list[Path] = []
    context_path = Path(args.context) if args.context else None
    if args.fixtures:
        fixture_dir = Path(args.fixtures)
        fixture_paths.extend(
            [
                fixture_dir / "compact-must-fail.jsonl",
                fixture_dir / "protobuf-must-fail.jsonl",
                fixture_dir / "gateway-must-fail.jsonl",
            ]
        )
        if context_path is None:
            context_path = fixture_dir / "context.jsonl"
    for raw in (args.compact, args.protobuf, args.gateway):
        if raw:
            fixture_paths.append(Path(raw))
    if not fixture_paths:
        fixture_dir = ROOT / "conformance" / "encoding-negative"
        fixture_paths = [
            fixture_dir / "compact-must-fail.jsonl",
            fixture_dir / "protobuf-must-fail.jsonl",
            fixture_dir / "gateway-must-fail.jsonl",
        ]
        context_path = context_path or fixture_dir / "context.jsonl"
    return fixture_paths, context_path


def run(
    *,
    compact_path: Path | str | None = None,
    protobuf_path: Path | str | None = None,
    gateway_path: Path | str | None = None,
    fixtures_dir: Path | str | None = None,
    context_path: Path | str | None = None,
    quiet: bool = False,
) -> int:
    if fixtures_dir:
        fixture_dir = Path(fixtures_dir)
        paths = [
            fixture_dir / "compact-must-fail.jsonl",
            fixture_dir / "protobuf-must-fail.jsonl",
            fixture_dir / "gateway-must-fail.jsonl",
        ]
        resolved_context_path = Path(context_path) if context_path else fixture_dir / "context.jsonl"
    else:
        paths = [
            Path(compact_path) if compact_path else ROOT / "conformance" / "encoding-negative" / "compact-must-fail.jsonl",
            Path(protobuf_path) if protobuf_path else ROOT / "conformance" / "encoding-negative" / "protobuf-must-fail.jsonl",
            Path(gateway_path) if gateway_path else ROOT / "conformance" / "encoding-negative" / "gateway-must-fail.jsonl",
        ]
        resolved_context_path = Path(context_path) if context_path else ROOT / "conformance" / "encoding-negative" / "context.jsonl"

    schema_validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")
    policy = validators.load_policy(ROOT / "policy")
    contexts = load_contexts(resolved_context_path)

    failures = 0
    passed = 0
    for path in paths:
        for line_no, fixture in iter_jsonl(path):
            label = _case_label(fixture, line_no)
            expected_stage = fixture.get("expected_stage")
            expected_code = fixture.get("expect_code")
            result = evaluate_fixture(fixture, schema_validator, policy, contexts)
            if result.get("stage") != expected_stage or result.get("code") != expected_code:
                failures += 1
                print(
                    f"FAIL name={label} expected={expected_stage}/{expected_code} "
                    f"got={result.get('stage')}/{result.get('code')}"
                )
                print(f"  {result.get('message')}")
            else:
                passed += 1
                if not quiet:
                    print(f"PASS name={label} expected={expected_stage}/{expected_code}")

    if failures:
        print(f"encoding negative failed total={passed} failures={failures}")
        return 1
    print(f"encoding negative ok total={passed}")
    return 0


def main() -> None:
    args = parse_args()
    paths, context_path = _fixture_paths(args)
    if args.fixtures:
        result = run(fixtures_dir=args.fixtures, context_path=context_path, quiet=args.quiet)
    else:
        compact = args.compact or str(paths[0])
        protobuf = args.protobuf or str(paths[1])
        gateway_file = args.gateway or str(paths[2])
        result = run(
            compact_path=compact,
            protobuf_path=protobuf,
            gateway_path=gateway_file,
            context_path=context_path,
            quiet=args.quiet,
        )
    raise SystemExit(result)


if __name__ == "__main__":
    main()
