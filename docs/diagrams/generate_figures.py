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
    d1-authority-stack.svg      The conflict-resolution authority stack, tier by tier
    d2-promotion-chain.svg      Promotion pipeline with schema/policy requirements per stage
    d3-true-today.svg           Counts of what exists today, read from the manifests
    e1-adapt-once.svg           Point-to-point bridges vs adapt-once, counted from adapters/
    e2-translation-pipeline.svg Native input -> normalize -> canonical event -> projections
    e3-wire-matrix.svg          Measured bytes across encodings and profiles
    e4-proof-surface.svg        The conformance proof surface, counted from the fixture suites
    f1-thin-waist.svg           The thin waist: replaceable products above and below one locked contract
    f2-behind-the-icon.svg      One display icon decomposed into the real event chain that carried it
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


# --------------------------------------------------------------------------- #
# Data helpers for the D-series (ontology reference) figures
# --------------------------------------------------------------------------- #
def _count_after_marker(path: Path, marker: str, pattern: str) -> Dict[str, int]:
    """Count regex group(1) values inside the block opened by the marker line.

    The scan stops at the next top-level key so a sibling block added after the
    marker cannot inflate the counts, and the result is cross-checked against
    the number of list records in the same block so an indentation reformat
    fails loudly instead of rendering zeros.
    """
    counts: Dict[str, int] = {}
    records = 0
    active = False
    rx = re.compile(pattern)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not active:
            if line.strip() == marker:
                active = True
            continue
        if line and not line[0].isspace():
            break
        if re.match(r"^  - ", line):
            records += 1
        m = rx.match(line)
        if m:
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    if sum(counts.values()) != records:
        raise ValueError(
            f"{path.name}: {records} records under '{marker}' but "
            f"{sum(counts.values())} status lines matched; layout drifted"
        )
    return counts


def _schema_stage_rules() -> Dict[str, Dict[str, str]]:
    """Read confidence/lineage posture per event_type from the v1.0 schema's allOf arms."""
    schema = json.loads((ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(encoding="utf-8"))
    rules: Dict[str, Dict[str, str]] = {}
    for arm in schema.get("allOf", []):
        if not isinstance(arm, dict) or "if" not in arm or "then" not in arm:
            continue
        try:
            etype = arm["if"]["properties"]["event"]["properties"]["event_type"]["const"]
        except (KeyError, TypeError):
            continue
        then = arm["then"]
        required = then.get("required", [])
        props = then.get("properties", {})
        confidence = "required" if "confidence" in required else (
            "prohibited" if props.get("confidence") is False else "optional")
        lineage = "required" if "lineage" in required else "optional"
        rules[etype] = {"confidence": confidence, "lineage": lineage}
    return rules


def _lineage_parent_map() -> Dict[str, List[str]]:
    """Parse allowed_parent_event_types from policy/lineage.yaml without a YAML dependency."""
    text = (ROOT / "policy" / "lineage.yaml").read_text(encoding="utf-8")
    parents: Dict[str, List[str]] = {}
    current: Optional[str] = None
    active = False
    for line in text.splitlines():
        if line.strip() == "allowed_parent_event_types:":
            active = True
            continue
        if not active:
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^    ([A-Z_]+):\s*$", line)
        if m:
            current = m.group(1)
            parents[current] = []
            continue
        m = re.match(r"^      - ([A-Z_]+)\s*$", line)
        if m and current:
            parents[current].append(m.group(1))
            continue
        if len(line) - len(line.lstrip()) <= 2:
            break
    return parents


def _external_promotion_mode() -> str:
    """Read the global external_state_promotion.mode from policy/producer-authority.yaml.

    Only the top-level block (2-space indent) is read; the scan stops when the
    block ends so a per-producer promotion block cannot supply the value.
    """
    active = False
    for line in (ROOT / "policy" / "producer-authority.yaml").read_text(encoding="utf-8").splitlines():
        if line == "  external_state_promotion:":
            active = True
            continue
        if active:
            m = re.match(r"^\s+mode:\s*(\w+)\s*$", line)
            if m:
                return m.group(1)
            if line.strip() and not line.lstrip().startswith("#") and len(line) - len(line.lstrip()) <= 2:
                break
    return "unknown"


def _short_family(fam: str) -> str:
    return fam.replace("_EVENT", "")


# --------------------------------------------------------------------------- #
# D1 - Authority stack
# --------------------------------------------------------------------------- #
def figure_authority_stack() -> None:
    # The six tiers mirror docs/zmeta_change_governance.md "Authority Stack".
    tiers = [
        ("1", "Semantic contract", "spec/semantics-contract.md", "normative meaning; v1.0 locked", FAMILY["COMMAND_EVENT"]),
        ("2", "Canonical schemas", "schema/*.schema.json", "structural enforcement", FAMILY["OBSERVATION_EVENT"]),
        ("3", "Policy YAML", "policy/*.yaml", "runtime enforcement, tunable", FAMILY["FUSION_EVENT"]),
        ("4", "Governance artifacts", "extension registry, conformance manifest, catalogs, release manifest", "governance records", FAMILY["INFERENCE_EVENT"]),
        ("5", "Validators and tests", "tools/*, gateway/tests/*", "the checking machinery", FAMILY["STATE_EVENT"]),
        ("6", "README, examples, adapters, docs", "reference and advisory surfaces", "explain, never redefine", MUTED),
    ]
    row_h = 64
    top = 96
    s = Svg(1000, top + row_h * len(tiers) + 66, "ZMeta authority stack")
    s.text(26, 34, "The authority stack", size=21, weight="700")
    s.text(26, 56, "Conflict resolution order (docs/zmeta_change_governance.md). Lower tiers must preserve higher ones.",
           size=13, fill=MUTED)

    w = 700
    for i, (num, name, paths, role, color) in enumerate(tiers):
        y = top + i * row_h
        inset = i * 18
        s.rect(26 + inset, y, w - inset, row_h - 10, fill=PANEL, stroke=color, sw=2, rx=10)
        s.circle(52 + inset, y + (row_h - 10) / 2, 13, fill=color)
        s.text(52 + inset, y + (row_h - 10) / 2 + 5, num, size=14, weight="700", fill="#ffffff", anchor="middle")
        s.text(76 + inset, y + 22, name, size=14.5, weight="700")
        s.text(76 + inset, y + 40, paths, size=11.5, family=MONO, fill=MUTED)
        s.text(745, y + 31, role, size=11.5, fill=INK)

    ay = top + 6
    by = top + row_h * len(tiers) - 16
    s.line(992, ay, 992, by, stroke=MUTED, sw=1.6)
    s.arrow(992, ay + 12, 992, ay, color=MUTED, sw=1.6, head=7)
    s.text(986, (ay + by) / 2, "authority", size=10.5, fill=MUTED, anchor="end")

    s.text(26, top + row_h * len(tiers) + 26,
           "A rule can be normative and unenforced, or enforced from an advisory origin; the tiers say who wins,",
           size=12, fill=MUTED)
    s.text(26, top + row_h * len(tiers) + 44,
           "not who checks. Enforcement lives in tier 5 and in the schema arms of tier 2.", size=12, fill=MUTED)
    s.save(IMG_DIR / "d1-authority-stack.svg")
    print("  wrote d1-authority-stack.svg")


# --------------------------------------------------------------------------- #
# D2 - Promotion chain with per-stage requirements
# --------------------------------------------------------------------------- #
def figure_promotion_chain() -> None:
    stage_rules = _schema_stage_rules()
    parent_map = _lineage_parent_map()
    promo_mode = _external_promotion_mode()

    chain = ["OBSERVATION_EVENT", "INFERENCE_EVENT", "FUSION_EVENT", "STATE_EVENT"]
    glosses = {
        "OBSERVATION_EVENT": "measured fact",
        "INFERENCE_EVENT": "analytic claim",
        "FUSION_EVENT": "track identity",
        "STATE_EVENT": "operator belief",
    }
    s = Svg(1000, 470, "ZMeta promotion chain with per-stage requirements")
    s.text(26, 34, "Promotion is earned, stage by stage", size=21, weight="700")
    s.text(26, 56, "Requirement chips are read from the v1.0 schema arms and the policy pack at generation time.",
           size=13, fill=MUTED)

    box_w, box_h = 216, 196
    gap = (1000 - 52 - box_w * 4) / 3
    y = 96
    for i, fam in enumerate(chain):
        x = 26 + i * (box_w + gap)
        color = FAMILY[fam]
        s.rect(x, y, box_w, box_h, fill=PANEL, stroke=color, sw=2, rx=10)
        s.rect(x, y, box_w, 8, fill=color, rx=4)
        s.rect(x, y + 4, box_w, 5, fill=color)
        s.text(x + 12, y + 30, _short_family(fam), size=15, weight="700", fill=color)
        s.text(x + 12, y + 48, glosses[fam], size=11.5, fill=MUTED)
        rules = stage_rules.get(fam, {})
        chips = [
            ("confidence " + rules.get("confidence", "?"),
             FAMILY["COMMAND_EVENT"] if rules.get("confidence") == "prohibited" else FAMILY["FUSION_EVENT"]),
            ("lineage " + rules.get("lineage", "?"),
             FAMILY["FUSION_EVENT"] if rules.get("lineage") == "required" else MUTED),
        ]
        allowed_parents = parent_map.get(fam)
        if allowed_parents:
            chips.append(("parents: " + ", ".join(_short_family(p) for p in allowed_parents), MUTED))
        elif fam == "OBSERVATION_EVENT":
            chips.append(("root: no parents needed", MUTED))
        cy = y + 66
        for label, color2 in chips:
            lines = [label]
            if len(label) > 28:
                words = label.split()
                lines = []
                cur = ""
                for wd in words:
                    if cur and len(cur) + len(wd) + 1 > 28:
                        lines.append(cur)
                        cur = wd
                    else:
                        cur = f"{cur} {wd}".strip()
                if cur:
                    lines.append(cur)
            chip_h = 14 + 14 * len(lines)
            s.rect(x + 12, cy, box_w - 24, chip_h, fill="#ffffff", stroke=color2, sw=1.4, rx=7)
            ty = cy + 18
            for ln in lines:
                s.text(x + 22, ty, ln, size=11, family=MONO, fill=INK)
                ty += 14
            cy += chip_h + 8
        if i < 3:
            s.arrow(x + box_w + 6, y + box_h / 2, x + box_w + gap - 6, y + box_h / 2, color=MUTED, sw=2.2, head=9)
            s.text(x + box_w + gap / 2, y + box_h / 2 - 10, "derive", size=10.5, fill=MUTED, anchor="middle")

    ext_y = y + box_h + 46
    ext_x = 26
    s.rect(ext_x, ext_y, 380, 58, fill=PANEL, stroke=FAMILY["COMMAND_EVENT"], sw=2, rx=10, dash="6 4")
    s.text(ext_x + 12, ext_y + 24, "External track (CoT / JREAP / MAVLink / SAPIENT)", size=12, weight="700")
    s.text(ext_x + 12, ext_y + 43, f"external_state_promotion: mode {promo_mode}; evidence required",
           size=11, family=MONO, fill=FAMILY["COMMAND_EVENT"])
    state_x = 26 + 3 * (box_w + gap)
    s.arrow(ext_x + 380, ext_y + 29, state_x + box_w / 2, y + box_h + 6, color=FAMILY["COMMAND_EVENT"], sw=2, head=9, dash="6 4")
    s.text(ext_x + 400, ext_y + 52,
           "promotion gate: new event_id, policy evidence, loop check", size=10.5,
           fill=FAMILY["COMMAND_EVENT"], anchor="start")

    s.text(26, ext_y + 92, "COMMAND_EVENT and SYSTEM_EVENT sit beside this chain: commands cite it as evidence and are",
           size=12, fill=MUTED)
    s.text(26, ext_y + 110, "deconflicted out of band; system events carry the health and diagnostics of every stage.",
           size=12, fill=MUTED)
    s.save(IMG_DIR / "d2-promotion-chain.svg")
    print("  wrote d2-promotion-chain.svg  stages=" + str(len(chain)) + " schema_arms=" + str(len(stage_rules)))


# --------------------------------------------------------------------------- #
# D3 - What is true today (counts read from the manifests)
# --------------------------------------------------------------------------- #
def figure_true_today() -> None:
    dispatcher = json.loads((ROOT / "schema" / "zmeta-event.schema.json").read_text(encoding="utf-8"))
    branches = []
    for arm in dispatcher.get("oneOf", []):
        ref = arm.get("$ref", "")
        m = re.search(r"zmeta-event-([0-9.]+)\.schema\.json", ref)
        if m:
            branches.append(m.group(1))

    class_counts = _count_after_marker(
        ROOT / "conformance" / "conformance_classes.yaml", "class_records:", r"^    status: (\w+)\s*$")
    registry_counts = _count_after_marker(
        ROOT / "spec" / "extension-registry.yaml", "entries:", r"^    status: (\w+)\s*$")

    codes_text = (ROOT / "policy" / "violation-codes.yaml").read_text(encoding="utf-8")
    code_total = len(re.findall(r"^\s*- code: ", codes_text, re.M))
    warn_total = len(re.findall(r"^\s*severity: warn\s*$", codes_text, re.M))

    ingress = sorted(
        p.name for p in (ROOT / "adapters" / "ingress").iterdir()
        if p.is_dir() and p.name not in ("__pycache__", "template"))
    egress = sorted(p.name for p in (ROOT / "adapters" / "egress").iterdir()
                    if p.is_dir() and p.name != "__pycache__")
    projector = sorted(p.name for p in (ROOT / "adapters" / "projector").iterdir()
                       if p.is_dir() and p.name != "__pycache__")

    roadmap_text = (ROOT / "spec" / "future-branch-roadmap.yaml").read_text(encoding="utf-8")
    candidates_block = roadmap_text.split("\ncandidates:\n", 1)[1].split("\nrejected_or_deferred:\n", 1)[0]
    decisions_block = roadmap_text.split("\nrejected_or_deferred:\n", 1)[1]
    roadmap_candidates = len(re.findall(r"^  - id: ", candidates_block, re.M))
    roadmap_decisions = len(re.findall(r"^  - id: ", decisions_block, re.M))

    release = "unknown"
    for line in (ROOT / "release" / "zmeta-release-manifest.yaml").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^release_id:\s*\"?([\w.\-]+)\"?", line)
        if m:
            release = m.group(1)
            break

    def fmt_counts(counts: Dict[str, int], order: List[str]) -> str:
        parts = [f"{counts[k]} {k}" for k in order if k in counts]
        parts += [f"{v} {k}" for k, v in sorted(counts.items()) if k not in order]
        return ", ".join(parts)

    rows = [
        ("Release", release, "release/zmeta-release-manifest.yaml"),
        ("Version branches", " and ".join(branches) + "  (1.0 locked, 1.1.0 experimental)", "schema/zmeta-event.schema.json"),
        ("Conformance classes", f"{sum(class_counts.values())} defined: " + fmt_counts(class_counts, ["implemented", "future", "planned", "reserved"]), "conformance/conformance_classes.yaml"),
        ("Registry entries", f"{sum(registry_counts.values())} recorded: " + fmt_counts(registry_counts, ["reserved", "experimental", "proposed", "adopted", "rejected"]), "spec/extension-registry.yaml"),
        ("Violation codes", f"{code_total} governed ({warn_total} warn, {code_total - warn_total} fail)", "policy/violation-codes.yaml"),
        ("Ingress adapters", f"{len(ingress)} shipped (plus the authoring template)", "adapters/ingress/"),
        ("Egress adapters", f"{len(egress)} shipped; projectors: {len(projector)}", "adapters/egress/, adapters/projector/"),
        ("Roadmap candidates", f"{roadmap_candidates} candidates, {roadmap_decisions} durable exclusions; none valid vocabulary today", "spec/future-branch-roadmap.yaml"),
    ]

    row_h = 46
    top = 96
    s = Svg(1000, top + row_h * len(rows) + 60, "What exists today, counted from the manifests")
    s.text(26, 34, "What is true today", size=21, weight="700")
    s.text(26, 56, "Every count on this card is read from the named machine-readable source at generation time.",
           size=13, fill=MUTED)
    for i, (label, value, src) in enumerate(rows):
        ry = top + i * row_h
        if i % 2 == 0:
            s.rect(26, ry - 14, 948, row_h - 6, fill=PANEL, rx=8)
        s.text(40, ry + 8, label, size=13, weight="700")
        s.text(240, ry + 8, value, size=12.5, family=MONO, fill=INK)
        s.text(966, ry + 24, src, size=9, family=MONO, fill=MUTED, anchor="end")
    s.text(26, top + row_h * len(rows) + 26,
           "Regenerate with python docs/diagrams/generate_figures.py after any release; stale counts are a defect.",
           size=12, fill=MUTED)
    s.save(IMG_DIR / "d3-true-today.svg")
    print(
        "  wrote d3-true-today.svg  classes=" + str(sum(class_counts.values()))
        + " registry=" + str(sum(registry_counts.values()))
        + " codes=" + str(code_total)
    )


# --------------------------------------------------------------------------- #
# E-series: the case for ZMeta, measured from the repo
# --------------------------------------------------------------------------- #
INGRESS_DISPLAY = {
    "adsb": "ADS-B", "ais": "AIS", "bladerf": "bladeRF EW", "cot": "CoT",
    "eo-cv": "EO-CV", "example-vendor": "Example-vendor", "jreap": "JREAP",
    "klv": "KLV", "kraken": "KrakenSDR", "mavlink": "MAVLink", "moth": "Moth",
    "sapient": "SAPIENT", "signalhunter": "SignalHunter",
}
# Directory -> projection label, pinned so a renamed or added egress directory
# fails loudly instead of shipping a stale label.
EGRESS_DISPLAY = {
    "cot": "CoT", "mavlink": "MissionIntent", "jreap": "JREAP",
    "klv": "KLV", "sapient": "SAPIENT",
}
EGRESS_ORDER = ["cot", "mavlink", "jreap", "klv", "sapient"]


def _adapter_dirs(kind: str) -> List[str]:
    return sorted(
        p.name for p in (ROOT / "adapters" / kind).iterdir()
        if p.is_dir() and p.name not in ("__pycache__", "template"))


def _ingress_names() -> List[str]:
    dirs = _adapter_dirs("ingress")
    unknown = [d for d in dirs if d not in INGRESS_DISPLAY]
    if unknown:
        raise ValueError(f"ingress dirs missing a display label: {unknown}")
    return [INGRESS_DISPLAY[d] for d in dirs]


def figure_adapt_once() -> None:
    sources = _ingress_names()
    egress_dirs = _adapter_dirs("egress")
    if set(egress_dirs) != set(EGRESS_DISPLAY):
        raise ValueError(f"egress dirs {egress_dirs} != pinned labels {sorted(EGRESS_DISPLAY)}")
    outputs = [EGRESS_DISPLAY[d] for d in EGRESS_ORDER]
    n, m = len(sources), len(egress_dirs)

    s = Svg(1000, 600, "Point-to-point bridges versus adapt-once through ZMeta")
    s.text(26, 34, "Adapt once, interoperate with everything ZMeta maps", size=21, weight="700")
    s.text(26, 56, f"This repository ships {n} ingress adapters and {m} egress projections; the counts below are those.",
           size=13, fill=MUTED)

    panel_y, panel_h = 84, 430
    src_top, src_gap = panel_y + 46, (panel_h - 80) / (n - 1)
    out_gap = (panel_h - 80) / (len(outputs) - 1)

    def draw_panel(px: float, hub: bool) -> None:
        s.rect(px, panel_y, 460, panel_h, fill=PANEL, stroke=PANEL_STROKE, sw=1.2, rx=10)
        title = "Through ZMeta: adapt once" if hub else "Without a shared model"
        s.text(px + 16, panel_y + 26, title, size=14.5, weight="700")
        sx, ox = px + 118, px + 350
        src_pts = [(sx, src_top + i * src_gap) for i in range(n)]
        out_pts = [(ox, src_top + j * out_gap) for j in range(len(outputs))]
        if hub:
            hx, hy = px + 234, panel_y + 46 + (panel_h - 80) / 2
            for (x, y) in src_pts:
                s.line(x + 6, y, hx - 30, hy, stroke=FAMILY["OBSERVATION_EVENT"], sw=1.1)
            for (x, y) in out_pts:
                s.line(hx + 30, hy, x - 6, y, stroke=FAMILY["STATE_EVENT"], sw=1.1)
            s.circle(hx, hy, 30, fill=FAMILY["FUSION_EVENT"])
            s.text(hx, hy - 2, "ZMeta", size=12, weight="700", fill="#ffffff", anchor="middle")
            s.text(hx, hy + 12, "canonical", size=8.5, fill="#ffffff", anchor="middle")
        else:
            for (x1, y1) in src_pts:
                for (x2, y2) in out_pts:
                    s.line(x1 + 6, y1, x2 - 6, y2, stroke="#c47f2a", sw=0.55)
        for i, (x, y) in enumerate(src_pts):
            s.circle(x, y, 4, fill=FAMILY["OBSERVATION_EVENT"])
            s.text(x - 10, y + 3, sources[i], size=9.5, family=MONO, fill=INK, anchor="end")
        for j, (x, y) in enumerate(out_pts):
            s.circle(x, y, 4, fill=FAMILY["STATE_EVENT"])
            s.text(x + 10, y + 3, outputs[j], size=9.5, family=MONO, fill=INK)
        count = f"{n} x {m} = {n * m} bespoke bridges" if not hub else f"{n} + {m} = {n + m} adapters, one semantic model"
        color = FAMILY["COMMAND_EVENT"] if not hub else FAMILY["FUSION_EVENT"]
        s.text(px + 16, panel_y + panel_h - 14, count, size=13.5, weight="700", fill=color)

    draw_panel(26, hub=False)
    draw_panel(514, hub=True)
    s.text(26, panel_y + panel_h + 32,
           "Each bridge re-decides meaning: units, timestamps, identity, confidence. The canonical model decides once,",
           size=12, fill=MUTED)
    s.text(26, panel_y + panel_h + 50,
           "and a new source costs one adapter instead of one bridge per consumer.", size=12, fill=MUTED)
    s.save(IMG_DIR / "e1-adapt-once.svg")
    print(f"  wrote e1-adapt-once.svg  sources={n} outputs={m}")


def figure_translation_pipeline() -> None:
    events = load_jsonl("zmeta-profile-H-examples.jsonl")
    obs = next(e for e in events if event_type(e) == "OBSERVATION_EVENT")
    obs_sizes = encoding_sizes(obs)

    s = Svg(1000, 470, "Normalization and translation pipeline")
    s.text(26, 34, "Normalize once at the boundary, project everywhere", size=21, weight="700")
    s.text(26, 56, "Structure is authoritative and projections are lossy by declaration, never silently.",
           size=13, fill=MUTED)

    col_y, col_h = 92, 270
    # Column 1: native inputs
    x1, w1 = 26, 208
    s.rect(x1, col_y, w1, col_h, fill=PANEL, stroke=PANEL_STROKE, sw=1.2, rx=10)
    s.text(x1 + 12, col_y + 24, "Native inputs", size=13.5, weight="700")
    native = ["MAVLink v2 telemetry", "KrakenSDR DOA CSV", "dump1090 aircraft.json",
              "AIS position reports", "SAPIENT protobuf-JSON", "CoT XML tracks"]
    ny = col_y + 46
    for label in native:
        s.rect(x1 + 12, ny, w1 - 24, 26, fill="#ffffff", stroke=PANEL_STROKE, sw=1, rx=6)
        s.text(x1 + 20, ny + 17, label, size=10, family=MONO, fill=INK)
        ny += 33
    s.text(x1 + 12, col_y + col_h - 12, "each speaks its own dialect", size=10.5, fill=MUTED)

    # Column 2: the boundary obligations
    x2, w2 = 286, 220
    s.rect(x2, col_y, w2, col_h, fill=PANEL, stroke=FAMILY["FUSION_EVENT"], sw=2, rx=10)
    s.text(x2 + 12, col_y + 24, "Adapter boundary", size=13.5, weight="700", fill=FAMILY["FUSION_EVENT"])
    duties = ["UTC-Z timestamps", "explicit units", "UUIDv7 identity", "lineage transform",
              "timing-quality fallback", "promotion evidence", "family separation"]
    dy = col_y + 46
    for d in duties:
        s.circle(x2 + 20, dy - 4, 3, fill=FAMILY["FUSION_EVENT"])
        s.text(x2 + 32, dy, d, size=11.5, fill=INK)
        dy += 26
    s.text(x2 + 12, col_y + col_h - 12, "obligations checked by the harness", size=10.5, fill=MUTED)

    # Column 3: canonical event (from the real H example)
    x3, w3 = 556, 190
    s.rect(x3, col_y, w3, col_h, fill=PANEL, stroke=FAMILY["OBSERVATION_EVENT"], sw=2, rx=10)
    s.text(x3 + 12, col_y + 24, "Canonical event", size=13.5, weight="700", fill=FAMILY["OBSERVATION_EVENT"])
    keys = ["zmeta_version", "event", "source", "payload", "confidence*", "lineage", "profile"]
    key_colors = ["#3a7ca5", FAMILY["INFERENCE_EVENT"], "#2e8b6f", "#c47f2a", "#b5483d", "#7a5ea8", "#6b7785"]
    ky = col_y + 46
    for k, c in zip(keys, key_colors):
        s.rect(x3 + 12, ky - 12, 10, 10, fill=c, rx=2)
        s.text(x3 + 30, ky - 3, k, size=11.5, family=MONO, fill=INK)
        ky += 26
    s.text(x3 + 12, col_y + col_h - 30, "* required or prohibited", size=9.5, fill=MUTED)
    s.text(x3 + 12, col_y + col_h - 16, "  per event family", size=9.5, fill=MUTED)

    # Column 4: projections
    x4, w4 = 796, 178
    s.rect(x4, col_y, w4, col_h, fill=PANEL, stroke=PANEL_STROKE, sw=1.2, rx=10)
    s.text(x4 + 12, col_y + 24, "Projections out", size=13.5, weight="700")
    proj = [("CoT to TAK", "display"), ("JREAP track JSON", "loss register"),
            ("KLV tag dict", "sensor metadata"), ("MissionIntent", "deconfliction"),
            ("SAPIENT", "counter-UAS")]
    py = col_y + 46
    for name, note in proj:
        s.text(x4 + 12, py, name, size=11, family=MONO, fill=INK)
        s.text(x4 + 12, py + 12, note, size=9, fill=MUTED)
        py += 32
    s.text(x4 + 12, py + 4, "wire encodings differ:", size=9.5, fill=MUTED)
    s.text(x4 + 12, py + 17, "they decode value-identically", size=9.5, fill=MUTED)
    s.text(x4 + 12, col_y + col_h - 12, "lossy by declaration", size=10.5, fill=MUTED)

    ac = col_y + col_h / 2
    s.arrow(x1 + w1 + 4, ac, x2 - 4, ac, color=MUTED, sw=2.2, head=9)
    s.text((x1 + w1 + x2) / 2, col_y - 8, "adapt once", size=10, fill=MUTED, anchor="middle")
    s.arrow(x2 + w2 + 4, ac, x3 - 4, ac, color=MUTED, sw=2.2, head=9)
    s.arrow(x3 + w3 + 4, ac, x4 - 4, ac, color=MUTED, sw=2.2, head=9)
    s.text((x3 + w3 + x4) / 2, col_y - 8, "project many", size=10, fill=MUTED, anchor="middle")

    sizes_line = "  |  ".join(f"{k} {v} B" for k, v in obs_sizes.items() if v is not None)
    s.text(26, col_y + col_h + 40,
           "The canonical event stays the source of truth, linked to raw artifacts through lineage; a re-imported",
           size=12, fill=MUTED)
    s.text(26, col_y + col_h + 58,
           "projection is never equal to the original. The same H-profile RF observation measured on the wire:",
           size=12, fill=MUTED)
    s.text(26, col_y + col_h + 80, sizes_line, size=12.5, family=MONO, fill=INK)
    s.save(IMG_DIR / "e2-translation-pipeline.svg")
    print("  wrote e2-translation-pipeline.svg  " + sizes_line)


def figure_wire_matrix() -> None:
    specs = [
        {"key": "h_obs", "file": "zmeta-profile-H-examples.jsonl", "etype": "OBSERVATION_EVENT",
         "head": "Profile H", "sub": "RF observation"},
        {"key": "h_state", "file": "zmeta-profile-H-examples.jsonl", "etype": "STATE_EVENT",
         "head": "Profile H", "sub": "track state"},
        {"key": "l_state", "file": "zmeta-profile-L-examples.jsonl", "etype": "STATE_EVENT",
         "head": "Profile L", "sub": "track state"},
    ]
    rows: Dict[str, Dict[str, Optional[int]]] = {}
    for spec in specs:
        ev = next(e for e in load_jsonl(spec["file"]) if event_type(e) == spec["etype"])
        rows[spec["key"]] = encoding_sizes(ev)

    order = ["JSON", "CBOR", "Compact", "Protobuf"]
    colors = {"JSON": "#3a7ca5", "CBOR": "#2e8b6f", "Compact": "#c47f2a", "Protobuf": "#7a5ea8"}
    max_v = max(v for sizes in rows.values() for v in sizes.values() if v is not None)

    row_h, bar_h, top = 86, 14, 118
    s = Svg(1000, top + row_h * len(specs) + 114, "Measured wire size across encodings and profiles")
    s.text(26, 34, "What honesty costs on the wire, measured", size=21, weight="700")
    s.text(26, 56, "Shipped example events from this repo, encoded with the repo encoders at generation time.",
           size=13, fill=MUTED)
    lx = 26
    for name in order:
        s.rect(lx, 74, 12, 12, fill=colors[name], rx=3)
        s.text(lx + 18, 84, name, size=11.5, fill=INK)
        lx += 30 + 8.2 * len(name)

    chart_x, chart_w = 300, 620
    for i, spec in enumerate(specs):
        sizes = rows[spec["key"]]
        ry = top + i * row_h
        s.text(26, ry + 8, spec["head"], size=13.5, weight="700")
        s.text(26, ry + 26, spec["sub"], size=11.5, fill=MUTED)
        by = ry - 6
        for name in order:
            v = sizes.get(name)
            if v is None:
                s.text(chart_x, by + bar_h - 3, "refused (fail closed)", size=10.5, family=MONO, fill=FAMILY["COMMAND_EVENT"])
            else:
                bw = (v / max_v) * chart_w
                s.rect(chart_x, by, bw, bar_h, fill=colors[name], rx=3)
                s.text(chart_x + bw + 8, by + bar_h - 3, f"{v} B", size=10.5, family=MONO, fill=INK)
            by += bar_h + 4
        if i < len(specs) - 1:
            s.line(26, ry + row_h - 16, 974, ry + row_h - 16, stroke=GRID, sw=1)

    h_json = rows["h_state"].get("JSON")
    l_compact = rows["l_state"].get("Compact")
    cy = top + row_h * len(specs) + 6
    if h_json and l_compact:
        pct = round((1 - l_compact / h_json) * 100)
        s.text(26, cy,
               f"The Profile H track-state example costs {h_json} B as JSON; the Profile L track-state example",
               size=12.5, fill=INK)
        s.text(26, cy + 18,
               f"costs {l_compact} B as a compact packet, {pct}% less wire. The two are different example tracks:",
               size=12.5, fill=INK)
        s.text(26, cy + 36,
               "the Profile L example omits per-event timing quality and relies on periodic TIME_STATUS packets",
               size=12.5, fill=INK)
        s.text(26, cy + 54,
               "not shown here. Every packet still decodes to a canonical event that passes the same validation.",
               size=12.5, fill=INK)
    s.save(IMG_DIR / "e3-wire-matrix.svg")
    print(f"  wrote e3-wire-matrix.svg  H_json={h_json} L_compact={l_compact}")


def figure_proof_surface() -> None:
    def nlines(rel: str) -> int:
        return sum(1 for ln in (ROOT / rel).read_text(encoding="utf-8").splitlines()
                   if ln.strip() and not ln.strip().startswith("#"))

    fail_suites = [
        ("schema/policy must-fail", "conformance/must-fail.jsonl"),
        ("bad-event corpus", "conformance/bad-events/must-fail.jsonl"),
        ("compact decode negatives", "conformance/encoding-negative/compact-must-fail.jsonl"),
        ("protobuf decode negatives", "conformance/encoding-negative/protobuf-must-fail.jsonl"),
        ("gateway CLI negatives", "conformance/encoding-negative/gateway-must-fail.jsonl"),
        ("projection must-fail", "conformance/profile-projection/must-fail.jsonl"),
        ("precision must-fail", "conformance/profile-precision/must-fail.jsonl"),
    ]
    pass_suites = [
        ("schema/policy must-pass", "conformance/must-pass.jsonl"),
        ("projection must-pass", "conformance/profile-projection/must-pass.jsonl"),
        ("precision must-pass", "conformance/profile-precision/must-pass.jsonl"),
        ("adapter harness", "conformance/adapter-harness/must-pass.jsonl"),
    ]
    fails = [(name, nlines(rel)) for name, rel in fail_suites]
    passes = [(name, nlines(rel)) for name, rel in pass_suites]
    fail_total = sum(v for _, v in fails)
    pass_total = sum(v for _, v in passes)

    manifest_path = ROOT / "conformance" / "conformance_classes.yaml"
    class_counts = _count_after_marker(manifest_path, "class_records:", r"^    status: (\w+)\s*$")
    classes_total = sum(class_counts.values())
    implemented = class_counts.get("implemented", 0)
    non_claimable_statuses = _count_after_marker(
        manifest_path, "non_claimable_statuses:", r"^  - (\w+)\s*$")
    if not non_claimable_statuses:
        raise ValueError("non_claimable_statuses not found in the conformance manifest")
    non_claimable = sum(class_counts.get(status, 0) for status in non_claimable_statuses)

    gate_text = (ROOT / "tools" / "validate_conformance.py").read_text(encoding="utf-8")
    m = re.search(r"KERNEL_GATE_CHECKS = \((.*?)\n\)", gate_text, re.S)
    if not m:
        raise ValueError("KERNEL_GATE_CHECKS tuple not found in tools/validate_conformance.py")
    gate_checks = len(re.findall(r'^\s*"\w+",\s*$', m.group(1), re.M))
    if gate_checks == 0:
        raise ValueError("KERNEL_GATE_CHECKS parsed to zero entries")

    s = Svg(1000, 560, "The conformance proof surface, counted from the fixture suites")
    s.text(26, 34, "Conformance you can run yourself", size=21, weight="700")
    s.text(26, 56, "Every count below is read from the fixture files and the gate definition at generation time.",
           size=13, fill=MUTED)

    tiles = [
        (str(fail_total), "vectors that must be caught", "schema, policy, encoding, projection", FAMILY["COMMAND_EVENT"]),
        (str(pass_total), "fixtures that MUST PASS", "including the shared adapter harness", FAMILY["FUSION_EVENT"]),
        (f"{classes_total}", "conformance classes", f"{implemented} implemented, {non_claimable} non-claimable", FAMILY["OBSERVATION_EVENT"]),
        (str(gate_checks), "checks in the kernel gate", "one flag, run on every CI push", FAMILY["INFERENCE_EVENT"]),
    ]
    tx, tw = 26, 232
    for i, (big, label, sub, color) in enumerate(tiles):
        x = tx + i * (tw + 6)
        s.rect(x, 80, tw, 108, fill=PANEL, stroke=color, sw=2, rx=10)
        s.text(x + 16, 134, big, size=38, weight="700", fill=color)
        s.text(x + 16, 156, label, size=12, weight="700", fill=INK)
        s.text(x + 16, 174, sub, size=10.5, fill=MUTED)

    s.text(26, 226, "Where the must-fail vectors live", size=14, weight="700")
    bx, bw_max, by = 300, 560, 244
    fmax = max(v for _, v in fails)
    for name, v in fails:
        s.text(288, by + 11, name, size=11.5, fill=INK, anchor="end")
        bw = (v / fmax) * bw_max
        s.rect(bx, by, bw, 15, fill=FAMILY["COMMAND_EVENT"], rx=3)
        s.text(bx + bw + 8, by + 12, str(v), size=11, family=MONO, fill=INK)
        by += 25

    by += 14
    s.text(26, by, "What a claim is", size=14, weight="700")
    claim_lines = [
        "A conformance claim is an attestation: required fields, the full dependency closure,",
        "and a recorded pass for every required command of every claimed class. The validator",
        "refuses claims against non-claimable classes, unknown classes, and missing closure.",
        "It does not execute the tests; anyone can independently rerun the commands a claim names.",
    ]
    ly = by + 22
    for ln in claim_lines:
        s.text(26, ly, ln, size=12.5, fill=INK)
        ly += 19
    s.save(IMG_DIR / "e4-proof-surface.svg")
    print(f"  wrote e4-proof-surface.svg  must_fail={fail_total} must_pass={pass_total} classes={classes_total} gate={gate_checks}")


# --------------------------------------------------------------------------- #
# F-series: seeing the layer
# --------------------------------------------------------------------------- #
def _event_family_count() -> int:
    schema = json.loads((ROOT / "schema" / "zmeta-event-1.0.schema.json").read_text(encoding="utf-8"))
    enum = schema["$defs"]["event"]["properties"]["event_type"]["enum"]
    return len(enum)


def figure_thin_waist() -> None:
    sources = _ingress_names()
    egress_dirs = _adapter_dirs("egress")
    if set(egress_dirs) != set(EGRESS_DISPLAY):
        raise ValueError(f"egress dirs {egress_dirs} != pinned labels {sorted(EGRESS_DISPLAY)}")
    if set(EGRESS_ORDER) != set(EGRESS_DISPLAY):
        raise ValueError("EGRESS_ORDER and EGRESS_DISPLAY disagree")
    projections = [EGRESS_DISPLAY[d] for d in EGRESS_ORDER]
    families = _event_family_count()
    consumers = ["COP / map client", "TAK / ATAK", "fusion service", "GCS workflow",
                 "analytics", "AAR / replay store"]

    s = Svg(1000, 660, "The thin waist: replaceable products above and below one locked contract")
    s.text(26, 34, "One agreement, many replaceable parts", size=21, weight="700")
    s.text(26, 56, "Products above and below the waist are replaceable. The waist is the agreement that persists.",
           size=13, fill=MUTED)

    # Top band: producers.
    top_y, band_h = 84, 150
    s.rect(26, top_y, 948, band_h, fill=PANEL, stroke=PANEL_STROKE, sw=1.2, rx=10)
    s.text(40, top_y + 24, "Producers and their products", size=14, weight="700")
    s.text(974 - 8, top_y + 24, "replaceable", size=11, family=MONO,
           fill=FAMILY["STATE_EVENT"], anchor="end")
    cx, cy = 40, top_y + 44
    for name in sources + ["...any sensor with an adapter"]:
        w = 18 + 6.4 * len(name)
        if cx + w > 960:
            cx = 40
            cy += 32
        if cy + 24 > top_y + band_h - 8:
            raise ValueError("f1 top band overflow: too many producer chips for the panel")
        s.rect(cx, cy, w, 24, fill="#ffffff", stroke=PANEL_STROKE, sw=1, rx=12)
        s.text(cx + 9, cy + 16, name, size=10, family=MONO, fill=INK)
        cx += w + 8

    # Funnel into the waist.
    waist_y, waist_h, waist_w = 292, 96, 380
    wx = (1000 - waist_w) / 2
    s.poly([(150, top_y + band_h), (850, top_y + band_h), (wx + waist_w, waist_y), (wx, waist_y)],
           fill=PANEL, stroke="none")
    s.poly([(wx, waist_y + waist_h), (wx + waist_w, waist_y + waist_h), (850, 446), (150, 446)],
           fill=PANEL, stroke="none")

    s.rect(wx, waist_y, waist_w, waist_h, fill=FAMILY["FUSION_EVENT"], rx=10)
    s.text(500, waist_y + 28, "THE CONTRACT", size=15, weight="700", fill="#ffffff", anchor="middle")
    s.text(500, waist_y + 50, f"{families} event families | one envelope | v1.0 locked",
           size=12, family=MONO, fill="#ffffff", anchor="middle")
    s.text(500, waist_y + 70, "honest labels travel with the data", size=11, fill="#ffffff", anchor="middle")
    s.text(wx - 12, waist_y + 44, "the only thing every", size=10.5, fill=MUTED, anchor="end")
    s.text(wx - 12, waist_y + 58, "party must agree on", size=10.5, fill=MUTED, anchor="end")
    s.text(wx + waist_w + 12, waist_y + 44, "small enough to lock,", size=10.5, fill=MUTED)
    s.text(wx + waist_w + 12, waist_y + 58, "complete enough to build on", size=10.5, fill=MUTED)

    # Bottom band: consumers.
    bot_y = 446
    s.rect(26, bot_y, 948, 130, fill=PANEL, stroke=PANEL_STROKE, sw=1.2, rx=10)
    s.text(40, bot_y + 24, "Consumers and their products", size=14, weight="700")
    s.text(974 - 8, bot_y + 24, "replaceable", size=11, family=MONO,
           fill=FAMILY["STATE_EVENT"], anchor="end")
    cx, cy = 40, bot_y + 42
    for name in consumers + [f"{p} projection" for p in projections]:
        w = 18 + 6.4 * len(name)
        if cx + w > 960:
            cx = 40
            cy += 32
        if cy + 24 > bot_y + 130 - 8:
            raise ValueError("f1 bottom band overflow: too many consumer chips for the panel")
        s.rect(cx, cy, w, 24, fill="#ffffff", stroke=PANEL_STROKE, sw=1, rx=12)
        s.text(cx + 9, cy + 16, name, size=10, family=MONO, fill=INK)
        cx += w + 8

    s.text(26, 606, "Swap any product above or below and the rest still interoperate, because they never agreed with",
           size=12, fill=MUTED)
    s.text(26, 624, "each other; each agreed with the waist. Delete the waist and every pair needs its own bridge again.",
           size=12, fill=MUTED)
    s.save(IMG_DIR / "f1-thin-waist.svg")
    print(f"  wrote f1-thin-waist.svg  sources={len(sources)} families={families} projections={len(projections)}")


def figure_behind_the_icon() -> None:
    events = load_jsonl("zmeta-eo-chain-examples.jsonl")
    by_type = {event_type(e): e for e in events}
    if len(by_type) != len(events):
        raise ValueError("eo-chain fixture carries a duplicated event family; the figure assumes one per type")
    obs, inf = by_type["OBSERVATION_EVENT"], by_type["INFERENCE_EVENT"]
    fus, st = by_type["FUSION_EVENT"], by_type["STATE_EVENT"]
    obs_conf = _schema_stage_rules()["OBSERVATION_EVENT"]["confidence"]
    if obs_conf != "prohibited":
        raise ValueError(f"schema no longer prohibits observation confidence ({obs_conf}); update the figure text")

    track = st["payload"]["track_id"]
    stale_s = st["payload"]["valid_for_ms"] / 1000.0
    tq = st["payload"]["timing_quality"]

    s = Svg(1000, 700, "One display icon decomposed into the real event chain that carried it")
    s.text(26, 34, "Behind the icon", size=21, weight="700")
    s.text(26, 56, "Built from the shipped EO example events, genuine lineage ids included.",
           size=13, fill=MUTED)

    # Left: what the operator sees.
    mx, my, mw, mh = 26, 96, 300, 240
    s.rect(mx, my, mw, mh, fill=PANEL, stroke=PANEL_STROKE, sw=1.2, rx=10)
    s.text(mx + 12, my + 24, "What the operator sees", size=13.5, weight="700")
    for gx in range(1, 6):
        s.line(mx + gx * mw / 6, my + 36, mx + gx * mw / 6, my + mh - 46, stroke=GRID, sw=1)
    for gy in range(1, 4):
        s.line(mx + 10, my + 36 + gy * (mh - 82) / 4, mx + mw - 10, my + 36 + gy * (mh - 82) / 4, stroke=GRID, sw=1)
    ix, iy = mx + mw * 0.58, my + 110
    s.poly([(ix, iy - 12), (ix + 12, iy), (ix, iy + 12), (ix - 12, iy)], fill=FAMILY["STATE_EVENT"])
    s.text(ix - 18, iy - 4, track, size=10.5, family=MONO, fill=INK, anchor="end")
    s.text(ix - 18, iy + 10, f"conf {st['confidence']}  stale in {stale_s:.0f} s", size=9.5, family=MONO,
           fill=MUTED, anchor="end")
    s.text(mx + 12, my + mh - 24, "one icon on a map, in whichever", size=10.5, fill=MUTED)
    s.text(mx + 12, my + mh - 10, "COP a mission happens to run", size=10.5, fill=MUTED)

    s.text(mx, my + mh + 36, "The display is a projection.", size=12.5, weight="700", fill=INK)
    swap_lines = [
        "Replace the COP and nothing in the",
        "chain changes. The state event",
        "carries its immediate parent's id;",
        "a consumer holding the retained",
        "events can walk back to the source",
        "clip. Profile allowlists govern",
        "which families travel (contract 4.8).",
    ]
    ly = my + mh + 56
    for ln in swap_lines:
        s.text(mx, ly, ln, size=12, fill=INK)
        ly += 18

    # Right: the chain, state at top, observation at bottom.
    cards = [
        (st, "STATE_EVENT / TRACK_STATE", [
            f"track_id {track}   confidence {st['confidence']}",
            f"valid_for_ms {st['payload']['valid_for_ms']}   geo {st['payload']['geo']['lat']}, {st['payload']['geo']['lon']}",
            f"timing {tq['time_source']} {tq['sync_state']} est_error {tq['est_error_ms']} ms",
        ]),
        (fus, "FUSION_EVENT / TRACK_FUSION", [
            f"mints {fus['payload']['track_id']}   confidence {fus['confidence']}",
            f"members {len(fus['payload']['members'])}   stability {fus['payload']['stability']}",
            "the only stage allowed to create track identity",
        ]),
        (inf, "INFERENCE_EVENT / CLASSIFICATION", [
            f"claim \"{inf['payload']['claim']['label']}\"   confidence {inf['confidence']}",
            f"model {inf['payload']['model']['name']} {inf['payload']['model']['version']}",
            "a claim, never a track: it cannot mint identity",
        ]),
        (obs, "OBSERVATION_EVENT / EO", [
            f"frame {obs['payload']['features']['frame_id']}   stream {obs['payload']['features']['stream_id']}",
            f"confidence {obs_conf}: measurements are facts",
            f"data_ref {obs['payload']['data_ref']['ref_id']}",
        ]),
    ]
    rx, rw, card_h, gap = 380, 594, 108, 28
    ry = 96
    for i, (ev, header, lines) in enumerate(cards):
        color = FAMILY[event_type(ev)]
        y = ry + i * (card_h + gap)
        s.rect(rx, y, rw, card_h, fill=PANEL, stroke=color, sw=2, rx=10)
        s.rect(rx, y, rw, 8, fill=color, rx=4)
        s.rect(rx, y + 4, rw, 5, fill=color)
        s.text(rx + 14, y + 28, header, size=12.5, weight="700", fill=color)
        s.text(rx + rw - 12, y + 28, "..." + ev["event"]["event_id"][-12:], size=10, family=MONO,
               fill=MUTED, anchor="end")
        ty = y + 50
        for ln in lines:
            s.text(rx + 14, ty, ln, size=11, family=MONO, fill=INK)
            ty += 19
        if i < len(cards) - 1:
            ax = rx + rw / 2
            s.arrow(ax, y + card_h + gap - 4, ax, y + card_h + 4, color=MUTED, sw=2, head=8)
            parent_id = cards[i + 1][0]["event"]["event_id"]
            child_parents = ev.get("lineage", {}).get("based_on", [])
            if parent_id not in child_parents:
                raise ValueError(
                    f"{header} lineage {child_parents} does not cite the drawn parent {parent_id}")
            s.text(ax + 12, y + card_h + gap / 2 + 4, f"based_on ...{parent_id[-12:]}", size=9.5, family=MONO, fill=MUTED)

    s.arrow(rx - 6, ry + 40, ix + 26, iy, color=FAMILY["STATE_EVENT"], sw=2, head=9, dash="6 4")
    s.text(rx - 16, ry + 26, "projected to the display", size=10, fill=FAMILY["STATE_EVENT"], anchor="end")

    s.save(IMG_DIR / "f2-behind-the-icon.svg")
    print(f"  wrote f2-behind-the-icon.svg  track={track} chain={len(cards)}")


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
        figure_authority_stack,
        figure_promotion_chain,
        figure_true_today,
        figure_adapt_once,
        figure_translation_pipeline,
        figure_wire_matrix,
        figure_proof_surface,
        figure_thin_waist,
        figure_behind_the_icon,
    ):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - keep generating remaining figures
            print(f"  ERROR in {fn.__name__}: {exc}")
    print("Done.")


if __name__ == "__main__":
    main()
