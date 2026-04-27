import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
import uuid
from copy import deepcopy
from pathlib import Path

from zmeta_uuid import uuid7


ROOT = Path(__file__).resolve().parents[2]

NORMALIZER_PATH = ROOT / "tools" / "compat_normalizer.py"
spec = importlib.util.spec_from_file_location("zmeta_compat_normalizer", NORMALIZER_PATH)
compat_normalizer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = compat_normalizer
spec.loader.exec_module(compat_normalizer)

VALIDATORS_PATH = ROOT / "gateway" / "src" / "validators.py"
spec_validators = importlib.util.spec_from_file_location("zmeta_validators", VALIDATORS_PATH)
validators = importlib.util.module_from_spec(spec_validators)
sys.modules[spec_validators.name] = validators
spec_validators.loader.exec_module(validators)


def platform_status(version="1.1.0"):
    return {
        "zmeta_version": version,
        "event": {
            "event_id": str(uuid7()),
            "event_type": "SYSTEM_EVENT",
            "event_subtype": "PLATFORM_STATUS",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "gateway-node-01",
            "node_role": "GATEWAY",
            "producer": "zmeta-gateway",
        },
        "profile": "H",
        "payload": {
            "system_type": "PLATFORM_STATUS",
            "state": "NOMINAL",
            "metrics": {"power_state": "EXTERNAL_POWER"},
        },
    }


def eo_observation():
    return {
        "zmeta_version": "1.1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "EO",
            "ts": "2025-01-17T14:32:10Z",
        },
        "source": {
            "platform_id": "camera-node-01",
            "node_role": "EDGE",
            "producer": "eo-camera",
        },
        "profile": "H",
        "payload": {
            "modality": "EO",
            "features": {
                "bbox": {"x": 10, "y": 20, "w": 30, "h": 40},
                "resolution_px": {"width": 1920, "height": 1080},
            },
            "timing_quality": {
                "time_source": "GPS_PPS",
                "sync_state": "LOCKED",
                "est_error_ms": 1,
                "last_sync_ts": "2025-01-17T14:29:59Z",
            },
        },
    }


class CompatibilityNormalizerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = validators.load_schema(ROOT / "schema" / "zmeta-event.schema.json")

    def assert_schema_valid(self, event):
        self.assertEqual([], list(self.validator.iter_errors(event)))

    def assert_schema_invalid(self, event):
        self.assertNotEqual([], list(self.validator.iter_errors(event)))

    def test_strict_schema_rejects_minor_version_alias(self):
        self.assert_schema_invalid(platform_status(version="1.1"))

    def test_opt_in_version_alias_normalizes_and_records_change(self):
        event = platform_status(version="1.1")
        normalized, changes = compat_normalizer.normalize_event(
            event,
            compat_normalizer.CompatibilityOptions(allow_version_alias=True),
        )

        self.assertEqual("1.1.0", normalized["zmeta_version"])
        self.assertEqual(
            [
                {
                    "path": "$.zmeta_version",
                    "from": "1.1",
                    "to": "1.1.0",
                    "reason": "Normalized minor version alias before schema validation.",
                }
            ],
            changes,
        )
        self.assertEqual("1.1", event["zmeta_version"])
        self.assert_schema_valid(normalized)

    def test_opt_in_endurance_seconds_converts_to_milliseconds(self):
        event = platform_status()
        metrics = event["payload"]["metrics"]
        del metrics["power_state"]
        metrics["endurance_remaining_sec"] = 12.5
        self.assert_schema_invalid(event)

        normalized, changes = compat_normalizer.normalize_event(
            event,
            compat_normalizer.CompatibilityOptions(convert_endurance_seconds=True),
        )

        self.assertNotIn("endurance_remaining_sec", normalized["payload"]["metrics"])
        self.assertEqual(12500.0, normalized["payload"]["metrics"]["endurance_remaining_ms"])
        self.assertEqual("$.payload.metrics.endurance_remaining_ms", changes[0]["path"])
        self.assert_schema_valid(normalized)

    def test_semantically_ambiguous_eo_bbox_is_rejected_by_default(self):
        with self.assertRaises(compat_normalizer.CompatibilityNormalizationError) as ctx:
            compat_normalizer.normalize_event(eo_observation(), compat_normalizer.CompatibilityOptions())

        self.assertEqual("COMPAT_EO_BBOX_SEMANTIC_AMBIGUITY", ctx.exception.code)

    def test_eo_bbox_to_roi_requires_explicit_option(self):
        event = eo_observation()
        self.assert_schema_invalid(event)

        normalized, changes = compat_normalizer.normalize_event(
            event,
            compat_normalizer.CompatibilityOptions(rename_eo_bbox_roi=True),
        )

        self.assertNotIn("bbox", normalized["payload"]["features"])
        self.assertEqual(
            {"x": 10, "y": 20, "w": 30, "h": 40},
            normalized["payload"]["features"]["roi_px"],
        )
        self.assertEqual("$.payload.features.roi_px", changes[0]["path"])
        self.assert_schema_valid(normalized)

    def test_normalizer_does_not_mutate_protected_fields(self):
        event = platform_status(version="1.1")
        original = deepcopy(event)
        normalized, _changes = compat_normalizer.normalize_event(
            event,
            compat_normalizer.CompatibilityOptions(allow_version_alias=True),
        )

        for path in (
            ("event", "event_id"),
            ("event", "ts"),
            ("event", "event_type"),
            ("event", "event_subtype"),
            ("source",),
            ("lineage",),
            ("payload", "track_id"),
        ):
            self.assertEqual(_get_path(original, path), _get_path(normalized, path))

    def test_cli_writes_normalized_event_and_sidecar_report(self):
        tmp_path = ROOT / ".pytest_tmp" / f"compat-{uuid.uuid4().hex}"
        tmp_path.mkdir(parents=True, exist_ok=False)
        try:
            input_path = tmp_path / "event.json"
            output_path = tmp_path / "normalized.json"
            report_path = tmp_path / "report.json"
            input_path.write_text(json.dumps(platform_status(version="1.1")), encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tools" / "compat_normalize.py"),
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--report",
                    str(report_path),
                    "--allow-version-alias",
                ],
                cwd=str(ROOT),
                check=True,
            )

            normalized = json.loads(output_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual("1.1.0", normalized["zmeta_version"])
            self.assertEqual([], report["rejected"])
            self.assertEqual("$.zmeta_version", report["changes"][0]["path"])
        finally:
            shutil.rmtree(tmp_path, ignore_errors=True)


def _get_path(data, path):
    current = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


if __name__ == "__main__":
    unittest.main()
