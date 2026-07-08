from adapters.ingress.time_utils import coerce_timing_quality, normalize_utc_z, utc_now_z
from zmeta_uuid import uuid7


ADAPTER_VERSION = "0.2.0"
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

    ``based_on`` may carry real parent ZMeta event ids (UUIDv7 strings); when
    None (default), lineage is omitted because the decoded KLV packet is an
    original observation with no ZMeta parent. Parent ids are never
    fabricated.
    """
    lat = decoded_klv.get("lat")
    lon = decoded_klv.get("lon")
    alt_m = decoded_klv.get("alt_m")

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
    if lat is not None and lon is not None and alt_m is not None:
        event["payload"]["geo"] = {"lat": lat, "lon": lon, "alt_m": alt_m}

    return event
