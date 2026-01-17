from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET


DEFAULT_COT_TYPE = "a-f-G-U-C"


def _parse_utc(ts):
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


def zmeta_to_cot(event):
    """
    Convert a ZMeta STATE_EVENT/Track State into CoT XML.
    Returns a string containing the <event>...</event> XML, or None if not applicable.
    """
    if event.get("event", {}).get("event_type") != "STATE_EVENT":
        return None
    if event.get("event", {}).get("event_subtype") != "TRACK_STATE":
        return None

    payload = event.get("payload", {})
    track_id = payload.get("track_id")
    geo = payload.get("geo", {})
    if not track_id or not geo:
        return None

    ts = event.get("event", {}).get("ts")
    valid_for_ms = payload.get("valid_for_ms")
    if not ts or valid_for_ms is None:
        return None

    time_dt = _parse_utc(ts)
    stale_dt = time_dt + timedelta(milliseconds=int(valid_for_ms))
    time_str = time_dt.isoformat().replace("+00:00", "Z")
    stale_str = stale_dt.isoformat().replace("+00:00", "Z")

    cot_type = payload.get("class") or DEFAULT_COT_TYPE

    root = ET.Element(
        "event",
        attrib={
            "version": "2.0",
            "uid": str(track_id),
            "type": str(cot_type),
            "time": time_str,
            "start": time_str,
            "stale": stale_str,
            "how": "m-g",
        },
    )

    ET.SubElement(
        root,
        "point",
        attrib={
            "lat": str(geo.get("lat")),
            "lon": str(geo.get("lon")),
            "hae": str(geo.get("alt_m")),
            "ce": "9999999",
            "le": "9999999",
        },
    )

    detail = ET.SubElement(root, "detail")
    confidence = event.get("confidence")
    source_summary = payload.get("source_summary")
    remarks_parts = []
    if confidence is not None:
        remarks_parts.append(f"confidence={confidence}")
    if source_summary:
        if isinstance(source_summary, list):
            remarks_parts.append(f"source_summary={','.join(str(x) for x in source_summary)}")
        else:
            remarks_parts.append(f"source_summary={source_summary}")
    if remarks_parts:
        remarks = ET.SubElement(detail, "remarks")
        remarks.text = "; ".join(remarks_parts)

    return ET.tostring(root, encoding="unicode")


def zmeta_to_cot_uncertainty_circle(zmeta_state_event, radius_m):
    """
    Convert a ZMeta STATE_EVENT/TRACK_STATE into CoT with an uncertainty ring.
    Returns a string containing the <event>...</event> XML, or None if not applicable.
    """
    cot_xml = zmeta_to_cot(zmeta_state_event)
    if not cot_xml:
        return None

    try:
        radius = float(radius_m)
    except (TypeError, ValueError):
        return None

    if radius <= 0:
        return None

    root = ET.fromstring(cot_xml)
    detail = root.find("detail")
    if detail is None:
        detail = ET.SubElement(root, "detail")

    ET.SubElement(detail, "circle", attrib={"radius": str(radius)})
    return ET.tostring(root, encoding="unicode")
