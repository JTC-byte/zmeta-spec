"""ZMeta STATE_EVENT to Cursor-on-Target (CoT) XML egress adapter.

Converts ZMeta STATE_EVENT track states into CoT v2.0 XML for TAK
(ATAK, WinTAK, TAK Server) interoperability.

Supports:
  - Configurable CE/LE from error_ellipse_m or defaults
  - Fusion-engine ce_display_m for probability-scaled uncertainty
  - Heading/speed track element (directional arrows on TAK map)
  - PrecisionLocation for MIL-STD-2525 elliptical uncertainty
  - ATAK team coloring (__group element) for friendly platforms
  - Hostile emitter callsign fallback logic
  - Persistent labels for hostile tracks
  - Source summary and error ellipse details in remarks
  - Custom icon support for drone platforms
  - Wall-clock timestamps so TAK shows fresh markers during replay

Source: Z-ISR zisr/transport/publisher.py (_builtin_zmeta_to_cot)
"""

from datetime import datetime, timedelta, timezone


DEFAULT_COT_TYPE = "a-u-G"
STATE_PROHIBITED_PAYLOAD_FIELDS = {
    "features",
    "raw_features",
    "modality",
    "measurement",
    "measurements",
    "t_start",
    "t_end",
    "data_ref",
    "data_refs",
}


def _parse_utc(ts):
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


def _esc(text):
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _has_state_prohibited_payload_fields(payload):
    if not isinstance(payload, dict):
        return True
    return any(field in payload for field in STATE_PROHIBITED_PAYLOAD_FIELDS)


def zmeta_to_cot(event, cot_config=None):
    """Convert a ZMeta STATE_EVENT into CoT XML.

    Args:
        event: ZMeta event dict. Must have event_type=STATE_EVENT.
        cot_config: Optional dict with configuration overrides:
            - default_type (str): Default CoT type (default "a-u-G")
            - default_valid_for_ms (int): Stale interval (default 300000)
            - default_ce (float): Default circular error metres (default 15.0)
            - default_le (float): Default linear error metres (default 10.0)
            - friendly_team_name (str): ATAK team name (default "Cyan")
            - friendly_team_role (str): ATAK team role (default "Team Member")
            - use_wall_clock (bool): Use current time for CoT timestamps
                so TAK always shows fresh markers, even during replay
                of historical data (default True)

    Returns:
        CoT XML string, or None if the event cannot be converted.
    """
    if event.get("event", {}).get("event_type") != "STATE_EVENT":
        return None

    cot_config = cot_config or {}
    payload = event.get("payload", {})
    if _has_state_prohibited_payload_fields(payload):
        return None

    geo = payload.get("geo")
    if not geo or geo.get("lat") is None or geo.get("lon") is None:
        return None

    track_id = payload.get("track_id")
    if not track_id:
        return None

    # Timestamps: wall-clock mode (default) keeps TAK markers fresh during
    # replay; event-time mode uses the original event timestamp.
    use_wall_clock = cot_config.get("use_wall_clock", True)
    if use_wall_clock:
        time_obj = datetime.now(timezone.utc)
    else:
        ts = event.get("event", {}).get("ts")
        if not ts:
            time_obj = datetime.now(timezone.utc)
        else:
            time_obj = _parse_utc(ts)

    default_valid_for_ms = cot_config.get("default_valid_for_ms", 300000)
    valid_for_ms = payload.get("valid_for_ms", default_valid_for_ms)
    stale_obj = time_obj + timedelta(milliseconds=valid_for_ms)

    time_str = time_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    stale_str = stale_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    default_type = cot_config.get("default_type", DEFAULT_COT_TYPE)
    cot_type = payload.get("class", default_type)
    lat = geo["lat"]
    lon = geo["lon"]
    hae = geo.get("alt_m", 0)

    # Circular error / linear error resolution:
    # 1. ce_display_m from fusion engine (probability-scaled + smoothed)
    # 2. error_ellipse_m semi_major/semi_minor
    # 3. Legacy ce/le fields on geo
    # 4. Config defaults
    default_ce = cot_config.get("default_ce", 15.0)
    default_le = cot_config.get("default_le", 10.0)
    ce_display = geo.get("ce_display_m")
    error_ellipse = geo.get("error_ellipse_m")

    if ce_display:
        ce = float(ce_display)
        le = error_ellipse.get("semi_minor", default_le) if error_ellipse else default_le
    elif error_ellipse and isinstance(error_ellipse, dict):
        ce = error_ellipse.get("semi_major", default_ce)
        le = error_ellipse.get("semi_minor", default_le)
    else:
        ce = geo.get("ce", default_ce)
        le = geo.get("le", default_le)

    # Callsign with hostile emitter fallback: never show raw track IDs
    # on TAK for hostile markers. Use "RF Emitter" or "Detection" instead.
    callsign = payload.get("callsign", f"Track {track_id}")
    if cot_type.startswith("a-h-"):
        if (
            not callsign
            or callsign == track_id
            or callsign.startswith("Track ")
            or callsign.startswith("torchai-track-")
        ):
            callsign = "RF Emitter"

    # Remarks from source_summary + error ellipse details
    source_summary = payload.get("source_summary", [])
    if isinstance(source_summary, list):
        remarks_text = "; ".join(str(s) for s in source_summary)
    else:
        remarks_text = str(source_summary) if source_summary else ""

    confidence = event.get("confidence")
    if confidence is not None and not remarks_text:
        remarks_text = f"confidence={confidence}"

    if error_ellipse and isinstance(error_ellipse, dict):
        semi_maj = error_ellipse.get("semi_major", 0)
        semi_min = error_ellipse.get("semi_minor", 0)
        orient = error_ellipse.get("orientation_deg", 0)
        parts = []
        if ce_display:
            parts.append(f"CE90: <{int(ce_display)}m")
        parts.append(f"Error ellipse: {semi_maj:.0f}m x {semi_min:.0f}m @ {orient:.0f}deg")
        ellipse_str = "; ".join(parts)
        if remarks_text:
            remarks_text += f"; {ellipse_str}"
        else:
            remarks_text = ellipse_str

    remarks_xml = ""
    if remarks_text:
        remarks_xml = f"\n    <remarks>{_esc(remarks_text)}</remarks>"

    # <track> element for heading/speed (TAK renders directional arrows)
    track_xml = ""
    heading = payload.get("heading_deg")
    speed = payload.get("speed_mps")
    if heading is not None or speed is not None:
        course = f"{heading:.1f}" if heading is not None else "0.0"
        spd = f"{speed:.1f}" if speed is not None else "0.0"
        track_xml = f'\n    <track course="{course}" speed="{spd}" />'

    # <precisionlocation> for MIL-STD-2525 elliptical uncertainty
    precision_xml = ""
    if error_ellipse and isinstance(error_ellipse, dict):
        precision_xml = (
            f'\n    <precisionlocation geopointsrc="GPS" altsrc="GPS"'
            f' ellipse_major="{error_ellipse.get("semi_major", 0):.1f}"'
            f' ellipse_minor="{error_ellipse.get("semi_minor", 0):.1f}"'
            f' ellipse_angle="{error_ellipse.get("orientation_deg", 0):.1f}" />'
        )

    # <__group> for ATAK team coloring on friendly platforms
    group_xml = ""
    if cot_type.startswith("a-f-"):
        group_name = cot_config.get("friendly_team_name", "Cyan")
        group_role = cot_config.get("friendly_team_role", "Team Member")
        group_xml = f'\n    <__group name="{_esc(group_name)}" role="{_esc(group_role)}" />'

    # Persistent labels for hostile tracks (CE readout always visible)
    labels_xml = ""
    if cot_type.startswith("a-h-"):
        labels_xml = '\n    <labels_on value="true" />'

    # Custom icon for drone/sensor platforms
    usericon_xml = ""
    if cot_type == "a-f-A-M-F-Q":
        usericon_xml = (
            '\n    <usericon iconsetpath='
            '"a1b2c3d4-e5f6-7890-abcd-ef1234567890'
            '/Torch Drones/quadcopter.png" />'
        )

    cot_xml = (
        f'<event version="2.0" type="{_esc(cot_type)}" uid="{_esc(track_id)}"'
        f' time="{time_str}" start="{time_str}" stale="{stale_str}" how="m-g">\n'
        f'  <point lat="{lat}" lon="{lon}" hae="{hae}" le="{le}" ce="{ce}" />\n'
        f"  <detail>\n"
        f'    <contact callsign="{_esc(callsign)}" />'
        f"{labels_xml}{remarks_xml}{track_xml}{precision_xml}{group_xml}{usericon_xml}\n"
        f"  </detail>\n"
        f"</event>"
    )
    return cot_xml


def zmeta_to_cot_uncertainty_circle(zmeta_state_event, radius_m, cot_config=None):
    """Convert a ZMeta STATE_EVENT into CoT with an explicit uncertainty ring.

    Args:
        zmeta_state_event: ZMeta STATE_EVENT dict.
        radius_m: Uncertainty radius in metres.
        cot_config: Optional config dict (see zmeta_to_cot).

    Returns:
        CoT XML string with <circle> element, or None.
    """
    import xml.etree.ElementTree as ET

    cot_xml = zmeta_to_cot(zmeta_state_event, cot_config=cot_config)
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
