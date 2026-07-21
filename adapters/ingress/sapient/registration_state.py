"""SAPIENT (BSI Flex 335 v2.0) Registration capture for the ingress adapter.

SAPIENT declares units, error statistics, taxonomy, modes, and node identity
out-of-band in the Registration message; DetectionReports then carry bare
numbers. ZMeta forbids unit inference (contract 6.7), so the registration
codex is a first-class adapter component: without a captured Registration,
signal/velocity/error values cannot be honestly mapped to canonical fields
and stay extension-only or are refused.

``RegistrationStore`` is a plain in-memory class (no persistence). Feed it
SapientMessage dicts (protobuf-JSON, lowerCamelCase or snake_case keys) via
``ingest()``; only ``registration`` content is captured. Lookups return
``None`` for anything the registration did not clearly declare — unknown or
conflicting declarations are never resolved by guessing.
"""

import re

__all__ = ["RegistrationStore", "snake_keys"]

_CAMEL_RE = re.compile(r"(?<=[a-z0-9])([A-Z])")

# TimeUnits -> milliseconds. Unknown units yield None, never a guessed scale.
_TIME_UNIT_MS = {
    "NANOSECONDS": 1e-6,
    "MICROSECONDS": 1e-3,
    "MILLISECONDS": 1.0,
    "SECONDS": 1000.0,
    "MINUTES": 60_000.0,
    "HOURS": 3_600_000.0,
    "DAYS": 86_400_000.0,
}

# ENUVelocityUnits SpeedUnits -> factor to m/s. Unknown units yield None.
_SPEED_FACTOR_MPS = {
    "MS": 1.0,
    "KPH": 1.0 / 3.6,
}

# Poison marker for conflicting declarations across modes: a value the
# registration contradicts itself on is unresolvable, not first-wins.
_CONFLICT = object()


def _snake(name):
    return _CAMEL_RE.sub(lambda m: "_" + m.group(1), name).lower()


def snake_keys(obj):
    """Recursively normalize dict keys from lowerCamelCase to snake_case.

    Values are never touched (enum strings stay verbatim); lists and nested
    dicts are traversed.
    """
    if isinstance(obj, dict):
        return {
            (_snake(key) if isinstance(key, str) else key): snake_keys(value)
            for key, value in obj.items()
        }
    if isinstance(obj, list):
        return [snake_keys(item) for item in obj]
    return obj


def enum_tail(value, prefix):
    """Return a proto enum value's short tail, accepting long or short form.

    ``enum_tail("LOCATION_DATUM_WGS84_E", "LOCATION_DATUM_")`` and
    ``enum_tail("WGS84_E", "LOCATION_DATUM_")`` both yield ``"WGS84_E"``.
    Non-string values (including protobuf-JSON integer enums) yield None:
    numeric enum decoding is the upstream decoder's job, not something this
    adapter guesses at.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().upper()
    prefix = prefix.upper()
    if text.startswith(prefix):
        text = text[len(prefix):]
    return text or None


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def duration_ms(duration):
    """Convert a SAPIENT Registration.Duration dict to milliseconds.

    Returns None when units are unknown/unspecified or the value is not
    numeric — a duration is never guessed.
    """
    if not isinstance(duration, dict):
        return None
    unit = enum_tail(duration.get("units"), "TIME_UNITS_")
    factor = _TIME_UNIT_MS.get(unit)
    value = duration.get("value")
    if factor is None or not _is_number(value):
        return None
    return float(value) * factor


def _merge(mapping, key, value):
    # Conflicting redeclaration poisons the key; lookups then return None.
    if key in mapping and mapping[key] != value:
        mapping[key] = _CONFLICT
    else:
        mapping.setdefault(key, value)


def _collect_class_names(definitions, into):
    for definition in definitions or []:
        if not isinstance(definition, dict):
            continue
        name = definition.get("type")
        if isinstance(name, str) and name:
            into.add(name)
        _collect_class_names(definition.get("sub_class"), into)


class RegistrationStore:
    """Per-node capture of SAPIENT Registration declarations.

    Captures, per node_id: node types and the fusion-node flag, model
    identity from config_data, mode latency/settle/tracking declarations,
    declared per-field units (the signal/track/object codex), ENU velocity
    unit factors, geometric-error statistics labeling, and declared
    class/behaviour taxonomy names (pack evidence; not enforced at runtime).
    """

    def __init__(self):
        self._nodes = {}

    def ingest(self, msg_dict):
        """Capture one SapientMessage carrying registration content.

        Returns the node_id on capture, None when the message is not a
        registration or lacks a usable node identity (nothing is stored for
        an anonymous registration — identity is never fabricated).
        """
        if not isinstance(msg_dict, dict):
            return None
        msg = snake_keys(msg_dict)
        node_id = msg.get("node_id")
        registration = msg.get("registration")
        if not isinstance(node_id, str) or not node_id or not isinstance(registration, dict):
            return None

        node_types = []
        for definition in registration.get("node_definition") or []:
            if not isinstance(definition, dict):
                continue
            tail = enum_tail(definition.get("node_type"), "NODE_TYPE_")
            if tail is not None:
                node_types.append(tail)

        model = None
        for config in registration.get("config_data") or []:
            if not isinstance(config, dict):
                continue
            manufacturer = config.get("manufacturer")
            model_name = config.get("model")
            if (
                isinstance(manufacturer, str) and manufacturer
                and isinstance(model_name, str) and model_name
            ):
                software_version = config.get("software_version")
                model = {
                    "name": f"{manufacturer} {model_name}",
                    "version": software_version
                    if isinstance(software_version, str) and software_version
                    else "unknown",
                }
            break

        modes = {}
        declared_units = {}
        velocity_factors = {}
        geometric_error = {}
        class_names = set()
        behaviour_names = set()

        for mode in registration.get("mode_definition") or []:
            if not isinstance(mode, dict):
                continue
            mode_name = mode.get("mode_name")
            if isinstance(mode_name, str) and mode_name:
                modes[mode_name] = {
                    "maximum_latency_ms": duration_ms(mode.get("maximum_latency")),
                    "settle_time_ms": duration_ms(mode.get("settle_time")),
                    "tracking_type": enum_tail(mode.get("tracking_type"), "TRACKING_TYPE_"),
                }
            for detection_definition in mode.get("detection_definition") or []:
                if not isinstance(detection_definition, dict):
                    continue
                for report in detection_definition.get("detection_report") or []:
                    if not isinstance(report, dict):
                        continue
                    category = enum_tail(
                        report.get("category"), "DETECTION_REPORT_CATEGORY_"
                    )
                    field_type = report.get("type")
                    units = report.get("units")
                    if category and isinstance(field_type, str) and field_type:
                        _merge(declared_units, (category, field_type.strip().lower()), units)
                velocity_type = detection_definition.get("velocity_type")
                if isinstance(velocity_type, dict):
                    enu_units = velocity_type.get("enu_velocity_units")
                    if isinstance(enu_units, dict):
                        _merge(
                            velocity_factors,
                            "east_north",
                            _SPEED_FACTOR_MPS.get(
                                enum_tail(
                                    enu_units.get("east_north_rate_units"), "SPEED_UNITS_"
                                )
                            ),
                        )
                        up_tail = enum_tail(enu_units.get("up_rate_units"), "SPEED_UNITS_")
                        if up_tail is not None:
                            _merge(velocity_factors, "up", _SPEED_FACTOR_MPS.get(up_tail))
                error = detection_definition.get("geometric_error")
                if isinstance(error, dict):
                    _merge(geometric_error, "type", error.get("type"))
                    _merge(geometric_error, "units", error.get("units"))
                for class_block in detection_definition.get("detection_class_definition") or []:
                    if isinstance(class_block, dict):
                        _collect_class_names(
                            class_block.get("class_definition"), class_names
                        )
                for behaviour in detection_definition.get("behaviour_definition") or []:
                    if isinstance(behaviour, dict):
                        name = behaviour.get("type")
                        if isinstance(name, str) and name:
                            behaviour_names.add(name)

        self._nodes[node_id] = {
            "node_types": node_types,
            "is_fusion_node": "FUSION_NODE" in node_types,
            "model": model,
            "modes": modes,
            "declared_units": declared_units,
            "velocity_factors": velocity_factors,
            "geometric_error": geometric_error,
            "class_names": sorted(class_names),
            "behaviour_names": sorted(behaviour_names),
        }
        return node_id

    def _node(self, node_id):
        return self._nodes.get(node_id)

    def node_types(self, node_id):
        node = self._node(node_id)
        return list(node["node_types"]) if node else []

    def is_fusion(self, node_id):
        node = self._node(node_id)
        return bool(node and node["is_fusion_node"])

    def model_identity(self, node_id):
        """Return {"name", "version"} from config_data, or None.

        None when the node never registered or registered without usable
        config_data — model identity is never synthesized from thin air
        (contract 7.5 / 11.1).
        """
        node = self._node(node_id)
        return dict(node["model"]) if node and node["model"] else None

    def max_latency_ms(self, node_id, mode=None):
        """Declared maximum detection->send latency in ms, or None.

        ``mode=None`` takes the maximum across all declared modes — the
        conservative bound when the active mode is unknown. A ``mode`` the
        registration did not declare, or declared without a resolvable
        latency, takes that same cross-mode maximum: an unmatched mode name
        must never yield a smaller error bound than no mode at all.
        """
        node = self._node(node_id)
        if not node:
            return None
        if mode is not None:
            entry = node["modes"].get(mode)
            if entry and entry["maximum_latency_ms"] is not None:
                return entry["maximum_latency_ms"]
        values = [
            entry["maximum_latency_ms"]
            for entry in node["modes"].values()
            if entry["maximum_latency_ms"] is not None
        ]
        return max(values) if values else None

    def declared_units(self, node_id):
        """Full units codex: {(category, type_lowercase): units_string}.

        Conflicting redeclarations resolve to None (unresolvable).
        """
        node = self._node(node_id)
        if not node:
            return {}
        return {
            key: (None if value is _CONFLICT else value)
            for key, value in node["declared_units"].items()
        }

    def signal_units(self, node_id):
        """Signal-category units only: {type_lowercase: units_string|None}."""
        return {
            field_type: units
            for (category, field_type), units in self.declared_units(node_id).items()
            if category == "SIGNAL"
        }

    def velocity_factor_mps(self, node_id, axis="east_north"):
        """Factor converting declared ENU velocity units to m/s, or None."""
        node = self._node(node_id)
        if not node:
            return None
        value = node["velocity_factors"].get(axis)
        return None if value is _CONFLICT else value

    def geometric_error(self, node_id):
        """Declared GeometricError {"type", "units"} labeling, or None."""
        node = self._node(node_id)
        if not node or not node["geometric_error"]:
            return None
        resolved = {
            key: (None if value is _CONFLICT else value)
            for key, value in node["geometric_error"].items()
        }
        return resolved if any(resolved.values()) else None

    def taxonomy(self, node_id):
        """Declared class/behaviour names (evidence only, not enforced)."""
        node = self._node(node_id)
        if not node:
            return {"classes": [], "behaviours": []}
        return {
            "classes": list(node["class_names"]),
            "behaviours": list(node["behaviour_names"]),
        }
