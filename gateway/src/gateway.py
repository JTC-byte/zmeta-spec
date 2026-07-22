import argparse
import hashlib
import json
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import cbor2
except ImportError:  # pragma: no cover - optional dependency
    cbor2 = None

MODULE_DIR = Path(__file__).resolve().parent
ROOT_DIR = MODULE_DIR.parents[1]
for path in (MODULE_DIR, ROOT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    import zmeta_cbor
except ImportError:  # pragma: no cover - optional dependency
    zmeta_cbor = None

try:
    import zmeta_compact
except ImportError:  # pragma: no cover - optional dependency
    zmeta_compact = None

try:
    import zmeta_proto
except ImportError:  # pragma: no cover - optional dependency
    zmeta_proto = None

from validators import (
    ValidationState,
    apply_external_promotion_policy_action,
    apply_timing_freshness_degradation,
    load_policy,
    load_schema,
    validate_lineage,
    validate_profile,
    validate_producer_authority,
    validate_role,
    validate_routing,
    validate_schema,
    validate_semantics,
    validate_timing_quality,
)

from adapters.egress.cot.zmeta_to_cot import zmeta_to_cot
from zmeta_uuid import uuid7

PROFILE_CHOICES = {"L", "M", "H"}
INPUT_ENCODING_CHOICES = {"json", "cbor", "compact", "proto", "auto"}
OUTPUT_ENCODING_CHOICES = {"json", "cbor", "compact", "proto"}
DEFAULT_STAMP_PROFILE_PROFILES = ["L", "M", "H"]
DEFAULT_STAMP_TIMING_PROFILES = ["L", "M", "H"]
DEFAULT_STRIP_OPTIONAL_FIELDS = [
    "source.sensor_id",
    "source.sw_version",
    "payload.data_ref",
    "payload.data_refs",
]
DEFAULT_STRIP_OPTIONAL_FIELDS_PROFILES = ["L", "M", "H"]
# Paths that strip_optional_fields must never remove, in whole or in part.
# Accepted-risk labels and external-promotion evidence exist so downstream
# consumers can filter by explicit policy decision; silently deleting them
# turns degraded/externally-promoted data back into clean-looking data
# (laundering). docs/zmeta_change_governance.md forbids silently stripping
# accepted-risk labels, use limits, or external-promotion evidence.
PROTECTED_STRIP_PATH_PREFIXES = [
    "payload.extensions.risk_adjudication",
    "payload.extensions.external_promotion",
]
DEFAULT_METRICS_INTERVAL_SEC = 30
DEFAULT_RATE_LIMIT_PER_SEC = 0
DEFAULT_RATE_LIMIT_PRODUCER_PER_SEC = 0
DEFAULT_METRICS_LOG_MAX_BYTES = 5_000_000
DEFAULT_METRICS_LOG_BACKUPS = 3
# Warn (metrics/log only) when an outgoing UDP datagram exceeds this many
# bytes. 0 disables the check. This is observability only: oversized
# datagrams are still sent unchanged (they may IP-fragment or be dropped by
# the network; UDP sends above ~65507 bytes fail at the socket layer).
DEFAULT_WARN_DATAGRAM_BYTES = 0


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_file(path: Path) -> bytes:
    hasher = hashlib.sha256()
    rel = path.name
    hasher.update(rel.encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(path.read_bytes())
    return hasher.digest()


def _hash_dir(dir_path: Path) -> bytes:
    hasher = hashlib.sha256()
    for path in sorted(dir_path.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(dir_path).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.digest()


def compute_contract_hash(schema_path: Path, policy_dir: Path, semantics_path: Path | None = None) -> dict:
    schema_digest = _hash_file(schema_path)
    policy_digest = _hash_dir(policy_dir)
    schema_hash = hashlib.sha256(schema_digest).hexdigest()
    policy_hash = hashlib.sha256(policy_digest).hexdigest()
    semantics_hash = None
    if semantics_path and semantics_path.is_file():
        semantics_hash = hashlib.sha256(_hash_file(semantics_path)).hexdigest()
    contract_hasher = hashlib.sha256()
    contract_hasher.update(schema_hash.encode("utf-8"))
    contract_hasher.update(policy_hash.encode("utf-8"))
    if semantics_hash:
        contract_hasher.update(semantics_hash.encode("utf-8"))
    contract_hash = contract_hasher.hexdigest()
    hashes = {
        "schema_hash": schema_hash,
        "policy_hash": policy_hash,
        "contract_hash": contract_hash,
    }
    if semantics_hash:
        hashes["semantics_hash"] = semantics_hash
    return hashes


class TaskDedupeCache:
    def __init__(self):
        self._cache = {}

    def _purge(self, now):
        expired = [key for key, expiry in self._cache.items() if expiry <= now]
        for key in expired:
            del self._cache[key]

    def check_and_set(self, task_id, ttl_ms):
        now = time.monotonic()
        self._purge(now)
        expiry = self._cache.get(task_id)
        if expiry and expiry > now:
            return True
        self._cache[task_id] = now + (ttl_ms / 1000.0)
        return False


class EventDedupeCache:
    def __init__(self, ttl_ms=300000):
        self.ttl_ms = int(ttl_ms)
        self._cache = {}

    def _purge(self, now):
        expired = [key for key, expiry in self._cache.items() if expiry <= now]
        for key in expired:
            del self._cache[key]

    def check_and_set(self, event_id):
        if not event_id:
            return False
        now = time.monotonic()
        self._purge(now)
        expiry = self._cache.get(event_id)
        if expiry and expiry > now:
            return True
        self._cache[event_id] = now + (self.ttl_ms / 1000.0)
        return False


class TaskAckDedupeCache:
    def __init__(self, ttl_ms=300000):
        self.ttl_ms = int(ttl_ms)
        self._cache = {}

    def _purge(self, now):
        expired = [key for key, expiry in self._cache.items() if expiry <= now]
        for key in expired:
            del self._cache[key]

    def check_and_set(self, event):
        payload = event.get("payload", {}) if isinstance(event, dict) else {}
        if payload.get("system_type") != "TASK_ACK":
            return False
        metrics = payload.get("metrics", {})
        if not isinstance(metrics, dict):
            return False
        key = (metrics.get("task_id"), metrics.get("original_event_id"), payload.get("state"))
        if not all(key):
            return False
        now = time.monotonic()
        self._purge(now)
        expiry = self._cache.get(key)
        if expiry and expiry > now:
            return True
        self._cache[key] = now + (self.ttl_ms / 1000.0)
        return False


class GatewayMetrics:
    def __init__(self, interval_sec=DEFAULT_METRICS_INTERVAL_SEC, emit=True, logger=None, contract_hash=None):
        self.emit = bool(emit)
        try:
            interval = int(interval_sec)
        except (TypeError, ValueError):
            interval = DEFAULT_METRICS_INTERVAL_SEC
        if interval <= 0:
            self.emit = False
        self.interval_sec = interval if interval > 0 else DEFAULT_METRICS_INTERVAL_SEC
        self.last_log = time.monotonic()
        self.logger = logger
        self.contract_hash = contract_hash
        self.total = self._new_window()
        self.window = self._new_window()

    @staticmethod
    def _new_window():
        return {
            "received": 0,
            "bytes": 0,
            "forwarded": 0,
            "cot": 0,
            "cot_skipped": 0,
            "timing_quality_source": 0,
            "timing_quality_fallback": 0,
            "drops": 0,
            "duplicates": 0,
            "violations": 0,
            "warnings": 0,
            "oversize_datagrams": 0,
            "send_failures": 0,
            "drop_reasons": {},
            "cot_skip_reasons": {},
            "timing_quality_modes": {},
            "violation_codes": {},
            "warning_codes": {},
            "oversize_datagram_kinds": {},
            "send_failure_kinds": {},
        }

    def _bump(self, key, inc=1):
        self.window[key] += inc
        self.total[key] += inc

    def _bump_map(self, key, code, inc=1):
        window_map = self.window[key]
        total_map = self.total[key]
        window_map[code] = window_map.get(code, 0) + inc
        total_map[code] = total_map.get(code, 0) + inc

    def record_received(self, size):
        self._bump("received", 1)
        self._bump("bytes", size)

    def record_forwarded(self, count=1):
        self._bump("forwarded", count)

    def record_cot(self, count=1):
        self._bump("cot", count)

    def record_cot_skipped(self, reason, event_id=None, producer=None):
        self._bump("cot_skipped", 1)
        self._bump_map("cot_skip_reasons", reason)
        payload = {"reason": reason}
        if event_id:
            payload["event_id"] = event_id
        if producer:
            payload["producer"] = producer
        self._log_event("cot_skipped", payload)

    def record_timing_quality(self, time_source, sync_state, event_id=None, producer=None):
        mode = f"{time_source or 'UNKNOWN'}/{sync_state or 'UNKNOWN'}"
        fallback = time_source == "UNKNOWN" and sync_state == "UNSYNCED"
        self._bump("timing_quality_fallback" if fallback else "timing_quality_source", 1)
        self._bump_map("timing_quality_modes", mode)
        payload = {"time_source": time_source, "sync_state": sync_state, "fallback": fallback}
        if event_id:
            payload["event_id"] = event_id
        if producer:
            payload["producer"] = producer
        self._log_event("timing_quality", payload)

    def _log_event(self, kind, payload):
        if not self.logger:
            return
        record = {"type": kind, "ts": utc_now(), **payload}
        if self.contract_hash:
            record["contract_hash"] = self.contract_hash
        self.logger.write(record)

    def record_drop(self, reason, producer=None):
        self._bump("drops", 1)
        self._bump_map("drop_reasons", reason)
        payload = {"reason": reason}
        if producer:
            payload["producer"] = producer
        self._log_event("drop", payload)

    def record_violation(self, code, event_id=None, producer=None):
        self._bump("violations", 1)
        self._bump_map("violation_codes", code)
        payload = {"code": code}
        if event_id:
            payload["event_id"] = event_id
        if producer:
            payload["producer"] = producer
        self._log_event("violation", payload)

    def record_warning(self, code, event_id=None, producer=None):
        self._bump("warnings", 1)
        self._bump_map("warning_codes", code)
        payload = {"code": code}
        if event_id:
            payload["event_id"] = event_id
        if producer:
            payload["producer"] = producer
        self._log_event("warning", payload)

    def record_oversize_datagram(self, size, threshold, kind, event_id=None, producer=None):
        self._bump("oversize_datagrams", 1)
        self._bump_map("oversize_datagram_kinds", kind)
        payload = {"size_bytes": size, "threshold_bytes": threshold, "kind": kind}
        if event_id:
            payload["event_id"] = event_id
        if producer:
            payload["producer"] = producer
        self._log_event("oversize_datagram", payload)

    def record_send_failure(self, kind, error, size, event_id=None, producer=None):
        self._bump("send_failures", 1)
        self._bump_map("send_failure_kinds", kind)
        payload = {"kind": kind, "error": error, "size_bytes": size}
        if event_id:
            payload["event_id"] = event_id
        if producer:
            payload["producer"] = producer
        self._log_event("send_failure", payload)

    def record_duplicate(self, task_id=None):
        self._bump("duplicates", 1)
        payload = {}
        if task_id:
            payload["task_id"] = task_id
        self._log_event("duplicate", payload)

    def maybe_log(self):
        if not self.emit:
            return
        now = time.monotonic()
        if now - self.last_log < self.interval_sec:
            return
        window = self.window
        print(
            "metrics "
            f"interval={self.interval_sec}s recv={window['received']} "
            f"bytes={window['bytes']} fwd={window['forwarded']} cot={window['cot']} "
            f"cot_skipped={window['cot_skipped']} "
            f"timing_source={window['timing_quality_source']} "
            f"timing_fallback={window['timing_quality_fallback']} "
            f"drops={window['drops']} violations={window['violations']} "
            f"warnings={window['warnings']} duplicates={window['duplicates']}"
        )
        if window["drop_reasons"]:
            reasons = ", ".join(f"{key}:{value}" for key, value in sorted(window["drop_reasons"].items()))
            print(f"metrics drop_reasons={reasons}")
        if window["cot_skip_reasons"]:
            reasons = ", ".join(
                f"{key}:{value}" for key, value in sorted(window["cot_skip_reasons"].items())
            )
            print(f"metrics cot_skip_reasons={reasons}")
        if window["timing_quality_modes"]:
            reasons = ", ".join(
                f"{key}:{value}" for key, value in sorted(window["timing_quality_modes"].items())
            )
            print(f"metrics timing_quality_modes={reasons}")
        if window["violation_codes"]:
            reasons = ", ".join(
                f"{key}:{value}" for key, value in sorted(window["violation_codes"].items())
            )
            print(f"metrics violation_codes={reasons}")
        if window["warning_codes"]:
            reasons = ", ".join(
                f"{key}:{value}" for key, value in sorted(window["warning_codes"].items())
            )
            print(f"metrics warning_codes={reasons}")
        if window["oversize_datagrams"]:
            kinds = ", ".join(
                f"{key}:{value}"
                for key, value in sorted(window["oversize_datagram_kinds"].items())
            )
            print(
                f"metrics oversize_datagrams={window['oversize_datagrams']} kinds={kinds}"
            )
        if window["send_failures"]:
            kinds = ", ".join(
                f"{key}:{value}"
                for key, value in sorted(window["send_failure_kinds"].items())
            )
            print(f"metrics send_failures={window['send_failures']} kinds={kinds}")
        self._log_event(
            "metrics",
            {
                "interval_sec": self.interval_sec,
                "received": window["received"],
                "bytes": window["bytes"],
                "forwarded": window["forwarded"],
                "cot": window["cot"],
                "cot_skipped": window["cot_skipped"],
                "timing_quality_source": window["timing_quality_source"],
                "timing_quality_fallback": window["timing_quality_fallback"],
                "drops": window["drops"],
                "violations": window["violations"],
                "warnings": window["warnings"],
                "duplicates": window["duplicates"],
                "oversize_datagrams": window["oversize_datagrams"],
                "send_failures": window["send_failures"],
                "drop_reasons": window["drop_reasons"],
                "cot_skip_reasons": window["cot_skip_reasons"],
                "timing_quality_modes": window["timing_quality_modes"],
                "violation_codes": window["violation_codes"],
                "warning_codes": window["warning_codes"],
                "oversize_datagram_kinds": window["oversize_datagram_kinds"],
                "send_failure_kinds": window["send_failure_kinds"],
            },
        )
        self.window = self._new_window()
        self.last_log = now


class MetricsLogger:
    def __init__(self, path, max_bytes=DEFAULT_METRICS_LOG_MAX_BYTES, backups=DEFAULT_METRICS_LOG_BACKUPS):
        self.path = Path(path)
        self.max_bytes = max(0, int(max_bytes)) if max_bytes is not None else 0
        self.backups = max(0, int(backups)) if backups is not None else 0

    def _rotate_if_needed(self):
        if not self.path.exists():
            return
        if self.max_bytes <= 0:
            return
        if self.path.stat().st_size < self.max_bytes:
            return
        if self.backups <= 0:
            self.path.write_text("", encoding="utf-8")
            return
        for idx in range(self.backups - 1, 0, -1):
            src = self.path.with_suffix(self.path.suffix + f".{idx}")
            dst = self.path.with_suffix(self.path.suffix + f".{idx + 1}")
            if src.exists():
                src.replace(dst)
        first = self.path.with_suffix(self.path.suffix + ".1")
        self.path.replace(first)

    def write(self, record):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._rotate_if_needed()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")


class ProducerRateLimiter:
    def __init__(self, limit_per_sec):
        try:
            limit = int(limit_per_sec)
        except (TypeError, ValueError):
            limit = 0
        self.limit = max(0, limit)
        self.counters = {}
        self._window = None

    def allow(self, producer):
        if self.limit <= 0:
            return True
        key = producer or "UNKNOWN"
        now_window = int(time.monotonic())
        if now_window != self._window:
            # Counts from previous one-second windows can never influence
            # another decision; drop them so the per-producer map stays
            # bounded by the number of producers seen in the current window.
            self._window = now_window
            self.counters.clear()
        count = self.counters.get(key, 0)
        if count >= self.limit:
            return False
        self.counters[key] = count + 1
        return True


def _check_datagram_size(metrics, payload_len, threshold, kind, event_id=None, producer=None):
    """Record an oversize-datagram warning; never alters send behavior.

    Returns True when a warning was recorded. Disabled when threshold is
    falsy/non-positive or when no metrics sink exists.
    """
    if not metrics or not threshold or threshold <= 0:
        return False
    if payload_len <= threshold:
        return False
    metrics.record_oversize_datagram(
        payload_len, threshold, kind, event_id=event_id, producer=producer
    )
    return True


def _send_datagram(sock, payload, addr, *, metrics=None, kind="forward", event_id=None, producer=None):
    """Send one UDP datagram; drop with an explicit diagnostic instead of crashing.

    UDP sends raise OSError for payloads above the ~65507-byte datagram limit
    and for transient socket errors. The gateway main loop must survive both:
    the datagram is dropped, the failure is counted and logged as a
    send_failure diagnostic, and the caller's success accounting only runs
    when the send actually happened. Nothing is truncated or retried, so no
    event is ever silently altered.
    """
    try:
        sock.sendto(payload, addr)
        return True
    except OSError as exc:
        if metrics:
            metrics.record_send_failure(
                kind, str(exc), len(payload), event_id=event_id, producer=producer
            )
        else:
            print(
                f"send failure kind={kind} bytes={len(payload)} error={exc}",
                file=sys.stderr,
            )
        return False


def ttl_ms_from_payload(payload):
    ttl_ms = payload.get("valid_for_ms")
    try:
        ttl_ms = int(ttl_ms)
    except (TypeError, ValueError):
        ttl_ms = 60000
    if ttl_ms <= 0:
        ttl_ms = 60000
    return min(ttl_ms, 300000)


def _resolve_relative_path(base_dir, value):
    path = Path(value)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path


def load_config(path):
    if not path:
        return {}
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"config not found: {config_path}")
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    base_dir = config_path.resolve().parent
    if "schema_path" in data:
        data["schema_path"] = _resolve_relative_path(base_dir, data["schema_path"])
    if "policy_dir" in data:
        data["policy_dir"] = _resolve_relative_path(base_dir, data["policy_dir"])
    return data


def _apply_address(config_value, host_key, port_key, settings):
    if not isinstance(config_value, dict):
        return
    host = config_value.get("host")
    port = config_value.get("port")
    if host:
        settings[host_key] = host
    if port is not None:
        settings[port_key] = port


def _validate_port(port, label):
    try:
        value = int(port)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if not (1 <= value <= 65535):
        raise ValueError(f"{label} must be between 1 and 65535")
    return value


def _normalize_int(value, label, allow_zero=True):
    if value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if number < 0 or (number == 0 and not allow_zero):
        raise ValueError(f"{label} must be positive")
    return number


def _load_jsonl(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        yield json.loads(line)


def run_self_test(root: Path, settings: dict):
    print("self-test: schema + policy")
    _ = load_schema(settings["schema_path"])
    _ = load_policy(settings["policy_dir"])

    examples_path = root / "tools" / "validate_examples.py"
    if examples_path.exists():
        print("self-test: validate examples")
        result = subprocess.call([sys.executable, str(examples_path), "--require-all", "--strict"])
        if result != 0:
            raise SystemExit("self-test failed: examples validation failed")

    conformance_path = root / "tools" / "validate_conformance.py"
    if conformance_path.exists():
        print("self-test: conformance pack")
        result = subprocess.call([sys.executable, str(conformance_path), "--strict"])
        if result != 0:
            raise SystemExit("self-test failed: conformance validation failed")

    roundtrip_path = root / "examples" / "encoding-roundtrip.jsonl"
    if roundtrip_path.exists():
        print("self-test: encoding round-trip")
        for event in _load_jsonl(roundtrip_path):
            encoded = _encode_cbor(event)
            decoded = _decode_cbor(encoded)
            if decoded != event:
                raise SystemExit("self-test failed: CBOR round-trip mismatch")
            if zmeta_compact is None:
                raise SystemExit("self-test failed: compact support missing")
            compact = zmeta_compact.dumps(event)
            expanded = zmeta_compact.loads(compact)
            if expanded != event:
                raise SystemExit("self-test failed: compact round-trip mismatch")
            if zmeta_proto is None:
                raise SystemExit("self-test failed: protobuf support missing")
            proto = zmeta_proto.dumps(event)
            proto_expanded = zmeta_proto.loads(proto)
            if proto_expanded != event:
                raise SystemExit("self-test failed: protobuf round-trip mismatch")

    print("self-test: ok")


def _normalize_profiles(value, fallback):
    if value is None:
        return list(fallback)
    if isinstance(value, str):
        tokens = [token.strip().upper() for token in value.split(",") if token.strip()]
        return tokens or list(fallback)
    if isinstance(value, list):
        tokens = [str(token).strip().upper() for token in value if str(token).strip()]
        return tokens or list(fallback)
    return list(fallback)


def _normalize_field_list(value, fallback):
    if value is None:
        return list(fallback)
    if isinstance(value, str):
        tokens = [token.strip() for token in value.split(",") if token.strip()]
        return tokens or list(fallback)
    if isinstance(value, list):
        tokens = [str(token).strip() for token in value if str(token).strip()]
        return tokens or list(fallback)
    return list(fallback)


def _reject_protected_strip_paths(fields):
    # Fail fast at config load: stripping an accepted-risk label or
    # external-promotion evidence path (or anything nested under one) would
    # silently launder degraded data (docs/zmeta_change_governance.md
    # no-silent-strip rule). Comparison is segment-wise so a protected prefix
    # matches itself and its children, but not lookalike sibling names.
    for path in fields:
        parts = [part for part in str(path).split(".") if part]
        for prefix in PROTECTED_STRIP_PATH_PREFIXES:
            prefix_parts = prefix.split(".")
            if parts[: len(prefix_parts)] == prefix_parts:
                raise ValueError(
                    f"strip_optional_fields entry '{path}' is protected: "
                    f"'{prefix}' carries accepted-risk labels or promotion "
                    "evidence and must not be silently stripped "
                    "(docs/zmeta_change_governance.md no-laundering rule)"
                )


def _should_apply(profile, enabled, profiles):
    if not enabled:
        return False
    if not profiles:
        return True
    return profile in profiles


def _require_cbor():
    if cbor2 is None and zmeta_cbor is None:
        raise SystemExit("CBOR support requires cbor2 or zmeta_cbor.")


def _require_compact():
    if zmeta_compact is None:
        raise SystemExit("Compact encoding requires zmeta_compact.")


# Exception tuple for except-clauses that must not reference zmeta_compact
# when the optional module is absent (an empty tuple matches nothing).
_COMPACT_UNREPRESENTABLE = (
    (zmeta_compact.CompactUnrepresentableError,) if zmeta_compact is not None else ()
)


def _require_proto():
    if zmeta_proto is None:
        raise SystemExit("Protobuf encoding requires zmeta_proto.")


def _cbor_self_test():
    _require_cbor()
    sample = {
        "a": 1,
        "b": -1,
        "c": 1.5,
        "d": "x",
        "e": [1, 2],
        "f": True,
        "g": None,
    }
    encoded = _encode_cbor(sample)
    decoded = _decode_cbor(encoded)
    if decoded != sample:
        raise SystemExit("CBOR self-test failed: round-trip mismatch")
    if _encode_cbor({"b": 1, "a": 2}) != _encode_cbor({"a": 2, "b": 1}):
        raise SystemExit("CBOR self-test failed: non-deterministic map encoding")


def _decode_cbor(message):
    _require_cbor()
    if zmeta_cbor is not None:
        return zmeta_cbor.loads(message)
    return cbor2.loads(message)


def _encode_cbor(obj):
    _require_cbor()
    if zmeta_cbor is not None:
        return zmeta_cbor.dumps(obj)
    return cbor2.dumps(obj, canonical=True)


def _looks_like_event(obj):
    return isinstance(obj, dict) and {"event", "source", "payload"}.issubset(obj)


def _decode_message(message, input_encoding):
    if input_encoding == "json":
        text = message.decode("utf-8")
        return json.loads(text)
    if input_encoding == "cbor":
        return _decode_cbor(message)
    if input_encoding == "compact":
        _require_compact()
        compact_obj = _decode_cbor(message)
        return zmeta_compact.decode_event(compact_obj)
    if input_encoding == "proto":
        _require_proto()
        return zmeta_proto.loads(message)
    if input_encoding == "auto":
        prefix = message.lstrip()[:1]
        if prefix in (b"{", b"["):
            try:
                text = message.decode("utf-8")
                return json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError):
                decoded = _decode_cbor(message)
                if zmeta_compact is not None and zmeta_compact.is_compact(decoded):
                    return zmeta_compact.decode_event(decoded)
                if _looks_like_event(decoded):
                    return decoded
        try:
            decoded = _decode_cbor(message)
            if zmeta_compact is not None and zmeta_compact.is_compact(decoded):
                return zmeta_compact.decode_event(decoded)
            if _looks_like_event(decoded):
                return decoded
        except Exception:
            pass
        if zmeta_proto is not None:
            try:
                return zmeta_proto.loads(message)
            except Exception:
                pass
        text = message.decode("utf-8")
        return json.loads(text)
    raise ValueError(f"unsupported input encoding: {input_encoding}")


def _encode_message(event, output_encoding):
    if output_encoding == "json":
        return json.dumps(event, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    if output_encoding == "cbor":
        return _encode_cbor(event)
    if output_encoding == "compact":
        _require_compact()
        zmeta_compact.verify_representable(event)
        compact_obj = zmeta_compact.encode_event(event)
        return _encode_cbor(compact_obj)
    if output_encoding == "proto":
        _require_proto()
        return zmeta_proto.dumps(event)
    raise ValueError(f"unsupported output encoding: {output_encoding}")


def _strip_optional_fields(event, fields):
    if not fields:
        return
    for path in fields:
        parts = [part for part in str(path).split(".") if part]
        if not parts:
            continue
        target = event
        for key in parts[:-1]:
            if not isinstance(target, dict):
                target = None
                break
            target = target.get(key)
        if isinstance(target, dict):
            target.pop(parts[-1], None)


def _source_key(event):
    source = event.get("source", {}) if isinstance(event, dict) else {}
    return (
        str(source.get("platform_id") or "UNKNOWN"),
        str(source.get("producer") or "UNKNOWN"),
        str(source.get("node_role") or "UNKNOWN"),
    )


def _event_timing_quality(event):
    if not isinstance(event, dict):
        return None
    payload = event.get("payload", {})
    if not isinstance(payload, dict):
        return None
    candidates = [
        payload.get("timing_quality"),
        payload.get("quality", {}).get("timing_quality")
        if isinstance(payload.get("quality"), dict)
        else None,
        payload.get("quality"),
    ]
    for timing in candidates:
        if not isinstance(timing, dict):
            continue
        if {"time_source", "sync_state", "est_error_ms", "last_sync_ts"}.issubset(timing):
            return timing
    return None


def _config_list_values(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _timing_use_limits(timing_freshness_policy, mode):
    if not isinstance(timing_freshness_policy, dict):
        return {}
    limits = timing_freshness_policy.get("use_limits", {})
    if not isinstance(limits, dict):
        return {}
    mode_limits = limits.get(mode, {})
    return mode_limits if isinstance(mode_limits, dict) else {}


def _append_gateway_risk_adjudication(event, record):
    payload = event.get("payload") if isinstance(event, dict) else None
    if not isinstance(payload, dict) or not isinstance(record, dict):
        return False
    extensions = payload.get("extensions")
    if not isinstance(extensions, dict):
        extensions = {}
        payload["extensions"] = extensions
    records = extensions.get("risk_adjudication")
    if not isinstance(records, list):
        records = []
        extensions["risk_adjudication"] = records
    records.append(record)
    return True


def _apply_failure_mode_degradation(
    event, failure_modes, timing_state, timing_freshness_policy=None
):
    if not failure_modes or not isinstance(event, dict):
        return False
    if event.get("event", {}).get("event_type") != "STATE_EVENT":
        return False
    timing_loss = failure_modes.get("timing_loss", {})
    if not isinstance(timing_loss, dict) or not timing_loss.get("enabled", False):
        return False
    latest = getattr(timing_state, "latest_timing", {}).get(_source_key(event)) if timing_state else None
    if timing_state and hasattr(timing_state, "get_timing"):
        _key, latest = timing_state.get_timing(event)
    if not latest or latest.get("sync_state") != "UNSYNCED":
        return False
    try:
        factor = float(timing_loss.get("confidence_reduction_factor", 2.0))
    except (TypeError, ValueError):
        factor = 2.0
    if factor <= 0:
        return False
    confidence = event.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return False

    event["confidence"] = max(0.0, min(1.0, confidence / factor))
    limits = _timing_use_limits(timing_freshness_policy, "degrade")
    record = {
        "risk_dimension": "timing",
        "reason_code": "TIMING_STATUS_UNSYNCED",
        "policy_mode": "degrade",
        "policy_decision": "DEGRADED_ACCEPT",
        "policy_ref": "gateway.failure_modes.timing_loss",
        "effects": {"confidence_reduction_factor": factor},
    }
    allowed_uses = _config_list_values(limits.get("allowed_uses"))
    prohibited_uses = _config_list_values(limits.get("prohibited_uses"))
    if allowed_uses:
        record["allowed_uses"] = allowed_uses
    if prohibited_uses:
        record["prohibited_uses"] = prohibited_uses
    source = event.get("source", {})
    if isinstance(source, dict):
        record["producer"] = source.get("producer")
    if isinstance(latest, dict):
        record["timing_status_ts"] = latest.get("_event_ts")
        record["sync_state"] = latest.get("sync_state")
    return _append_gateway_risk_adjudication(event, record)


def _cot_skip_reason(event):
    if not isinstance(event, dict):
        return None
    event_block = event.get("event", {})
    if not isinstance(event_block, dict) or event_block.get("event_type") != "STATE_EVENT":
        return None
    payload = event.get("payload", {})
    if not isinstance(payload, dict):
        return "PAYLOAD_INVALID"
    if not payload.get("track_id"):
        return "MISSING_TRACK_ID"
    geo = payload.get("geo")
    if not isinstance(geo, dict) or geo.get("lat") is None or geo.get("lon") is None:
        return "MISSING_GEO"
    return "UNCONVERTIBLE"


def validate_outgoing_event(event, validator, policy, profile):
    severity_map = policy.get("violation_severities", {})
    checks = []
    checks.extend(validate_schema(event, validator, severity_map)[1])
    if checks:
        return checks
    checks.extend(
        validate_role(event, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map)[1]
    )
    checks.extend(validate_profile(event, profile, policy["profiles"], severity_map)[1])
    checks.extend(validate_semantics(event, policy["semantics"], severity_map)[1])
    checks.extend(
        validate_lineage(
            event,
            policy.get("lineage", {}),
            state=None,
            profile=profile,
            severity_map=severity_map,
        )[1]
    )
    checks.extend(
        validate_producer_authority(
            event, policy.get("producer_authority", {}), severity_map
        )[1]
    )
    checks.extend(validate_routing(event, policy["routing"], severity_map)[1])
    return [violation for violation in checks if violation.get("severity") != "warn"]


def build_settings(root, args, config):
    settings = {
        "profile": None,
        "listen_host": "0.0.0.0",
        "listen_port": 5555,
        "forward_host": "127.0.0.1",
        "forward_port": 5556,
        "emit_cot": False,
        "cot_host": "127.0.0.1",
        "cot_port": 6969,
        "schema_path": root / "schema" / "zmeta-event-1.0.schema.json",
        "policy_dir": root / "policy",
        "input_encoding": "json",
        "output_encoding": "json",
        "stamp_profile": True,
        "stamp_profile_profiles": list(DEFAULT_STAMP_PROFILE_PROFILES),
        "stamp_timing": True,
        "stamp_timing_profiles": list(DEFAULT_STAMP_TIMING_PROFILES),
        "strip_optional_fields": list(DEFAULT_STRIP_OPTIONAL_FIELDS),
        "strip_optional_fields_profiles": list(DEFAULT_STRIP_OPTIONAL_FIELDS_PROFILES),
        "strict_validation": False,
        "emit_metrics": True,
        "metrics_interval_sec": DEFAULT_METRICS_INTERVAL_SEC,
        "rate_limit_per_sec": DEFAULT_RATE_LIMIT_PER_SEC,
        "rate_limit_producer_per_sec": DEFAULT_RATE_LIMIT_PRODUCER_PER_SEC,
        "metrics_log_path": None,
        "metrics_log_max_bytes": DEFAULT_METRICS_LOG_MAX_BYTES,
        "metrics_log_backups": DEFAULT_METRICS_LOG_BACKUPS,
        "warn_datagram_bytes": DEFAULT_WARN_DATAGRAM_BYTES,
        "stamp_contract_hash": False,
        "require_schema_hash": None,
        "require_policy_hash": None,
        "require_contract_hash": None,
        "failure_modes": {},
    }

    if config:
        settings["profile"] = config.get("profile", settings["profile"])
        _apply_address(config.get("listen"), "listen_host", "listen_port", settings)
        _apply_address(config.get("forward"), "forward_host", "forward_port", settings)
        _apply_address(config.get("cot"), "cot_host", "cot_port", settings)
        if "emit_cot" in config:
            settings["emit_cot"] = bool(config["emit_cot"])
        if "schema_path" in config:
            settings["schema_path"] = Path(config["schema_path"])
        if "policy_dir" in config:
            settings["policy_dir"] = Path(config["policy_dir"])
        if "input_encoding" in config:
            settings["input_encoding"] = str(config["input_encoding"]).strip().lower()
        if "output_encoding" in config:
            settings["output_encoding"] = str(config["output_encoding"]).strip().lower()
        if "stamp_profile" in config:
            settings["stamp_profile"] = bool(config["stamp_profile"])
        if "stamp_profile_profiles" in config:
            settings["stamp_profile_profiles"] = _normalize_profiles(
                config["stamp_profile_profiles"], settings["stamp_profile_profiles"]
            )
        if "stamp_timing" in config:
            settings["stamp_timing"] = bool(config["stamp_timing"])
        if "stamp_timing_profiles" in config:
            settings["stamp_timing_profiles"] = _normalize_profiles(
                config["stamp_timing_profiles"], settings["stamp_timing_profiles"]
            )
        if "strip_optional_fields" in config:
            if config["strip_optional_fields"] is False:
                settings["strip_optional_fields"] = []
            else:
                settings["strip_optional_fields"] = _normalize_field_list(
                    config["strip_optional_fields"], settings["strip_optional_fields"]
                )
        if "strip_optional_fields_profiles" in config:
            settings["strip_optional_fields_profiles"] = _normalize_profiles(
                config["strip_optional_fields_profiles"],
                settings["strip_optional_fields_profiles"],
            )
        if "strict_validation" in config:
            settings["strict_validation"] = bool(config["strict_validation"])
        if "emit_metrics" in config:
            settings["emit_metrics"] = bool(config["emit_metrics"])
        if "metrics_interval_sec" in config:
            settings["metrics_interval_sec"] = _normalize_int(
                config["metrics_interval_sec"], "metrics_interval_sec", allow_zero=True
            )
        if "rate_limit_per_sec" in config:
            settings["rate_limit_per_sec"] = _normalize_int(
                config["rate_limit_per_sec"], "rate_limit_per_sec", allow_zero=True
            )
        if "rate_limit_producer_per_sec" in config:
            settings["rate_limit_producer_per_sec"] = _normalize_int(
                config["rate_limit_producer_per_sec"], "rate_limit_producer_per_sec", allow_zero=True
            )
        if "metrics_log_path" in config:
            if config["metrics_log_path"] is None:
                settings["metrics_log_path"] = None
            else:
                value = str(config["metrics_log_path"]).strip()
                settings["metrics_log_path"] = value or None
        if "metrics_log_max_bytes" in config:
            settings["metrics_log_max_bytes"] = _normalize_int(
                config["metrics_log_max_bytes"], "metrics_log_max_bytes", allow_zero=True
            )
        if "metrics_log_backups" in config:
            settings["metrics_log_backups"] = _normalize_int(
                config["metrics_log_backups"], "metrics_log_backups", allow_zero=True
            )
        if "warn_datagram_bytes" in config:
            settings["warn_datagram_bytes"] = _normalize_int(
                config["warn_datagram_bytes"], "warn_datagram_bytes", allow_zero=True
            )
        if "stamp_contract_hash" in config:
            settings["stamp_contract_hash"] = bool(config["stamp_contract_hash"])
        if "require_schema_hash" in config:
            value = config["require_schema_hash"]
            settings["require_schema_hash"] = str(value).strip() if value is not None else None
        if "require_policy_hash" in config:
            value = config["require_policy_hash"]
            settings["require_policy_hash"] = str(value).strip() if value is not None else None
        if "require_contract_hash" in config:
            value = config["require_contract_hash"]
            settings["require_contract_hash"] = str(value).strip() if value is not None else None
        if "failure_modes" in config and isinstance(config["failure_modes"], dict):
            settings["failure_modes"] = config["failure_modes"]

    if args.profile:
        settings["profile"] = args.profile
    if args.listen_host:
        settings["listen_host"] = args.listen_host
    if args.listen_port is not None:
        settings["listen_port"] = args.listen_port
    if args.forward_host:
        settings["forward_host"] = args.forward_host
    if args.forward_port is not None:
        settings["forward_port"] = args.forward_port
    if args.cot_host:
        settings["cot_host"] = args.cot_host
    if args.cot_port is not None:
        settings["cot_port"] = args.cot_port
    if args.schema_path:
        settings["schema_path"] = Path(args.schema_path)
    if args.policy_dir:
        settings["policy_dir"] = Path(args.policy_dir)
    if args.input_encoding:
        settings["input_encoding"] = args.input_encoding
    if args.output_encoding:
        settings["output_encoding"] = args.output_encoding
    if args.emit_cot:
        settings["emit_cot"] = True
    if args.no_emit_cot:
        settings["emit_cot"] = False
    if args.no_stamp_profile:
        settings["stamp_profile"] = False
    if args.no_stamp_timing:
        settings["stamp_timing"] = False
    if args.no_strip_optional_fields:
        settings["strip_optional_fields"] = []
    if args.strict_validation:
        settings["strict_validation"] = True
    if args.metrics_interval_sec is not None:
        settings["metrics_interval_sec"] = _normalize_int(
            args.metrics_interval_sec, "metrics_interval_sec", allow_zero=True
        )
    if args.rate_limit_per_sec is not None:
        settings["rate_limit_per_sec"] = _normalize_int(
            args.rate_limit_per_sec, "rate_limit_per_sec", allow_zero=True
        )
    if args.rate_limit_producer_per_sec is not None:
        settings["rate_limit_producer_per_sec"] = _normalize_int(
            args.rate_limit_producer_per_sec, "rate_limit_producer_per_sec", allow_zero=True
        )
    if args.no_metrics:
        settings["emit_metrics"] = False
    if args.metrics_log_path:
        settings["metrics_log_path"] = str(args.metrics_log_path).strip() or None
    if args.metrics_log_max_bytes is not None:
        settings["metrics_log_max_bytes"] = _normalize_int(
            args.metrics_log_max_bytes, "metrics_log_max_bytes", allow_zero=True
        )
    if args.metrics_log_backups is not None:
        settings["metrics_log_backups"] = _normalize_int(
            args.metrics_log_backups, "metrics_log_backups", allow_zero=True
        )
    if args.warn_datagram_bytes is not None:
        settings["warn_datagram_bytes"] = _normalize_int(
            args.warn_datagram_bytes, "warn_datagram_bytes", allow_zero=True
        )
    if args.stamp_contract_hash:
        settings["stamp_contract_hash"] = True
    if args.require_schema_hash:
        settings["require_schema_hash"] = str(args.require_schema_hash).strip() or None
    if args.require_policy_hash:
        settings["require_policy_hash"] = str(args.require_policy_hash).strip() or None
    if args.require_contract_hash:
        settings["require_contract_hash"] = str(args.require_contract_hash).strip() or None

    if settings["profile"] not in PROFILE_CHOICES:
        raise ValueError("profile is required and must be one of L, M, H")
    if settings["input_encoding"] not in INPUT_ENCODING_CHOICES:
        raise ValueError("input_encoding must be one of json, cbor, compact, proto, auto")
    if settings["output_encoding"] not in OUTPUT_ENCODING_CHOICES:
        raise ValueError("output_encoding must be one of json, cbor, compact, proto")
    _reject_protected_strip_paths(settings["strip_optional_fields"])

    if settings["input_encoding"] in {"cbor", "compact"} or settings["output_encoding"] in {
        "cbor",
        "compact",
    }:
        _cbor_self_test()
    if settings["input_encoding"] == "compact" or settings["output_encoding"] == "compact":
        _require_compact()
    if settings["input_encoding"] == "proto" or settings["output_encoding"] == "proto":
        _require_proto()
    settings["listen_port"] = _validate_port(settings["listen_port"], "listen_port")
    settings["forward_port"] = _validate_port(settings["forward_port"], "forward_port")
    settings["cot_port"] = _validate_port(settings["cot_port"], "cot_port")

    if settings["metrics_interval_sec"] is None:
        settings["metrics_interval_sec"] = DEFAULT_METRICS_INTERVAL_SEC
    if settings["metrics_interval_sec"] <= 0:
        settings["emit_metrics"] = False
    if settings["rate_limit_per_sec"] is None or settings["rate_limit_per_sec"] <= 0:
        settings["rate_limit_per_sec"] = 0
    if settings["rate_limit_producer_per_sec"] is None or settings["rate_limit_producer_per_sec"] <= 0:
        settings["rate_limit_producer_per_sec"] = 0
    if settings["metrics_log_max_bytes"] is None:
        settings["metrics_log_max_bytes"] = DEFAULT_METRICS_LOG_MAX_BYTES
    if settings["metrics_log_backups"] is None or settings["metrics_log_backups"] < 0:
        settings["metrics_log_backups"] = DEFAULT_METRICS_LOG_BACKUPS
    if settings["warn_datagram_bytes"] is None or settings["warn_datagram_bytes"] <= 0:
        settings["warn_datagram_bytes"] = 0

    if not settings["schema_path"].is_file():
        raise FileNotFoundError(f"schema not found: {settings['schema_path']}")
    if not settings["policy_dir"].is_dir():
        raise FileNotFoundError(f"policy dir not found: {settings['policy_dir']}")

    return settings


def _attach_contract_hash(metrics, contract_hashes=None, stamp_contract_hash=False):
    if not stamp_contract_hash or not contract_hashes:
        return
    metrics["contract_hash"] = contract_hashes.get("contract_hash")
    metrics["schema_hash"] = contract_hashes.get("schema_hash")
    metrics["policy_hash"] = contract_hashes.get("policy_hash")
    if contract_hashes.get("semantics_hash"):
        metrics["semantics_hash"] = contract_hashes.get("semantics_hash")


def build_violation_event(reason_code, original=None, details=None, contract_hashes=None, stamp_contract_hash=False, force_schema_violation=False):
    original_event = original.get("event", {}) if isinstance(original, dict) else {}
    original_source = original.get("source", {}) if isinstance(original, dict) else {}
    original_payload = original.get("payload", {}) if isinstance(original, dict) else {}

    # force_schema_violation keeps wire-level diagnostics (e.g.
    # ENCODING_UNSUPPORTED) out of the TASK_ACK shape, whose reason_code
    # vocabulary is deliberately task-limited.
    is_command = (not force_schema_violation) and original_event.get("event_type") == "COMMAND_EVENT"
    event_subtype = "TASK_ACK" if is_command else "SCHEMA_VIOLATION"
    system_type = "TASK_ACK" if is_command else "SCHEMA_VIOLATION"

    metrics = {"reason_code": reason_code}
    if is_command:
        metrics["task_id"] = (
            original_payload.get("task_id") if isinstance(original_payload, dict) else None
        ) or "UNKNOWN"
        metrics["original_event_id"] = original_event.get("event_id") or "UNKNOWN"
    else:
        metrics["original_event_id"] = original_event.get("event_id") or "UNKNOWN"
    if original_source.get("platform_id"):
        metrics["source_platform_id"] = original_source.get("platform_id")
    if original_source.get("producer"):
        metrics["source_producer"] = original_source.get("producer")
    if details:
        metrics.update(details)
    _attach_contract_hash(metrics, contract_hashes, stamp_contract_hash)

    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": event_subtype,
            "ts": utc_now(),
        },
        "source": {
            "platform_id": "zmeta-gateway",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "payload": {
            "system_type": system_type,
            "state": "REJECTED",
            "metrics": metrics,
        },
    }


def build_warning_event(reason_code, original=None, details=None, contract_hashes=None, stamp_contract_hash=False):
    original_event = original.get("event", {}) if isinstance(original, dict) else {}
    original_source = original.get("source", {}) if isinstance(original, dict) else {}

    metrics = {"reason_code": reason_code, "original_event_id": original_event.get("event_id") or "UNKNOWN"}
    if original_source.get("platform_id"):
        metrics["source_platform_id"] = original_source.get("platform_id")
    if original_source.get("producer"):
        metrics["source_producer"] = original_source.get("producer")
    if details:
        metrics.update(details)
    _attach_contract_hash(metrics, contract_hashes, stamp_contract_hash)

    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "SCHEMA_VIOLATION",
            "ts": utc_now(),
        },
        "source": {
            "platform_id": "zmeta-gateway",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "payload": {
            "system_type": "SCHEMA_VIOLATION",
            "state": "WARNING",
            "metrics": metrics,
        },
    }


def build_duplicate_ack(original, contract_hashes=None, stamp_contract_hash=False):
    original_event = original.get("event", {}) if isinstance(original, dict) else {}
    original_payload = original.get("payload", {}) if isinstance(original, dict) else {}

    metrics = {
        "reason_code": "TASK_DUPLICATE",
        "task_id": original_payload.get("task_id"),
        "original_event_id": original_event.get("event_id"),
    }
    _attach_contract_hash(metrics, contract_hashes, stamp_contract_hash)

    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "TASK_ACK",
            "ts": utc_now(),
        },
        "source": {
            "platform_id": "zmeta-gateway",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "payload": {
            "system_type": "TASK_ACK",
            "state": "DUPLICATE_IGNORED",
            "metrics": metrics,
        },
    }


def _split_violations(violations):
    fails = []
    warns = []
    for violation in violations:
        if violation.get("severity") == "warn":
            warns.append(violation)
        else:
            fails.append(violation)
    return fails, warns


def process_message(
    message,
    validator,
    policy,
    profile,
    dedupe_cache,
    input_encoding,
    event_dedupe_cache=None,
    task_ack_dedupe_cache=None,
    timing_state=None,
    strict_validation=False,
    metrics=None,
    rate_limiter=None,
    contract_hashes=None,
    stamp_contract_hash=False,
):
    try:
        instance = _decode_message(message, input_encoding)
    except Exception as exc:
        if metrics:
            metrics.record_violation("SCHEMA_INVALID")
        return [
            build_violation_event(
                "SCHEMA_INVALID",
                details={"error": str(exc)},
                contract_hashes=contract_hashes,
                stamp_contract_hash=stamp_contract_hash,
            )
        ]

    severity_map = policy.get("violation_severities", {})
    warnings = []
    event_block = instance.get("event", {}) if isinstance(instance, dict) else {}
    source = instance.get("source", {}) if isinstance(instance, dict) else {}
    event_id = event_block.get("event_id")
    producer = source.get("producer") if isinstance(source, dict) else None

    if rate_limiter and not rate_limiter.allow(producer):
        if metrics:
            metrics.record_drop("RATE_LIMIT_PRODUCER", producer=producer)
        return []

    ok, violations = validate_schema(instance, validator, severity_map)
    if not ok:
        violation = violations[0]
        if metrics:
            metrics.record_violation(violation["code"], event_id=event_id, producer=producer)
        return [
            build_violation_event(
                violation["code"],
                original=instance,
                details={"error": violation["message"], **violation.get("details", {})},
                contract_hashes=contract_hashes,
                stamp_contract_hash=stamp_contract_hash,
            )
        ]

    ok, violations = validate_role(
        instance, {"roles": policy["roles"], "deny": policy["deny"]}, severity_map
    )
    if violations:
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            if metrics:
                metrics.record_violation(violation["code"], event_id=event_id, producer=producer)
            return [
                build_violation_event(
                    violation["code"],
                    original=instance,
                    details=violation.get("details"),
                    contract_hashes=contract_hashes,
                    stamp_contract_hash=stamp_contract_hash,
                )
            ]
        warnings.extend(warns)

    ok, violations = validate_profile(instance, profile, policy["profiles"], severity_map)
    if violations:
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            if metrics:
                metrics.record_violation(violation["code"], event_id=event_id, producer=producer)
            return [
                build_violation_event(
                    violation["code"],
                    original=instance,
                    details=violation.get("details"),
                    contract_hashes=contract_hashes,
                    stamp_contract_hash=stamp_contract_hash,
                )
            ]
        warnings.extend(warns)

    if timing_state is not None:
        ok, violations = validate_timing_quality(
            instance,
            policy["semantics"],
            state=timing_state,
            severity_map=severity_map,
            timing_freshness_policy=policy.get("timing_freshness", {}),
            profile=profile,
        )
        apply_timing_freshness_degradation(
            instance, violations, policy.get("timing_freshness", {})
        )
        if violations:
            fails, warns = _split_violations(violations)
            if fails:
                violation = fails[0]
                if metrics:
                    metrics.record_violation(violation["code"], event_id=event_id, producer=producer)
                return [
                    build_violation_event(
                        violation["code"],
                        original=instance,
                        details=violation.get("details"),
                        contract_hashes=contract_hashes,
                        stamp_contract_hash=stamp_contract_hash,
                    )
                ]
            warnings.extend(warns)

    if metrics:
        timing_quality = _event_timing_quality(instance)
        if timing_quality:
            metrics.record_timing_quality(
                timing_quality.get("time_source"),
                timing_quality.get("sync_state"),
                event_id=event_id,
                producer=producer,
            )

    ok, violations = validate_semantics(instance, policy["semantics"], severity_map)
    if violations:
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            if metrics:
                metrics.record_violation(violation["code"], event_id=event_id, producer=producer)
            return [
                build_violation_event(
                    violation["code"],
                    original=instance,
                    details=violation.get("details"),
                    contract_hashes=contract_hashes,
                    stamp_contract_hash=stamp_contract_hash,
                )
            ]
        warnings.extend(warns)

    ok, violations = validate_lineage(
        instance,
        policy.get("lineage", {}),
        state=timing_state,
        profile=profile,
        severity_map=severity_map,
    )
    if violations:
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            if metrics:
                metrics.record_violation(violation["code"], event_id=event_id, producer=producer)
            return [
                build_violation_event(
                    violation["code"],
                    original=instance,
                    details=violation.get("details"),
                    contract_hashes=contract_hashes,
                    stamp_contract_hash=stamp_contract_hash,
                )
            ]
        warnings.extend(warns)

    ok, violations = validate_producer_authority(
        instance, policy.get("producer_authority", {}), severity_map
    )
    if violations:
        apply_external_promotion_policy_action(
            instance, violations, policy.get("producer_authority", {})
        )
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            if metrics:
                metrics.record_violation(violation["code"], event_id=event_id, producer=producer)
            return [
                build_violation_event(
                    violation["code"],
                    original=instance,
                    details=violation.get("details"),
                    contract_hashes=contract_hashes,
                    stamp_contract_hash=stamp_contract_hash,
                )
            ]
        warnings.extend(warns)

    ok, violations = validate_routing(instance, policy["routing"], severity_map)
    if violations:
        fails, warns = _split_violations(violations)
        if fails:
            violation = fails[0]
            if metrics:
                metrics.record_violation(violation["code"], event_id=event_id, producer=producer)
            return [
                build_violation_event(
                    violation["code"],
                    original=instance,
                    details=violation.get("details"),
                    contract_hashes=contract_hashes,
                    stamp_contract_hash=stamp_contract_hash,
                )
            ]
        warnings.extend(warns)

    event_type = instance.get("event", {}).get("event_type")
    if event_type != "COMMAND_EVENT" and event_dedupe_cache:
        if event_dedupe_cache.check_and_set(event_id):
            if metrics:
                metrics.record_duplicate()
            return []

    if event_type == "SYSTEM_EVENT" and task_ack_dedupe_cache:
        if task_ack_dedupe_cache.check_and_set(instance):
            if metrics:
                metrics.record_duplicate()
            return []

    if strict_validation and warnings:
        violation = warnings[0]
        if metrics:
            metrics.record_violation(violation["code"], event_id=event_id, producer=producer)
        return [
            build_violation_event(
                violation["code"],
                original=instance,
                details=violation.get("details"),
                contract_hashes=contract_hashes,
                stamp_contract_hash=stamp_contract_hash,
            )
        ]

    if event_type == "COMMAND_EVENT":
        payload = instance.get("payload", {})
        task_id = payload.get("task_id")
        if task_id and dedupe_cache:
            ttl_ms = ttl_ms_from_payload(payload)
            if dedupe_cache.check_and_set(task_id, ttl_ms):
                if metrics:
                    metrics.record_duplicate(task_id=task_id)
                    metrics.record_violation("TASK_DUPLICATE", event_id=event_id, producer=producer)
                return [
                    build_duplicate_ack(
                        instance,
                        contract_hashes=contract_hashes,
                        stamp_contract_hash=stamp_contract_hash,
                    )
                ]

    if timing_state is not None:
        timing_state.record(instance)

    outgoing = [instance]
    for warning in warnings:
        if metrics:
            metrics.record_warning(warning["code"], event_id=event_id, producer=producer)
        outgoing.append(
            build_warning_event(
                warning["code"],
                original=instance,
                details=warning.get("details"),
                contract_hashes=contract_hashes,
                stamp_contract_hash=stamp_contract_hash,
            )
        )
    return outgoing


def parse_args():
    parser = argparse.ArgumentParser(description="ZMeta minimal reference gateway")
    parser.add_argument("--config", help="Path to gateway config JSON")
    parser.add_argument("--profile", choices=sorted(PROFILE_CHOICES))
    parser.add_argument("--listen-host")
    parser.add_argument("--listen-port", type=int)
    parser.add_argument("--forward-host")
    parser.add_argument("--forward-port", type=int)
    parser.add_argument("--cot-host")
    parser.add_argument("--cot-port", type=int)
    parser.add_argument("--schema-path")
    parser.add_argument("--policy-dir")
    parser.add_argument("--input-encoding", choices=sorted(INPUT_ENCODING_CHOICES))
    parser.add_argument("--output-encoding", choices=sorted(OUTPUT_ENCODING_CHOICES))
    emit_group = parser.add_mutually_exclusive_group()
    emit_group.add_argument("--emit-cot", action="store_true")
    emit_group.add_argument("--no-emit-cot", action="store_true")
    parser.add_argument("--no-stamp-profile", action="store_true")
    parser.add_argument("--no-stamp-timing", action="store_true")
    parser.add_argument("--no-strip-optional-fields", action="store_true")
    parser.add_argument("--strict-validation", action="store_true")
    parser.add_argument("--rate-limit-per-sec", type=int)
    parser.add_argument("--metrics-interval-sec", type=int)
    parser.add_argument("--no-metrics", action="store_true")
    parser.add_argument("--rate-limit-producer-per-sec", type=int)
    parser.add_argument("--metrics-log-path")
    parser.add_argument("--metrics-log-max-bytes", type=int)
    parser.add_argument("--metrics-log-backups", type=int)
    parser.add_argument("--warn-datagram-bytes", type=int)
    parser.add_argument("--stamp-contract-hash", action="store_true")
    parser.add_argument("--require-schema-hash")
    parser.add_argument("--require-policy-hash")
    parser.add_argument("--require-contract-hash")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.self_test and not args.profile and not args.config:
        args.profile = "H"
    try:
        config = load_config(args.config)
        settings = build_settings(root, args, config)
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc))

    semantics_path = root / "spec" / "semantics-contract.md"
    contract_hashes = compute_contract_hash(settings["schema_path"], settings["policy_dir"], semantics_path)
    if settings["require_schema_hash"] and settings["require_schema_hash"] != contract_hashes["schema_hash"]:
        raise SystemExit("schema hash mismatch: update config or schema")
    if settings["require_policy_hash"] and settings["require_policy_hash"] != contract_hashes["policy_hash"]:
        raise SystemExit("policy hash mismatch: update config or policy")
    if settings["require_contract_hash"] and settings["require_contract_hash"] != contract_hashes["contract_hash"]:
        raise SystemExit("contract hash mismatch: update config or schema/policy")

    if args.self_test:
        run_self_test(root, settings)
        return

    validator = load_schema(settings["schema_path"])
    policy = load_policy(settings["policy_dir"])

    listen_addr = (settings["listen_host"], settings["listen_port"])
    forward_addr = (settings["forward_host"], settings["forward_port"])

    sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_in.bind(listen_addr)
    sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(
        "gateway listening on "
        f"{listen_addr[0]}:{listen_addr[1]} (profile {settings['profile']}, "
        f"in={settings['input_encoding']} out={settings['output_encoding']})"
    )
    if settings["output_encoding"] in {"cbor", "proto"} and not settings["emit_cot"]:
        print(
            f"WARNING: output_encoding={settings['output_encoding']}; TAK expects CoT XML. "
            "Enable emit_cot or ensure downstream decodes this binary encoding."
        )
    print(f"forwarding to {forward_addr[0]}:{forward_addr[1]}")
    print(f"schema_hash={contract_hashes['schema_hash']}")
    print(f"policy_hash={contract_hashes['policy_hash']}")
    if contract_hashes.get("semantics_hash"):
        print(f"semantics_hash={contract_hashes['semantics_hash']}")
    print(f"contract_hash={contract_hashes['contract_hash']}")
    if settings["rate_limit_per_sec"]:
        print(f"rate limit: {settings['rate_limit_per_sec']} msg/s")
    if settings["rate_limit_producer_per_sec"]:
        print(f"per-producer rate limit: {settings['rate_limit_producer_per_sec']} msg/s")
    if settings["emit_metrics"]:
        print(f"metrics interval: {settings['metrics_interval_sec']}s")
    if settings["metrics_log_path"]:
        print(f"metrics log: {settings['metrics_log_path']}")
    if settings["strict_validation"]:
        print("strict validation enabled (warnings treated as failures)")

    dedupe_cache = TaskDedupeCache()
    event_dedupe_cache = EventDedupeCache()
    task_ack_dedupe_cache = TaskAckDedupeCache()
    validation_state = ValidationState()
    logger = None
    if settings["metrics_log_path"]:
        logger = MetricsLogger(
            settings["metrics_log_path"],
            max_bytes=settings["metrics_log_max_bytes"],
            backups=settings["metrics_log_backups"],
        )
    metrics = GatewayMetrics(
        interval_sec=settings["metrics_interval_sec"],
        emit=settings["emit_metrics"],
        logger=logger,
        contract_hash=contract_hashes["contract_hash"],
    )
    rate_limit = settings["rate_limit_per_sec"]
    producer_rate_limiter = (
        ProducerRateLimiter(settings["rate_limit_producer_per_sec"])
        if settings["rate_limit_producer_per_sec"]
        else None
    )
    rate_window = None
    rate_count = 0

    cot_addr = (settings["cot_host"], settings["cot_port"])

    while True:
        data, _addr = sock_in.recvfrom(65535)
        if metrics:
            metrics.record_received(len(data))
        if rate_limit:
            now_window = int(time.monotonic())
            if rate_window != now_window:
                rate_window = now_window
                rate_count = 0
            if rate_count >= rate_limit:
                if metrics:
                    metrics.record_drop("RATE_LIMIT")
                    metrics.maybe_log()
                continue
            rate_count += 1
        out_events = process_message(
            data,
            validator,
            policy,
            settings["profile"],
            dedupe_cache,
            settings["input_encoding"],
            event_dedupe_cache=event_dedupe_cache,
            task_ack_dedupe_cache=task_ack_dedupe_cache,
            timing_state=validation_state,
            strict_validation=settings["strict_validation"],
            metrics=metrics,
            rate_limiter=producer_rate_limiter,
            contract_hashes=contract_hashes,
            stamp_contract_hash=settings["stamp_contract_hash"],
        )
        for outgoing in out_events:
            should_stamp_timing = _should_apply(
                settings["profile"], settings["stamp_timing"], settings["stamp_timing_profiles"]
            )
            if should_stamp_timing:
                event_block = outgoing.get("event")
                if isinstance(event_block, dict):
                    receive_ts = event_block.get("t_receive")
                    if not receive_ts:
                        receive_ts = utc_now()
                        event_block["t_receive"] = receive_ts
                    if not event_block.get("t_publish"):
                        event_block["t_publish"] = receive_ts

            should_stamp_profile = _should_apply(
                settings["profile"], settings["stamp_profile"], settings["stamp_profile_profiles"]
            )
            if should_stamp_profile:
                outgoing["profile"] = settings["profile"]

            should_strip = _should_apply(
                settings["profile"],
                bool(settings["strip_optional_fields"]),
                settings["strip_optional_fields_profiles"],
            )
            if should_strip:
                _strip_optional_fields(outgoing, settings["strip_optional_fields"])
            _apply_failure_mode_degradation(
                outgoing,
                settings["failure_modes"],
                validation_state,
                policy.get("timing_freshness", {}),
            )
            violations = validate_outgoing_event(outgoing, validator, policy, settings["profile"])
            if violations:
                violation = violations[0]
                if metrics:
                    event_block = outgoing.get("event", {}) if isinstance(outgoing, dict) else {}
                    source = outgoing.get("source", {}) if isinstance(outgoing, dict) else {}
                    metrics.record_violation(
                        violation["code"],
                        event_id=event_block.get("event_id"),
                        producer=source.get("producer") if isinstance(source, dict) else None,
                    )
                outgoing = build_violation_event(
                    violation["code"],
                    original=outgoing,
                    details=violation.get("details"),
                    contract_hashes=contract_hashes,
                    stamp_contract_hash=settings["stamp_contract_hash"],
                )
                if should_stamp_profile:
                    outgoing["profile"] = settings["profile"]
            try:
                payload = _encode_message(outgoing, settings["output_encoding"])
            except _COMPACT_UNREPRESENTABLE as exc:
                if metrics:
                    event_block = outgoing.get("event", {}) if isinstance(outgoing, dict) else {}
                    source = outgoing.get("source", {}) if isinstance(outgoing, dict) else {}
                    metrics.record_violation(
                        "ENCODING_UNSUPPORTED",
                        event_id=event_block.get("event_id"),
                        producer=source.get("producer") if isinstance(source, dict) else None,
                    )
                outgoing = build_violation_event(
                    "ENCODING_UNSUPPORTED",
                    original=outgoing,
                    details={"error": str(exc)},
                    contract_hashes=contract_hashes,
                    stamp_contract_hash=settings["stamp_contract_hash"],
                    force_schema_violation=True,
                )
                if should_stamp_profile:
                    outgoing["profile"] = settings["profile"]
                payload = _encode_message(outgoing, settings["output_encoding"])
            event_block = outgoing.get("event", {}) if isinstance(outgoing, dict) else {}
            source_block = outgoing.get("source", {}) if isinstance(outgoing, dict) else {}
            _check_datagram_size(
                metrics,
                len(payload),
                settings["warn_datagram_bytes"],
                "forward",
                event_id=event_block.get("event_id") if isinstance(event_block, dict) else None,
                producer=source_block.get("producer") if isinstance(source_block, dict) else None,
            )
            sent = _send_datagram(
                sock_out,
                payload,
                forward_addr,
                metrics=metrics,
                kind="forward",
                event_id=event_block.get("event_id") if isinstance(event_block, dict) else None,
                producer=source_block.get("producer") if isinstance(source_block, dict) else None,
            )
            if sent and metrics:
                metrics.record_forwarded()
            if settings["emit_cot"]:
                cot_xml = zmeta_to_cot(outgoing)
                if cot_xml:
                    cot_payload = cot_xml.encode("utf-8")
                    _check_datagram_size(
                        metrics,
                        len(cot_payload),
                        settings["warn_datagram_bytes"],
                        "cot",
                        event_id=event_block.get("event_id") if isinstance(event_block, dict) else None,
                        producer=source_block.get("producer") if isinstance(source_block, dict) else None,
                    )
                    cot_sent = _send_datagram(
                        sock_out,
                        cot_payload,
                        cot_addr,
                        metrics=metrics,
                        kind="cot",
                        event_id=event_block.get("event_id") if isinstance(event_block, dict) else None,
                        producer=source_block.get("producer") if isinstance(source_block, dict) else None,
                    )
                    if cot_sent and metrics:
                        metrics.record_cot()
                elif metrics:
                    reason = _cot_skip_reason(outgoing)
                    if reason:
                        event_block = outgoing.get("event", {}) if isinstance(outgoing, dict) else {}
                        source = outgoing.get("source", {}) if isinstance(outgoing, dict) else {}
                        metrics.record_cot_skipped(
                            reason,
                            event_id=event_block.get("event_id"),
                            producer=source.get("producer") if isinstance(source, dict) else None,
                        )
        if metrics:
            metrics.maybe_log()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
