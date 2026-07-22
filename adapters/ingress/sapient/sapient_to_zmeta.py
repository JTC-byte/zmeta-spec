"""SAPIENT (BSI Flex 335 v2.0) SapientMessage to ZMeta event translator.

Translates one SapientMessage dict (protobuf-JSON; lowerCamelCase or
snake_case keys) into ZMeta events, un-collapsing SAPIENT's fused
fact/opinion DetectionReport into the ZMeta layer model:

  SAPIENT content     ZMeta output (zmeta_version)
  ----------------    -------------------------------------------------
  detection_report    0..1 OBSERVATION_EVENT + 0..n INFERENCE_EVENT (1.0),
                      or STATE_EVENT/TRACK_STATE promotion for fusion
                      nodes (1.0, contract 4.5.1 gate)
  status_report       SENSOR_STATUS + 0..1 PLATFORM_STATUS (1.1.0)
  alert               INFERENCE_EVENT/ANOMALY (1.0)
  task_ack            SYSTEM_EVENT/TASK_ACK (1.0)
  error               SYSTEM_EVENT/SCHEMA_VIOLATION (1.0)
  registration        no events; feeds the caller's RegistrationStore
  registration_ack /
  alert_ack           no events (ack loops terminate at the adapter)
  task                no events; SAPIENT->COMMAND ingress is out of scope
                      in v1 (command safety; see README)

SAPIENT declares units, error statistics, model identity, and latency
bounds out-of-band in Registration. ZMeta forbids unit inference (contract
6.7) and fabricated model identity (7.5), so canonical emission of signal,
velocity, and error data requires a ``registration`` RegistrationStore;
without the relevant declaration those values stay in the
``payload.extensions["vendor.sapient"]`` provenance block or the event is
refused. Refusal is per event: ``translate()`` returns whatever subset can
be honestly emitted, and ``[]`` when nothing can.

Timing: the one mandatory SAPIENT timestamp is message SEND time, not
capture time, so ``event.ts`` inherits the capture->send gap.
``coerce_timing_quality()`` provides the degraded UNKNOWN/UNSYNCED
fallback, and ``est_error_ms`` is then widened by the registration-declared
``maximum_latency`` — including when the caller supplies its own
``timing_quality`` — because that latency is real even with a good clock.

``bandwidth_hz: 0.0`` is the repository's declared "not measured" sentinel
(kraken/moth/signalhunter convention): a SAPIENT Signal without both band
edges cannot state emitter bandwidth, so the sentinel marks it rather than
inventing a value. See README for the full mapping and refusal matrix.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from adapters.ingress.sapient.registration_state import enum_tail, snake_keys
from adapters.ingress.time_utils import coerce_timing_quality, normalize_utc_z
from zmeta_uuid import uuid7

ADAPTER_VERSION = "1.0.0"
SCHEMA_ID = "vendor:sapient_bsi335:v2"
PRODUCER = "sapient-ingress"
PROMOTION_POLICY_ID = "PROMOTE-SAPIENT-STATE-V1"
DEFAULT_VALID_FOR_MS = 5000
VENDOR_EXTENSION_KEY = "vendor.sapient"

# Declared "not measured" sentinel shared with the kraken/moth/signalhunter
# adapters; documented in this adapter's README (AUTHORING.md section 3).
BANDWIDTH_SENTINEL_HZ = 0.0

_CONTENT_KEYS = (
    "registration",
    "registration_ack",
    "status_report",
    "detection_report",
    "alert",
    "alert_ack",
    "task",
    "task_ack",
    "error",
)
_NO_EVENT_CONTENT = ("registration_ack", "alert_ack", "task")

# Signal frequency units the registration codex may resolve to Hz.
_FREQ_FACTOR_HZ = {"hz": 1.0, "mhz": 1e6, "ghz": 1e9}

# StatusReport.System -> SENSOR_STATUS state (1.1.0 schema vocabulary).
_SENSOR_STATE = {
    "OK": "ACTIVE",
    "WARNING": "DEGRADED",
    "ERROR": "DEGRADED",
    "GOODBYE": "OFFLINE",
}
_FAULT_STATUS_TYPES = {"INTERNAL_FAULT", "EXTERNAL_FAULT", "NOT_DETECTING"}

# TaskAck.TaskStatus -> (TASK_ACK state, required reason_code|None).
_TASK_ACK_STATE = {
    "ACCEPTED": ("ACCEPTED", None),
    "REJECTED": ("REJECTED", "TASK_REJECTED"),
    "COMPLETED": ("COMPLETED", None),
    "FAILED": ("FAILED", "TASK_FAILED"),
}

# PowerSource -> PLATFORM_STATUS power_state; unmapped sources are omitted.
_POWER_STATE = {
    "MAINS": "EXTERNAL_POWER",
    "INTERNAL_BATTERY": "BATTERY",
    "EXTERNAL_BATTERY": "BATTERY",
}

_SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schema"
_SCHEMA_FILES = {
    "1.0": "zmeta-event-1.0.schema.json",
    "1.1.0": "zmeta-event-1.1.0.schema.json",
}
_schema_cache = {}


def _is_number(value):
    # Finite only: NaN/inf from the wire would ride through every
    # numeric guard and vacuously pass jsonschema range checks (min/max
    # comparisons against NaN are all False) — a meaningless confidence
    # or measurement must refuse, not validate clean.
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


_DROP_CONTAINER = object()


def _drop_non_finite(value):
    """Strip non-finite floats from a native pass-through structure.

    Applied to verbatim vendor blocks only — canonical fields refuse via
    _is_number instead. Dropping the key is the honest shape: a NaN/inf
    carries no measurement information, and keeping it would make the
    whole event unserializable to strict RFC-8259 JSON.

    A bare non-finite element inside a LIST drops the whole list instead,
    because position carries meaning in a numeric array: removing one
    element silently re-indexes the rest, so [1.0, NaN, 3.0] would arrive
    as a clean two-element array and the consumer could never tell. An
    absent key is honestly absent; a silently shortened array is not.
    Lists of objects are unaffected — every element is preserved and
    cleaned in place, so no index moves.
    """
    cleaned = _drop_non_finite_inner(value)
    if cleaned is _DROP_CONTAINER:
        return [] if isinstance(value, list) else {}
    return cleaned


def _drop_non_finite_inner(value):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if isinstance(item, float) and not math.isfinite(item):
                continue
            child = _drop_non_finite_inner(item)
            if child is _DROP_CONTAINER:
                continue
            out[key] = child
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, float) and not math.isfinite(item):
                return _DROP_CONTAINER
            child = _drop_non_finite_inner(item)
            if child is _DROP_CONTAINER:
                return _DROP_CONTAINER
            out.append(child)
        return out
    return value


def _envelope_ts(value):
    """Normalize the envelope timestamp (RFC3339 string or protobuf
    Timestamp dict) to UTC-Z, or None."""
    if isinstance(value, dict):
        seconds = value.get("seconds")
        nanos = value.get("nanos") or 0
        if not _is_number(seconds) or not _is_number(nanos):
            return None
        # Out-of-range epochs refuse like any other unparseable timestamp:
        # wire data must never crash the ingest loop (fail closed).
        try:
            moment = datetime.fromtimestamp(
                float(seconds) + float(nanos) / 1e9, tz=timezone.utc
            )
        except (OverflowError, OSError, ValueError):
            return None
        return normalize_utc_z(moment)
    return normalize_utc_z(value)


def _content(msg):
    """Return (content_key, content_dict) when exactly one oneof branch is
    present, else None."""
    present = [key for key in _CONTENT_KEYS if isinstance(msg.get(key), dict)]
    if len(present) != 1:
        return None
    return present[0], msg[present[0]]


def detect(input_bytes):
    """Return the schema_id when the payload looks like a SapientMessage."""
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
    if not isinstance(obj, dict):
        return None
    msg = snake_keys(obj)
    node_id = msg.get("node_id")
    if not isinstance(node_id, str) or not node_id:
        return None
    if msg.get("timestamp") is None:
        return None
    if _content(msg) is None:
        return None
    return SCHEMA_ID


def _timing(timing_quality, ts, registration, node_id, active_mode):
    """Fallback timing plus the SAPIENT send-time widen.

    The widen applies to caller-supplied timing too: the envelope timestamp
    is send time, so the declared capture->send latency bound is additional
    absolute timestamp error regardless of clock quality.
    """
    timing = coerce_timing_quality(timing_quality, event_ts=ts)
    if registration is not None:
        latency_ms = registration.max_latency_ms(node_id, mode=active_mode)
        if latency_ms is not None:
            timing["est_error_ms"] = float(timing["est_error_ms"]) + float(latency_ms)
    return timing


def _source(node_id, node_role="EDGE"):
    return {
        "platform_id": node_id,
        "node_role": node_role,
        "producer": PRODUCER,
        "sensor_id": node_id,
    }


def _envelope(event_type, event_subtype, ts, node_id, *, zmeta_version="1.0", node_role="EDGE"):
    return {
        "zmeta_version": zmeta_version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": event_type,
            "event_subtype": event_subtype,
            "ts": ts,
        },
        "source": _source(node_id, node_role),
    }


def _translate_lineage(based_on):
    return {
        "based_on": [str(item) for item in based_on],
        "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
    }


def _canonical_geo(location):
    """Resolve a SAPIENT Location to canonical geo.

    Returns (geo|None, omitted_reason|None). Canonical geo requires
    LAT_LNG_DEG_M or LAT_LNG_RAD_M coordinates, the WGS84 ellipsoid datum,
    an explicit z, plausible ranges, and a non-(0,0) position (contract
    6.1/6.2/6.8). Anything else yields no canonical geo and a reason tag
    for the raw preservation block.
    """
    if not isinstance(location, dict):
        return None, None
    units = enum_tail(location.get("coordinate_system"), "LOCATION_COORDINATE_SYSTEM_")
    if units == "UTM_M":
        return None, "UTM_UNSUPPORTED"
    if units not in ("LAT_LNG_DEG_M", "LAT_LNG_RAD_M"):
        return None, "UNITS_UNSPECIFIED"
    datum = enum_tail(location.get("datum"), "LOCATION_DATUM_")
    if datum == "WGS84_G":
        return None, "GEOID_DATUM"
    if datum != "WGS84_E":
        return None, "DATUM_UNSPECIFIED"
    x = location.get("x")
    y = location.get("y")
    if not _is_number(x) or not _is_number(y):
        return None, "COORDS_MISSING"
    if x == 0 and y == 0:
        return None, "ZERO_FILL_SUSPECT"
    if units == "LAT_LNG_RAD_M":
        lat, lon = math.degrees(float(y)), math.degrees(float(x))
    else:
        lat, lon = float(y), float(x)
    z = location.get("z")
    if not _is_number(z):
        return None, "NO_ALTITUDE"
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None, "RANGE_INVALID"
    return {"lat": lat, "lon": lon, "alt_m": float(z)}, None


def _range_bearing_map(range_bearing):
    """Map a SAPIENT RangeBearing to canonical/non-canonical carriers.

    Returns (bearing|None, features_dict, fully_carried). Canonical
    ``payload.bearing`` only for RANGE_BEARING_DATUM_TRUE (contract 6.4);
    MAGNETIC/GRID/PLATFORM bearings stay in explicitly named
    ``features.bearing_native_deg`` / ``features.bearing_native_datum``
    fields. Range converts to meters per the self-describing coordinate
    system. ``fully_carried`` is False when any component (unspecified
    units/datum, per-axis errors) needs raw preservation.
    """
    features = {}
    if not isinstance(range_bearing, dict):
        return None, features, True
    units = enum_tail(
        range_bearing.get("coordinate_system"), "RANGE_BEARING_COORDINATE_SYSTEM_"
    )
    datum = enum_tail(range_bearing.get("datum"), "RANGE_BEARING_DATUM_")
    angle_in_radians = units in ("RADIANS_M", "RADIANS_KM")
    angle_known = units in ("DEGREES_M", "DEGREES_KM", "RADIANS_M", "RADIANS_KM")
    range_factor = {"DEGREES_M": 1.0, "RADIANS_M": 1.0, "DEGREES_KM": 1000.0, "RADIANS_KM": 1000.0}.get(units)

    fully_carried = True
    rng = range_bearing.get("range")
    if _is_number(rng):
        if range_factor is not None:
            features["range_m"] = float(rng) * range_factor
        else:
            fully_carried = False

    bearing = None
    azimuth = range_bearing.get("azimuth")
    elevation = range_bearing.get("elevation")
    if _is_number(azimuth):
        if not angle_known:
            fully_carried = False
        else:
            az_deg = math.degrees(float(azimuth)) if angle_in_radians else float(azimuth)
            el_deg = None
            if _is_number(elevation):
                el_deg = (
                    math.degrees(float(elevation)) if angle_in_radians else float(elevation)
                )
            if datum == "TRUE":
                bearing = {"az_deg": az_deg % 360.0}
                if el_deg is not None and -90.0 <= el_deg <= 90.0:
                    bearing["el_deg"] = el_deg
                elif el_deg is not None:
                    fully_carried = False
            elif datum in ("MAGNETIC", "GRID", "PLATFORM"):
                features["bearing_native_deg"] = az_deg % 360.0
                features["bearing_native_datum"] = datum
                if el_deg is not None:
                    features["bearing_native_el_deg"] = el_deg
            else:
                fully_carried = False

    if any(
        _is_number(range_bearing.get(key))
        for key in ("azimuth_error", "elevation_error", "range_error")
    ):
        fully_carried = False
    return bearing, features, fully_carried


def _canonical_rf_features(signals, signal_units):
    """Build the canonical RF feature triple from the first signal entry.

    Returns None unless the registration codex resolves centre_frequency to
    Hz/MHz/GHz AND amplitude to dBm — amplitude with non-dBm or unknown
    units is never mapped to ``power_dbm``, and unresolved units leave the
    whole signal block extension-only (contract 6.5/6.7). ``bandwidth_hz``
    is stop-start when both edges resolve; otherwise the declared 0.0
    "not measured" sentinel.
    """
    if not signals or not isinstance(signals[0], dict) or not signal_units:
        return None
    first = signals[0]

    def _freq_hz(field):
        value = first.get(field)
        units = signal_units.get(field)
        if not _is_number(value) or not isinstance(units, str):
            return None
        factor = _FREQ_FACTOR_HZ.get(units.strip().lower())
        if factor is None:
            return None
        return float(value) * factor

    center_hz = _freq_hz("centre_frequency")
    if center_hz is None:
        return None
    amplitude = first.get("amplitude")
    amplitude_units = signal_units.get("amplitude")
    if (
        not _is_number(amplitude)
        or not isinstance(amplitude_units, str)
        or amplitude_units.strip().lower() != "dbm"
    ):
        return None

    features = {"center_freq_hz": center_hz, "power_dbm": float(amplitude)}
    start_hz = _freq_hz("start_frequency")
    stop_hz = _freq_hz("stop_frequency")
    if start_hz is not None and stop_hz is not None and stop_hz >= start_hz:
        features["bandwidth_hz"] = stop_hz - start_hz
    else:
        features["bandwidth_hz"] = BANDWIDTH_SENTINEL_HZ
    return features


def _node_modality(node_types):
    # Node types with no valid v1.x observation modality (RADAR/LIDAR/
    # SEISMIC/CHEMICAL/... without a resolvable signal block) yield None:
    # no observation is emitted for them (documented degradation until the
    # queued RADAR-family feature contracts land).
    if "CAMERA" in node_types:
        return "EO"
    if "ACOUSTIC" in node_types:
        return "ACOUSTIC"
    if "CYBER" in node_types:
        return "NETWORK"
    return None


def _velocity_enu_mps(enu_velocity, registration, node_id):
    """Convert ENU velocity via the registration factor, or None.

    Returns (canonical|None, fully_carried). ``up`` is included only when
    ``up_rate`` is present AND the registration declared up-axis units.
    """
    if not isinstance(enu_velocity, dict):
        return None, True
    factor = registration.velocity_factor_mps(node_id) if registration else None
    east = enu_velocity.get("east_rate")
    north = enu_velocity.get("north_rate")
    if factor is None or not _is_number(east) or not _is_number(north):
        return None, False
    velocity = {"east": float(east) * factor, "north": float(north) * factor}
    fully_carried = not any(
        _is_number(enu_velocity.get(key))
        for key in ("east_rate_error", "north_rate_error", "up_rate_error")
    )
    up = enu_velocity.get("up_rate")
    if _is_number(up):
        up_factor = registration.velocity_factor_mps(node_id, axis="up")
        if up_factor is not None:
            velocity["up"] = float(up) * up_factor
        else:
            fully_carried = False
    return velocity, fully_carried


def _measurement_error(location, registration, node_id):
    """Map x/y/z_error to quality.measurement_error, or None.

    Mapped ONLY when the registration GeometricError clearly declares a
    standard-deviation metric in meters; the value is the conservative
    maximum of the per-axis errors (raw per-axis values are preserved in
    the vendor extension regardless).
    """
    errors = [
        float(location[key])
        for key in ("x_error", "y_error", "z_error")
        if _is_number(location.get(key))
    ]
    if not errors or registration is None:
        return None
    declared = registration.geometric_error(node_id)
    if not declared:
        return None
    error_type = declared.get("type")
    error_units = declared.get("units")
    if not isinstance(error_type, str) or not isinstance(error_units, str):
        return None
    if "standard deviation" not in error_type.strip().lower():
        return None
    if error_units.strip().lower() not in ("m", "metre", "metres", "meter", "meters"):
        return None
    return {"value": max(errors), "unit": "m", "metric": "1_SIGMA"}


def _location_errors(location):
    errors = {
        key: location[key]
        for key in ("x_error", "y_error", "z_error")
        if _is_number(location.get(key))
    }
    return errors or None


def _inference_event(
    *,
    node_id,
    ts,
    subtype,
    claim,
    confidence,
    model,
    parents,
    timing,
    vendor_ext,
):
    event = _envelope("INFERENCE_EVENT", subtype, ts, node_id)
    event["payload"] = {
        "inference_type": subtype,
        "claim": claim,
        "model": dict(model),
        "based_on": list(parents),
        "timing_quality": dict(timing),
        "extensions": {VENDOR_EXTENSION_KEY: _drop_non_finite(vendor_ext)},
    }
    event["confidence"] = confidence
    event["lineage"] = {
        "based_on": list(parents),
        "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
    }
    return event


def _translate_detection(
    body, node_id, ts, *, registration, based_on, timing_quality, promotion, active_mode, valid_for_ms
):
    # Fusion determination: registration knowledge wins; the promotion
    # kwarg asserts a fusion-node feed only when the store does not know
    # the node as a (non-fusion) sensor.
    known_types = registration.node_types(node_id) if registration else []
    known_fusion = "FUSION_NODE" in known_types
    if known_fusion or (promotion is not None and not known_types):
        return _promote_fusion_detection(
            body,
            node_id,
            ts,
            registration=registration,
            based_on=based_on,
            timing_quality=timing_quality,
            promotion=promotion,
            active_mode=active_mode,
            valid_for_ms=valid_for_ms,
        )

    timing = _timing(timing_quality, ts, registration, node_id, active_mode)
    node_types = registration.node_types(node_id) if registration else []
    signals = [entry for entry in body.get("signal") or [] if isinstance(entry, dict)]
    signal_units = registration.signal_units(node_id) if registration else {}
    rf_features = _canonical_rf_features(signals, signal_units)
    modality = "RF" if rf_features else _node_modality(node_types)

    location = body.get("location") if isinstance(body.get("location"), dict) else None
    geo, geo_reason = _canonical_geo(location)
    bearing, rb_features, rb_fully_carried = _range_bearing_map(body.get("range_bearing"))
    velocity, velocity_fully_carried = _velocity_enu_mps(
        body.get("enu_velocity"), registration, node_id
    )

    # Provenance block: native ids/fields actually present, keyed to avoid
    # the observation denylist names (confidence/classification/track_id/
    # entity_class/label). object_id is a NON-authoritative correlation
    # hint, never a track_id.
    vendor_ext = {}
    for key in (
        "report_id",
        "object_id",
        "task_id",
        "state",
        "id",
        "detection_confidence",
        "prediction_location",
        "associated_detection",
        "derived_detection",
        "associated_file",
        "track_info",
        "object_info",
    ):
        if body.get(key) is not None:
            vendor_ext[key] = body[key]
    if body.get("classification"):
        vendor_ext["native_classification"] = body["classification"]
    if body.get("behaviour"):
        vendor_ext["native_behaviour"] = body["behaviour"]
    if signals and rf_features is None:
        vendor_ext["signal"] = signals
    elif len(signals) > 1:
        # Canonical RF features map from signal[0] only; further entries
        # (additional emitters) are preserved verbatim, never dropped.
        vendor_ext["signal_additional"] = signals[1:]
    if body.get("enu_velocity") is not None and (velocity is None or not velocity_fully_carried):
        vendor_ext["enu_velocity"] = body["enu_velocity"]
    if location is not None and geo is None:
        vendor_ext["location"] = dict(location)
        if geo_reason is not None:
            vendor_ext["location"]["omitted_reason"] = geo_reason
    elif location is not None and _location_errors(location):
        vendor_ext["location_errors"] = _location_errors(location)
    if isinstance(body.get("range_bearing"), dict) and not rb_fully_carried:
        vendor_ext["range_bearing"] = body["range_bearing"]
    # proto3 JSON permits "NaN"/"Infinity" float values; a bare NaN in the
    # verbatim native block poisons RFC-8259 serialization of the whole
    # event downstream. A non-finite number is a non-claim — omit the key.
    # Applied at each point of use below (not once here), so a later
    # mutation of vendor_ext cannot silently bypass the guard.

    events = []
    observation_id = None
    if modality is not None:
        features = dict(rf_features) if rf_features else {}
        features.update(rb_features)
        if velocity is not None:
            features["velocity_enu_mps"] = velocity
        colour = body.get("colour")
        if isinstance(colour, str) and colour:
            if modality in ("EO", "IR"):
                features["colour"] = colour
            else:
                vendor_ext["colour"] = colour

        quality = {"geo_status": "AVAILABLE" if geo else "UNAVAILABLE"}
        if bearing is not None:
            quality["bearing_frame"] = "TRUE_NORTH"
        if location is not None and geo is not None:
            error = _measurement_error(location, registration, node_id)
            if error is not None:
                quality["measurement_error"] = error

        event = _envelope("OBSERVATION_EVENT", modality, ts, node_id)
        payload = {
            "modality": modality,
            "features": features,
            "quality": quality,
            "timing_quality": dict(timing),
            "extensions": {VENDOR_EXTENSION_KEY: _drop_non_finite(vendor_ext)},
        }
        if geo is not None:
            payload["geo"] = geo
        if bearing is not None:
            payload["bearing"] = bearing
        event["payload"] = payload
        if based_on:
            event["lineage"] = _translate_lineage(based_on)
        observation_id = event["event"]["event_id"]
        events.append(event)

    # Inference emission requires real model identity (contract 7.5) and a
    # real parent: the observation emitted in this same call, else caller
    # lineage. Neither is ever fabricated (contract 4.8) — without both,
    # native classification/behaviour stay extension-only.
    model = registration.model_identity(node_id) if registration else None
    if observation_id is not None:
        parents = [observation_id]
    elif based_on:
        parents = [str(item) for item in based_on]
    else:
        parents = None
    if model is not None and parents is not None:
        inference_ext = {
            key: body[key] for key in ("report_id", "object_id") if body.get(key) is not None
        }
        for entry in body.get("classification") or []:
            if not isinstance(entry, dict):
                continue
            entry_type = entry.get("type")
            confidence = entry.get("confidence")
            # Inference confidence is schema-required (contract 8.1): an
            # entry without one is refused, never defaulted.
            if not isinstance(entry_type, str) or not entry_type or not _is_number(confidence):
                continue
            claim = {"type": entry_type}
            if entry.get("sub_class"):
                claim["sub_class"] = entry["sub_class"]
            events.append(
                _inference_event(
                    node_id=node_id,
                    ts=ts,
                    subtype="CLASSIFICATION",
                    claim=claim,
                    confidence=confidence,
                    model=model,
                    parents=parents,
                    timing=timing,
                    vendor_ext=inference_ext,
                )
            )
        for entry in body.get("behaviour") or []:
            if not isinstance(entry, dict):
                continue
            entry_type = entry.get("type")
            confidence = entry.get("confidence")
            if not isinstance(entry_type, str) or not entry_type or not _is_number(confidence):
                continue
            events.append(
                _inference_event(
                    node_id=node_id,
                    ts=ts,
                    subtype="BEHAVIOR",
                    claim={"type": entry_type},
                    confidence=confidence,
                    model=model,
                    parents=parents,
                    timing=timing,
                    vendor_ext=inference_ext,
                )
            )
        detection_confidence = body.get("detection_confidence")
        if observation_id is not None and _is_number(detection_confidence):
            events.append(
                _inference_event(
                    node_id=node_id,
                    ts=ts,
                    subtype="CLASSIFICATION",
                    claim={"claim_type": "object_present"},
                    confidence=detection_confidence,
                    model=model,
                    parents=[observation_id],
                    timing=timing,
                    vendor_ext=inference_ext,
                )
            )
    return events


def _promote_fusion_detection(
    body, node_id, ts, *, registration, based_on, timing_quality, promotion, active_mode, valid_for_ms
):
    """Promote a fusion-node DetectionReport to STATE_EVENT/TRACK_STATE.

    The contract 4.5.1 gate: caller-supplied ``promotion`` metadata is
    REQUIRED — without it the detection is refused outright, never silently
    downgraded to an observation. ``promotion["loop_status"]`` is likewise
    caller-required: it is a verification claim (reflection check) the
    adapter never performs, so it is never self-asserted — this gateway's
    own SAPIENT egress makes a fusion node re-reporting an exported track a
    live reflection scenario. STATE_EVENT additionally requires real
    lineage, an explicit external confidence, and full canonical geo; any
    of these missing refuses the promotion (contract 4.8, 7.7, 8.1).
    Confidence is the SAPIENT ``detection_confidence`` as-is — never
    increased (contract 4.5.1).
    """
    if not isinstance(promotion, dict):
        return []
    loop_status = promotion.get("loop_status")
    if not isinstance(loop_status, str) or not loop_status:
        return []
    if not based_on:
        return []
    confidence = body.get("detection_confidence")
    if not _is_number(confidence):
        return []
    object_id = body.get("object_id")
    if not isinstance(object_id, str) or not object_id:
        return []
    geo, _reason = _canonical_geo(body.get("location"))
    if geo is None:
        return []

    # Caller-supplied promotion evidence wins key-by-key, but only within
    # the enumerated promotion vocabulary (contract 4.5.1): promotion
    # metadata must never smuggle raw measurements, observation features,
    # or unenumerated keys into STATE. Unknown keys refuse the promotion
    # (fail closed) rather than merging or silently dropping. Unlike the
    # CoT template (fixed key set, message-carried values), this whole
    # dict is caller-supplied — which is why it is allowlisted.
    allowed_caller_keys = {
        "loop_status",
        "state_category",
        "origin_kind",
        "projection_id",
        "promotion_policy_id",
        "trust_ref",
        "lineage_status",
        "confidence_basis",
        "source_event_uid",
        "freshness_ms",
    }
    if set(promotion) - allowed_caller_keys:
        return []
    promotion_meta = {
        "state_category": "PROMOTED_EXTERNAL_STATE",
        "origin_kind": "EXTERNAL_REPORT",
        "projection_id": "sapient",
        "promotion_policy_id": PROMOTION_POLICY_ID,
        "trust_ref": f"producer-authority:{PRODUCER}",
        "lineage_status": "EXTERNAL_SOURCE",
        "confidence_basis": "EXPLICIT_EXTERNAL_CONFIDENCE",
        "source_event_uid": object_id,
        "freshness_ms": valid_for_ms,
    }
    promotion_meta.update({key: value for key, value in promotion.items() if value is not None})

    # STATE carries no raw artifacts (contract 7.7): the vendor block keeps
    # compact native ids only — never signal, track_info, or features.
    vendor_ext = {
        key: body[key]
        for key in ("report_id", "object_id", "task_id", "state", "detection_confidence")
        if body.get(key) is not None
    }

    best_class = None
    best_confidence = -1.0
    for entry in body.get("classification") or []:
        if not isinstance(entry, dict):
            continue
        entry_type = entry.get("type")
        if not isinstance(entry_type, str) or not entry_type:
            continue
        entry_confidence = entry.get("confidence") if _is_number(entry.get("confidence")) else -0.5
        if entry_confidence > best_confidence:
            best_confidence = entry_confidence
            best_class = entry_type

    event = _envelope("STATE_EVENT", "TRACK_STATE", ts, node_id, node_role="GATEWAY")
    payload = {
        "track_id": object_id,
        "geo": geo,
        "valid_for_ms": int(valid_for_ms),
        "timing_quality": _timing(timing_quality, ts, registration, node_id, active_mode),
        "extensions": {
            "external_promotion": promotion_meta,
            VENDOR_EXTENSION_KEY: _drop_non_finite(vendor_ext),
        },
    }
    if best_class is not None:
        payload["class"] = best_class
    event["payload"] = payload
    event["confidence"] = confidence
    event["lineage"] = {
        "based_on": [str(item) for item in based_on],
        "transform": f"promote:sapient@{ADAPTER_VERSION}:{promotion_meta['promotion_policy_id']}",
    }
    return [event]


def _translate_status(body, node_id, ts, *, registration, active_mode):
    system_tail = enum_tail(body.get("system"), "SYSTEM_")
    state = _SENSOR_STATE.get(system_tail, "UNKNOWN")
    status_entries = [
        entry for entry in body.get("status") or [] if isinstance(entry, dict)
    ]
    has_fault = any(
        enum_tail(entry.get("status_type"), "STATUS_TYPE_") in _FAULT_STATUS_TYPES
        for entry in status_entries
    )
    if has_fault and state in ("ACTIVE", "UNKNOWN"):
        state = "DEGRADED"

    metrics = {"sensor_id": node_id}
    mode = body.get("mode")
    if isinstance(mode, str) and mode:
        metrics["mode"] = mode

    # fov_deg only from a TRUE-datum range-bearing cone with a horizontal
    # extent in a degrees-family coordinate system; anything else is omitted
    # rather than fabricated.
    fov = body.get("field_of_view")
    fov_mapped = False
    if isinstance(fov, dict) and isinstance(fov.get("range_bearing"), dict):
        cone = fov["range_bearing"]
        cone_units = enum_tail(
            cone.get("coordinate_system"), "RANGE_BEARING_COORDINATE_SYSTEM_"
        )
        cone_datum = enum_tail(cone.get("datum"), "RANGE_BEARING_DATUM_")
        extent = cone.get("horizontal_extent")
        if (
            cone_datum == "TRUE"
            and cone_units in ("DEGREES_M", "DEGREES_KM")
            and _is_number(extent)
            and 0.0 <= float(extent) <= 360.0
        ):
            metrics["fov_deg"] = float(extent)
            fov_mapped = True

    vendor_ext = {}
    for key in ("report_id", "active_task_id", "info"):
        if body.get(key) is not None:
            vendor_ext[key] = body[key]
    if status_entries:
        vendor_ext["status"] = status_entries
    if fov is not None and not fov_mapped:
        vendor_ext["field_of_view"] = fov
    # No kernel home for these: extension-only, never canonical geo.
    for key in ("node_location", "coverage", "obscuration"):
        if body.get(key) is not None:
            vendor_ext[key] = body[key]

    sensor_event = _envelope(
        "SYSTEM_EVENT", "SENSOR_STATUS", ts, node_id, zmeta_version="1.1.0"
    )
    sensor_event["payload"] = {
        "system_type": "SENSOR_STATUS",
        "state": state,
        "metrics": metrics,
        "extensions": {VENDOR_EXTENSION_KEY: _drop_non_finite(vendor_ext)},
    }
    events = [sensor_event]

    power = body.get("power")
    if isinstance(power, dict):
        platform_metrics = {}
        level = power.get("level")
        if _is_number(level) and 0 <= level <= 100:
            platform_metrics["battery_pct"] = int(level)
        power_state = _POWER_STATE.get(enum_tail(power.get("source"), "POWERSOURCE_"))
        if power_state is not None:
            platform_metrics["power_state"] = power_state
        # PLATFORM_STATUS metrics require at least one power fact; a power
        # block that maps to none is refused, not padded.
        if platform_metrics:
            status_tail = enum_tail(power.get("status"), "POWERSTATUS_")
            platform_state = {"OK": "NOMINAL", "FAULT": "WARNING"}.get(status_tail, "UNKNOWN")
            platform_event = _envelope(
                "SYSTEM_EVENT", "PLATFORM_STATUS", ts, node_id, zmeta_version="1.1.0"
            )
            platform_event["payload"] = {
                "system_type": "PLATFORM_STATUS",
                "state": platform_state,
                "metrics": platform_metrics,
                "extensions": {
                    VENDOR_EXTENSION_KEY: _drop_non_finite({"power": power})
                },
            }
            events.append(platform_event)
    return events


def _translate_alert(body, node_id, ts, *, registration, based_on, timing_quality, active_mode):
    """Alert -> INFERENCE_EVENT/ANOMALY, or refusal.

    Requires registration model identity (contract 7.5), the alert's own
    confidence (8.1), and caller-supplied real lineage — SAPIENT
    ``associated_detection`` references are object-scoped, not ZMeta event
    ids, so an unresolved association means no lineage and therefore no
    event (contract 4.8: mandatory-lineage families refuse, never invent).
    """
    model = registration.model_identity(node_id) if registration else None
    if model is None:
        return []
    confidence = body.get("confidence")
    if not _is_number(confidence):
        return []
    if not based_on:
        return []

    claim = {}
    alert_type = enum_tail(body.get("alert_type"), "ALERT_TYPE_")
    if alert_type is not None:
        claim["alert_type"] = alert_type
    description = body.get("description")
    if isinstance(description, str) and description:
        claim["description"] = description
    region_id = body.get("region_id")
    if isinstance(region_id, str) and region_id:
        claim["region_id"] = region_id
    geo, geo_reason = _canonical_geo(body.get("location"))
    if geo is not None:
        claim["geo"] = geo

    vendor_ext = {}
    for key in (
        "alert_id",
        "status",
        "priority",
        "ranking",
        "associated_file",
        "associated_detection",
        "additional_information",
    ):
        if body.get(key) is not None:
            vendor_ext[key] = body[key]
    if isinstance(body.get("location"), dict) and geo is None:
        vendor_ext["location"] = dict(body["location"])
        if geo_reason is not None:
            vendor_ext["location"]["omitted_reason"] = geo_reason
    if body.get("range_bearing") is not None:
        vendor_ext["range_bearing"] = body["range_bearing"]

    parents = [str(item) for item in based_on]
    event = _inference_event(
        node_id=node_id,
        ts=ts,
        subtype="ANOMALY",
        claim=claim,
        confidence=confidence,
        model=model,
        parents=parents,
        timing=_timing(timing_quality, ts, registration, node_id, active_mode),
        vendor_ext=vendor_ext,
    )
    event["payload"]["inference_type"] = "ANOMALY"
    return [event]


def _translate_task_ack(body, node_id, ts, *, task_index, based_on):
    """TaskAck -> SYSTEM_EVENT/TASK_ACK, or refusal.

    ``metrics.original_event_id`` must be the real originating COMMAND
    event id, resolved through the caller's ``task_index``; an
    unresolvable task_id refuses the ack — the correlation is never
    fabricated. TASK_STATUS_UNSPECIFIED refuses (no honest state).
    """
    task_id = body.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        return []
    mapped = _TASK_ACK_STATE.get(enum_tail(body.get("task_status"), "TASK_STATUS_"))
    if mapped is None:
        return []
    if not isinstance(task_index, dict):
        return []
    original_event_id = task_index.get(task_id)
    if not isinstance(original_event_id, str) or not original_event_id:
        # A present-but-null/empty mapping is as unresolvable as a missing
        # one; str()-coercing it would fabricate the literal "None" as a
        # correlation id (the R1-10 A1 class).
        return []
    state, reason_code = mapped

    metrics = {"task_id": task_id, "original_event_id": original_event_id}
    if reason_code is not None:
        metrics["reason_code"] = reason_code
    reasons = [item for item in body.get("reason") or [] if isinstance(item, str) and item]
    if reasons:
        metrics["error"] = "; ".join(reasons)

    vendor_ext = {"task_id": task_id}
    if body.get("associated_file") is not None:
        vendor_ext["associated_file"] = body["associated_file"]

    event = _envelope("SYSTEM_EVENT", "TASK_ACK", ts, node_id)
    event["payload"] = {
        "system_type": "TASK_ACK",
        "state": state,
        "metrics": metrics,
        "extensions": {VENDOR_EXTENSION_KEY: _drop_non_finite(vendor_ext)},
    }
    if based_on:
        event["lineage"] = _translate_lineage(based_on)
    return [event]


def _translate_error(body, node_id, ts):
    """Error -> SYSTEM_EVENT/SCHEMA_VIOLATION.

    SAPIENT Error carries the offending packet, not a ZMeta event id, so
    ``metrics.original_event_id`` uses the gateway's documented "UNKNOWN"
    sentinel (gateway/src/gateway.py precedent) — an adapter-synthesized
    correlation id is forbidden.
    """
    metrics = {"reason_code": "SCHEMA_INVALID", "original_event_id": "UNKNOWN"}
    messages = [
        item for item in body.get("error_message") or [] if isinstance(item, str) and item
    ]
    if messages:
        metrics["error"] = "; ".join(messages)

    vendor_ext = {}
    if body.get("packet") is not None:
        vendor_ext["packet"] = body["packet"]

    event = _envelope("SYSTEM_EVENT", "SCHEMA_VIOLATION", ts, node_id)
    event["payload"] = {
        "system_type": "SCHEMA_VIOLATION",
        "state": "REJECTED",
        "metrics": metrics,
    }
    if vendor_ext:
        event["payload"]["extensions"] = {
            VENDOR_EXTENSION_KEY: _drop_non_finite(vendor_ext)
        }
    return [event]


def translate(
    input_obj,
    schema_id,
    *,
    registration=None,
    based_on=None,
    timing_quality=None,
    promotion=None,
    task_index=None,
    active_mode=None,
    valid_for_ms=DEFAULT_VALID_FOR_MS,
):
    """Translate one SapientMessage dict into ZMeta events.

    Returns a list of events — the subset of the message that can be
    honestly emitted — or ``[]`` when nothing can (fail closed; contract
    3.4). Envelope refusals: a missing/unparseable ``timestamp`` or a
    null/missing ``node_id`` refuses the whole message (identity is never
    fabricated).

    Args:
        input_obj: SapientMessage as a protobuf-JSON dict; lowerCamelCase
            and snake_case keys are both accepted.
        schema_id: must be ``vendor:sapient_bsi335:v2``.
        registration: optional RegistrationStore holding this node's
            Registration capture. Without it, unit-bearing fields stay in
            the vendor extension, no inference events are emitted (no
            model identity), and node-type modality is unknown.
            Registration content messages are ingested into this store.
        based_on: optional list of real parent ZMeta event ids (UUIDv7).
            Lineage comes only from here or from an observation emitted in
            the same call; it is never fabricated (contract 4.8).
        timing_quality: optional source timing metadata; the degraded
            UNKNOWN/UNSYNCED fallback applies otherwise, and either way
            ``est_error_ms`` widens by the registration-declared
            ``maximum_latency`` (envelope ts is send time).
        promotion: caller-supplied external-promotion metadata dict —
            REQUIRED for fusion-node detections to be promoted to
            STATE_EVENT; absent means the detection is refused, never
            downgraded to an observation. Must include ``loop_status``
            (the caller's reflection-check verdict): the adapter never
            performs that check, so it never asserts one.
        task_index: dict mapping SAPIENT task_id -> originating ZMeta
            COMMAND event_id; required to emit TASK_ACK.
        active_mode: the node's active SAPIENT mode name; scopes the
            timing widen to that mode's declared latency. When None — or
            when the name matches no declared mode with a resolvable
            latency — the maximum across declared modes applies
            (conservative; a mismatched mode name never shrinks the
            claimed error).
        valid_for_ms: TTL for promoted STATE_EVENTs (default 5000, same as
            the CoT template).

    Detection event order: observation first, then classification
    inferences (input order), behaviour inferences, and the
    detection-existence claim last.
    """
    if schema_id != SCHEMA_ID or not isinstance(input_obj, dict):
        return []
    msg = snake_keys(input_obj)
    node_id = msg.get("node_id")
    if not isinstance(node_id, str) or not node_id:
        return []
    ts = _envelope_ts(msg.get("timestamp"))
    if ts is None:
        return []
    content = _content(msg)
    if content is None:
        return []
    key, body = content

    if key == "registration":
        if registration is not None:
            registration.ingest(msg)
        return []
    if key in _NO_EVENT_CONTENT:
        return []
    if key == "detection_report":
        return _translate_detection(
            body,
            node_id,
            ts,
            registration=registration,
            based_on=based_on,
            timing_quality=timing_quality,
            promotion=promotion,
            active_mode=active_mode,
            valid_for_ms=valid_for_ms,
        )
    if key == "status_report":
        return _translate_status(
            body, node_id, ts, registration=registration, active_mode=active_mode
        )
    if key == "alert":
        return _translate_alert(
            body,
            node_id,
            ts,
            registration=registration,
            based_on=based_on,
            timing_quality=timing_quality,
            active_mode=active_mode,
        )
    if key == "task_ack":
        return _translate_task_ack(body, node_id, ts, task_index=task_index, based_on=based_on)
    if key == "error":
        return _translate_error(body, node_id, ts)
    return []


def validate(zmeta_event):
    """Validate one event against its declared schema branch.

    Version-aware: selects the locked v1.0 or the v1.1.0 extension schema
    per the event's ``zmeta_version`` (both loaded lazily). Returns
    ("pass", []) or ("fail", [violation strings]).
    """
    import jsonschema

    version = zmeta_event.get("zmeta_version") if isinstance(zmeta_event, dict) else None
    filename = _SCHEMA_FILES.get(version)
    if filename is None:
        return ("fail", [f"zmeta_version: unsupported version {version!r}"])
    if filename not in _schema_cache:
        _schema_cache[filename] = json.loads(
            (_SCHEMA_DIR / filename).read_text(encoding="utf-8")
        )
    validator = jsonschema.Draft202012Validator(_schema_cache[filename])
    violations = [
        f"{'/'.join(str(part) for part in error.absolute_path)}: {error.message}"
        for error in validator.iter_errors(zmeta_event)
    ]
    return ("pass", []) if not violations else ("fail", violations)
