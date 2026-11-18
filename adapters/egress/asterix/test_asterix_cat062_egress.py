"""ASTERIX CAT062 ed. 1.21 egress: one ZMeta STATE_EVENT/TRACK_STATE to one
system track record, and the data block that carries records.

The known-answer records are computed by hand in this file from CAT062 ed. 1.21
(EUROCONTROL-SPEC-0149-9): the UAP of §5.3 (Table 1) for the FSPEC, and the
layouts and LSBs of §5.2 for the items. The arithmetic was done in exact
fractions and 50-digit decimals, not with the encoder, so the expected bytes do
not depend on the encoder's own tables. The small decoder below reads records
back for the tests that check one field; it knows only the items this adapter
writes, so a record carrying any other item fails it.

A cross-check against libasterix (BSD-3-Clause) runs only when the environment
variable `ASTERIX_SITE` names a directory holding its `asterix` package. The
repository vendors no copy and the adapter does not import it. The check runs
in a separate `python -I` process, because this test package's own import
name under pytest, `asterix`, would shadow the library's in this one.

WHAT THIS FILE DOES NOT PROVE: that any CAT062 consumer (a surveillance data
processing system, a display or a recorder) accepts the records. No consumer
was driven with them.
"""

import ast
import inspect
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.egress.asterix import zmeta_to_asterix_cat062 as cat062  # noqa: E402
from adapters.egress.cot import zmeta_to_cot as cot  # noqa: E402

CONFIG = {"sac": 25, "sic": 7, "monosensor": False, "tentative": False, "simulated": False,
          "allow_holdover_or_unsynced": False}
TRACKS = {"track-alpha": 1234, "track-omega": 65535}
LSB_DEG = 180 / 2**25
DELETE = object()
LOCKED = {"time_source": "GPS_PPS", "sync_state": "LOCKED", "est_error_ms": 1.0, "last_sync_ts": "2026-11-14T12:34:56Z"}
UNSYNCED = {"time_source": "UNKNOWN", "sync_state": "UNSYNCED", "est_error_ms": 5000.0,
            "last_sync_ts": "2026-11-14T12:34:56.789Z"}


def make_event(ts="2026-11-14T12:34:56.789Z", geo=None, **payload):
    """A STATE_EVENT/TRACK_STATE with invented values. `geo` replaces the
    default declared 2-D position; a payload keyword replaces or adds a member,
    and DELETE removes it."""
    event = {
        "zmeta_version": "1.1.0",
        "event": {
            "event_id": "01938f2a-0000-7000-8000-000000000001",
            "event_type": "STATE_EVENT",
            "event_subtype": "TRACK_STATE",
            "ts": ts,
        },
        "source": {"platform_id": "test-platform", "node_role": "GATEWAY", "producer": "test-producer"},
        "confidence": 0.5,
        "lineage": {"based_on": ["01938f2a-0000-7000-8000-000000000002"]},
        "payload": {
            "track_id": "track-alpha",
            "geo": geo if geo is not None else {"lat": 45.0, "lon": -90.0, "dimensionality": "2D"},
            "valid_for_ms": 5000,
            "timing_quality": dict(LOCKED),
        },
    }
    for key, value in payload.items():
        if value is DELETE:
            event["payload"].pop(key, None)
        else:
            event["payload"][key] = value
    if ts is DELETE:
        del event["event"]["ts"]
    return event


def encode(event, config=None, tracks=None, **kwargs):
    """(record or None, refusal reason or None)."""
    refusal = {}
    record = cat062.zmeta_state_to_asterix_cat062(
        event,
        CONFIG if config is None else config,
        track_numbers=TRACKS if tracks is None else tracks,
        refusal=refusal,
        **kwargs,
    )
    return record, refusal.get("reason")


def refused(event, reason, **kwargs):
    record, got = encode(event, **kwargs)
    assert record is None, f"expected a refusal {reason}, got a record {record.hex(' ') if record else record}"
    assert got == reason


# The items this adapter may write, by FRN (§5.3, Table 1), with their fixed lengths.
FRN_ITEM = {1: "010", 3: "015", 4: "070", 5: "105", 7: "185", 12: "040", 13: "080", 18: "130", 27: "500"}
FIXED_LENGTH = {"010": 2, "015": 1, "070": 3, "105": 8, "185": 4, "040": 2, "130": 2}
# I062/500's subfields in primary-subfield bit order (§5.2.26) and their lengths.
SUBFIELD_LENGTH = (("APC", 4), ("COV", 2), ("APW", 4), ("AGA", 1), ("ABA", 1), ("ATV", 2), ("AA", 2), ("ARC", 1))


def items_of(record):
    """Decode one record of this adapter into {item: bytes}; fail on anything else."""
    fspec = []
    pos = 0
    while True:
        octet = record[pos]
        fspec.append(octet)
        pos += 1
        if not octet & 1:
            break
    frns = [7 * i + j + 1 for i, octet in enumerate(fspec) for j in range(7) if octet & (0x80 >> j)]
    items = {}
    for frn in frns:
        name = FRN_ITEM[frn]
        if name in FIXED_LENGTH:
            n = FIXED_LENGTH[name]
        elif name == "080":
            n = 1
            while record[pos + n - 1] & 1:
                n += 1
        else:  # "500"
            primary = [record[pos]]
            while primary[-1] & 1:
                primary.append(record[pos + len(primary)])
            bits = [(primary[i // 7] >> (7 - i % 7)) & 1 if i // 7 < len(primary) else 0 for i in range(8)]
            n = len(primary) + sum(length for (name_, length), bit in zip(SUBFIELD_LENGTH, bits) if bit)
        items[name] = bytes(record[pos:pos + n])
        pos += n
    assert pos == len(record), f"{len(record) - pos} octets after the last item"
    return items


def s16(b):
    return int.from_bytes(b, "big", signed=True)


def s32(b):
    return int.from_bytes(b, "big", signed=True)


# --- known answers, by hand from ed. 1.21 ---------------------------------------

# The minimum record: SAC 25, SIC 7; time 12:34:56.789 UTC = 45,296.789 s, x 128 = 5,797,988.992, floored to
# 5,797,988 = 0x587864; latitude 45.0 = 2^23 counts; longitude -90.0 = -2^24 counts; track number 1234 = 0x04D2;
# track status MON 0, SPI 0, MRH 1, SRC 000, CNF 0, FX 0 = 0x20. FSPEC: FRN 1, 4, 5 and FX = 0x99; FRN 12, 13 = 0x0C.
MINIMUM_RECORD = bytes.fromhex("99 0C 19 07 58 78 64 00 80 00 00 FF 00 00 00 04 D2 20")

# The full record: FSPEC FRN 1, 3, 4, 5, 7 and FX = 0xBB; FRN 12, 13 and FX = 0x0D; FRN 18 and FX = 0x11; FRN 27 = 0x04.
# I062/015 = 3. Time 23:59:59.999 = 86,399.999 s, x 128 = 11,059,199.872, floored to 0xA8BFFF (rounding would give
# 0xA8C000, a full day). Latitude 12.345678 / (180/2^25) = 2,301,401.18, nearest 2,301,401 = 0x00231DD9; longitude
# -98.765432 -> -18,411,210.96, nearest -18,411,211 = 0xFEE71135. Course 90, speed 100 m/s: Vx = 100 m/s = 400 counts
# = 0x0190 east, Vy = 0. Track number 65,535. Track status MON 1, MRH 1, CNF 1 = 0xA2. Altitude 1,905 m / 1.905 m =
# 1,000 = 0x03E8. I062/500: primary subfield APW only = 0x20; a 1-sigma ellipse a 30 m, b 10 m, orientation 30 degrees
# gives north and east deviations sqrt(700) = 26.4575 m and sqrt(300) = 17.3205 m; at 12.345678 degrees the WGS-84
# radii are M = 6,338,348.688 m and N = 6,379,113.173 m, so latitude 44.5834 counts -> 45 = 0x002D and longitude
# 29.6866 counts -> 30 = 0x001E, each rounded up.
FULL_RECORD = bytes.fromhex(
    "BB 0D 11 04 19 07 03 A8 BF FF 00 23 1D D9 FE E7 11 35 01 90 00 00 FF FF A2 03 E8 20 00 2D 00 1E"
)
FULL_CONFIG = dict(CONFIG, service_id=3, monosensor=True, tentative=True)


def full_event():
    return make_event(
        ts="2026-11-14T23:59:59.999Z",
        geo={
            "lat": 12.345678,
            "lon": -98.765432,
            "alt_m": 1905.0,
            "error_ellipse_m": {"semi_major": 30.0, "semi_minor": 10.0, "orientation_deg": 30.0, "probability": "1_SIGMA"},
        },
        track_id="track-omega",
        heading_deg=90.0,
        speed_mps=100.0,
    )


def test_known_answer_minimum_record():
    record, reason = encode(make_event())
    assert reason is None
    assert record == MINIMUM_RECORD
    assert cat062.cat062_data_block([record]) == bytes.fromhex("3E 00 15") + MINIMUM_RECORD


def test_known_answer_full_record():
    record, reason = encode(full_event(), config=FULL_CONFIG)
    assert reason is None
    assert record == FULL_RECORD
    assert cat062.cat062_data_block([record]) == bytes.fromhex("3E 00 23") + FULL_RECORD


def test_the_data_block_carries_one_or_more_records():
    first = encode(make_event())[0]
    second = encode(full_event(), config=FULL_CONFIG)[0]
    block = cat062.cat062_data_block([first, second])
    assert block[0] == 62
    assert int.from_bytes(block[1:3], "big") == len(block) == 3 + len(first) + len(second)
    assert block[3:] == first + second
    assert cat062.cat062_data_block((bytearray(first),)) == bytes.fromhex("3E 00 15") + first


@pytest.mark.parametrize(
    "records",
    [[], [b""], ["99 0C"], [None], [b"\x99" * 65533]],
    ids=["no records", "an empty record", "a string", "None", "longer than LEN can state"],
)
def test_the_data_block_refuses_what_it_cannot_frame(records):
    with pytest.raises(ValueError):
        cat062.cat062_data_block(records)


def test_the_data_block_takes_the_longest_block_len_can_state():
    block = cat062.cat062_data_block([b"\x99" * 65532])
    assert len(block) == 65535 and block[1:3] == b"\xff\xff"


@pytest.mark.parametrize(
    "extra, config, fspec",
    [
        ({}, CONFIG, "99 0C"),
        ({"heading_deg": 0.0, "speed_mps": 1.0}, CONFIG, "9B 0C"),
        ({}, dict(CONFIG, service_id=0), "B9 0C"),
        ({"geo": {"lat": 45.0, "lon": -90.0, "alt_m": 0.0}}, CONFIG, "99 0D 10"),
        ({"geo": {"lat": 45.0, "lon": -90.0, "dimensionality": "2D",
                  "error_ellipse_m": {"semi_major": 1, "semi_minor": 1, "orientation_deg": 0, "probability": "1_SIGMA"}}},
         CONFIG, "99 0D 01 04"),
        ({"geo": {"lat": 45.0, "lon": -90.0, "alt_m": 0.0,
                  "error_ellipse_m": {"semi_major": 1, "semi_minor": 1, "orientation_deg": 0, "probability": "1_SIGMA"}}},
         CONFIG, "99 0D 11 04"),
    ],
    ids=["minimum", "+185", "+015", "+130", "+500", "+130+500"],
)
def test_the_fspec_follows_the_uap(extra, config, fspec):
    geo = extra.pop("geo", None)
    record, reason = encode(make_event(geo=geo, **extra), config=config)
    assert reason is None
    assert record.startswith(bytes.fromhex(fspec))
    assert record[len(bytes.fromhex(fspec)) - 1] & 1 == 0


# --- R1: input --------------------------------------------------------------------

@pytest.mark.parametrize(
    "mutate",
    [
        lambda e: e["event"].__setitem__("event_type", "OBSERVATION_EVENT"),
        lambda e: e["event"].__setitem__("event_type", "FUSION_EVENT"),
        lambda e: e["event"].__setitem__("event_subtype", "PLATFORM_STATE"),
        lambda e: e["event"].pop("event_subtype"),
        lambda e: e.__setitem__("event", "STATE_EVENT"),
        lambda e: e.__setitem__("payload", ["track-alpha"]),
    ],
    ids=["observation", "fusion", "another state subtype", "no subtype", "event not an object", "payload not an object"],
)
def test_r1_only_a_track_state_is_accepted(mutate):
    event = make_event()
    mutate(event)
    refused(event, "CAT062_NOT_TRACK_STATE")


@pytest.mark.parametrize("event", [None, 7, "STATE_EVENT", [], {}, {"event": None}, {"event": {}, "payload": {}}])
def test_r1_refuses_input_that_is_not_an_event(event):
    refused(event, "CAT062_NOT_TRACK_STATE")


def test_the_projection_never_raises():
    awkward = [
        make_event(geo={"lat": "45", "lon": -90.0, "dimensionality": "2D"}),
        make_event(geo=["45.0", "-90.0"]),
        make_event(track_id=["track-alpha"]),
        make_event(track_id={"id": 1}),
        make_event(ts=1731587696),
        make_event(ts=None),
        make_event(heading_deg="90", speed_mps=1.0),
        make_event(heading_deg=float("nan"), speed_mps=float("inf")),
        make_event(geo={"lat": 45.0, "lon": -90.0, "alt_m": 10**400}),
        make_event(geo={"lat": 10**400, "lon": -90.0, "dimensionality": "2D"}),
        make_event(geo={"lat": 45.0, "lon": -90.0, "dimensionality": "2D", "error_ellipse_m": ["1_SIGMA"]}),
        make_event(geo={"lat": 45.0, "lon": -90.0, "dimensionality": "2D",
                        "error_ellipse_m": {"semi_major": 10**400, "semi_minor": 1, "orientation_deg": 0,
                                            "probability": "1_SIGMA"}}),
        make_event(extensions="risk"),
        make_event(extensions={"risk_adjudication": "WARN_ACCEPT"}),
    ]
    for event in awkward:
        record, reason = encode(event)
        assert record is None and isinstance(reason, str) and reason.startswith("CAT062_"), (event, reason)
    for tracks, reason in ((None, "CAT062_TRACK_UNMAPPED"), ([], "CAT062_TRACK_UNMAPPED"),
                           ("track-alpha", "CAT062_TRACK_UNMAPPED"), ({"track-alpha": None}, "CAT062_TRACK_NUMBER_INVALID")):
        refusal = {}
        assert cat062.zmeta_state_to_asterix_cat062(make_event(), CONFIG, track_numbers=tracks, refusal=refusal) is None
        assert refusal == {"reason": reason}, tracks
    for config in (None, [], "sac", {"sac": None}, {}):
        refusal = {}
        assert cat062.zmeta_state_to_asterix_cat062(make_event(), config, track_numbers=TRACKS, refusal=refusal) is None
        assert refusal == {"reason": "CAT062_CONFIG_INVALID"}, config


def test_extreme_values_refuse_or_saturate_without_raising():
    # Schema-valid extremes: speed_mps has no maximum, and json.loads gives a long integer literal an int.
    refused(make_event(heading_deg=0.0, speed_mps=1.0e308), "CAT062_VELOCITY_OUT_OF_RANGE")
    refused(make_event(heading_deg=0.0, speed_mps=10**308), "CAT062_VELOCITY_OUT_OF_RANGE")
    refused(make_event(heading_deg=45.0, speed_mps=11586.0), "CAT062_VELOCITY_OUT_OF_RANGE")
    # The nearest-count range decides below the overflow guard: at 225 degrees both components of 11,585.3 m/s
    # are -8,192.05 m/s, which round to -32,768 counts, inside the item.
    assert velocity_counts(225.0, 11585.3) == (-32768, -32768)
    # A huge semi-major axis saturates the north deviation, and the east one stays exact: b = 1 m at 45
    # degrees is 2.36 counts, rounded up to 3.
    for a in (10**160, 1.0e200):
        assert apw_counts(45.0, a, 1.0, 0.0) == (65535, 3), a
    # Both deviations beyond float range near a pole saturate rather than read as zero.
    assert apw_counts(89.9999999, 1.7e308, 1.7e308, 45.0) == (65535, 65535)


def test_refusal_reason_is_written_only_by_the_refusal_that_fired():
    refusal = {"untouched": True}
    record = cat062.zmeta_state_to_asterix_cat062(make_event(), CONFIG, track_numbers=TRACKS, refusal=refusal)
    assert record == MINIMUM_RECORD and refusal == {"untouched": True}
    assert cat062.zmeta_state_to_asterix_cat062(make_event(track_id="nobody"), CONFIG, track_numbers=TRACKS) is None
    refusal = {}
    cat062.zmeta_state_to_asterix_cat062(make_event(track_id="nobody"), CONFIG, track_numbers=TRACKS, refusal=refusal)
    assert refusal == {"reason": "CAT062_TRACK_UNMAPPED"}


# --- R2: track number ---------------------------------------------------------------

def test_r2_the_track_number_comes_from_the_caller_map():
    for track_id, number in (("track-alpha", 0), ("track-alpha", 1234), ("track-omega", 65535)):
        record, reason = encode(make_event(track_id=track_id), tracks={track_id: number})
        assert reason is None
        assert int.from_bytes(items_of(record)["040"], "big") == number


@pytest.mark.parametrize("track_id", ["nobody", "", DELETE, None, 1234])
def test_r2_an_unmapped_or_missing_track_id_is_refused(track_id):
    refused(make_event(track_id=track_id), "CAT062_TRACK_UNMAPPED")


@pytest.mark.parametrize("number", [-1, 65536, 70000, True, False, 3.0, "7", None])
def test_r2_a_number_outside_the_item_is_refused(number):
    refused(make_event(), "CAT062_TRACK_NUMBER_INVALID", tracks={"track-alpha": number})


def test_r2_no_number_is_minted():
    refused(make_event(), "CAT062_TRACK_UNMAPPED", tracks={})
    refused(make_event(), "CAT062_TRACK_UNMAPPED", tracks={"track-omega": 1})
    first = items_of(encode(make_event(ts="2026-11-14T00:00:01Z"))[0])["040"]
    second = items_of(encode(make_event(ts="2026-11-14T00:00:02Z"))[0])["040"]
    assert first == second == (1234).to_bytes(2, "big")


# --- R3 and the declarations: I062/010, I062/015, I062/080 ------------------------------

# The values each timing declaration accepts: the accepting counterpart of every value the test below refuses for
# that key, so that a refusal is the value's and not the key's.
TIMING_DECLARATIONS_ACCEPT = {
    "allow_holdover_or_unsynced": (False, True),
    "sync_state_when_absent": ("LOCKED", "HOLDOVER", "UNSYNCED", None),
}


def declaration_message(change):
    """The pattern the refusal of a timing declaration's value must match; None for the other declarations, whose
    messages this test does not pin. Only the removed name's pattern matches the unknown-key message."""
    if "allow_degraded_timing" in change:
        return r"does not know the key\(s\) allow_degraded_timing"
    if change.get("allow_holdover_or_unsynced", True) is DELETE:
        return r"must declare allow_holdover_or_unsynced$"
    if "allow_holdover_or_unsynced" in change:
        return r"^allow_holdover_or_unsynced must be true or false$"
    if "sync_state_when_absent" in change:
        return r"^sync_state_when_absent must be exactly LOCKED, HOLDOVER or UNSYNCED, or be left out$"
    return None


def with_change(config, change):
    config = dict(config)
    for key, value in change.items():
        if value is DELETE:
            config.pop(key)
        else:
            config[key] = value
    return config


@pytest.mark.parametrize(
    "change",
    [{"sac": DELETE}, {"sic": DELETE}, {"sac": 256}, {"sic": -1}, {"sac": True}, {"sic": "7"}, {"sac": 25.0},
     {"monosensor": DELETE}, {"tentative": DELETE}, {"simulated": DELETE}, {"monosensor": 1}, {"tentative": 0},
     {"simulated": "false"}, {"service_id": 256}, {"service_id": -1}, {"service_id": True}, {"surveillance": 1},
     {"allow_holdover_or_unsynced": DELETE}, {"allow_holdover_or_unsynced": "false"},
     {"allow_holdover_or_unsynced": "True"}, {"allow_holdover_or_unsynced": 1}, {"allow_holdover_or_unsynced": 0},
     {"allow_holdover_or_unsynced": None}, {"allow_holdover_or_unsynced": [True]},
     {"sync_state_when_absent": "locked"}, {"sync_state_when_absent": "LOCKED "}, {"sync_state_when_absent": ""},
     {"sync_state_when_absent": "FREEWHEEL"}, {"sync_state_when_absent": True}, {"sync_state_when_absent": 1},
     {"sync_state_when_absent": ["LOCKED"]}, {"sync_state_when_absent": {"sync_state": "LOCKED"}},
     {"allow_degraded_timing": True}, {"allow_holdover_or_unsynced": DELETE, "allow_degraded_timing": True}],
    ids=lambda c: ",".join(f"{k}={'absent' if v is DELETE else v!r}" for k, v in c.items()),
)
def test_r3_every_declaration_is_required_and_checked(change):
    config = with_change(CONFIG, change)
    refused(make_event(), "CAT062_CONFIG_INVALID", config=config)
    with pytest.raises(ValueError, match=declaration_message(change)):
        cat062.validate_asterix_config(config)
    # The accepting counterpart: each timing declaration the case names is accepted with every value it takes.
    # The removed name allow_degraded_timing takes none: in the configuration it is an unknown key.
    for key in change:
        for value in TIMING_DECLARATIONS_ACCEPT.get(key, ()):
            accepted = dict(CONFIG, **{key: value})
            declarations = cat062.validate_asterix_config(accepted)
            assert declarations["allow_holdover_or_unsynced"] is accepted["allow_holdover_or_unsynced"]
            record, reason = encode(make_event(), config=accepted)
            assert reason is None and record == MINIMUM_RECORD, (key, value, reason)


def test_r3_sac_and_sic_are_written_as_declared():
    for sac, sic in ((0, 0), (25, 7), (255, 255)):
        record, reason = encode(make_event(), config=dict(CONFIG, sac=sac, sic=sic))
        assert reason is None and items_of(record)["010"] == bytes([sac, sic])


def test_validate_asterix_config_returns_the_declarations():
    assert cat062.validate_asterix_config(dict(CONFIG, service_id=9)) == dict(CONFIG, service_id=9)
    assert cat062.validate_asterix_config(CONFIG) == CONFIG
    # The allowance is always returned; the statement is returned when declared, and left out when absent or
    # null, as service_id is.
    for allowance in (False, True):
        config = dict(CONFIG, allow_holdover_or_unsynced=allowance)
        assert cat062.validate_asterix_config(config) == config
        assert cat062.validate_asterix_config(dict(config, sync_state_when_absent=None)) == config
        for statement in ("LOCKED", "HOLDOVER", "UNSYNCED"):
            declared_config = dict(config, sync_state_when_absent=statement)
            assert cat062.validate_asterix_config(declared_config) == declared_config


@pytest.mark.parametrize(
    "monosensor, tentative, octet",
    [(False, False, 0x20), (True, False, 0xA0), (False, True, 0x22), (True, True, 0xA2)],
)
def test_p1_track_status_is_the_first_octet_alone(monosensor, tentative, octet):
    config = dict(CONFIG, monosensor=monosensor, tentative=tentative)
    for event in (make_event(), full_event()):
        record, reason = encode(event, config=config)
        assert reason is None
        # MON and CNF as declared; SPI 0; MRH 1 (geometric) and SRC 000 (no source), 2-D or 3-D; FX 0: no extent.
        assert items_of(record)["080"] == bytes([octet])


def test_p1f_simulated_true_is_refused():
    refused(make_event(), "CAT062_SIMULATED_UNSUPPORTED", config=dict(CONFIG, simulated=True))
    with pytest.raises(ValueError, match="KOS"):
        cat062.validate_asterix_config(dict(CONFIG, simulated=True))


def test_p8_service_identification_only_when_declared():
    record, _ = encode(make_event())
    assert "015" not in items_of(record)
    for service_id in (0, 3, 255):
        record, reason = encode(make_event(), config=dict(CONFIG, service_id=service_id))
        assert reason is None and items_of(record)["015"] == bytes([service_id])


@pytest.mark.parametrize("export_use", ["", "   ", None, 7, ["COALITION_EXPORT"]])
def test_an_export_use_that_is_not_a_label_is_refused(export_use):
    refused(make_event(), "CAT062_CONFIG_INVALID", export_use=export_use)


# --- R4: time -------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ts, count",
    [
        ("2026-11-14T12:34:56.789Z", 0x587864),
        ("2026-11-14T23:59:59.999Z", 0xA8BFFF),
        ("2026-11-14T00:00:00.0078Z", 0),
        ("2026-11-14T00:00:00Z", 0),
        ("2026-11-14T00:00:00.0079Z", 1),
        ("2026-11-14T12:00:00.9999999Z", 5529727),
        ("2026-11-14T13:34:56.789+01:00", 0x587864),
    ],
)
def test_r4_the_time_is_floored_never_rounded(ts, count):
    record, reason = encode(make_event(ts=ts))
    assert reason is None
    assert int.from_bytes(items_of(record)["070"], "big") == count


def test_r4_the_date_is_not_carried():
    one = encode(make_event(ts="2026-11-14T12:34:56.789Z"))[0]
    two = encode(make_event(ts="2031-02-03T12:34:56.789Z"))[0]
    assert one == two == MINIMUM_RECORD


@pytest.mark.parametrize(
    "ts",
    ["2026-11-14T12:34:56", "2026-11-14", "1969-12-31Z", "2026-11-14T25:00:00Z", "2026-11-14T23:59:60Z",
     "not a time", "", 1731587696, None, DELETE],
)
def test_r4_a_time_that_does_not_parse_to_an_instant_is_refused(ts):
    refused(make_event(ts=ts), "CAT062_TIME_UNPARSEABLE")


def test_p9_the_timestamp_parse_is_the_cot_siblings():
    assert cat062._parse_utc is cot._parse_utc


# --- R5 and P4: position ------------------------------------------------------------

def position_counts(lat, lon):
    record, reason = encode(make_event(geo={"lat": lat, "lon": lon, "dimensionality": "2D"}))
    assert reason is None, reason
    item = items_of(record)["105"]
    return s32(item[:4]), s32(item[4:])


def test_r5_the_position_is_the_nearest_count():
    assert position_counts(12.345678, -98.765432) == (2301401, -18411211)
    for lat, lon in ((0.1, 0.1), (-33.3, 151.1), (51.477, -0.001), (89.99, 179.9), (-0.000001, -179.999)):
        got_lat, got_lon = position_counts(lat, lon)
        assert abs(got_lat * LSB_DEG - lat) <= LSB_DEG / 2 + 1e-12
        assert abs(got_lon * LSB_DEG - lon) <= LSB_DEG / 2 + 1e-12


def test_r5_the_ranges_ends():
    assert position_counts(90.0, 0.0) == (2**24, 0)
    assert position_counts(-90.0, -180.0) == (-(2**24), -(2**25))


@pytest.mark.parametrize(
    "lon, count",
    [(180.0, -(2**25)), (180.0 - LSB_DEG / 4, -(2**25)), (180.0 - 0.75 * LSB_DEG, 2**25 - 1), (-180.0, -(2**25))],
    ids=["+180", "within half a count of +180", "the last count below +180", "-180"],
)
def test_p4_longitude_plus_180_is_written_as_minus_180(lon, count):
    assert position_counts(0.0, lon)[1] == count


@pytest.mark.parametrize(
    "geo",
    [
        None,
        {"lon": -90.0, "dimensionality": "2D"},
        {"lat": 45.0, "dimensionality": "2D"},
        {"lat": float("nan"), "lon": -90.0, "dimensionality": "2D"},
        {"lat": 45.0, "lon": float("inf"), "dimensionality": "2D"},
        {"lat": True, "lon": -90.0, "dimensionality": "2D"},
        {"lat": "45.0", "lon": -90.0, "dimensionality": "2D"},
        {"lat": 90.0001, "lon": -90.0, "dimensionality": "2D"},
        {"lat": -90.5, "lon": -90.0, "dimensionality": "2D"},
        {"lat": 45.0, "lon": 180.0001, "dimensionality": "2D"},
        {"lat": 45.0, "lon": -180.5, "dimensionality": "2D"},
        {"lat": 10**400, "lon": -90.0, "dimensionality": "2D"},
    ],
)
def test_r5_a_missing_or_impossible_position_is_refused(geo):
    event = make_event()
    if geo is None:
        del event["payload"]["geo"]
    else:
        event["payload"]["geo"] = geo
    refused(event, "CAT062_POSITION_INVALID")


# --- R6 and P5: velocity ------------------------------------------------------------

def velocity_counts(heading, speed):
    record, reason = encode(make_event(heading_deg=heading, speed_mps=speed))
    assert reason is None, reason
    item = items_of(record)["185"]
    return s16(item[:2]), s16(item[2:])


@pytest.mark.parametrize(
    "heading, speed, counts",
    [(90.0, 100.0, (400, 0)), (0.0, 100.0, (0, 400)), (180.0, 100.0, (0, -400)), (270.0, 100.0, (-400, 0)),
     (30.0, 10.0, (20, 35)), (360.0, 4.0, (0, 16)), (45.0, 0.0, (0, 0))],
)
def test_r6_vx_is_east_and_vy_is_north(heading, speed, counts):
    assert velocity_counts(heading, speed) == counts


@pytest.mark.parametrize(
    "members", [{"heading_deg": 90.0}, {"speed_mps": 100.0}, {"heading_deg": 90.0, "speed_mps": None}, {}],
)
def test_r6_velocity_only_from_both_course_and_speed(members):
    record, reason = encode(make_event(**members))
    assert reason is None and "185" not in items_of(record)


@pytest.mark.parametrize(
    "heading, speed",
    [(float("nan"), 1.0), (90.0, float("inf")), (361.0, 1.0), (-1.0, 1.0), (90.0, -0.5), (True, 1.0), ("90", 1.0)],
)
def test_r6_an_impossible_course_or_speed_is_refused(heading, speed):
    refused(make_event(heading_deg=heading, speed_mps=speed), "CAT062_VELOCITY_INVALID")


def test_p5_a_component_beyond_the_item_is_refused():
    refused(make_event(heading_deg=0.0, speed_mps=8192.0), "CAT062_VELOCITY_OUT_OF_RANGE")
    refused(make_event(heading_deg=90.0, speed_mps=9000.0), "CAT062_VELOCITY_OUT_OF_RANGE")
    assert velocity_counts(180.0, 8192.0) == (0, -32768)
    assert velocity_counts(0.0, 8191.75) == (0, 32767)


# --- R8 and P6: altitude ----------------------------------------------------------------

def test_r8_a_declared_2d_geo_writes_no_altitude():
    record, reason = encode(make_event())
    assert reason is None and "130" not in items_of(record)


@pytest.mark.parametrize(
    "geo, count",
    [
        ({"lat": 45.0, "lon": -90.0, "alt_m": 1905.0}, 1000),
        ({"lat": 45.0, "lon": -90.0, "alt_m": 1905.0, "dimensionality": "3D"}, 1000),
        ({"lat": 45.0, "lon": -90.0, "alt_m": -12.0}, -6),
        ({"lat": 45.0, "lon": -90.0, "alt_m": 45720.0}, 24000),
        ({"lat": 45.0, "lon": -90.0, "alt_m": -457.2}, -240),
    ],
)
def test_r8_a_3d_geo_writes_its_height_above_the_ellipsoid(geo, count):
    record, reason = encode(make_event(geo=geo))
    assert reason is None
    assert s16(items_of(record)["130"]) == count


@pytest.mark.parametrize(
    "geo",
    [
        {"lat": 45.0, "lon": -90.0, "dimensionality": "2D", "alt_m": 10.0},
        {"lat": 45.0, "lon": -90.0},
        {"lat": 45.0, "lon": -90.0, "dimensionality": "3D"},
        {"lat": 45.0, "lon": -90.0, "alt_m": float("nan")},
        {"lat": 45.0, "lon": -90.0, "alt_m": True},
        {"lat": 45.0, "lon": -90.0, "alt_m": 10.0, "dimensionality": "2d"},
    ],
    ids=["2-D with alt_m", "3-D without alt_m", "declared 3-D without alt_m", "NaN", "a bool", "an unknown dimensionality"],
)
def test_r8_an_incoherent_or_missing_altitude_is_refused(geo):
    refused(make_event(geo=geo), "CAT062_ALTITUDE_INVALID")


@pytest.mark.parametrize("alt_m", [45722.0, -458.2, 1.0e6, -1.0e4])
def test_p6_an_altitude_beyond_the_item_is_refused(alt_m):
    refused(make_event(geo={"lat": 45.0, "lon": -90.0, "alt_m": alt_m}), "CAT062_ALTITUDE_OUT_OF_RANGE")


# --- R7 and P3: accuracy -----------------------------------------------------------------

def ellipse(a, b, theta, probability="1_SIGMA"):
    value = {"semi_major": a, "semi_minor": b, "orientation_deg": theta}
    if probability is not None:
        value["probability"] = probability
    return value


def apw_counts(lat, a, b, theta, lon=10.0):
    record, reason = encode(make_event(geo={"lat": lat, "lon": lon, "dimensionality": "2D",
                                            "error_ellipse_m": ellipse(a, b, theta)}))
    assert reason is None, reason
    item = items_of(record)["500"]
    assert item[0] == 0x20, "the primary subfield must carry APW alone"
    assert len(item) == 5
    return int.from_bytes(item[1:3], "big"), int.from_bytes(item[3:5], "big")


@pytest.mark.parametrize(
    "lat, a, b, theta, counts",
    [
        (12.345678, 30.0, 10.0, 30.0, (45, 30)),
        (12.345678, 30.0, 10.0, 210.0, (45, 30)),
        (45.0, 30.0, 10.0, 0.0, (51, 24)),
        (-45.0, 30.0, 10.0, 0.0, (51, 24)),
        (45.0, 30.0, 10.0, 90.0, (17, 71)),
        (0.0, 1000.0, 1000.0, 0.0, (1686, 1675)),
        (45.0, 0.0, 0.0, 0.0, (0, 0)),
    ],
    ids=["12.3 deg, 30 by 10 at 30", "the same at 210", "45 deg, major north", "-45 deg, major north",
         "45 deg, major east", "equator, 1 km circle", "zero"],
)
def test_p3_apw_is_the_north_and_east_marginals_in_degrees(lat, a, b, theta, counts):
    assert apw_counts(lat, a, b, theta) == counts


def test_p3_each_deviation_is_rounded_up():
    # 60 degrees, a 100 m circle: 167.32 and 334.07 counts; to the nearest they would be 167 and 334.
    assert apw_counts(60.0, 100.0, 100.0, 0.0) == (168, 335)


def test_p3_a_deviation_beyond_the_item_saturates():
    assert apw_counts(45.0, 1.0e6, 1.0e6, 0.0) == (65535, 65535)
    assert apw_counts(89.9999999, 10.0, 10.0, 0.0) == (17, 65535)


@pytest.mark.parametrize("lat", [90.0, -90.0])
def test_p3_no_accuracy_item_at_a_pole(lat):
    record, reason = encode(make_event(geo={"lat": lat, "lon": 0.0, "dimensionality": "2D",
                                            "error_ellipse_m": ellipse(10.0, 10.0, 0.0)}))
    assert reason is None and "500" not in items_of(record)


@pytest.mark.parametrize("probability", ["CEP", "CE_90", "CE_95", None, "2_SIGMA", 1])
def test_r7_any_other_probability_writes_no_accuracy_item(probability):
    record, reason = encode(make_event(geo={"lat": 45.0, "lon": -90.0, "dimensionality": "2D",
                                            "error_ellipse_m": ellipse(10.0, 10.0, 0.0, probability)}))
    assert reason is None and "500" not in items_of(record)


@pytest.mark.parametrize(
    "value",
    [
        ellipse(-1.0, 1.0, 0.0),
        ellipse(1.0, -1.0, 0.0),
        ellipse(float("nan"), 1.0, 0.0),
        ellipse(1.0, 1.0, float("inf")),
        ellipse(1.0, 1.0, 400.0),
        ellipse(1.0, 1.0, -0.5),
        ellipse(True, 1.0, 0.0),
        {"semi_major": 1.0, "semi_minor": 1.0, "probability": "1_SIGMA"},
        {"semi_minor": 1.0, "orientation_deg": 0.0, "probability": "1_SIGMA"},
        ["1_SIGMA"],
        "1_SIGMA",
    ],
)
def test_r7_a_malformed_ellipse_is_refused(value):
    refused(make_event(geo={"lat": 45.0, "lon": -90.0, "dimensionality": "2D", "error_ellipse_m": value}),
            "CAT062_ACCURACY_INVALID")


def test_p3_a_2d_and_a_3d_geo_carry_the_same_accuracy():
    two = apw_counts(45.0, 30.0, 10.0, 0.0)
    record, reason = encode(make_event(geo={"lat": 45.0, "lon": 10.0, "alt_m": 5.0,
                                            "error_ellipse_m": ellipse(30.0, 10.0, 0.0)}))
    assert reason is None
    item = items_of(record)["500"]
    assert (int.from_bytes(item[1:3], "big"), int.from_bytes(item[3:5], "big")) == two


# --- R10 and P2: what has no carrier, and the risk gate -----------------------------------

def test_r10_members_without_a_carrier_do_not_change_the_record():
    base = encode(make_event())[0]
    assert base == MINIMUM_RECORD
    event = make_event(
        valid_for_ms=999999,
        timing_quality={"time_source": "NTP", "sync_state": "LOCKED", "est_error_ms": 30.0,
                        "last_sync_ts": "2026-11-14T12:00:00Z", "est_error_basis": "MEASURED"},
        source_summary=["eo", "rf"],
        provenance={"note": "invented"},
        quality={"geo_status": "VERTICAL_UNAVAILABLE"},
        extensions={"vendor.example": {"x": 1}},
        callsign="INVENTED1",
        **{"class": "vehicle"},
    )
    event["confidence"] = 0.99
    event["lineage"] = {"based_on": ["01938f2a-0000-7000-8000-000000000003"], "transform": "fuse"}
    event["profile"] = "H"
    event["event"]["t_publish"] = "2026-11-14T12:35:00Z"
    event["event"]["event_id"] = "01938f2a-0000-7000-8000-0000000000ff"
    event["zmeta_version"] = "1.0"
    assert encode(event)[0] == base


# --- P10: timing quality ---------------------------------------------------------------

@pytest.mark.parametrize(
    "timing, reason",
    [
        (dict(LOCKED, sync_state="HOLDOVER"), "CAT062_TIMING_HOLDOVER"),
        (UNSYNCED, "CAT062_TIMING_UNSYNCED"),
        (DELETE, "CAT062_TIMING_ABSENT"),
        (None, "CAT062_TIMING_MALFORMED"),
        ("LOCKED", "CAT062_TIMING_MALFORMED"),
        (["LOCKED"], "CAT062_TIMING_MALFORMED"),
        (dict(LOCKED, sync_state="locked"), "CAT062_TIMING_MALFORMED"),
        (dict(LOCKED, sync_state="FREEWHEEL"), "CAT062_TIMING_MALFORMED"),
        ({k: v for k, v in LOCKED.items() if k != "sync_state"}, "CAT062_TIMING_MALFORMED"),
    ],
    ids=["holdover", "unsynced", "absent", "null", "a string", "a list", "lower case", "an unknown token",
         "no sync_state"],
)
def test_p10_timing_that_is_not_locked_is_refused_unless_allowed(timing, reason):
    event = make_event(timing_quality=timing)
    # The allowance is a declaration in the configuration: false refuses each case with its own reason.
    refused(event, reason)
    refused(event, reason, config=dict(CONFIG, allow_holdover_or_unsynced=False))
    allowed = dict(CONFIG, allow_holdover_or_unsynced=True)
    if reason in ("CAT062_TIMING_MALFORMED", "CAT062_TIMING_ABSENT"):
        # The allowance covers a stated HOLDOVER or UNSYNCED only. Unreadable timing fails closed, and an event that
        # carries no timing quality, with nothing declared for it, is refused whatever the allowance says.
        refused(event, reason, config=allowed)
        return
    record, got = encode(event, config=allowed)
    # With the allowance the record is the locked event's, byte for byte: it carries no notice of the clock.
    assert got is None and record == MINIMUM_RECORD


def test_p10_malformed_timing_never_exports():
    # From the seeded review of 2026-11-14: a malformed timing_quality is refused whatever the allowance says, and
    # whatever the configuration states for events that carry no timing quality.
    for timing in ("LOCKED", ["LOCKED"], None, dict(LOCKED, sync_state="FREEWHEEL")):
        for statement in (None, "LOCKED", "HOLDOVER", "UNSYNCED"):
            for allowance in (False, True):
                config = dict(CONFIG, allow_holdover_or_unsynced=allowance, sync_state_when_absent=statement)
                refused(make_event(timing_quality=timing), "CAT062_TIMING_MALFORMED", config=config)
    for timing in (dict(LOCKED, sync_state="HOLDOVER"), UNSYNCED):
        record, reason = encode(make_event(timing_quality=timing), config=dict(CONFIG, allow_holdover_or_unsynced=True))
        assert reason is None and record == MINIMUM_RECORD


def test_p10_locked_timing_exports_without_the_allowance():
    config = dict(CONFIG, allow_holdover_or_unsynced=False)
    record, reason = encode(make_event(), config=config)
    assert reason is None and record == MINIMUM_RECORD
    # No threshold on est_error_ms: a locked claim with any stated bound exports.
    record, reason = encode(make_event(timing_quality=dict(LOCKED, est_error_ms=1.0e9)), config=config)
    assert reason is None and record == MINIMUM_RECORD


def test_p10_the_allowance_is_no_longer_a_keyword():
    # Both timing declarations live in the configuration. The signature names neither, nor the keyword the
    # allowance once was, and a call that passes that keyword raises TypeError from Python's own argument binding,
    # before any record leaves.
    assert list(inspect.signature(cat062.zmeta_state_to_asterix_cat062).parameters) == [
        "event", "asterix_config", "track_numbers", "export_use", "refusal"]
    for value in (True, False):
        with pytest.raises(TypeError, match="allow_degraded_timing"):
            cat062.zmeta_state_to_asterix_cat062(make_event(timing_quality=UNSYNCED), CONFIG, track_numbers=TRACKS,
                                                 allow_degraded_timing=value)


def test_p10_the_allowance_never_opens_the_risk_gate():
    # The record the reference gateway writes on a state whose node is unsynchronized (gateway.py,
    # _apply_failure_mode_degradation), on an event whose own timing is unsynchronized.
    record = {"risk_dimension": "timing", "reason_code": "TIMING_STATUS_UNSYNCED", "policy_mode": "degrade",
              "policy_decision": "DEGRADED_ACCEPT", "policy_ref": "gateway.failure_modes.timing_loss",
              "effects": {"confidence_reduction_factor": 2.0}, "sync_state": "UNSYNCED"}
    event = make_event(timing_quality=UNSYNCED, extensions={"risk_adjudication": [record]})
    refused(event, "CAT062_RISK_DEGRADED_ACCEPT", config=dict(CONFIG, allow_holdover_or_unsynced=True))
    refused(event, "CAT062_RISK_DEGRADED_ACCEPT")
    # Nor does a statement: a declared LOCKED for an event that carries no timing quality, with the same record.
    # Without the record the same event exports, so the refusal is the risk gate's.
    absent = make_event(timing_quality=DELETE, extensions={"risk_adjudication": [record]})
    for allowance in (False, True):
        config = dict(CONFIG, sync_state_when_absent="LOCKED", allow_holdover_or_unsynced=allowance)
        refused(absent, "CAT062_RISK_DEGRADED_ACCEPT", config=config)
        exported, reason = encode(make_event(timing_quality=DELETE), config=config)
        assert reason is None and exported == MINIMUM_RECORD


def test_p10_the_order_of_the_gates():
    # Risk before timing; timing before the time parse; the configuration after the input type.
    refused(make_event(timing_quality=UNSYNCED, extensions={"risk_adjudication": [{"policy_decision": "WARN_ACCEPT"}]}),
            "CAT062_RISK_WARN_ACCEPT")
    refused(make_event(ts="not a time", timing_quality=UNSYNCED), "CAT062_TIMING_UNSYNCED")
    refused(make_event(ts="not a time", timing_quality=UNSYNCED), "CAT062_TIME_UNPARSEABLE",
            config=dict(CONFIG, allow_holdover_or_unsynced=True))
    refused(make_event(ts="not a time", timing_quality=DELETE), "CAT062_TIMING_ABSENT",
            config=dict(CONFIG, allow_holdover_or_unsynced=True))
    refused(make_event(ts="not a time", timing_quality=DELETE), "CAT062_TIME_UNPARSEABLE",
            config=dict(CONFIG, sync_state_when_absent="LOCKED"))
    observation = make_event(timing_quality=UNSYNCED)
    observation["event"]["event_type"] = "OBSERVATION_EVENT"
    refused(observation, "CAT062_NOT_TRACK_STATE", config=dict(CONFIG, allow_holdover_or_unsynced="yes"))
    refused(make_event(timing_quality=UNSYNCED), "CAT062_CONFIG_INVALID", config=dict(CONFIG, sac=999))


# --- P10: the statement for events that carry no timing quality, and the allowance ------------

def declared(statement=None, allowance=False):
    """CONFIG with the allowance, and with the statement for events that carry no timing quality when one is
    given."""
    config = dict(CONFIG, allow_holdover_or_unsynced=allowance)
    if statement is not None:
        config["sync_state_when_absent"] = statement
    return config


def test_p10_a_declared_locked_supplies_the_state_an_event_lacks():
    # An event that carries no timing quality, under a declared LOCKED and the allowance false, exports, and its
    # record is byte for byte the record of the same event stating LOCKED itself: as clean as the declaration and
    # no cleaner.
    record, reason = encode(make_event(timing_quality=DELETE), config=declared("LOCKED"))
    assert reason is None and record == MINIMUM_RECORD == encode(make_event())[0]


@pytest.mark.parametrize(
    "statement, reason", [("HOLDOVER", "CAT062_TIMING_HOLDOVER"), ("UNSYNCED", "CAT062_TIMING_UNSYNCED")]
)
def test_p10_a_declared_holdover_or_unsynced_exports_only_with_the_allowance(statement, reason):
    event = make_event(timing_quality=DELETE)
    refused(event, reason, config=declared(statement, allowance=False))
    record, got = encode(event, config=declared(statement, allowance=True))
    assert got is None and record == MINIMUM_RECORD


def test_p10_nothing_declared_leaves_an_absent_timing_quality_refused():
    # The allowance covers a stated HOLDOVER or UNSYNCED only, and an event that carries no timing quality states
    # no sync state of its own.
    event = make_event(timing_quality=DELETE)
    for allowance in (False, True):
        refused(event, "CAT062_TIMING_ABSENT", config=declared(allowance=allowance))
        # A null statement is left out, as a null service_id is.
        refused(event, "CAT062_TIMING_ABSENT", config=dict(declared(allowance=allowance), sync_state_when_absent=None))


def test_p10_the_statement_never_overrides_an_events_own_timing():
    for timing, reason in ((UNSYNCED, "CAT062_TIMING_UNSYNCED"),
                           (dict(LOCKED, sync_state="HOLDOVER"), "CAT062_TIMING_HOLDOVER")):
        refused(make_event(timing_quality=timing), reason, config=declared("LOCKED"))
    # An event that states LOCKED exports on its own statement, whatever is declared for events that state none.
    for statement in ("HOLDOVER", "UNSYNCED"):
        record, reason = encode(make_event(), config=declared(statement))
        assert reason is None and record == MINIMUM_RECORD


def test_p10_the_statement_never_repairs_a_malformed_timing_quality():
    for timing in (None, "LOCKED", ["LOCKED"], dict(LOCKED, sync_state="locked"), dict(LOCKED, sync_state="FREEWHEEL"),
                   {k: v for k, v in LOCKED.items() if k != "sync_state"}):
        refused(make_event(timing_quality=timing), "CAT062_TIMING_MALFORMED", config=declared("LOCKED", allowance=True))


def test_p10_the_statement_in_force_is_the_calls():
    # The configuration is read on every call, so the statement passed with an event is the one that applies.
    event = make_event(timing_quality=DELETE)
    record, reason = encode(event, config=declared("LOCKED"))
    assert reason is None and record == MINIMUM_RECORD
    refused(event, "CAT062_TIMING_ABSENT", config=declared())
    refused(event, "CAT062_TIMING_UNSYNCED", config=declared("UNSYNCED"))
    record, reason = encode(event, config=declared("LOCKED"))
    assert reason is None and record == MINIMUM_RECORD


@pytest.mark.parametrize(
    "change",
    [{"allow_holdover_or_unsynced": "true"}, {"allow_holdover_or_unsynced": None},
     {"sync_state_when_absent": "locked"}, {"sync_state_when_absent": 1}],
    ids=lambda c: ",".join(f"{k}={v!r}" for k, v in c.items()),
)
def test_p10_the_timing_declarations_are_checked_before_the_simulated_refusal(change):
    config = with_change(dict(CONFIG, simulated=True), change)
    refused(make_event(), "CAT062_CONFIG_INVALID", config=config)
    with pytest.raises(ValueError, match=declaration_message(change)):
        cat062.validate_asterix_config(config)


def test_p10_the_statement_is_a_plain_string():
    # Only a plain str is a statement, as only a plain bool is an allowance. A str subclass can compare equal to a
    # token it does not spell, so the value check alone is not exact: one that folds case reads "locked" as
    # "LOCKED".
    class FoldsCase(str):
        def __eq__(self, other):
            return str.lower(self) == str(other).lower()

        __hash__ = str.__hash__

    for value in (FoldsCase("locked"), FoldsCase("LOCKED")):
        config = dict(CONFIG, sync_state_when_absent=value)
        refused(make_event(timing_quality=DELETE), "CAT062_CONFIG_INVALID", config=config)
        with pytest.raises(ValueError, match=declaration_message({"sync_state_when_absent": value})):
            cat062.validate_asterix_config(config)
    # The accepting counterpart: the same token as a plain str.
    record, reason = encode(make_event(timing_quality=DELETE), config=dict(CONFIG, sync_state_when_absent="LOCKED"))
    assert reason is None and record == MINIMUM_RECORD


# Timing quality at the two other per-event paths the reference policy reads, in each shape a path can take there:
# a member of payload.quality, and the timing fields in payload.quality itself.
TIMING_ELSEWHERE = [
    {"timing_quality": dict(UNSYNCED)},
    {"timing_quality": dict(LOCKED)},
    {"timing_quality": None},
    dict(UNSYNCED),
    dict(LOCKED),
    {"sync_state": "LOCKED"},
]


def policy_per_event_timing_paths():
    """The per-event timing paths of the reference policy, policy/semantics.yaml."""
    import yaml

    with open(ROOT / "policy" / "semantics.yaml", encoding="utf-8") as handle:
        return yaml.safe_load(handle)["semantics"]["timing_quality"]["per_event_paths"]


def test_p10_timing_at_a_path_the_adapter_does_not_read_is_refused_as_absent():
    # The reference policy reads per-event timing quality at three paths, and this adapter reads the first alone. A
    # statement never speaks for an event that states its own timing quality, so an event whose timing quality sits
    # at either other path is refused as absent, whatever is declared and whatever the allowance says.
    assert policy_per_event_timing_paths() == [
        "payload.timing_quality", "payload.quality.timing_quality", "payload.quality"]
    for quality in TIMING_ELSEWHERE:
        event = make_event(timing_quality=DELETE, quality=quality)
        for statement in ("LOCKED", "HOLDOVER", "UNSYNCED", None):
            for allowance in (False, True):
                refused(event, "CAT062_TIMING_ABSENT", config=declared(statement, allowance))


# --- P10: an incomplete or poisoned payload.timing_quality ------------------------------------
#
# A payload.timing_quality that lacks one of the four timing fields the reference policy requires
# (policy/semantics.yaml, timing_quality.required_fields) is not taken as per-event timing quality by the reference
# gateway's readers, and the adapter refuses it as malformed, whatever is declared and whatever the allowance says.
# So is one whose est_error_ms is poisoned (not a finite non-negative number), which adapters/AUTHORING.md rule 5
# and adapters/ingress/time_utils.py pass through untouched for an adapter's refusal gate to reject whole.

TIMING_FIELDS = ("time_source", "sync_state", "est_error_ms", "last_sync_ts")
HOLDOVER = dict(LOCKED, sync_state="HOLDOVER")
# A 1.1.0 block with the optional est_error_basis beside the four fields: with one field removed it still holds four
# keys, so a check that counts keys instead of naming them passes it.
LOCKED_WITH_BASIS = dict(LOCKED, est_error_basis="MEASURED")
WHOLE_BLOCKS = (("LOCKED", LOCKED), ("HOLDOVER", HOLDOVER), ("UNSYNCED", UNSYNCED),
                ("LOCKED with est_error_basis", LOCKED_WITH_BASIS))


def without(block, field):
    return {key: value for key, value in block.items() if key != field}


# Each whole block with each of the four fields removed in turn.
INCOMPLETE = [(f"{name} without {field}", without(block, field)) for name, block in WHOLE_BLOCKS
              for field in TIMING_FIELDS]
# The review's probe: a payload.timing_quality holding only a sync_state, alone and beside a whole UNSYNCED block at
# each of the other two per-event paths, as payload members.
SYNC_STATE_ONLY = [
    {"timing_quality": {"sync_state": "LOCKED"}},
    {"timing_quality": {"sync_state": "LOCKED"}, "quality": {"timing_quality": dict(UNSYNCED)}},
    {"timing_quality": {"sync_state": "LOCKED"}, "quality": dict(UNSYNCED)},
]
# est_error_ms values the reference ingress passes through untouched as poisoned: wrong type, non-finite or
# negative. A Python int beyond the float64 range, which json.loads builds from a long literal, counts as
# non-finite.
POISONED_BOUNDS = [None, float("nan"), float("inf"), float("-inf"), -1, -1.0e-9, "1.0", True, False, [1.0],
                   10**400]
POISONED = [(f"{name}, est_error_ms={bound!r:.12}", dict(block, est_error_ms=bound)) for name, block in WHOLE_BLOCKS
            for bound in POISONED_BOUNDS]
# Case H: the four keys, sync_state LOCKED and the other three null.
POISONED.append(("case H", dict(LOCKED, time_source=None, est_error_ms=None, last_sync_ts=None)))


def every_declaration():
    for statement in STATEMENTS:
        for allowance in ALLOWANCES:
            yield declared(statement, allowance)


@pytest.mark.parametrize("timing", [block for _id, block in INCOMPLETE], ids=[name for name, _b in INCOMPLETE])
def test_p10_t1_a_timing_quality_without_one_of_the_four_fields_is_malformed(timing):
    # Refused whatever the statement (none, LOCKED, HOLDOVER, UNSYNCED) and whatever the allowance. The rows without
    # sync_state are also refused by the token check; T5 is the test that pins sync_state among the four.
    for config in every_declaration():
        refused(make_event(timing_quality=timing), "CAT062_TIMING_MALFORMED", config=config)


@pytest.mark.parametrize("members", SYNC_STATE_ONLY, ids=["alone", "beside quality.timing_quality", "beside quality"])
def test_p10_t2_a_sync_state_alone_is_malformed_wherever_else_timing_sits(members):
    # The reference gateway's reader skips the incomplete member and takes the whole UNSYNCED block at the next path;
    # the adapter reads payload.timing_quality alone and refuses it, so it never exports what that reader takes as
    # UNSYNCED.
    for config in every_declaration():
        refused(make_event(**members), "CAT062_TIMING_MALFORMED", config=config)


@pytest.mark.parametrize("state", ["HOLDOVER", "UNSYNCED"])
def test_p10_t3_the_allowance_never_opens_an_incomplete_holdover_or_unsynced(state):
    for statement in STATEMENTS:
        refused(make_event(timing_quality={"sync_state": state}), "CAT062_TIMING_MALFORMED",
                config=declared(statement, allowance=True))


def test_p10_t4_a_block_holding_the_four_fields_exports_on_its_sync_state():
    # The accepting counterpart of T1 to T3: the new check refuses a missing field or a poisoned bound and nothing
    # else. A whole LOCKED block exports under every declaration, with or without est_error_basis.
    for block in (LOCKED, LOCKED_WITH_BASIS):
        for config in every_declaration():
            record, reason = encode(make_event(timing_quality=dict(block)), config=config)
            assert reason is None and record == MINIMUM_RECORD, (block, config)
    # A whole HOLDOVER or UNSYNCED block, with or without est_error_basis, exports under the allowance.
    for block in (HOLDOVER, UNSYNCED, dict(UNSYNCED, est_error_basis="CONVENTION_DEFAULT")):
        record, reason = encode(make_event(timing_quality=dict(block)), config=declared(allowance=True))
        assert reason is None and record == MINIMUM_RECORD, block
    # Presence is the test for time_source and last_sync_ts: their values are not read.
    for block in (dict(LOCKED, time_source=None, last_sync_ts=None), dict(LOCKED, time_source="FREEWHEEL"),
                  dict(LOCKED, last_sync_ts="not a time")):
        record, reason = encode(make_event(timing_quality=block))
        assert reason is None and record == MINIMUM_RECORD, block
    # Any finite non-negative bound exports, zero and an integer included: no timing threshold.
    for bound in (0, 0.0, 3, 1.0e9):
        record, reason = encode(make_event(timing_quality=dict(LOCKED, est_error_ms=bound)))
        assert reason is None and record == MINIMUM_RECORD, bound


def test_p10_t5_the_four_fields_are_the_policys_and_the_schemas():
    # The module writes the names itself (it imports only the standard library and its CoT sibling); they are the
    # reference policy's required_fields and each event schema's timing_quality.required, read from the files.
    import yaml

    with open(ROOT / "policy" / "semantics.yaml", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)["semantics"]["timing_quality"]["required_fields"]
    assert tuple(cat062._TIMING_FIELDS) == tuple(policy) == TIMING_FIELDS
    for name in ("zmeta-event-1.0.schema.json", "zmeta-event-1.1.0.schema.json"):
        with open(ROOT / "schema" / name, encoding="utf-8") as handle:
            required = json.load(handle)["$defs"]["timing_quality"]["required"]
        assert tuple(required) == TIMING_FIELDS, name


@pytest.mark.parametrize("timing", [block for _id, block in POISONED], ids=[name for name, _b in POISONED])
def test_p10_a_poisoned_est_error_ms_is_malformed(timing):
    # Case H and its kin: the four keys present, the bound poisoned. The reference ingress passes such a claim
    # through untouched so that an adapter's refusal gate rejects it whole (adapters/AUTHORING.md, rule 5), and a
    # pipeline with no gateway has no schema stage before this adapter.
    for config in every_declaration():
        refused(make_event(timing_quality=timing), "CAT062_TIMING_MALFORMED", config=config)


# The timing gate as a table, one row per rule: the event's timing quality, the statement declared for events that
# carry none, the allowance, and the result (None: the event exports). ANY stands for every value of its column.
ANY = object()
STATEMENTS = (None, "LOCKED", "HOLDOVER", "UNSYNCED")
ALLOWANCES = (False, True)
TIMING_GATE = [
    ("LOCKED", ANY, ANY, None),
    ("HOLDOVER", ANY, False, "CAT062_TIMING_HOLDOVER"),
    ("HOLDOVER", ANY, True, None),
    ("UNSYNCED", ANY, False, "CAT062_TIMING_UNSYNCED"),
    ("UNSYNCED", ANY, True, None),
    ("malformed", ANY, ANY, "CAT062_TIMING_MALFORMED"),
    ("absent", None, ANY, "CAT062_TIMING_ABSENT"),
    ("absent", "LOCKED", ANY, None),
    ("absent", "HOLDOVER", False, "CAT062_TIMING_HOLDOVER"),
    ("absent", "HOLDOVER", True, None),
    ("absent", "UNSYNCED", False, "CAT062_TIMING_UNSYNCED"),
    ("absent", "UNSYNCED", True, None),
    ("at another path", ANY, ANY, "CAT062_TIMING_ABSENT"),
]
# The payload members of the events for each value of the first column. An event that carries no timing quality
# may still carry a payload.quality without timing members, or one that is not an object.
TIMING_EVENTS = {
    "LOCKED": [{"timing_quality": dict(LOCKED)}],
    "HOLDOVER": [{"timing_quality": dict(LOCKED, sync_state="HOLDOVER")}],
    "UNSYNCED": [{"timing_quality": dict(UNSYNCED)}],
    "malformed": [{"timing_quality": value} for value in (
        None, "LOCKED", ["LOCKED"], dict(LOCKED, sync_state="locked"), dict(LOCKED, sync_state="FREEWHEEL"),
        {k: v for k, v in LOCKED.items() if k != "sync_state"})]
    + [{"timing_quality": block} for _name, block in INCOMPLETE + POISONED]
    + SYNC_STATE_ONLY,
    "absent": [{"timing_quality": DELETE},
               {"timing_quality": DELETE, "quality": {"geo_status": "VERTICAL_UNAVAILABLE"}},
               {"timing_quality": DELETE, "quality": "sync_state"}],
    "at another path": [{"timing_quality": DELETE, "quality": quality} for quality in TIMING_ELSEWHERE],
}


def test_p10_the_timing_gate_table():
    covered = {}
    for timing, statement, allowance, result in TIMING_GATE:
        for s in (STATEMENTS if statement is ANY else (statement,)):
            for a in (ALLOWANCES if allowance is ANY else (allowance,)):
                assert (timing, s, a) not in covered, (timing, s, a)
                covered[(timing, s, a)] = result
                for members in TIMING_EVENTS[timing]:
                    record, reason = encode(make_event(**members), config=declared(s, a))
                    if result is None:
                        assert reason is None and record == MINIMUM_RECORD, (timing, s, a, members, reason)
                    else:
                        assert record is None and reason == result, (timing, s, a, members, reason)
    # Every combination of the three columns is exactly one row's.
    assert set(covered) == {(t, s, a) for t in TIMING_EVENTS for s in STATEMENTS for a in ALLOWANCES}


def test_r10_the_loss_register_names_every_member_without_a_carrier():
    for member in ("date", "event_identity", "source_identity", "confidence", "lineage", "timing_quality",
                   "valid_for_ms", "class", "source_summary", "provenance_and_quality", "extensions",
                   "risk_adjudication", "geo_uncertainty", "altitude_source", "track_status_declarations",
                   "lifecycle", "simulation", "course_or_speed_alone", "callsign"):
        assert isinstance(cat062.ASTERIX_EGRESS_LOSS_NOTES.get(member), str), member


def risk(*records):
    return make_event(extensions={"risk_adjudication": list(records)})


@pytest.mark.parametrize(
    "records",
    [(), ({"policy_decision": "IGNORED"},), ({"policy_decision": "ignored", "risk_dimension": "timing"},),
     ({"policy_decision": "IGNORED", "allowed_uses": ["COALITION_EXPORT", "DISPLAY"]},),
     ({"policy_decision": "IGNORED", "prohibited_uses": ["AUTONOMY_TASKING"]},)],
    ids=["no record", "ignored", "ignored in lower case", "ignored, export granted", "ignored, another use barred"],
)
def test_p2_an_event_whose_records_all_ignore_without_restriction_is_exported(records):
    record, reason = encode(risk(*records))
    assert reason is None and record == MINIMUM_RECORD


@pytest.mark.parametrize(
    "decision, reason",
    [("WARN_ACCEPT", "CAT062_RISK_WARN_ACCEPT"), ("DEGRADED_ACCEPT", "CAT062_RISK_DEGRADED_ACCEPT"),
     ("QUARANTINE_ACCEPT", "CAT062_RISK_QUARANTINE_ACCEPT"), ("REJECTED", "CAT062_RISK_REJECTED"),
     (" warn_accept ", "CAT062_RISK_WARN_ACCEPT"), ("LOCAL_HOLD", "CAT062_RISK_UNKNOWN_DECISION"),
     ("", "CAT062_RISK_UNKNOWN_DECISION"), (None, "CAT062_RISK_UNKNOWN_DECISION")],
)
def test_p2_every_other_decision_is_refused_with_its_own_reason(decision, reason):
    record = {"risk_dimension": "timing", "reason_code": "TIMING_UNSYNCED"}
    if decision is not None:
        record["policy_decision"] = decision
    refused(risk(record), reason)


def test_p2_a_use_restriction_on_the_export_use_is_refused():
    refused(risk({"policy_decision": "IGNORED", "prohibited_uses": ["COALITION_EXPORT"]}), "CAT062_RISK_USE_RESTRICTED")
    refused(risk({"policy_decision": "IGNORED", "prohibited_uses": "coalition_export"}), "CAT062_RISK_USE_RESTRICTED")
    refused(risk({"policy_decision": "IGNORED", "allowed_uses": ["DISPLAY"]}), "CAT062_RISK_USE_RESTRICTED")
    event = risk({"policy_decision": "IGNORED", "prohibited_uses": ["COALITION_EXPORT"]})
    record, reason = encode(event, export_use="display")
    assert reason is None and record == MINIMUM_RECORD
    refused(risk({"policy_decision": "IGNORED", "allowed_uses": ["COALITION_EXPORT"]}), "CAT062_RISK_USE_RESTRICTED",
            export_use="DISPLAY")


def test_p2_use_labels_and_the_export_use_are_folded_before_they_are_compared():
    refused(risk({"policy_decision": "IGNORED", "prohibited_uses": ["coalition_export"]}), "CAT062_RISK_USE_RESTRICTED")
    refused(risk({"policy_decision": "IGNORED", "prohibited_uses": ["COALITION_EXPORT"]}), "CAT062_RISK_USE_RESTRICTED",
            export_use=" coalition_export ")
    refused(risk({"policy_decision": "IGNORED", "allowed_uses": [" display "]}), "CAT062_RISK_USE_RESTRICTED")
    record, reason = encode(risk({"policy_decision": "IGNORED", "allowed_uses": [" coalition_export "]}))
    assert reason is None and record == MINIMUM_RECORD


def test_the_refusal_order_follows_the_readme():
    refused(make_event(), "CAT062_CONFIG_INVALID", config=dict(CONFIG, simulated=True), export_use="")
    refused(risk({"policy_decision": "REJECTED"}), "CAT062_CONFIG_INVALID", config=dict(CONFIG, sic=300))
    refused(make_event(ts="not a time", track_id="nobody"), "CAT062_TIME_UNPARSEABLE")
    refused(make_event(track_id="nobody", geo={"lat": 99.0, "lon": 0.0, "dimensionality": "2D"}), "CAT062_TRACK_UNMAPPED")
    refused(make_event(geo={"lat": 99.0, "lon": 0.0, "dimensionality": "2D", "alt_m": 1.0}), "CAT062_POSITION_INVALID")
    refused(make_event(geo={"lat": 45.0, "lon": 0.0}, heading_deg=999.0, speed_mps=1.0), "CAT062_ALTITUDE_INVALID")
    refused(make_event(geo={"lat": 45.0, "lon": 0.0, "dimensionality": "2D", "error_ellipse_m": ellipse(-1.0, 1.0, 0.0)},
                       heading_deg=999.0, speed_mps=1.0), "CAT062_VELOCITY_INVALID")


def test_p2_the_most_severe_record_names_the_reason():
    refused(risk({"policy_decision": "WARN_ACCEPT"}, {"policy_decision": "REJECTED"}), "CAT062_RISK_REJECTED")
    refused(risk({"policy_decision": "IGNORED", "prohibited_uses": ["COALITION_EXPORT"]},
                 {"policy_decision": "DEGRADED_ACCEPT"}), "CAT062_RISK_DEGRADED_ACCEPT")
    refused(risk({"policy_decision": "QUARANTINE_ACCEPT"}, {"policy_decision": "LOCAL_HOLD"}),
            "CAT062_RISK_UNKNOWN_DECISION")
    refused(risk({"policy_decision": "REJECTED"}, "a record that is not an object"), "CAT062_RISK_UNREADABLE")


@pytest.mark.parametrize(
    "extensions",
    [{"risk_adjudication": {"policy_decision": "IGNORED"}}, {"risk_adjudication": ["WARN_ACCEPT"]},
     {"risk_adjudication": [{"policy_decision": "IGNORED", "prohibited_uses": {"COALITION_EXPORT": True}}]},
     {"risk_adjudication": [{"policy_decision": "IGNORED", "allowed_uses": ("DISPLAY",)}]},
     ["risk_adjudication"], "risk"],
    ids=["records not a list", "a record not an object", "prohibited uses not a list",
         "allowed uses a tuple", "extensions a list", "extensions a string"],
)
def test_p2_records_the_gate_cannot_read_are_refused(extensions):
    refused(make_event(extensions=extensions), "CAT062_RISK_UNREADABLE")


# --- the README's usage example ---------------------------------------------------------------

def readme_usage_block():
    readme = (Path(cat062.__file__).parent / "README.md").read_text(encoding="utf-8")
    return readme.split("### Usage", 1)[1].split("```python", 1)[1].split("```", 1)[0]


def test_the_readme_usage_example_runs_as_printed():
    block = readme_usage_block()
    assert "allow_degraded_timing" not in block
    printed = []
    namespace = {"event": make_event(track_id="<track_id>"), "print": printed.append}
    exec(compile(block, "README.md, Usage", "exec"), namespace)
    assert printed == [] and namespace["block"] == bytes.fromhex("3E 00 15") + MINIMUM_RECORD
    # Each configuration the example shows passes the startup check and declares the allowance.
    configs = [value for value in namespace.values() if isinstance(value, dict) and "sac" in value]
    assert len(configs) == 2, configs
    for config in configs:
        assert "allow_holdover_or_unsynced" in config and cat062.validate_asterix_config(config) == config
    # The second states LOCKED for a node whose events carry no timing quality.
    record, reason = encode(make_event(timing_quality=DELETE), config=namespace["node_config"])
    assert reason is None and record == MINIMUM_RECORD


# --- R11: no runtime dependency --------------------------------------------------------

def test_r11_the_encoder_imports_the_standard_library_and_its_cot_sibling_only():
    source = Path(cat062.__file__).read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module)
    assert imported <= {"math", "struct", "collections.abc", "adapters.egress.cot.zmeta_to_cot"}, imported
    assert not any(name.split(".")[0] == "asterix" for name in imported)


# --- optional cross-check against libasterix -----------------------------------------------

LIBASTERIX_SCRIPT = r'''
import json, sys
request = json.loads(sys.stdin.read())
sys.path.insert(0, request["site"])
from asterix.base import Bits, RawDatablock
from asterix import generated as g
Cat = g.Cat_062_1_21
Rec = Cat.cv_uap.cv_record

def args(items):
    out = {}
    for name, value in items.items():
        if name == "500":
            out[name] = {k: tuple(v) for k, v in value.items()}
        elif isinstance(value, list):
            out[name] = tuple(value)
        else:
            out[name] = value
    return out

def parse(block_hex):
    blocks = RawDatablock.parse(Bits.from_bytes(bytes.fromhex(block_hex)))
    if isinstance(blocks, ValueError) or len(blocks) != 1:
        return {"error": f"datablock: {blocks!r}"}
    block = blocks[0]
    if block.get_category() != 62:
        return {"error": "category"}
    records = Cat.cv_uap.parse(block.get_raw_records())
    if isinstance(records, ValueError):
        return {"error": f"records: {records}"}
    out = []
    for r in records:
        present = {}
        for name in ("010", "015", "070", "105", "100", "185", "210", "060", "245", "380", "040", "080", "290",
                     "200", "295", "136", "130", "135", "220", "390", "270", "300", "110", "120", "510", "500", "340"):
            item = r.get_item(name)
            if item is not None:
                present[name] = item.unparse().to_bytes().hex()
        out.append({"unparsed": r.unparse().to_bytes().hex(), "items": present})
    return {"records": out}

results = []
for case in request["cases"]:
    theirs = Cat.create([Rec.create(args(case["items"]))]).unparse().to_bytes().hex()
    results.append({"theirs": theirs, "parsed": parse(case["ours"]), "control": parse(case["control"])})
print(json.dumps(results))
'''


def _asterix_site():
    site = os.environ.get("ASTERIX_SITE")
    if not site or not (Path(site) / "asterix" / "generated.py").is_file():
        return None
    return site


def u(value, bits):
    return value & ((1 << bits) - 1)


def cross_check_cases():
    """(event, config, the item values libasterix is given, as integer counts)."""
    p4 = make_event(geo={"lat": 0.0, "lon": 180.0, "dimensionality": "2D"}, heading_deg=180.0, speed_mps=8192.0)
    pole = make_event(geo={"lat": -90.0, "lon": -180.0, "alt_m": -457.2,
                           "error_ellipse_m": ellipse(10.0, 10.0, 0.0)})
    big = make_event(geo={"lat": 45.0, "lon": 10.0, "dimensionality": "2D",
                          "error_ellipse_m": ellipse(1.0e6, 1.0e6, 0.0)}, track_id="track-omega")
    return [
        (make_event(), CONFIG, {"010": [25, 7], "070": 0x587864, "105": [2**23, u(-(2**24), 32)], "040": 1234,
                                "080": [0b0010000]}),
        (full_event(), FULL_CONFIG, {"010": [25, 7], "015": 3, "070": 0xA8BFFF,
                                     "105": [2301401, u(-18411211, 32)], "185": [400, 0], "040": 65535,
                                     "080": [0b1010001], "130": 1000, "500": {"APW": [45, 30]}}),
        (p4, dict(CONFIG, service_id=0, monosensor=True), {"010": [25, 7], "015": 0, "070": 0x587864,
                                                           "105": [0, u(-(2**25), 32)], "185": [0, u(-32768, 16)],
                                                           "040": 1234, "080": [0b1010000]}),
        (pole, dict(CONFIG, tentative=True), {"010": [25, 7], "070": 0x587864,
                                              "105": [u(-(2**24), 32), u(-(2**25), 32)], "040": 1234,
                                              "080": [0b0010001], "130": u(-240, 16)}),
        (big, dict(CONFIG, sac=255, sic=0), {"010": [255, 0], "070": 0x587864, "105": [2**23, 1864135],
                                             "040": 65535, "080": [0b0010000], "500": {"APW": [65535, 65535]}}),
    ]


@pytest.mark.skipif(_asterix_site() is None, reason="ASTERIX_SITE does not name a directory holding libasterix")
def test_bytes_match_libasterix_and_parse_back(tmp_path):
    cases = []
    ours = []
    for event, config, items in cross_check_cases():
        record, reason = encode(event, config=config)
        assert reason is None, reason
        block = cat062.cat062_data_block([record])
        ours.append(block)
        cases.append({"items": items, "ours": block.hex(), "control": block[:-1].hex()})
    request = json.dumps({"site": _asterix_site(), "cases": cases})
    run = subprocess.run(
        [sys.executable, "-I", "-X", f"pycache_prefix={tmp_path}", "-c", LIBASTERIX_SCRIPT],
        input=request, capture_output=True, text=True, timeout=300,
    )
    assert run.returncode == 0, run.stderr
    results = json.loads(run.stdout)
    for block, result in zip(ours, results):
        assert result["theirs"] == block.hex(), (result["theirs"], block.hex())
        parsed = result["parsed"]
        assert "error" not in parsed, parsed
        assert [r["unparsed"] for r in parsed["records"]] == [block[3:].hex()]
        assert {name: bytes.fromhex(value) for name, value in parsed["records"][0]["items"].items()} == items_of(block[3:])
        assert "error" in result["control"], "a block one octet short must fail to parse"
