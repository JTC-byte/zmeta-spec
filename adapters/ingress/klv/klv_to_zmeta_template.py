from adapters.ingress.time_utils import coerce_timing_quality, normalize_utc_z, utc_now_z
from zmeta_uuid import uuid7


ADAPTER_VERSION = "0.3.0"
SCHEMA_ID = "klv"


def klv_decoded_to_zmeta_observation(
    decoded_klv: dict,
    *,
    platform_id: str,
    sensor_id: str | None,
    producer: str,
    ts: str,
    based_on: list[str] | None = None,
) -> dict:
    """
    Template: Convert decoded KLV tags into a single OBSERVATION_EVENT.

    Altitude datum (contract 6.2, doctrine C1-01): MISB ST 0601 defines its
    dominant altitude tags as MSL (Tag 15 Sensor True Altitude, Tag 25 Frame
    Center Elevation, Tag 42 Target Location Elevation); only Tag 75 (Sensor
    Ellipsoid Height) and Tag 78 (Frame Center Height Above Ellipsoid) are
    HAE. The decode boundary therefore names the datum: the decoder feeding
    this template maps HAE tags to ``alt_hae_m`` and MSL tags to
    ``alt_msl_m``, and only ``alt_hae_m`` may occupy canonical
    payload.geo.alt_m. An MSL-only position degrades to the declared 2-D geo
    form (doctrine A1-02, forced 1.1.0 stamp) with the reported value
    preserved as non-canonical quality.klv_alt_msl_m. The legacy generic
    ``alt_m`` key asserts no datum at all and gets the same 2-D degrade with
    the value preserved as quality.klv_alt_unspecified_datum_m. No altitude
    of any kind omits geo entirely (all-or-nothing, contract 6.8). This
    template's geo asserts the sensor position (Tags 13/14 + 75); frame
    center and target location are different world points and do not belong
    in it.

    ``based_on`` may carry real parent ZMeta event ids (UUIDv7 strings); when
    None (default), lineage is omitted because the decoded KLV packet is an
    original observation with no ZMeta parent. Parent ids are never
    fabricated.
    """
    lat = decoded_klv.get("lat")
    lon = decoded_klv.get("lon")
    # The two datums are read into separate names and only one of them can
    # reach canonical geo, mirroring the MAVLink reference implementation
    # (adapters/ingress/mavlink/mavlink_to_zmeta_template.py). A value under
    # the legacy generic key is unspecified-datum: worse than MSL, because
    # nothing at all is known about it.
    alt_hae_m = decoded_klv.get("alt_hae_m")
    alt_msl_m = decoded_klv.get("alt_msl_m")
    alt_unspecified_m = decoded_klv.get("alt_m")

    event_ts = normalize_utc_z(ts) or utc_now_z()
    event = {
        "zmeta_version": "1.0",
        "event": {
            "event_id": str(uuid7()),
            "event_type": "OBSERVATION_EVENT",
            "event_subtype": "EO",
            "ts": event_ts,
        },
        "source": {
            "platform_id": platform_id,
            "node_role": "EDGE",
            "producer": producer,
        },
        "payload": {
            "modality": "EO",
            "features": {
                "klv": decoded_klv
            },
            "timing_quality": coerce_timing_quality(
                decoded_klv.get("timing_quality"),
                event_ts=event_ts,
            ),
        },
    }
    if based_on:
        event["lineage"] = {
            "based_on": [str(item) for item in based_on],
            "transform": f"translate:{SCHEMA_ID}@{ADAPTER_VERSION}",
        }

    if sensor_id is not None:
        event["source"]["sensor_id"] = sensor_id
    if lat is not None and lon is not None:
        if alt_hae_m is not None:
            # Only an ellipsoidal altitude may occupy canonical geo.alt_m;
            # when both datums arrive, HAE wins and the event keeps the 1.0
            # stamp unchanged.
            event["payload"]["geo"] = {"lat": lat, "lon": lon, "alt_m": alt_hae_m}
        elif alt_msl_m is not None or alt_unspecified_m is not None:
            # A reported vertical in a datum this template cannot state
            # canonically: the horizontal fix is still real and is published
            # as the declared 2-D form rather than withheld or laundered.
            # dimensionality is v1.1.0 vocabulary, so this branch must stamp
            # 1.1.0 (the locked v1.0 geo def is additionalProperties:false
            # over lat/lon/alt_m). The reported values are preserved under
            # datum-named non-canonical keys; a consumer with its own geoid
            # model can still use them, and nothing downstream can mistake
            # them for canonical HAE.
            event["payload"]["geo"] = {"lat": lat, "lon": lon, "dimensionality": "2D"}
            event["zmeta_version"] = "1.1.0"
            quality = event["payload"].setdefault("quality", {})
            quality["geo_status"] = "VERTICAL_UNAVAILABLE"
            if alt_msl_m is not None:
                quality["klv_alt_msl_m"] = alt_msl_m
            if alt_unspecified_m is not None:
                quality["klv_alt_unspecified_datum_m"] = alt_unspecified_m
        # No altitude of any kind: geo stays omitted entirely (all-or-nothing,
        # contract 6.8), never zero-filled.

    return event
