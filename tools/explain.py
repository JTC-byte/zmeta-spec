"""Run validate.py, then add structural advisory guidance to whatever failed.

Non-normative. Compliance is defined by the semantic contract and the schema;
nothing this script prints changes what conforms. validate.py already prints
per-code remediation guidance inline; this tool adds the structural layer on
top: rules that detect the shape of the event rather than the violation code,
so they still work on dialect input where the raw validator output degrades
to a whole-event dump. Rules live in tools/validation_guidance.yaml under
`structural_rules`, and every rule points back at the primary source because
the hint is a signpost and the contract is the authority.

Usage:
    python tools/explain.py --file <events.jsonl> --profile H [--strict]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GUIDANCE = ROOT / "tools" / "validation_guidance.yaml"
KNOWN_VERSIONS = {"1.0", "1.1.0"}
# Every key a rule may use under `detect:`; the fixture asserts the file stays
# inside this set so a mistyped key cannot silently disable a rule.
HANDLED_DETECT_KEYS = {
    "event_type", "zmeta_version", "zmeta_version_not", "modality", "has_path",
    "absent_path", "any_path", "absent_any_path", "absent_all_paths",
    "negative_alt_m", "naive_timestamp", "unknown_version",
}
TIMESTAMP_KEYS = {"ts", "observed_at", "received_at", "last_sync_ts", "last_seen_ts", "t_start", "t_end"}


def dig(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def walk(node, fn):
    if isinstance(node, dict):
        for k, v in node.items():
            fn(k, v)
            walk(v, fn)
    elif isinstance(node, list):
        for v in node:
            walk(v, fn)


def has_negative_alt(event):
    found = []

    def check(k, v):
        if k == "alt_m" and isinstance(v, (int, float)) and v < 0:
            found.append(v)

    walk(event, check)
    return bool(found)


def has_naive_timestamp(event):
    found = []

    def check(k, v):
        if k in TIMESTAMP_KEYS and isinstance(v, str) and "T" in v:
            if not (v.endswith("Z") or "+" in v[10:]):
                found.append(v)

    walk(event, check)
    return bool(found)


def matches(rule, event):
    d = rule.get("detect", {}) or {}
    etype = (event.get("event") or {}).get("event_type")

    want = d.get("event_type")
    if want is not None:
        allowed = want if isinstance(want, list) else [want]
        if etype not in allowed:
            return False

    # Lane gates. `zmeta_version` requires an exact lane; `zmeta_version_not`
    # excludes one, so a rule about 1.1.0 vocabulary still fires on dialect
    # input that declares no version (2026-09-10 acoustic evidence).
    if "zmeta_version" in d and event.get("zmeta_version") != d["zmeta_version"]:
        return False
    if "zmeta_version_not" in d and event.get("zmeta_version") == d["zmeta_version_not"]:
        return False

    if "modality" in d:
        mod, _ = dig(event, "payload.modality")
        if mod != d["modality"]:
            return False

    if "has_path" in d and not dig(event, d["has_path"])[1]:
        return False

    if "absent_path" in d and dig(event, d["absent_path"])[1]:
        return False

    if "any_path" in d and not any(dig(event, p)[1] for p in d["any_path"]):
        return False

    if "absent_any_path" in d and not any(not dig(event, p)[1] for p in d["absent_any_path"]):
        return False

    if "absent_all_paths" in d and any(dig(event, p)[1] for p in d["absent_all_paths"]):
        return False

    if d.get("negative_alt_m") and not has_negative_alt(event):
        return False

    if d.get("naive_timestamp") and not has_naive_timestamp(event):
        return False

    if d.get("unknown_version") and event.get("zmeta_version") in KNOWN_VERSIONS:
        return False

    return True


def wrap(text, width=74, indent="     "):
    words = " ".join((text or "").split())
    out, line = [], ""
    for w in words.split(" "):
        if len(line) + len(w) + 1 > width:
            out.append(indent + line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(indent + line)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--profile", default="H", choices=["L", "M", "H"])
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    cmd = [sys.executable, str(ROOT / "tools" / "validate.py"), "--file", args.file, "--profile", args.profile]
    if args.strict:
        cmd.append("--strict")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    print(out.rstrip())

    if "failed=0" in out and "FAIL" not in out:
        return proc.returncode

    rules = yaml.safe_load(GUIDANCE.read_text(encoding="utf-8")).get("structural_rules", [])

    events = []
    with open(args.file, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    fired = []
    for ev in events:
        eid = (ev.get("event") or {}).get("event_id", "UNKNOWN")
        for r in rules:
            if matches(r, ev):
                fired.append((eid, r))

    if not fired:
        return proc.returncode

    print()
    print("-" * 78)
    print("GUIDANCE (advisory, non-normative - the contract and schema govern)")
    print("-" * 78)
    for eid, r in fired:
        tag = r.get("severity_of_hint", "likely fix").upper()
        print(f"\n  [{tag}] {r['id']}   event_id={eid}")
        print(wrap(r["hint"]))
        print(f"     see: {r['see']}")
    print()
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
