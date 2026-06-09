import argparse
import json
import sys
from pathlib import Path


DECISION_RANKS = {
    "IGNORED": 0,
    "WARN_ACCEPT": 1,
    "DEGRADED_ACCEPT": 2,
    "QUARANTINE_ACCEPT": 3,
    "REJECTED": 4,
}

MAX_RISK_RANKS = {
    "clean": 0,
    "warn": 1,
    "degrade": 2,
    "quarantine": 3,
    "rejected": 4,
}

PRESETS = {
    "display": {
        "description": "Allow data usable for operator display/local awareness, including quarantined display paths.",
        "max_risk": "quarantine",
        "require_uses": ["DISPLAY"],
    },
    "fusion": {
        "description": "Allow clean or warning-labeled data explicitly usable as fusion input.",
        "max_risk": "warn",
        "require_uses": ["FUSION_INPUT"],
    },
    "state": {
        "description": "Allow clean or warning-labeled data explicitly usable for state update.",
        "max_risk": "warn",
        "require_uses": ["STATE_UPDATE"],
    },
    "command": {
        "description": "Allow only clean data for command-basis use.",
        "max_risk": "clean",
        "require_uses": ["COMMAND_BASIS"],
    },
    "autonomy": {
        "description": "Allow only clean data for autonomy tasking.",
        "max_risk": "clean",
        "require_uses": ["AUTONOMY_TASKING"],
    },
    "aar": {
        "description": "Allow data usable for after-action review, including quarantine/AAR paths.",
        "max_risk": "quarantine",
        "require_uses": ["AAR_ONLY"],
    },
    "audit": {
        "description": "Pass clean, accepted-risk, quarantine, and rejected diagnostic events for audit review.",
        "max_risk": "rejected",
        "require_uses": [],
    },
}

RISK_KEYS = {
    "risk_dimension",
    "reason_code",
    "policy_mode",
    "policy_decision",
    "policy_ref",
    "allowed_uses",
    "prohibited_uses",
    "effects",
}


def _list_values(value):
    if isinstance(value, list):
        return [str(item).strip().upper() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip().upper()]
    return []


def _decision(value):
    text = str(value or "UNKNOWN").strip().upper()
    return text if text else "UNKNOWN"


def _risk_dimension(value):
    text = str(value or "unknown").strip().lower()
    return text if text else "unknown"


def _is_diagnostic(event):
    if not isinstance(event, dict):
        return False
    event_block = event.get("event", {})
    payload = event.get("payload", {})
    return (
        isinstance(event_block, dict)
        and isinstance(payload, dict)
        and event_block.get("event_type") == "SYSTEM_EVENT"
        and payload.get("system_type") == "SCHEMA_VIOLATION"
    )


def _normalize_record(record, source):
    result = {}
    for key in RISK_KEYS:
        if key in record:
            result[key] = record[key]
    result["source"] = source
    if "policy_decision" in result:
        result["policy_decision"] = _decision(result["policy_decision"])
    if "risk_dimension" in result:
        result["risk_dimension"] = _risk_dimension(result["risk_dimension"])
    if "allowed_uses" in result:
        result["allowed_uses"] = _list_values(result["allowed_uses"])
    if "prohibited_uses" in result:
        result["prohibited_uses"] = _list_values(result["prohibited_uses"])
    return result


def risk_records(event):
    if not isinstance(event, dict):
        return []
    records = []
    payload = event.get("payload", {})
    if isinstance(payload, dict):
        extensions = payload.get("extensions", {})
        if isinstance(extensions, dict):
            event_records = extensions.get("risk_adjudication", [])
            if isinstance(event_records, list):
                for record in event_records:
                    if isinstance(record, dict):
                        records.append(_normalize_record(record, "event"))

        if _is_diagnostic(event):
            metrics = payload.get("metrics", {})
            if isinstance(metrics, dict) and any(key in metrics for key in RISK_KEYS):
                records.append(_normalize_record(metrics, "diagnostic"))
    return records


def _decision_rank(decision):
    return DECISION_RANKS.get(_decision(decision), max(DECISION_RANKS.values()))


def _apply_preset(args):
    preset = PRESETS.get(args.preset or "")
    max_risk = args.max_risk
    required_uses = list(args.require_use or [])
    if preset:
        if max_risk is None:
            max_risk = preset["max_risk"]
        required_uses = list(preset["require_uses"]) + required_uses
    if max_risk is None:
        max_risk = "quarantine"
    return max_risk, [use.strip().upper() for use in required_uses if use.strip()]


def evaluate_event(
    event,
    *,
    max_risk="quarantine",
    require_uses=None,
    allow_decisions=None,
    deny_decisions=None,
    allow_dimensions=None,
    deny_dimensions=None,
    require_risk=False,
    drop_diagnostics=False,
    permit_unlabeled_use=False,
):
    records = risk_records(event)
    reasons = []

    if drop_diagnostics and _is_diagnostic(event):
        reasons.append("diagnostic_event")

    if require_risk and not records:
        reasons.append("missing_risk_label")

    max_rank = MAX_RISK_RANKS[max_risk]
    allowed_decisions = {_decision(item) for item in allow_decisions or []}
    denied_decisions = {_decision(item) for item in deny_decisions or []}
    allowed_dimensions = {_risk_dimension(item) for item in allow_dimensions or []}
    denied_dimensions = {_risk_dimension(item) for item in deny_dimensions or []}
    required_uses = [str(item).strip().upper() for item in require_uses or [] if str(item).strip()]

    for idx, record in enumerate(records):
        decision = _decision(record.get("policy_decision"))
        decision_rank = _decision_rank(decision)
        dimension = _risk_dimension(record.get("risk_dimension"))
        prefix = f"risk[{idx}]"

        if decision_rank > max_rank:
            reasons.append(f"{prefix}.risk_exceeds_{max_risk}:{decision}")
        if allowed_decisions and decision not in allowed_decisions:
            reasons.append(f"{prefix}.decision_not_allowed:{decision}")
        if decision in denied_decisions:
            reasons.append(f"{prefix}.decision_denied:{decision}")
        if allowed_dimensions and dimension not in allowed_dimensions:
            reasons.append(f"{prefix}.dimension_not_allowed:{dimension}")
        if dimension in denied_dimensions:
            reasons.append(f"{prefix}.dimension_denied:{dimension}")

        allowed_uses = set(_list_values(record.get("allowed_uses")))
        prohibited_uses = set(_list_values(record.get("prohibited_uses")))
        for use in required_uses:
            if use in prohibited_uses:
                reasons.append(f"{prefix}.use_prohibited:{use}")
            elif allowed_uses and use not in allowed_uses:
                reasons.append(f"{prefix}.use_not_allowed:{use}")
            elif not allowed_uses and not permit_unlabeled_use:
                reasons.append(f"{prefix}.use_not_explicitly_allowed:{use}")

    return {
        "passed": not reasons,
        "reasons": reasons,
        "risk_records": records,
    }


def _iter_jsonl(path):
    handle = sys.stdin if path == "-" else Path(path).open("r", encoding="utf-8")
    close = handle is not sys.stdin
    try:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc.msg}") from exc
            yield line_no, event
    finally:
        if close:
            handle.close()


def _open_output(path):
    if path == "-":
        return sys.stdout, False
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target.open("w", encoding="utf-8"), True


def _validate_distinct_paths(args):
    paths = {}
    for label, value in (
        ("input", args.input),
        ("output", args.output),
        ("dropped-output", args.dropped_output),
    ):
        if not value or value == "-":
            continue
        resolved = Path(value).expanduser().resolve(strict=False)
        if resolved in paths:
            raise ValueError(
                f"{label} path must differ from {paths[resolved]} path: {resolved}"
            )
        paths[resolved] = label


def _write_jsonl(handle, value):
    handle.write(json.dumps(value, separators=(",", ":"), ensure_ascii=True) + "\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Filter ZMeta JSONL streams using explicit risk labels."
    )
    parser.add_argument("--input", "-i", default="-", help="Input JSONL path or '-' for stdin.")
    parser.add_argument("--output", "-o", default="-", help="Passed-event JSONL path or '-' for stdout.")
    parser.add_argument(
        "--dropped-output",
        help="Optional JSONL sidecar for dropped events and reasons.",
    )
    parser.add_argument("--preset", choices=sorted(PRESETS), help="Operator risk preset.")
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="Print available presets and exit.",
    )
    parser.add_argument(
        "--max-risk",
        choices=sorted(MAX_RISK_RANKS),
        help="Maximum accepted risk level. Default is preset value or quarantine.",
    )
    parser.add_argument(
        "--require-use",
        action="append",
        default=[],
        help="Require every risk label to explicitly allow this use and not prohibit it. Repeatable.",
    )
    parser.add_argument(
        "--permit-unlabeled-use",
        action="store_true",
        help="With --require-use, allow risk records that omit allowed_uses/prohibited_uses.",
    )
    parser.add_argument(
        "--allow-decision",
        action="append",
        default=[],
        help="Allow only these policy_decision values. Repeatable.",
    )
    parser.add_argument(
        "--deny-decision",
        action="append",
        default=[],
        help="Drop these policy_decision values. Repeatable.",
    )
    parser.add_argument(
        "--allow-dimension",
        action="append",
        default=[],
        help="Allow only these risk_dimension values. Repeatable.",
    )
    parser.add_argument(
        "--deny-dimension",
        action="append",
        default=[],
        help="Drop these risk_dimension values. Repeatable.",
    )
    parser.add_argument(
        "--require-risk",
        action="store_true",
        help="Drop events with no risk labels.",
    )
    parser.add_argument(
        "--drop-diagnostics",
        action="store_true",
        help="Drop SYSTEM_EVENT/SCHEMA_VIOLATION diagnostic events.",
    )
    parser.add_argument(
        "--fail-on-drop",
        action="store_true",
        help="Exit non-zero when any event is dropped.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress summary output.")
    return parser.parse_args()


def run(args):
    if args.list_presets:
        for name in sorted(PRESETS):
            preset = PRESETS[name]
            uses = ",".join(preset["require_uses"]) or "-"
            print(f"{name}: max_risk={preset['max_risk']} require_uses={uses} - {preset['description']}")
        return 0

    _validate_distinct_paths(args)

    max_risk, required_uses = _apply_preset(args)
    passed = 0
    dropped = 0
    total = 0

    output, close_output = _open_output(args.output)
    dropped_output = None
    close_dropped = False
    if args.dropped_output:
        dropped_output, close_dropped = _open_output(args.dropped_output)

    try:
        for line_no, event in _iter_jsonl(args.input):
            total += 1
            result = evaluate_event(
                event,
                max_risk=max_risk,
                require_uses=required_uses,
                allow_decisions=args.allow_decision,
                deny_decisions=args.deny_decision,
                allow_dimensions=args.allow_dimension,
                deny_dimensions=args.deny_dimension,
                require_risk=args.require_risk,
                drop_diagnostics=args.drop_diagnostics,
                permit_unlabeled_use=args.permit_unlabeled_use,
            )
            if result["passed"]:
                passed += 1
                _write_jsonl(output, event)
            else:
                dropped += 1
                if dropped_output:
                    _write_jsonl(
                        dropped_output,
                        {
                            "line": line_no,
                            "decision": "drop",
                            "reasons": result["reasons"],
                            "risk_records": result["risk_records"],
                            "event": event,
                        },
                    )
    finally:
        if close_output:
            output.close()
        if close_dropped:
            dropped_output.close()

    if not args.quiet:
        print(
            f"risk filter ok total={total} passed={passed} dropped={dropped} "
            f"preset={args.preset or 'custom'} max_risk={max_risk}",
            file=sys.stderr,
        )
    return 1 if args.fail_on_drop and dropped else 0


def main():
    args = parse_args()
    try:
        raise SystemExit(run(args))
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
