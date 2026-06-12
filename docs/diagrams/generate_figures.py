"""Generate the data-driven SVG figures used by docs/zmeta_professional_overview.md.

These figures are vendor-neutral and reproducible. They are built only from the
ZMeta spec repo's own example events (examples/*.jsonl), the policy pack
(policy/profiles.yaml), and the repo encoding modules (zmeta_cbor, zmeta_compact,
zmeta_proto). No third-party dependencies are required; output is plain SVG so it
renders inline on GitHub and scales cleanly.

Usage:
    python docs/diagrams/generate_figures.py

Outputs (written to docs/img/):
    b1-event-anatomy.svg        Annotated anatomy of a ZMeta event envelope
    b2-lineage-chain.svg        based_on lineage: observation -> inference -> fusion -> state
    b3-encoding-sizes.svg       Wire-size comparison: JSON / CBOR / compact CBOR / protobuf
    b4-profile-matrix.svg       Export profiles (H/M/L) vs allowed event families
    b5-triangulation.svg        Multi-LOB triangulation and error-ellipse reduction
"""

from __future__ import annotations

import json
import math
import re
import sys
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXAMPLES = ROOT / "examples"
IMG_DIR = ROOT / "docs" / "img"

# Palette (dark ink on a white card so figures stay legible in light or dark themes).
BG = "#ffffff"
INK = "#1b2330"
MUTED = "#5b6b7b"
PANEL = "#f3f6fa"
PANEL_STROKE = "#cdd8e3"
GRID = "#e4ebf2"
FAMILY = {
    "OBSERVATION_EVENT": "#2f6f9f",
    "INFERENCE_EVENT": "#7a5ea8",
    "FUSION_EVENT": "#2e8b6f",
    "STATE_EVENT": "#c47f2a",
    "COMMAND_EVENT": "#b5483d",
    "SYSTEM_EVENT": "#6b7785",
}
MONO = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


# --------------------------------------------------------------------------- #
# Minimal SVG builder
# --------------------------------------------------------------------------- #
class Svg:
    def __init__(self, width: int, height: int, title: str = "") -> None:
        self.w = width
        self.h = height
        self.parts: List[str] = []
        self.parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" font-family="{SANS}" role="img" '
            f'aria-label="{escape(title)}">'
        )
        self.rect(0, 0, width, height, fill=BG, rx=0)

    def rect(self, x, y, w, h, fill="none", stroke="none", sw=1.0, rx=0, dash=None, opacity=1.0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity != 1.0 else ""
        self.parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{o}/>'
        )

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>'
        )

    def text(self, x, y, s, size=14, fill=INK, anchor="start", weight="normal", family=SANS):
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" font-family="{family}">{escape(str(s))}</text>'
        )

    def ellipse(self, cx, cy, rx, ry, angle=0.0, fill="none", stroke=INK, sw=1.5, opacity=1.0):
        t = f' transform="rotate({angle:.2f} {cx:.1f} {cy:.1f})"' if angle else ""
        self.parts.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"{t}/>'
        )

    def circle(self, cx, cy, r, fill=INK, stroke="none", sw=1.0):
        self.parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def poly(self, pts: List[Tuple[float, float]], fill=INK, stroke="none", sw=1.0):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.parts.append(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def arrow(self, x1, y1, x2, y2, color=INK, sw=2.0, head=8.0, dash=None):
        ang = math.atan2(y2 - y1, x2 - x1)
        bx = x2 - head * math.cos(ang)
        by = y2 - head * math.sin(ang)
        self.line(x1, y1, bx, by, stroke=color, sw=sw, dash=dash)
        left = (x2 - head * math.cos(ang - 0.45), y2 - head * math.sin(ang - 0.45))
        right = (x2 - head * math.cos(ang + 0.45), y2 - head * math.sin(ang + 0.45))
        self.poly([(x2, y2), left, right], fill=color)

    def save(self, path: Path) -> None:
        self.parts.append("</svg>")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self.parts) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Data helpers
# --------------------------------------------------------------------------- #
def load_jsonl(name: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for line in (EXAMPLES / name).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            events.append(json.loads(line))
    return events


def short_id(event_id: str) -> str:
    return event_id[-8:] if event_id else "?"


def event_type(ev: Dict[str, Any]) -> str:
    return ev.get("event", {}).get("event_type", "UNKNOWN")


def parse_profiles() -> Dict[str, List[str]]:
    """Parse policy/profiles.yaml without a YAML dependency."""
    text = (ROOT / "policy" / "profiles.yaml").read_text(encoding="utf-8")
    profiles: Dict[str, List[str]] = {}
    current: Optional[str] = None
    for line in text.splitlines():
        m = re.match(r"^  ([A-Z]):\s*$", line)
        if m:
            current = m.group(1)
            profiles[current] = []
            continue
        m = re.match(r"^\s*-\s*([A-Z_]+)\s*$", line)
        if m and current:
            profiles[current].append(m.group(1))
    return profiles


def encoding_sizes(event: Dict[str, Any]) -> Dict[str, Optional[int]]:
    import zmeta_cbor
    import zmeta_compact
    import zmeta_proto

    sizes: Dict[str, Optional[int]] = {}
    sizes["JSON"] = len(json.dumps(event, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    for name, fn in (("CBOR", zmeta_cbor.dumps), ("Compact", zmeta_compact.dumps), ("Protobuf", zmeta_proto.dumps)):
        try:
            sizes[name] = len(fn(event))
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"  note: {name} encoding skipped ({exc})")
            sizes[name] = None
    return sizes


# --------------------------------------------------------------------------- #
# B1 - Anatomy of a ZMeta event
# --------------------------------------------------------------------------- #
def figure_event_anatomy() -> None:
    events = load_jsonl("zmeta-profile-H-examples.jsonl")
    inf = next(e for e in events if event_type(e) == "INFERENCE_EVENT")
    pretty = json.dumps(inf, indent=2, ensure_ascii=False).splitlines()

    line_h = 17
    pad = 22
    panel_x, panel_y = 26, 70
    panel_w = 470
    panel_h = pad * 2 + line_h * len(pretty)
    height = max(panel_y + panel_h + 30, 600)
    s = Svg(940, height, "Anatomy of a ZMeta event")

    s.text(26, 34, "Anatomy of a ZMeta event", size=21, weight="700")
    s.text(26, 56, "Every event is self-describing: identity, origin, meaning, trust, and lineage travel together.",
           size=13, fill=MUTED)

    s.rect(panel_x, panel_y, panel_w, panel_h, fill=PANEL, stroke=PANEL_STROKE, sw=1.2, rx=10)
    # Map JSON top-level keys to a callout color.
    key_color = {
        '"zmeta_version"': "#3a7ca5",
        '"event"': FAMILY["INFERENCE_EVENT"],
        '"source"': "#2e8b6f",
        '"payload"': "#c47f2a",
        '"confidence"': "#b5483d",
        '"lineage"': "#7a5ea8",
        '"profile"': "#6b7785",
    }
    y = panel_y + pad + 4
    for raw in pretty:
        color = INK
        for key, col in key_color.items():
            if raw.lstrip().startswith(key):
                color = col
                break
        s.text(panel_x + 14, y, raw, size=12.5, family=MONO, fill=color)
        y += line_h

    # Callouts on the right.
    cx = panel_x + panel_w + 40
    callouts = [
        ("#3a7ca5", "zmeta_version", "Exact version dispatch - the schema validates strictly by this."),
        (FAMILY["INFERENCE_EVENT"], "event", "Identity + family: UUIDv7 event_id, event_type/subtype, UTC ts."),
        ("#2e8b6f", "source", "Who produced it: platform, node role, producer - basis for authority."),
        ("#c47f2a", "payload", "Family-specific body. Here: an AI claim with model + version."),
        ("#b5483d", "confidence", "Calibrated trust - present or prohibited per event family."),
        ("#7a5ea8", "lineage", "based_on links back to source observations; transform records the adapter."),
        ("#6b7785", "profile", "Export tier (H/M/L) governing what may be thinned for the wire."),
    ]
    cy = panel_y + 6
    for color, key, desc in callouts:
        s.rect(cx, cy, 12, 12, fill=color, rx=3)
        s.text(cx + 22, cy + 11, key, size=13.5, weight="700", fill=color)
        # wrap description to ~46 chars
        words = desc.split()
        lines: List[str] = []
        cur = ""
        for w in words:
            if len(cur) + len(w) + 1 > 50:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            lines.append(cur)
        ty = cy + 29
        for ln in lines:
            s.text(cx + 22, ty, ln, size=12, fill=INK)
            ty += 15
        cy = ty + 10

    s.save(IMG_DIR / "b1-event-anatomy.svg")
    print("  wrote b1-event-anatomy.svg")


# --------------------------------------------------------------------------- #
# B2 - Lineage chain
# --------------------------------------------------------------------------- #
def figure_lineage_chain() -> None:
    events = load_jsonl("zmeta-profile-H-examples.jsonl")
    chain_types = ["OBSERVATION_EVENT", "INFERENCE_EVENT", "FUSION_EVENT", "STATE_EVENT"]
    nodes = []
    for t in chain_types:
        ev = next((e for e in events if event_type(e) == t), None)
        if ev:
            nodes.append(ev)

    s = Svg(1000, 320, "ZMeta lineage chain")
    s.text(26, 34, "Lineage you can audit", size=21, weight="700")
    s.text(26, 56, "Each derived event carries based_on back to its evidence - no stage silently becomes the next.",
           size=13, fill=MUTED)

    box_w, box_h = 206, 96
    gap = (1000 - 52 - box_w * len(nodes)) / max(len(nodes) - 1, 1)
    y = 110
    centers = []
    for i, ev in enumerate(nodes):
        x = 26 + i * (box_w + gap)
        et = event_type(ev)
        color = FAMILY.get(et, MUTED)
        s.rect(x, y, box_w, box_h, fill=PANEL, stroke=color, sw=2, rx=10)
        s.rect(x, y, box_w, 26, fill=color, rx=10)
        s.rect(x, y + 14, box_w, 12, fill=color)  # square off lower corners of header
        s.text(x + 12, y + 18, et, size=12.5, weight="700", fill="#ffffff")
        eid = ev.get("event", {}).get("event_id", "")
        s.text(x + 12, y + 48, "event_id", size=11, fill=MUTED)
        s.text(x + 12, y + 64, "..." + short_id(eid), size=13, family=MONO, fill=INK)
        based = ev.get("lineage", {}).get("based_on", []) or ev.get("payload", {}).get("based_on", [])
        if based:
            s.text(x + 12, y + 84, "based_on ..." + short_id(based[0]), size=11, family=MONO, fill=MUTED)
        else:
            s.text(x + 12, y + 84, "root (measured fact)", size=11, fill=MUTED)
        centers.append((x, x + box_w, y + box_h / 2))

    for i in range(len(centers) - 1):
        _, x_end, yc = centers[i]
        x_start = centers[i + 1][0]
        s.arrow(x_end + 6, yc, x_start - 6, yc, color=MUTED, sw=2.2, head=9)
        midx = (x_end + x_start) / 2
        s.text(midx, yc - 10, "based_on", size=10.5, fill=MUTED, anchor="middle")

    s.text(26, y + box_h + 46, "COMMAND_EVENT and SYSTEM_EVENT reference this same chain, so retasking intent and "
           "task acknowledgements stay tied to the evidence that justified them.", size=12, fill=MUTED)
    s.save(IMG_DIR / "b2-lineage-chain.svg")
    print("  wrote b2-lineage-chain.svg")


# --------------------------------------------------------------------------- #
# B3 - Encoding sizes
# --------------------------------------------------------------------------- #
def figure_encoding_sizes() -> None:
    l_events = load_jsonl("zmeta-profile-L-examples.jsonl")
    state = next(e for e in l_events if event_type(e) == "STATE_EVENT")
    sizes = encoding_sizes(state)

    order = ["JSON", "CBOR", "Compact", "Protobuf"]
    colors = {"JSON": "#3a7ca5", "CBOR": "#2e8b6f", "Compact": "#c47f2a", "Protobuf": "#7a5ea8"}
    vals = [(k, sizes.get(k)) for k in order if sizes.get(k) is not None]
    max_v = max(v for _, v in vals)
    json_v = sizes.get("JSON") or max_v

    s = Svg(780, 470, "ZMeta wire-size comparison")
    s.text(26, 34, "Same event, four wire formats", size=21, weight="700")
    s.text(26, 56, "Profile L STATE_EVENT (TRACK_STATE). Decoding always recovers the identical canonical JSON.",
           size=13, fill=MUTED)

    base_y = 380
    chart_x = 70
    chart_w = 660
    bar_w = 96
    slot = chart_w / len(vals)
    top = 96
    # gridlines
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        gy = base_y - frac * (base_y - top)
        s.line(chart_x, gy, chart_x + chart_w, gy, stroke=GRID, sw=1)
        s.text(chart_x - 10, gy + 4, f"{int(frac * max_v)}", size=10.5, fill=MUTED, anchor="end")
    s.text(28, top - 14, "bytes", size=11, fill=MUTED)

    for i, (name, v) in enumerate(vals):
        bx = chart_x + slot * i + (slot - bar_w) / 2
        bh = (v / max_v) * (base_y - top)
        s.rect(bx, base_y - bh, bar_w, bh, fill=colors.get(name, MUTED), rx=6)
        s.text(bx + bar_w / 2, base_y - bh - 22, f"{v} B", size=15, weight="700", anchor="middle")
        if name != "JSON":
            red = round((1 - v / json_v) * 100)
            s.text(bx + bar_w / 2, base_y - bh - 6, f"-{red}% vs JSON", size=10.5, fill=MUTED, anchor="middle")
        s.text(bx + bar_w / 2, base_y + 20, name, size=13, weight="600", anchor="middle")
    s.line(chart_x, base_y, chart_x + chart_w, base_y, stroke=INK, sw=1.4)

    s.text(26, 442, "Compact CBOR (integer keys, binary UUID, epoch-ms time) is sized for tight Profile L packet budgets.",
           size=12, fill=MUTED)
    s.save(IMG_DIR / "b3-encoding-sizes.svg")
    print("  wrote b3-encoding-sizes.svg  sizes=" + ", ".join(f"{k}:{sizes[k]}" for k in order if sizes.get(k)))


# --------------------------------------------------------------------------- #
# B4 - Profile / event-family matrix
# --------------------------------------------------------------------------- #
def figure_profile_matrix() -> None:
    profiles = parse_profiles()
    families = ["OBSERVATION_EVENT", "INFERENCE_EVENT", "FUSION_EVENT", "STATE_EVENT", "COMMAND_EVENT", "SYSTEM_EVENT"]
    rows = ["H", "M", "L"]
    row_use = {
        "H": "high-fidelity / audit",
        "M": "moderate (no inference)",
        "L": "constrained tactical",
    }

    s = Svg(1000, 430, "Export profiles and allowed event families")
    s.text(26, 34, "Profiles thin the stream without changing meaning", size=21, weight="700")
    s.text(26, 56, "Which event families each export profile may carry (policy/profiles.yaml).", size=13, fill=MUTED)

    grid_x = 250
    col_w = 116
    head_y = 110
    row_h = 70
    grid_top = head_y + 14

    # column headers (event families, rotated-free: stacked short labels)
    for j, fam in enumerate(families):
        cx = grid_x + j * col_w + col_w / 2
        color = FAMILY[fam]
        short = fam.replace("_EVENT", "")
        s.rect(grid_x + j * col_w + 8, head_y - 22, col_w - 16, 24, fill=color, rx=6)
        s.text(cx, head_y - 5, short, size=11.5, weight="700", fill="#ffffff", anchor="middle")

    for i, prof in enumerate(rows):
        ry = grid_top + i * row_h
        allowed = set(profiles.get(prof, []))
        s.text(40, ry + row_h / 2 - 2, f"Profile {prof}", size=16, weight="700")
        s.text(40, ry + row_h / 2 + 16, row_use[prof], size=11, fill=MUTED)
        for j, fam in enumerate(families):
            cx = grid_x + j * col_w + col_w / 2
            cell_x = grid_x + j * col_w + 8
            cell_w = col_w - 16
            s.rect(cell_x, ry + 8, cell_w, row_h - 16, fill=PANEL, stroke=PANEL_STROKE, sw=1, rx=8)
            if fam in allowed:
                color = FAMILY[fam]
                s.circle(cx, ry + row_h / 2, 13, fill=color)
                # check mark
                s.parts.append(
                    f'<path d="M {cx-6:.1f} {ry+row_h/2:.1f} l 4 5 l 8 -10" fill="none" '
                    f'stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
                )
            else:
                s.text(cx, ry + row_h / 2 + 5, "\u2014", size=18, fill="#b9c4d0", anchor="middle")

    s.text(26, 410, "Allowed families are preserved in full; profile projection never strips identity, lineage, "
           "timing, or risk labels.", size=12, fill=MUTED)
    s.save(IMG_DIR / "b4-profile-matrix.svg")
    print("  wrote b4-profile-matrix.svg")


# --------------------------------------------------------------------------- #
# B5 - Triangulation + error ellipse
# --------------------------------------------------------------------------- #
def _solve(sensors: List[Tuple[float, float, float]]) -> Optional[Dict[str, float]]:
    """Least-squares intersection of bearing lines + (unscaled) covariance ellipse.

    sensors: (x, y, bearing_deg), bearing measured from +x axis (math convention).
    Each LOB contributes a constraint normal to its direction: n . (p - s) = 0.
    Covariance is the inverse of the summed information matrix (unit variance per LOB),
    so semi-axes are sqrt(eigenvalues); callers apply a shared pixel scale.
    """
    info11 = info12 = info22 = 0.0
    b1 = b2 = 0.0
    for (sx, sy, bdeg) in sensors:
        br = math.radians(bdeg)
        nx, ny = -math.sin(br), math.cos(br)
        info11 += nx * nx
        info12 += nx * ny
        info22 += ny * ny
        proj = nx * sx + ny * sy
        b1 += nx * proj
        b2 += ny * proj
    det = info11 * info22 - info12 * info12
    if abs(det) < 1e-9:
        return None
    px = (b1 * info22 - b2 * info12) / det
    py = (info11 * b2 - info12 * b1) / det
    c11 = info22 / det
    c12 = -info12 / det
    c22 = info11 / det
    tr = c11 + c22
    diff = math.sqrt(max((c11 - c22) ** 2 + 4 * c12 * c12, 0.0))
    lam1 = (tr + diff) / 2
    lam2 = (tr - diff) / 2
    return {
        "px": px,
        "py": py,
        "lam1": lam1,
        "lam2": lam2,
        "angle": math.degrees(0.5 * math.atan2(2 * c12, c11 - c22)),
        "gdop": math.sqrt(max(tr, 0.0)),
    }


def _draw_triangulation(s: Svg, ox: float, oy: float, w: float, h: float, title: str,
                        sensors: List[Tuple[float, float, float]], emitter: Tuple[float, float],
                        sol: Dict[str, float], scale: float, area_ref: float) -> None:
    s.rect(ox, oy, w, h, fill=PANEL, stroke=PANEL_STROKE, sw=1.2, rx=10)
    s.text(ox + 16, oy + 26, title, size=14.5, weight="700")

    def tx(x):
        return ox + 30 + x

    def ty(y):
        return oy + h - 44 - y

    for (sx, sy, bdeg) in sensors:
        br = math.radians(bdeg)
        ex = sx + 210 * math.cos(br)
        ey = sy + 210 * math.sin(br)
        s.line(tx(sx), ty(sy), tx(ex), ty(ey), stroke="#9fb0c0", sw=1.6, dash="5 4")

    sma = scale * math.sqrt(max(sol["lam1"], 1e-6))
    smi = scale * math.sqrt(max(sol["lam2"], 1e-6))
    s.ellipse(tx(sol["px"]), ty(sol["py"]), max(sma, 6), max(smi, 4), angle=-sol["angle"],
              fill=FAMILY["FUSION_EVENT"], stroke="none", opacity=0.16)
    s.ellipse(tx(sol["px"]), ty(sol["py"]), max(sma, 6), max(smi, 4), angle=-sol["angle"],
              fill="none", stroke=FAMILY["FUSION_EVENT"], sw=2)
    area = math.pi * sma * smi
    s.text(ox + 16, oy + h - 16,
           f"GDOP {sol['gdop']:.2f}    ellipse area {area / area_ref:.2f}x",
           size=12.5, weight="700", fill=FAMILY["FUSION_EVENT"])

    ex, ey = emitter
    s.circle(tx(ex), ty(ey), 4.5, fill=FAMILY["COMMAND_EVENT"])
    s.text(tx(ex) + 9, ty(ey) + 4, "emitter", size=11, fill=FAMILY["COMMAND_EVENT"])

    for idx, (sx, sy, _b) in enumerate(sensors, 1):
        s.poly([(tx(sx), ty(sy) - 6), (tx(sx) - 6, ty(sy) + 5), (tx(sx) + 6, ty(sy) + 5)],
               fill=FAMILY["OBSERVATION_EVENT"])
        s.text(tx(sx) + 9, ty(sy) + 4, f"S{idx}", size=11, fill=FAMILY["OBSERVATION_EVENT"])


def figure_triangulation() -> None:
    s = Svg(1000, 430, "Multi-LOB triangulation and error-ellipse reduction")
    s.text(26, 34, "Fusion: more bearings, tighter fix", size=21, weight="700")
    s.text(26, 56, "Independent RF lines of bearing intersect into a track; geometry drives the error ellipse.",
           size=13, fill=MUTED)

    # Before: 2 LOBs from a short baseline -> shallow crossing -> elongated ellipse.
    before = [(40, 55, 42.0), (110, 42, 63.0)]
    # After: retask a platform to add a 3rd LOB with a strong crossing angle.
    after = [(40, 55, 42.0), (110, 42, 63.0), (300, 90, 150.0)]
    emitter = (170, 170)

    sb = _solve(before)
    sa = _solve(after)
    # Shared scale: size the (larger) "before" major axis to a fixed pixel target.
    scale = 125.0 / math.sqrt(sb["lam1"]) if sb else 32.0
    area_ref = math.pi * (scale * math.sqrt(sb["lam1"])) * (scale * math.sqrt(sb["lam2"]))

    _draw_triangulation(s, 26, 78, 460, 320, "2 LOBs - single retask pending", before, emitter, sb, scale, area_ref)
    _draw_triangulation(s, 514, 78, 460, 320, "3 LOBs - after retasking", after, emitter, sa, scale, area_ref)

    s.arrow(489, 238, 511, 238, color=MUTED, sw=2.4, head=9)
    s.save(IMG_DIR / "b5-triangulation.svg")
    print(f"  wrote b5-triangulation.svg  gdop {sb['gdop']:.2f} -> {sa['gdop']:.2f}")


def figure_at_a_glance() -> None:
    s = Svg(1000, 360, "ZMeta at a glance")
    s.text(26, 34, "ZMeta at a glance", size=21, weight="700")
    s.text(26, 56, "Sensors become governed events that move - lane by lane - to operator display and bounded "
           "mission intent.", size=13, fill=MUTED)

    chips = [
        ("collect", "Sensors", MUTED, "SDR / EO-IR / MAVLink"),
        ("translate", "OBSERVATION", FAMILY["OBSERVATION_EVENT"], "edge adapter normalizes"),
        ("infer", "INFERENCE", FAMILY["INFERENCE_EVENT"], "AI / analytic claim"),
        ("fuse", "FUSION", FAMILY["FUSION_EVENT"], "track identity"),
        ("project", "STATE", FAMILY["STATE_EVENT"], "CoT to TAK / ATAK"),
        ("retask", "COMMAND", FAMILY["COMMAND_EVENT"], "bounded mission intent"),
    ]
    n = len(chips)
    x0, cw, cy, ch = 26, 138, 96, 86
    gap = (1000 - 2 * 26 - cw * n) / (n - 1)
    centers: List[Tuple[float, float, float]] = []
    for i, (verb, fam, color, note) in enumerate(chips):
        x = x0 + i * (cw + gap)
        s.text(x + cw / 2, cy - 8, verb, size=11, fill=MUTED, anchor="middle")
        s.rect(x, cy, cw, ch, fill=PANEL, stroke=color, sw=2, rx=10)
        s.rect(x, cy, cw, 8, fill=color, rx=4)
        s.rect(x, cy + 4, cw, 5, fill=color)
        s.text(x + cw / 2, cy + 40, fam, size=14, weight="700", fill=color, anchor="middle")
        s.text(x + cw / 2, cy + 62, note, size=10.5, fill=INK, anchor="middle")
        centers.append((x, x + cw, cy + ch / 2))

    for i in range(n - 1):
        _, xe, yc = centers[i]
        xs = centers[i + 1][0]
        s.arrow(xe + 4, yc, xs - 4, yc, color=MUTED, sw=2, head=8)

    # Retask loop: COMMAND back to Sensors.
    yloop = cy + ch + 42
    x_cmd = (centers[-1][0] + centers[-1][1]) / 2
    x_sen = (centers[0][0] + centers[0][1]) / 2
    red = FAMILY["COMMAND_EVENT"]
    s.line(x_cmd, cy + ch, x_cmd, yloop, stroke=red, sw=2)
    s.line(x_cmd, yloop, x_sen, yloop, stroke=red, sw=2)
    s.arrow(x_sen, yloop, x_sen, cy + ch + 2, color=red, sw=2, head=8)
    s.text((x_cmd + x_sen) / 2, yloop - 8,
           "retask loop: COMMAND_EVENT -> deconfliction -> new collection", size=11, fill=red, anchor="middle")

    sy = yloop + 30
    s.rect(26, sy, 948, 26, fill="#eef2f6", stroke=PANEL_STROKE, sw=1, rx=8)
    s.text(36, sy + 17, "SYSTEM_EVENT - timing, link, validation, and TASK_ACK status run across every stage",
           size=11.5, fill=MUTED)
    fy = sy + 50
    s.text(26, fy, "Profiles:  H high-fidelity  |  M moderate  |  L constrained tactical", size=11.5, fill=INK)
    s.text(26, fy + 18, "Encodings:  JSON  |  CBOR  |  compact CBOR  |  protobuf   (all decode to canonical JSON)",
           size=11.5, fill=INK)
    s.save(IMG_DIR / "c1-zmeta-at-a-glance.svg")
    print("  wrote c1-zmeta-at-a-glance.svg")


def main() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Writing figures to {IMG_DIR}")
    for fn in (
        figure_at_a_glance,
        figure_event_anatomy,
        figure_lineage_chain,
        figure_encoding_sizes,
        figure_profile_matrix,
        figure_triangulation,
    ):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - keep generating remaining figures
            print(f"  ERROR in {fn.__name__}: {exc}")
    print("Done.")


if __name__ == "__main__":
    main()
