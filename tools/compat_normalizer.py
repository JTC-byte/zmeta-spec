from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CompatibilityOptions:
    allow_version_alias: bool = False
    convert_endurance_seconds: bool = False
    rename_eo_bbox_roi: bool = False


class CompatibilityNormalizationError(ValueError):
    def __init__(self, code: str, message: str, path: str | None = None):
        super().__init__(message)
        self.code = code
        self.path = path

    def to_dict(self) -> dict[str, str]:
        data = {"code": self.code, "message": str(self)}
        if self.path:
            data["path"] = self.path
        return data


def normalize_event(
    event: dict[str, Any],
    options: CompatibilityOptions | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Normalize known legacy wire forms before normative schema validation.

    This helper is intentionally conservative. It never mutates the input event
    and only applies transforms that the caller explicitly enables.
    """

    if not isinstance(event, dict):
        raise CompatibilityNormalizationError(
            "COMPAT_INPUT_NOT_OBJECT",
            "Compatibility normalizer expects one JSON object event.",
            "$",
        )

    options = options or CompatibilityOptions()
    original = deepcopy(event)
    normalized = deepcopy(event)
    changes: list[dict[str, Any]] = []

    _normalize_version_alias(normalized, options, changes)
    _normalize_platform_endurance(normalized, options, changes)
    _normalize_eo_bbox_roi(normalized, options, changes)
    _assert_protected_fields_unchanged(original, normalized)

    return normalized, changes


def _normalize_version_alias(
    event: dict[str, Any],
    options: CompatibilityOptions,
    changes: list[dict[str, Any]],
) -> None:
    version = event.get("zmeta_version")
    if version == "1.1":
        if not options.allow_version_alias:
            raise CompatibilityNormalizationError(
                "COMPAT_VERSION_ALIAS_DISABLED",
                'zmeta_version "1.1" requires allow_version_alias.',
                "$.zmeta_version",
            )
        event["zmeta_version"] = "1.1.0"
        _record_change(
            changes,
            "$.zmeta_version",
            "1.1",
            "1.1.0",
            "Normalized minor version alias before schema validation.",
        )


def _normalize_platform_endurance(
    event: dict[str, Any],
    options: CompatibilityOptions,
    changes: list[dict[str, Any]],
) -> None:
    payload = event.get("payload")
    if not isinstance(payload, dict) or payload.get("system_type") != "PLATFORM_STATUS":
        return

    metrics = payload.get("metrics")
    if not isinstance(metrics, dict) or "endurance_remaining_sec" not in metrics:
        return

    if not options.convert_endurance_seconds:
        raise CompatibilityNormalizationError(
            "COMPAT_ENDURANCE_SECONDS_DISABLED",
            "endurance_remaining_sec requires convert_endurance_seconds.",
            "$.payload.metrics.endurance_remaining_sec",
        )
    if "endurance_remaining_ms" in metrics:
        raise CompatibilityNormalizationError(
            "COMPAT_ENDURANCE_SECONDS_CONFLICT",
            "Cannot normalize endurance_remaining_sec when endurance_remaining_ms is already present.",
            "$.payload.metrics",
        )

    seconds = metrics["endurance_remaining_sec"]
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool):
        raise CompatibilityNormalizationError(
            "COMPAT_ENDURANCE_SECONDS_INVALID",
            "endurance_remaining_sec must be numeric to normalize.",
            "$.payload.metrics.endurance_remaining_sec",
        )

    milliseconds = seconds * 1000
    if isinstance(seconds, int):
        milliseconds = int(milliseconds)

    metrics["endurance_remaining_ms"] = milliseconds
    del metrics["endurance_remaining_sec"]
    _record_change(
        changes,
        "$.payload.metrics.endurance_remaining_ms",
        seconds,
        milliseconds,
        "Converted endurance from seconds to milliseconds.",
    )


def _normalize_eo_bbox_roi(
    event: dict[str, Any],
    options: CompatibilityOptions,
    changes: list[dict[str, Any]],
) -> None:
    payload = event.get("payload")
    if not isinstance(payload, dict) or payload.get("modality") != "EO":
        return

    features = payload.get("features")
    if not isinstance(features, dict) or "bbox" not in features:
        return

    if not options.rename_eo_bbox_roi:
        raise CompatibilityNormalizationError(
            "COMPAT_EO_BBOX_SEMANTIC_AMBIGUITY",
            "EO bbox may mean detection; enable rename_eo_bbox_roi only for known ROI metadata.",
            "$.payload.features.bbox",
        )
    if "roi_px" in features:
        raise CompatibilityNormalizationError(
            "COMPAT_EO_BBOX_CONFLICT",
            "Cannot normalize bbox when roi_px is already present.",
            "$.payload.features",
        )

    bbox = features["bbox"]
    if not _looks_like_roi_px(bbox):
        raise CompatibilityNormalizationError(
            "COMPAT_EO_BBOX_INVALID",
            "EO bbox must contain numeric x, y, w, and h fields to normalize to roi_px.",
            "$.payload.features.bbox",
        )

    features["roi_px"] = deepcopy(bbox)
    del features["bbox"]
    _record_change(
        changes,
        "$.payload.features.roi_px",
        bbox,
        bbox,
        "Renamed EO bbox to roi_px under explicit ROI compatibility option.",
    )


def _looks_like_roi_px(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if set(value.keys()) != {"x", "y", "w", "h"}:
        return False
    return all(isinstance(value[key], (int, float)) and not isinstance(value[key], bool) for key in value)


def _assert_protected_fields_unchanged(original: dict[str, Any], normalized: dict[str, Any]) -> None:
    protected_paths = [
        ("event", "event_id"),
        ("event", "ts"),
        ("event", "t_publish"),
        ("event", "t_receive"),
        ("event", "event_type"),
        ("event", "event_subtype"),
        ("source",),
        ("lineage",),
        ("payload", "track_id"),
    ]
    for path in protected_paths:
        if _get_path(original, path) != _get_path(normalized, path):
            raise CompatibilityNormalizationError(
                "COMPAT_PROTECTED_FIELD_MUTATION",
                f"Compatibility normalization attempted to modify protected field {_format_path(path)}.",
                _format_path(path),
            )


def _get_path(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _format_path(path: tuple[str, ...]) -> str:
    return "$" + "".join(f".{part}" for part in path)


def _record_change(
    changes: list[dict[str, Any]],
    path: str,
    original: Any,
    normalized: Any,
    reason: str,
) -> None:
    changes.append(
        {
            "path": path,
            "from": original,
            "to": normalized,
            "reason": reason,
        }
    )
