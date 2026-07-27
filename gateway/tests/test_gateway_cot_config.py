"""The gateway passes deployment CoT projection knobs through to egress.

Before 2026-07-27 the serve loop called ``zmeta_to_cot(outgoing)`` bare, so
a deployment could never assert its position-source pedigree: the
``<precisionlocation>`` ellipse detail and the ``how`` attribute were
unconditionally omitted (the honest default for an UNASSERTED source), with
no way to assert one. The two-node quickstart's TAK-display story depends
on this knob: ellipse detail on a COP requires the deployment to assert
``geopointsrc``/``altsrc`` in ``cot.config`` -- it is never fabricated.

Red-first: on the pre-fix gateway, ``build_settings`` had no ``cot_config``
key (KeyError) and the serve loop ignored the block entirely.
"""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATEWAY_PATH = ROOT / "gateway" / "src" / "gateway.py"
spec = importlib.util.spec_from_file_location("zmeta_gateway_cot_config", GATEWAY_PATH)
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)

from adapters.egress.cot.zmeta_to_cot import zmeta_to_cot  # noqa: E402


def _no_cli_args():
    """The gateway's own parser with no CLI overrides (config-file run).

    Using the real parser keeps this namespace true as flags evolve,
    instead of a hand-mirrored attribute list that drifts.
    """
    import sys

    argv = sys.argv
    sys.argv = ["gateway.py"]
    try:
        return gateway.parse_args()
    finally:
        sys.argv = argv


def _ellipse_state_event():
    return {
        "zmeta_version": "1.0",
        "event": {
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": "2026-07-27T12:00:00Z",
        },
        "payload": {
            "track_id": "trk-quickstart-01",
            "class": "a-h-G",
            "geo": {
                "lat": 35.0,
                "lon": -117.0,
                "alt_m": 1200.0,
                "error_ellipse_m": {
                    "semi_major": 150.0,
                    "semi_minor": 80.0,
                    "orientation_deg": 45.0,
                },
            },
            "valid_for_ms": 60000,
        },
    }


def test_build_settings_carries_cot_config_block():
    config = {
        "profile": "H",
        "emit_cot": True,
        "cot": {
            "host": "127.0.0.1",
            "port": 6969,
            "config": {"geopointsrc": "GPS", "altsrc": "GPS", "how": "m-g"},
        },
    }
    settings = gateway.build_settings(ROOT, _no_cli_args(), config)
    assert settings["cot_config"] == {
        "geopointsrc": "GPS",
        "altsrc": "GPS",
        "how": "m-g",
    }
    # Address plumbing is untouched by the new sub-block.
    assert settings["cot_host"] == "127.0.0.1"
    assert settings["cot_port"] == 6969


def test_default_settings_leave_cot_config_unasserted():
    settings = gateway.build_settings(ROOT, _no_cli_args(), {"profile": "H", "emit_cot": True})
    assert settings["cot_config"] is None
    # And the projection honors the unasserted default: no pedigree, no
    # precisionlocation, no how -- omitted, never fabricated.
    xml = zmeta_to_cot(_ellipse_state_event(), cot_config=settings["cot_config"])
    assert "<precisionlocation" not in xml
    assert " how=" not in xml


def test_asserted_config_projects_pedigree_and_ellipse_detail():
    config = {
        "profile": "H",
        "cot": {"config": {"geopointsrc": "GPS", "altsrc": "GPS", "how": "m-g"}}
    }
    settings = gateway.build_settings(ROOT, _no_cli_args(), config)
    xml = zmeta_to_cot(_ellipse_state_event(), cot_config=settings["cot_config"])
    assert 'geopointsrc="GPS"' in xml
    assert 'altsrc="GPS"' in xml
    assert 'how="m-g"' in xml
    assert 'ellipse_major="150.0"' in xml
    assert 'ellipse_minor="80.0"' in xml
    # The vertical-error field still never inherits the horizontal ellipse.
    assert 'le="9999999.0"' in xml


def test_malformed_config_block_is_ignored_not_crashed():
    for bad in ("GPS", ["GPS"], 7, None):
        settings = gateway.build_settings(ROOT, _no_cli_args(), {"profile": "H", "cot": {"config": bad}})
        assert settings["cot_config"] is None
