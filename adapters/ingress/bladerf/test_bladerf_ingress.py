"""Colocated tests for the bladeRF ingress adapter.

Two layers, per AUTHORING sections 5 and 8:

1. **Acceptance** -- the two real-capture fixture pairs from
   ``adapters/mapping-packs/edge-comms-bladerf`` are run through the adapter and
   must reproduce ``expected.json`` exactly (ignoring only the runtime-minted
   UUIDv7 ``event_id``), then validate against the locked v1.0 schema.
2. **Honesty pins** -- the semantics that matter are pinned directly: geo
   refusal on null / null-island positions, the frame-unlabeled bearing
   demotion (canonical ``bearing`` omitted, native value kept in features),
   no fabricated quality metrics, the degraded-timing fallback, whitelisted
   metadata, omit-or-stamp lineage, and one fail-closed refusal per
   schema-required field (AUTHORING section 9).
"""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from adapters.ingress.bladerf.bladerf_to_zmeta import (
    ADAPTER_VERSION,
    SCHEMA_ID,
    detect,
    translate,
    translate_detection,
    validate,
)

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schema" / "zmeta-event-1.0.schema.json"
VALIDATOR = Draft202012Validator(
    json.loads(SCHEMA_PATH.read_text(encoding="utf-8")), format_checker=FormatChecker()
)

PACK = ROOT / "adapters" / "mapping-packs" / "edge-comms-bladerf" / "tests"
CASES = ["case-01-vhf-orbit", "case-02-cband-fft"]
PLATFORM_ID = "uav-believer-01-bladerf"


def _load(case):
    raw = json.loads((PACK / case / "input.json").read_text(encoding="utf-8"))
    expected = json.loads((PACK / case / "expected.json").read_text(encoding="utf-8"))
    return raw, expected


def _translate_case(case, **kwargs):
    raw, expected = _load(case)
    events = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID, **kwargs)
    assert len(events) == 1
    return events[0], expected


# --------------------------------------------------------------------------
# Acceptance: reproduce the pack's expected outputs exactly
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_acceptance_reproduces_expected_output(case):
    event, expected = _translate_case(case)
    # event_id is a runtime-minted UUIDv7 (pack README: "ignore generated
    # event_id"); everything else must match byte-for-byte.
    assert event["event"]["event_id"] != expected["event"]["event_id"]
    normalized = copy.deepcopy(event)
    normalized["event"]["event_id"] = expected["event"]["event_id"]
    assert normalized == expected


@pytest.mark.parametrize("case", CASES)
def test_acceptance_event_validates_against_v1_0_schema(case):
    event, _ = _translate_case(case)
    VALIDATOR.validate(event)
    assert validate(event) == ("pass", [])


@pytest.mark.parametrize("case", CASES)
def test_minted_event_id_is_uuidv7(case):
    event, _ = _translate_case(case)
    eid = event["event"]["event_id"]
    # UUIDv7: version nibble 7, RFC4122 variant (8/9/a/b).
    assert eid[14] == "7"
    assert eid[19] in "89ab"


# --------------------------------------------------------------------------
# Honesty pin: canonical bearing is demoted (no frame assertion)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_canonical_bearing_omitted_no_frame_assertion(case):
    # contract 6.4 / AUTHORING rule 2: the native bearing is heading-derived
    # and asserts no reference frame, so payload.bearing is never emitted --
    # in BOTH cases, including case-02 whose bearing_source is heading_at_peak.
    event, _ = _translate_case(case)
    assert "bearing" not in event["payload"]
    assert "bearing_frame" not in event["payload"]["quality"]
    assert "heading_source" not in event["payload"]["quality"]


@pytest.mark.parametrize("case", CASES)
def test_native_bearing_kept_in_explicit_features(case):
    raw, _ = _load(case)
    event, _ = _translate_case(case)
    features = event["payload"]["features"]
    assert features["native_bearing_deg"] == raw["bearing_deg"]
    assert features["native_bearing_error_deg"] == raw["bearing_error_deg"]


def test_no_fabricated_measurement_error():
    # The raw bearing_error_deg declares no statistical metric, so no canonical
    # quality.measurement_error is minted from it (AUTHORING rule 3).
    for case in CASES:
        event, _ = _translate_case(case)
        assert "measurement_error" not in event["payload"]["quality"]


# --------------------------------------------------------------------------
# Honesty pin: canonical geo is all-or-nothing (null + null-island)
# --------------------------------------------------------------------------


def test_null_sensor_position_refuses_geo():
    # case-01: sensor_lat/lon/alt are null -> geo omitted, status UNAVAILABLE.
    event, _ = _translate_case("case-01-vhf-orbit")
    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"


def test_null_island_sensor_position_refuses_geo():
    # case-02: sensor position is (0.0, 0.0) -> null-island sentinel, not a fix.
    event, _ = _translate_case("case-02-cband-fft")
    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"


def test_real_sensor_position_emits_geo():
    # Proves the geo gate is not stuck off: a genuine fix DOES map to canonical
    # geo with status AVAILABLE (contract 6.8 all-or-nothing, satisfied here).
    raw, _ = _load("case-02-cband-fft")
    raw = copy.deepcopy(raw)
    raw["sensor_lat"], raw["sensor_lon"], raw["sensor_alt_m"] = 43.49, -112.04, 1450.0
    event = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID)[0]
    assert event["payload"]["geo"] == {"lat": 43.49, "lon": -112.04, "alt_m": 1450.0}
    assert event["payload"]["quality"]["geo_status"] == "AVAILABLE"
    VALIDATOR.validate(event)


def test_partial_sensor_position_refuses_geo():
    # All-or-nothing: a fix missing alt_m is omitted, never zero-filled.
    raw, _ = _load("case-02-cband-fft")
    raw = copy.deepcopy(raw)
    raw["sensor_lat"], raw["sensor_lon"], raw["sensor_alt_m"] = 43.49, -112.04, None
    event = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID)[0]
    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"


# --------------------------------------------------------------------------
# Honesty pin: no fabricated quality / no leaked metadata / degraded timing
# --------------------------------------------------------------------------


def test_snr_omitted_when_absent():
    # snr_db is a real measurement, never invented: drop it from the input and
    # both features.snr_db and quality.snr_db disappear.
    raw, _ = _load("case-01-vhf-orbit")
    raw = copy.deepcopy(raw)
    raw.pop("snr_db")
    event = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID)[0]
    assert "snr_db" not in event["payload"]["features"]
    assert "snr_db" not in event["payload"]["quality"]
    VALIDATOR.validate(event)


@pytest.mark.parametrize("case", CASES)
def test_unmapped_metadata_not_leaked(case):
    # Only whitelisted metadata crosses into features; vendor quirks stay out.
    event, _ = _translate_case(case)
    features = event["payload"]["features"]
    for leaked in ("antenna_left", "antenna_right", "baseline_m", "scan_state",
                   "pdoa_active", "heading_age_ms", "scan_sweep_id", "latitude",
                   "longitude", "l_profile_ok"):
        assert leaked not in features


@pytest.mark.parametrize("case", CASES)
def test_degraded_timing_fallback(case):
    event, _ = _translate_case(case)
    tq = event["payload"]["timing_quality"]
    assert tq["time_source"] == "UNKNOWN"
    assert tq["sync_state"] == "UNSYNCED"
    assert tq["est_error_ms"] == 60000
    # last_sync_ts mirrors event.ts at millisecond precision.
    assert tq["last_sync_ts"] == event["event"]["ts"]


@pytest.mark.parametrize("case", CASES)
def test_calibration_defaults_uncalibrated(case):
    event, _ = _translate_case(case)
    assert event["payload"]["quality"]["calibration_state"] == "UNCALIBRATED"


def test_caller_timing_quality_is_preserved():
    # A deployment with real GPS/NTP/PTP metadata replaces the degraded
    # fallback; the supplied values pass through unaltered (contract 5.3).
    supplied = {
        "time_source": "GPS_PPS",
        "sync_state": "LOCKED",
        "est_error_ms": 1,
        "last_sync_ts": "2026-05-14T14:12:33Z",
    }
    event, _ = _translate_case("case-01-vhf-orbit", timing_quality=supplied)
    assert event["payload"]["timing_quality"] == supplied
    VALIDATOR.validate(event)


def test_non_dict_metadata_treated_as_absent():
    # A malformed metadata container degrades honestly: metadata-derived
    # features and sensor_id are omitted (never guessed), while the top-level
    # RF minimum set still emits a valid observation.
    raw, _ = _load("case-01-vhf-orbit")
    raw = copy.deepcopy(raw)
    raw["metadata"] = "corrupt"
    event = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID)[0]
    assert "sensor_id" not in event["source"]
    assert "sensor_hw" not in event["payload"]["features"]
    assert event["payload"]["features"]["center_freq_hz"] == raw["center_freq_hz"]
    VALIDATOR.validate(event)


# --------------------------------------------------------------------------
# Honesty pin: lineage is omitted or genuinely stamped, never fabricated
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_lineage_omitted_without_parents(case):
    event, _ = _translate_case(case)
    assert "lineage" not in event


def test_lineage_stamped_with_real_parents():
    parent = "019c2b5c-c053-70e1-b6aa-340000000001"
    event, _ = _translate_case("case-01-vhf-orbit", based_on=[parent])
    assert event["lineage"]["based_on"] == [parent]
    assert event["lineage"]["transform"] == f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}"
    VALIDATOR.validate(event)


# --------------------------------------------------------------------------
# Fail-closed: one refusal per schema-required field (AUTHORING section 9)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["center_freq_hz", "bandwidth_hz", "power_dbm"])
def test_refuses_missing_required_rf_feature(field):
    raw, _ = _load("case-02-cband-fft")
    raw = copy.deepcopy(raw)
    del raw[field]
    assert translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID) == []


@pytest.mark.parametrize("field", ["center_freq_hz", "bandwidth_hz", "power_dbm"])
def test_refuses_null_required_rf_feature(field):
    raw, _ = _load("case-02-cband-fft")
    raw = copy.deepcopy(raw)
    raw[field] = None
    assert translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID) == []


def test_refuses_null_platform_id():
    raw, _ = _load("case-01-vhf-orbit")
    assert translate(raw, SCHEMA_ID, platform_id=None) == []


def test_refuses_blank_platform_id():
    raw, _ = _load("case-01-vhf-orbit")
    assert translate(raw, SCHEMA_ID, platform_id="   ") == []


def test_refuses_missing_timestamp_ms_even_with_string_timestamp():
    # mapping.yaml maps event.ts from input.timestamp_ms alone. The paired
    # human-readable "timestamp" string is a rendering of the same instant,
    # not an alternate authority: it must never rescue a record whose mapped
    # source is missing (refuse rather than guess an alternate mapping).
    raw, _ = _load("case-01-vhf-orbit")
    raw = copy.deepcopy(raw)
    del raw["timestamp_ms"]
    assert "timestamp" in raw  # the rendering is still present...
    assert translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID) == []  # ...and does not rescue


@pytest.mark.parametrize(
    "bad_ts", [None, "1778767953876", "yesterday-ish", True, [], {}, float("nan")]
)
def test_refuses_unparseable_timestamp_ms(bad_ts):
    # Fail closed, never crash: non-numeric, boolean, or non-finite
    # timestamp_ms values are refusals, not exceptions and not coerced epochs.
    raw, _ = _load("case-01-vhf-orbit")
    raw = copy.deepcopy(raw)
    raw["timestamp_ms"] = bad_ts
    assert translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID) == []


def test_refuses_non_finite_snr():
    # A NaN/inf SNR is in the JSON value model by type and outside it by
    # value: not a measurement, so the whole event refuses rather than
    # laundering it into a canonical quality field.
    for bad in (float("nan"), float("inf")):
        raw, _ = _load("case-01-vhf-orbit")
        raw = copy.deepcopy(raw)
        raw["snr_db"] = bad
        assert translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID) == []


def test_non_finite_geo_component_refuses_geo():
    # A non-finite coordinate is not a position: geo is refused (omitted +
    # UNAVAILABLE) while the otherwise-honest observation still emits.
    raw, _ = _load("case-02-cband-fft")
    raw = copy.deepcopy(raw)
    raw["sensor_lat"], raw["sensor_lon"], raw["sensor_alt_m"] = float("inf"), -112.04, 1450.0
    event = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID)[0]
    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"
    VALIDATOR.validate(event)


def test_refuses_wrong_schema_id():
    raw, _ = _load("case-01-vhf-orbit")
    assert translate(raw, "vendor:something_else:v1", platform_id=PLATFORM_ID) == []


def test_refuses_omitted_platform_id():
    # platform_id defaults to None so an unconfigured deployment registers a
    # fail-closed refusal, not a TypeError crash.
    raw, _ = _load("case-01-vhf-orbit")
    assert translate(raw, SCHEMA_ID) == []


def test_refuses_non_dict_input():
    assert translate(None, SCHEMA_ID, platform_id=PLATFORM_ID) == []
    assert translate("not a dict", SCHEMA_ID, platform_id=PLATFORM_ID) == []


# --------------------------------------------------------------------------
# sensor_id handling and detect()
# --------------------------------------------------------------------------


def test_sensor_id_defaults_from_metadata():
    event, _ = _translate_case("case-01-vhf-orbit")
    assert event["source"]["sensor_id"] == "bladerf_ew"


def test_sensor_id_omitted_when_unavailable():
    # zmeta_sensor_id is the only source; absent + no override -> omit the
    # schema-optional field rather than fabricate an identity.
    raw, _ = _load("case-01-vhf-orbit")
    raw = copy.deepcopy(raw)
    raw["metadata"].pop("zmeta_sensor_id")
    event = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID)[0]
    assert "sensor_id" not in event["source"]
    VALIDATOR.validate(event)


@pytest.mark.parametrize("case", CASES)
def test_detect_recognizes_bladerf(case):
    raw, _ = _load(case)
    assert detect(json.dumps(raw).encode("utf-8")) == SCHEMA_ID


def test_detect_rejects_non_bladerf():
    assert detect(b"not json") is None
    assert detect(json.dumps({"detection_id": "x"}).encode()) is None
    # right shape but wrong hardware -> not ours.
    foreign = {"detection_id": "x", "center_freq_hz": 1.0, "power_dbm": -1.0,
               "metadata": {"sensor_hw": "krakensdr"}}
    assert detect(json.dumps(foreign).encode()) is None


def test_translate_detection_single_record_worker():
    # The single-record worker returns a dict (or None), the list wrapper wraps.
    raw, expected = _load("case-01-vhf-orbit")
    event = translate_detection(raw, platform_id=PLATFORM_ID)
    assert isinstance(event, dict)
    assert event["event"]["event_type"] == "OBSERVATION_EVENT"
    assert translate_detection(raw, platform_id=None) is None


# Value-honesty pins (attack-pass finding, 2026-07-27): a non-finite numeric
# is not a measurement, so no canonical field may carry one -- the adapter
# refuses or omits at its own boundary, not only at the gateway.


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_geo_component_refuses_geo_not_available(bad):
    raw, _ = _load("case-01-vhf-orbit")
    raw = copy.deepcopy(raw)
    raw["sensor_lat"] = bad
    raw["sensor_lon"] = 34.0
    raw["sensor_alt_m"] = 100.0
    event = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID)[0]
    assert "geo" not in event["payload"]
    assert event["payload"]["quality"]["geo_status"] == "UNAVAILABLE"
    VALIDATOR.validate(event)


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_snr_refuses_the_event(bad):
    raw, _ = _load("case-01-vhf-orbit")
    raw = copy.deepcopy(raw)
    raw["snr_db"] = bad
    assert translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID) == []


@pytest.mark.parametrize("key", ["center_freq_hz", "bandwidth_hz", "power_dbm"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_required_feature_refuses_the_event(key, bad):
    raw, _ = _load("case-02-cband-fft")
    raw = copy.deepcopy(raw)
    raw[key] = bad
    assert translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID) == []


def test_non_finite_optional_feature_is_omitted_not_laundered():
    raw, _ = _load("case-01-vhf-orbit")
    raw = copy.deepcopy(raw)
    raw["noise_floor_dbm"] = float("nan")
    event = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID)[0]
    assert "noise_floor_dbm" not in event["payload"]["features"]
    VALIDATOR.validate(event)


def test_zero_bandwidth_stays_valid_fft_convention():
    # 0.0 bandwidth is the documented FFT-bin-width convention, NOT a
    # non-finite sentinel -- it must still translate cleanly.
    raw, _ = _load("case-02-cband-fft")
    raw = copy.deepcopy(raw)
    raw["bandwidth_hz"] = 0.0
    event = translate(raw, SCHEMA_ID, platform_id=PLATFORM_ID)[0]
    assert event["payload"]["features"]["bandwidth_hz"] == 0.0
    VALIDATOR.validate(event)
