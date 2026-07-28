"""dump1090 / readsb ``aircraft.json`` -> ZMeta OBSERVATION_EVENT.

ADS-B is a **cooperative broadcast**: the aircraft transmits its own position,
identity and velocity, and a receiver decodes it. That shapes every honesty
decision in this file, because almost nothing here is our measurement.

WHY MODALITY IS ``NETWORK`` AND NOT ``RF``
------------------------------------------
The obvious reading is "we received a 1090 MHz signal, so it is RF". But
semantics-contract 7.4 gives RF a normative minimum feature set --
``center_freq_hz``, ``bandwidth_hz``, ``power_dbm`` -- and **dump1090 reports
``rssi`` in dBFS, not dBm**. dBFS is relative to the receiver's full scale and
depends on the antenna, LNA and gain chain; converting it to absolute dBm
requires a calibration this adapter does not have and must not invent. Emitting
an uncalibrated dBFS number in a field named ``power_dbm`` is precisely the
laundering the contract forbids.

What we can state honestly without calibration is the *decoded message*, so the
observation is modelled as ``NETWORK`` modality and ``rssi`` is carried as an
explicitly named native feature, ``rssi_dbfs``, never as ``power_dbm``.

**This is a modelling judgement, not a settled rule** -- see the adapter README.
A deployment with a calibrated receiver could honestly emit RF; that is a later
refinement, not something to fake here.

WHY ``OBSERVATION_EVENT`` AND NOT ``STATE_EVENT``
-------------------------------------------------
The MAVLink adapter maps a platform's self-reported position to
``STATE_EVENT``/``TRACK_STATE``, and ADS-B looks structurally identical. But
STATE_EVENT lineage is mandatory (contract 4.8) and must reference real parent
events; an ADS-B receiver has no ZMeta parent -- it is an original observation
of a broadcast. Original observations omit lineage. So this is an
OBSERVATION_EVENT, and a downstream fusion or state-projection stage is what
turns a stream of these into tracks.

HONESTY RULES ENFORCED HERE
---------------------------
* **No position is invented.** An aircraft entry with no ``lat``/``lon`` -- a
  Mode S-only target, or ADS-B before position lock -- is still a real
  detection of a real emitter. ``payload.geo`` is omitted entirely rather than
  filled with a default or a null island.
* **Pressure altitude is not geometric altitude.** ``alt_geom`` is WGS84 and may
  become ``geo.alt_m``. ``alt_baro`` is a pressure altitude referenced to
  1013.25 hPa and is NOT a height above the ellipsoid; it is carried only as a
  named native feature. This is the altitude-datum defect the July audit found
  in a fielded stack, refused here at the source.
* **Declared accuracy travels, absence does not become precision.** ``nac_p``
  maps to a declared horizontal bound; when it is absent no bound is invented.
* **Non-finite is not a value.** NaN/inf in any numeric refuses that field, and
  refuses the whole event where the field is required.
* **The emitter identity is required.** Without ``hex`` there is no subject for
  the observation, so the entry is refused rather than emitted anonymous.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from adapters.ingress.time_utils import coerce_timing_quality

try:  # pragma: no cover - import shape differs in-repo vs copied out
    from zmeta_uuid import uuid7
except ImportError:  # pragma: no cover
    from uuid import uuid4 as uuid7

ADAPTER_VERSION = "1.0.0"

# ADS-B 1090ES extended squitter. A constant of the datalink, not a guess about
# any particular receiver, so it is honest to state -- but it lives in native
# features, not in RF minimum features, for the dBFS reason above.
ADSB_DOWNLINK_HZ = 1090_000_000

# NACp -> 95% horizontal containment radius in metres (DO-260B table). Only the
# categories with a bounded radius are usable; 0 and 1 mean "unknown" or ">10 NM"
# and are deliberately absent so they map to no claim at all.
_NACP_HORIZONTAL_M = {
    2: 18520.0,   # < 10 NM
    3: 7408.0,    # < 4 NM
    4: 3704.0,    # < 2 NM
    5: 1852.0,    # < 1 NM
    6: 926.0,     # < 0.5 NM
    7: 370.4,     # < 0.2 NM
    8: 185.2,     # < 0.1 NM
    9: 30.0,      # < 30 m
    10: 10.0,     # < 10 m
    11: 3.0,      # < 3 m
}


def _finite(value):
    """The value when it is a real finite number, else None.

    A NaN coordinate is not a position and a NaN altitude is not a height, so
    non-finite input never reaches the canonical fields.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) else None


def _utc_z(epoch_seconds):
    """Epoch seconds -> UTC-Z timestamp, or None when unusable."""
    seconds = _finite(epoch_seconds)
    if seconds is None:
        return None
    try:
        moment = datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


def _geo(entry):
    """Canonical geo, or None to omit it entirely.

    All-or-nothing per contract 6.8: a position with one component missing is
    not a position. Altitude is included ONLY from ``alt_geom`` (WGS84);
    ``alt_baro`` is a pressure altitude and never becomes ``alt_m``.
    """
    lat = _finite(entry.get("lat"))
    lon = _finite(entry.get("lon"))
    if lat is None or lon is None:
        return None
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        return None
    alt_geom = _finite(entry.get("alt_geom"))
    if alt_geom is None:
        # Canonical geo requires alt_m (contract 6.8, all-or-nothing), and the
        # only altitude many ADS-B targets report is `alt_baro` -- a PRESSURE
        # altitude referenced to 1013.25 hPa. Converting it to a geometric
        # height needs local QNH, which the message does not carry. So there is
        # no honest canonical geo here.
        #
        # The horizontal position is real, though, and discarding it would be
        # its own dishonesty. It is demoted to explicitly named native features
        # by the caller -- the same convert-or-demote rule the bladeRF adapter
        # applies to a frame-unlabelled bearing.
        return None
    return {"lat": lat, "lon": lon, "alt_m": alt_geom * 0.3048}  # feet -> metres


def _quality(entry, has_geo):
    """Declared quality, carrying only what the message actually asserts."""
    quality = {}
    nac_p = entry.get("nac_p")
    if has_geo and isinstance(nac_p, int) and not isinstance(nac_p, bool):
        radius = _NACP_HORIZONTAL_M.get(nac_p)
        if radius is not None:
            # A declared containment radius, expressed as a circular bound.
            quality["error_ellipse_m"] = {
                "semi_major_m": radius,
                "semi_minor_m": radius,
                "orientation_deg": 0.0,
            }
    if not has_geo:
        # A real detection with no position. Say so rather than stay silent.
        quality["geo_status"] = "UNAVAILABLE"
    return quality or None


def _native_features(entry, receiver_id):
    """Everything ADS-B asserts, under explicitly named native keys.

    Native rather than canonical because these are the emitter's claims and the
    receiver's raw indications, not normalized ZMeta semantics. Naming them
    explicitly is what keeps them out of fields that would imply more than the
    data supports (contract 6.4).
    """
    features = {
        "adsb_icao24": str(entry["hex"]).strip().lower(),
        "adsb_downlink_hz": ADSB_DOWNLINK_HZ,
    }
    if receiver_id is not None:
        features["adsb_receiver_id"] = str(receiver_id)

    flight = entry.get("flight")
    if isinstance(flight, str) and flight.strip():
        features["adsb_callsign"] = flight.strip()

    squawk = entry.get("squawk")
    if isinstance(squawk, str) and squawk.strip():
        features["adsb_squawk"] = squawk.strip()

    # rssi is dBFS. The key says so; it never becomes power_dbm.
    rssi = _finite(entry.get("rssi"))
    if rssi is not None:
        features["rssi_dbfs"] = rssi

    # A horizontal position that could not become canonical geo -- because the
    # target reported no geometric altitude and canonical geo is all-or-nothing
    # -- is preserved here under explicitly native keys. It makes no canonical
    # claim, and `quality.geo_status` says the canonical position is
    # unavailable, so nothing downstream can mistake this for a ZMeta position.
    lat = _finite(entry.get("lat"))
    lon = _finite(entry.get("lon"))
    if lat is not None and lon is not None and _finite(entry.get("alt_geom")) is None:
        features["adsb_lat_deg"] = lat
        features["adsb_lon_deg"] = lon

    # Pressure altitude, explicitly named as such so nothing mistakes it for a
    # geometric height.
    alt_baro = _finite(entry.get("alt_baro"))
    if alt_baro is not None:
        features["adsb_alt_baro_ft"] = alt_baro

    for native_key, feature_key in (
        ("gs", "adsb_ground_speed_kt"),
        ("track", "adsb_track_deg_true"),
        ("baro_rate", "adsb_baro_rate_fpm"),
        ("messages", "adsb_message_count"),
        ("seen", "adsb_seen_s"),
        ("seen_pos", "adsb_seen_pos_s"),
        ("nac_p", "adsb_nac_p"),
        ("nac_v", "adsb_nac_v"),
        ("sil", "adsb_sil"),
        ("nic", "adsb_nic"),
    ):
        value = _finite(entry.get(native_key))
        if value is not None:
            features[feature_key] = value
    return features


def translate_aircraft(
    entry,
    *,
    now_epoch_s,
    platform_id,
    producer="rf-sensor-adsb-01",
    receiver_id=None,
    sensor_id=None,
    timing_quality=None,
):
    """Translate one ``aircraft.json`` entry into a ZMeta OBSERVATION_EVENT.

    Args:
        entry: one element of the ``aircraft`` array.
        now_epoch_s: the file-level ``now`` value, in epoch seconds.
        platform_id: the deployment's platform identifier.
        producer: must satisfy producer-authority policy; the reference
            wildcards include ``rf-sensor-*`` (see adapters/AUTHORING.md 7).
        receiver_id: optional receiver identifier, recorded natively.
        sensor_id: optional ZMeta ``source.sensor_id``; omitted when absent
            rather than invented.
        timing_quality: real clock metadata when the deployment has it. Absent,
            the governed degraded fallback is used -- never a synchronization
            claim nobody made.

    Returns:
        The event dict, or ``None`` when the entry cannot honestly become one:
        no ``hex`` (no subject), or no usable timestamp.
    """
    if not isinstance(entry, dict):
        return None
    hex_id = entry.get("hex")
    if not isinstance(hex_id, str) or not hex_id.strip():
        return None

    # The position was observed `seen_pos` seconds ago; a positionless entry is
    # timestamped by `seen`. Both are relative to the file's `now`.
    now_s = _finite(now_epoch_s)
    if now_s is None:
        return None
    age = _finite(entry.get("seen_pos"))
    if age is None:
        age = _finite(entry.get("seen")) or 0.0
    ts = _utc_z(now_s - age)
    if ts is None:
        return None

    geo = _geo(entry)
    quality = _quality(entry, geo is not None)

    payload = {
        "modality": "NETWORK",
        "features": _native_features(entry, receiver_id),
        # An RTL-SDR ADS-B receiver has no disciplined clock: dump1090 stamps on
        # receipt from the host system clock, and ADS-B messages carry no
        # transmission time. So the honest default is the governed degraded
        # fallback (UNKNOWN / UNSYNCED) rather than a claim of synchronization
        # nobody made. A deployment that HAS real GPS/NTP/PTP metadata passes it
        # in `timing_quality` and it is preserved as supplied.
        "timing_quality": coerce_timing_quality(timing_quality, event_ts=ts),
    }
    if geo is not None:
        payload["geo"] = geo
    if quality is not None:
        payload["quality"] = quality

    source = {
        "platform_id": platform_id,
        # An ADS-B receiver sits at the edge of the network. `node_role` is a
        # topology position, not a device kind -- the enum is
        # EDGE/GATEWAY/APEX/DMZ/CLOUD and there is no "SENSOR".
        "node_role": "EDGE",
        "producer": producer,
    }
    if sensor_id is not None:
        source["sensor_id"] = str(sensor_id)

    return {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "NETWORK",
            "ts": ts,
        },
        "source": source,
        "payload": payload,
    }


def translate_snapshot(snapshot, *, platform_id, **kwargs):
    """Translate a whole ``aircraft.json`` document.

    Entries that cannot honestly become events are dropped, not patched. The
    count of refusals is the caller's to observe -- an adapter that silently
    invents a position to keep its yield up is the failure mode this whole
    file exists to avoid.
    """
    if not isinstance(snapshot, dict):
        return []
    now_epoch_s = snapshot.get("now")
    aircraft = snapshot.get("aircraft")
    if not isinstance(aircraft, list):
        return []
    events = []
    for entry in aircraft:
        event = translate_aircraft(
            entry, now_epoch_s=now_epoch_s, platform_id=platform_id, **kwargs
        )
        if event is not None:
            events.append(event)
    return events
