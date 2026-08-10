import json
import math
from collections import OrderedDict, deque
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from decimal import Decimal
from fnmatch import fnmatchcase
from datetime import datetime, timezone
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


# Bound on the command-evidence index a ValidationState keeps (event_id ->
# event_type + adjudicated prohibited uses). The index exists so a
# COMMAND_EVENT's lineage citations can be checked against what the gateway
# actually saw upstream; the index evicts oldest-first at this cap and an
# evicted parent resolves as UNRESOLVED — the honest disposition, never a
# silent pass (policy/command-evidence.yaml#evidence_index_max_entries).
#
# Scope of the bound, stated honestly (pre-cut review): this caps THIS
# index only. `ValidationState.events` in the same object is a plain dict
# that retains full events and is not pruned, so a long-lived gateway
# process is not bounded overall by this constant — capping the evidence
# summary is a targeted limit on the new surface, not a memory guarantee
# for the whole validation state. Bounding `events` is a separate,
# behavior-visible change (dedupe and lineage resolution read it) and is
# recorded as a register candidate rather than smuggled in here.
DEFAULT_COMMAND_EVIDENCE_INDEX_MAX_ENTRIES = 4096

# Internal marker (never policy or event vocabulary) recorded when a
# parent's risk_adjudication is present but not the documented list shape,
# so its labels cannot be read. Citations of such a parent take the
# prohibited path: an unreadable label set may prohibit command basis, and
# reading it as "says nothing" would be the exact laundering the
# command-evidence check exists to prevent.
_UNADJUDICABLE_RISK_SHAPE = "UNADJUDICABLE_RISK_SHAPE"


class ValidationState:
    def __init__(self, command_evidence_max_entries=None):
        self.timing_sources = set()
        self.latest_timing = {}
        self.events = {}
        self.event_ids = set()
        self.command_task_ids = set()
        self.task_ack_keys = set()
        try:
            cap = int(command_evidence_max_entries)
        except (TypeError, ValueError):
            cap = 0
        if cap <= 0:
            # A mangled cap must not silently disable resolution (everything
            # would report unresolved) or unbound the index; fall back loud
            # in documentation, quiet in behavior: the shipped default.
            cap = DEFAULT_COMMAND_EVIDENCE_INDEX_MAX_ENTRIES
        self.command_evidence_max_entries = cap
        self.command_evidence = OrderedDict()

    def has_timing(self, event):
        return self.get_timing(event)[1] is not None

    def get_timing(self, event):
        for key in _source_keys(event):
            if key in self.latest_timing:
                return key, self.latest_timing[key]
        return None, None

    def record(self, event):
        self.record_timing(event)
        event_block = event.get("event", {}) if isinstance(event, dict) else {}
        payload = event.get("payload", {}) if isinstance(event, dict) else {}
        event_type = event_block.get("event_type")
        system_type = payload.get("system_type") if isinstance(payload, dict) else None
        event_id = event_block.get("event_id")
        if event_id:
            self.event_ids.add(event_id)
            self.events[event_id] = {
                "event_type": event_type,
                "event_subtype": event_block.get("event_subtype"),
                "event": event,
            }
            self._record_command_evidence(event_id, event_type, payload)
        if event_type == "COMMAND_EVENT" and isinstance(payload, dict):
            task_id = payload.get("task_id")
            if task_id:
                self.command_task_ids.add(task_id)
        if event_type == "SYSTEM_EVENT" and system_type == "TASK_ACK" and isinstance(payload, dict):
            metrics = payload.get("metrics", {})
            if isinstance(metrics, dict):
                key = (metrics.get("task_id"), metrics.get("original_event_id"), payload.get("state"))
                if all(key):
                    self.task_ack_keys.add(key)

    def get_event(self, event_id):
        return self.events.get(event_id)

    def _record_command_evidence(self, event_id, event_type, payload):
        """Record the bounded summary the command-evidence check reads.

        Only what the check needs is kept: the parent's event_type (can it
        motivate a command at all?) and the use tokens its risk_adjudication
        records prohibit, with the reason codes that carried them (so a
        refusal can name the upstream adjudication it is honoring). The full
        token set is stored rather than a pre-filtered command subset, so a
        policy change to command_basis_use_tokens applies honestly to
        evidence recorded before it.
        """
        prohibited = set()
        reason_codes = set()
        if isinstance(payload, dict):
            extensions = payload.get("extensions")
            if isinstance(extensions, dict):
                records = extensions.get("risk_adjudication")
                if isinstance(records, list):
                    for record in records:
                        if not isinstance(record, dict):
                            continue
                        tokens = _list_values(record.get("prohibited_uses"))
                        if not tokens:
                            continue
                        prohibited.update(token.upper() for token in tokens)
                        code = record.get("reason_code")
                        if isinstance(code, str) and code.strip():
                            reason_codes.add(code.strip())
                elif records is not None:
                    # Present but not the documented list shape: the labels
                    # cannot be read, so the evidence is UNADJUDICABLE, not
                    # unlabeled. Recording it as clean would drop a
                    # prohibition the producer may well have expressed
                    # (pre-cut review). The sentinel makes every citation of
                    # this parent take the prohibited path rather than pass.
                    prohibited.add(_UNADJUDICABLE_RISK_SHAPE)
        prior = self.command_evidence.get(event_id)
        if isinstance(prior, dict):
            # NEVER let a re-send downgrade what this gateway already
            # observed (pre-cut review): duplicate suppression is
            # time-bounded (EventDedupeCache TTL) while this index is only
            # cardinality-bounded, so a clean copy of an already-seen
            # event_id arriving after the dedupe window used to erase the
            # recorded prohibition and let a citing command forward clean.
            # Labels are sticky and unioned: a prohibition observed once
            # stays observed for as long as the entry lives.
            prohibited.update(prior.get("prohibited_uses") or ())
            reason_codes.update(prior.get("risk_reason_codes") or ())
        self.command_evidence[event_id] = {
            "event_type": event_type,
            "prohibited_uses": tuple(sorted(prohibited)),
            "risk_reason_codes": tuple(sorted(reason_codes)),
        }
        self.command_evidence.move_to_end(event_id)
        while len(self.command_evidence) > self.command_evidence_max_entries:
            self.command_evidence.popitem(last=False)

    def record_timing(self, event):
        event_block = event.get("event", {}) if isinstance(event, dict) else {}
        payload = event.get("payload", {}) if isinstance(event, dict) else {}
        event_type = event_block.get("event_type")
        system_type = payload.get("system_type") if isinstance(payload, dict) else None
        if event_type == "SYSTEM_EVENT" and system_type == "TIME_STATUS":
            metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
            if isinstance(metrics, dict):
                status = dict(metrics)
                status["_event_ts"] = event_block.get("ts")
                if _parse_utc_z(status["_event_ts"]) is None:
                    # A TIME_STATUS whose own ts cannot be parsed to an
                    # aware instant cannot honestly stand as a source's
                    # "latest": it cannot be ordered against anything, and
                    # recording it converted the hard TIMING_STATUS_MISSING
                    # refusal into a silent clean pass for that source
                    # (attack finding, 2026-07-27). Not recording keeps the
                    # source on the existing loud MISSING disposition - no
                    # new vocabulary, no silent participation.
                    return
                for key in _source_keys(event):
                    self.timing_sources.add(key)
                    current = self.latest_timing.get(key)
                    if _should_replace_timing_status(current, status):
                        self.latest_timing[key] = dict(status)


def load_schema(schema_path):
    schema_path = Path(schema_path)
    with open(schema_path, "r", encoding="utf-8") as handle:
        schema = json.load(handle)

    resources = []
    for candidate in sorted(schema_path.parent.glob("*.schema.json")):
        try:
            with open(candidate, "r", encoding="utf-8") as handle:
                candidate_schema = json.load(handle)
        except json.JSONDecodeError:
            continue
        schema_id = candidate_schema.get("$id")
        if schema_id:
            resources.append(
                (
                    schema_id,
                    Resource.from_contents(candidate_schema, default_specification=DRAFT202012),
                )
            )

    registry = Registry().with_resources(resources)
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def load_policy(policy_dir):
    policy_dir = Path(policy_dir)
    roles_cfg = load_yaml(policy_dir / "roles.yaml")
    profiles_cfg = load_yaml(policy_dir / "profiles.yaml")
    semantics_cfg = load_yaml(policy_dir / "semantics.yaml")
    routing_cfg = load_yaml(policy_dir / "routing.yaml")
    producer_authority_path = policy_dir / "producer-authority.yaml"
    producer_authority_cfg = (
        load_yaml(producer_authority_path) if producer_authority_path.exists() else {}
    )
    lineage_path = policy_dir / "lineage.yaml"
    lineage_cfg = load_yaml(lineage_path) if lineage_path.exists() else {}
    timing_freshness_path = policy_dir / "timing-freshness.yaml"
    timing_freshness_cfg = (
        load_yaml(timing_freshness_path) if timing_freshness_path.exists() else {}
    )
    command_evidence_path = policy_dir / "command-evidence.yaml"
    command_evidence_cfg = (
        load_yaml(command_evidence_path) if command_evidence_path.exists() else {}
    )
    codes_cfg = load_yaml(policy_dir / "violation-codes.yaml")
    severity_map = {}
    for item in codes_cfg.get("violation_codes", []):
        if isinstance(item, dict) and "code" in item:
            severity_map[item["code"]] = item.get("severity", "fail")

    return {
        "roles": roles_cfg.get("roles", {}),
        "deny": roles_cfg.get("deny", []),
        "profiles": profiles_cfg.get("profiles", {}),
        "semantics": semantics_cfg.get("semantics", {}),
        "routing": routing_cfg.get("routing", {}),
        "producer_authority": producer_authority_cfg.get("producer_authority", producer_authority_cfg),
        "lineage": lineage_cfg.get("lineage", lineage_cfg),
        "timing_freshness": timing_freshness_cfg.get("timing_freshness", timing_freshness_cfg),
        "command_evidence": command_evidence_cfg.get("command_evidence", command_evidence_cfg),
        "violation_codes": codes_cfg.get("violation_codes", []),
        "violation_severities": severity_map,
    }


def _resolve_severity(code, severity_map):
    if not severity_map:
        return "fail"
    return severity_map.get(code, "fail")


def _violation(code, message, details=None, severity_map=None, severity=None):
    return {
        "code": code,
        "message": message,
        "severity": severity or _resolve_severity(code, severity_map),
        "details": details or {},
    }


_POLICY_DECISION_BY_MODE = {
    "reject": "REJECTED",
    "warn": "WARN_ACCEPT",
    "degrade": "DEGRADED_ACCEPT",
    "quarantine": "QUARANTINE_ACCEPT",
    "ignore": "IGNORED",
}


def _policy_decision_for_mode(mode):
    return _POLICY_DECISION_BY_MODE.get(str(mode or "").strip().lower(), "REJECTED")


def _risk_use_limits(policy, mode):
    if not isinstance(policy, dict):
        return {}
    configured = policy.get("use_limits", {})
    if not isinstance(configured, dict):
        return {}
    limits = configured.get(str(mode or "").strip().lower(), {})
    return limits if isinstance(limits, dict) else {}


def _risk_details(
    details,
    risk_dimension,
    mode,
    policy=None,
    policy_ref=None,
    policy_decision=None,
):
    result = dict(details or {})
    mode = str(mode or "reject").strip().lower()
    result["risk_dimension"] = risk_dimension
    result["policy_mode"] = mode
    result["policy_decision"] = policy_decision or _policy_decision_for_mode(mode)
    if policy_ref:
        result["policy_ref"] = policy_ref

    limits = _risk_use_limits(policy, mode)
    for key in ("allowed_uses", "prohibited_uses"):
        if key in result:
            continue
        values = _list_values(limits.get(key))
        if values:
            result[key] = values
    return result


def _append_risk_adjudication(event, violation, effects=None):
    if not isinstance(event, dict) or not isinstance(violation, dict):
        return False
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return False
    details = violation.get("details", {})
    if not isinstance(details, dict):
        return False
    risk_dimension = details.get("risk_dimension")
    policy_decision = details.get("policy_decision")
    if not risk_dimension or not policy_decision:
        return False

    extensions = payload.get("extensions")
    if not isinstance(extensions, dict):
        extensions = {}
        payload["extensions"] = extensions
    records = extensions.get("risk_adjudication")
    if not isinstance(records, list):
        records = []
        extensions["risk_adjudication"] = records

    record = {
        "risk_dimension": risk_dimension,
        "reason_code": violation.get("code"),
        "policy_mode": details.get("policy_mode"),
        "policy_decision": policy_decision,
    }
    for key in (
        "policy_ref",
        "profile",
        "producer",
        "event_type",
        "event_subtype",
        "allowed_uses",
        "prohibited_uses",
    ):
        value = details.get(key)
        if value is not None:
            record[key] = value
    configured_effects = details.get("effects")
    if isinstance(configured_effects, dict):
        record["effects"] = dict(configured_effects)
    if isinstance(effects, dict):
        record["effects"] = {**record.get("effects", {}), **effects}

    records.append(record)
    return True


def _source_keys(event):
    source = event.get("source", {}) if isinstance(event, dict) else {}
    platform_id = str(source.get("platform_id") or "UNKNOWN")
    producer = str(source.get("producer") or "UNKNOWN")
    sensor_id = source.get("sensor_id")
    node_role = source.get("node_role")

    keys = []
    if sensor_id:
        keys.append((platform_id, producer, str(sensor_id)))
    keys.append((platform_id, producer))
    if node_role:
        # Legacy compatibility for existing gateway failure-mode lookups.
        keys.append((platform_id, producer, str(node_role)))

    unique = []
    for key in keys:
        if key not in unique:
            unique.append(key)
    return unique


def _source_key(event):
    return _source_keys(event)[0]


def _resolve_path(value, dotted_path):
    target = value
    for part in str(dotted_path).split("."):
        if not part:
            continue
        if not isinstance(target, dict):
            return None
        target = target.get(part)
    return target


def _normalize_key(value):
    # Normalize a key for denylist comparison: strip surrounding whitespace and
    # casefold, so whitespace- or case-padded copies of a reserved name (e.g.
    # "features ", "\tRAW_FEATURES") cannot slip past the semantic denylist that
    # the schema pins only for the exact bytes. Both the payload key and the
    # forbidden set are normalized the same way for a symmetric compare.
    return str(value).strip().casefold()


# Leaf types that are text, not containers. They are Sequences, so they have
# to be excluded before the Sequence branch or every string becomes a walk
# over its own characters.
_TEXT_LEAF_TYPES = (str, bytes, bytearray)


def _is_non_finite_number(value):
    # Only a float or a Decimal can carry NaN/Infinity. A Python int is always
    # an exact finite value and is deliberately NOT converted: math.isfinite()
    # on an int outside float64 range raises OverflowError, which would trade
    # this laundering defect for a crash (the arm that bit the SAPIENT
    # adapter's _is_number in the same audit).
    #
    # Decimal is here because it is reachable from the wire, not for
    # completeness: cbor2 decodes CBOR tag 5 (bigfloat) with a NaN mantissa
    # into Decimal('NaN'), and `isinstance(Decimal('NaN'), float)` is False,
    # so the float-only leaf test walked straight past it and the event was
    # forwarded (R1-11 residual against A-01).
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, Decimal):
        return not value.is_finite()
    return False


def _is_traversable(value):
    if isinstance(value, _TEXT_LEAF_TYPES):
        return False
    if isinstance(value, (dict, list, tuple)):
        return True
    if isinstance(value, (Mapping, AbstractSet, Sequence)):
        return True
    return hasattr(value, "tag") and hasattr(value, "value")


def _child_entries(current):
    """(label, child) for every value reachable one step from `current`.

    Container coverage is by ABSTRACT type, not by a list of concrete ones.
    The decoders this gateway supports do not produce only dict/list. cbor2 -
    the fallback backend `gateway._decode_cbor` explicitly supports when
    zmeta_cbor is absent - decodes CBOR tag 258 into a `set`, a map used as a
    map key into a `cbor2.frozendict` (a Mapping that is NOT a dict), and any
    tag it does not recognise into a `CBORTag` whose `.value` holds fully
    decoded content that still goes back out on the wire. A
    `dict` / `(list, tuple)` dispatch misses all three, so a NaN inside any of
    them passed the whole kernel and reached the CBOR wire with
    strict_validation=True (R1-11 residual against A-01).

    Mapping keys are yielded as children too, labelled `<key>`, and only when
    they are not `str`: a CBOR map key can itself be a frozendict or a
    frozenset holding a non-finite value, while a str key never can and
    yielding those would double the node count of every JSON event.

    Concrete dict/list are matched first: this runs on every event, and the
    abstract isinstance checks are measurably slower than the exact ones.
    """
    if isinstance(current, dict):
        return _mapping_entries(current.items())
    if isinstance(current, list):
        return [(str(idx), item) for idx, item in enumerate(current)]
    if isinstance(current, _TEXT_LEAF_TYPES):
        return []
    if isinstance(current, Mapping):
        return _mapping_entries(current.items())
    if isinstance(current, AbstractSet):
        # Set iteration order is arbitrary, so an index would be a path the
        # operator cannot re-derive. `<set>` says "a member of this set",
        # which is the most that is true.
        return [("<set>", item) for item in current]
    if isinstance(current, Sequence):
        return [(str(idx), item) for idx, item in enumerate(current)]
    if hasattr(current, "tag") and hasattr(current, "value"):
        return [("<tag>", current.value)]
    return []


def _mapping_entries(items):
    entries = []
    for key, item in items:
        if not isinstance(key, str):
            entries.append(("<key>", key))
        entries.append((str(key), item))
    return entries


def _find_forbidden_key(value, forbidden_keys):
    # Iterative breadth-first traversal: recursing here would tie the process
    # stack to sender-controlled nesting depth, so a deeply nested but
    # schema-valid payload could kill the gateway with RecursionError at
    # ingress before any egress guard runs. An explicit queue makes depth a
    # memory cost, never a crash; the shallowest forbidden key is found first.
    #
    # Removing the crash is only half of it: the walk must also TERMINATE.
    # Ingress structure is not guaranteed acyclic. `json.loads` cannot build a
    # cycle, but CBOR ingress can - cbor2 honours the value-sharing tags
    # (28 shareable / 29 sharedref) by default, so a ~600 byte datagram
    # decodes into a self-referential dict on a cbor2-only install, which
    # gateway._decode_cbor explicitly supports. Without the seen-set this walk
    # then never returns and the receive loop is wedged on one datagram with
    # the heap rising: an unauthenticated remote hang, ahead of every other
    # check (R1-11 residual against the A-04 wave; same defect class as
    # zmeta_compact._find_unencodable_int).
    #
    # Skipping an already-queued container cannot hide a forbidden key: this
    # is breadth-first, so the first visit is the SHALLOWEST one, and the
    # shallowest is the answer this function is specified to return. The set
    # also caps a shared (acyclic) subtree at one visit rather than one per
    # path to it, which is what stops CBOR value sharing from turning a few
    # hundred wire bytes into exponential work. A node bound was the
    # alternative and is rejected: any budget refuses some large-but-honest
    # event, and dropping good data to save work is not an honest default.
    #
    # Container dispatch is shared with _find_non_finite (_child_entries) so
    # the two walks cannot drift apart on which decoded types they can see. It
    # is not hypothetical here either: a frozendict is hashable, so a cbor2
    # `set` or a map key can carry a whole map - and therefore a forbidden
    # key - that a dict/list dispatch never enqueues.
    queue = deque([(value, [])])
    seen = set()
    while queue:
        current, path = queue.popleft()
        if _is_traversable(current):
            marker = id(current)
            if marker in seen:
                continue
            seen.add(marker)
        if isinstance(current, Mapping):
            # Only MAPPING keys are keys. List indices reach _child_entries as
            # labels too, and testing those against the denylist would make a
            # list element named "0" a forbidden key.
            for key in current.keys():
                key_str = str(key)
                if _normalize_key(key_str) in forbidden_keys:
                    return key_str, path + [key_str]
        for label, child in _child_entries(current):
            queue.append((child, path + [label]))
    return None


def _find_non_finite(value):
    # Iterative breadth-first traversal for NaN / +Inf / -Inf ANYWHERE in the
    # event, keys included. Deliberately VALUE scoped, not field scoped: a
    # candidate list of numeric fields only closes the fields someone thought
    # of, and the same jsonschema blindness that motivated the confidence
    # check (minimum/maximum comparisons are vacuous against NaN) applies
    # identically to geo.lat/lon, alt_m, bearing.az_deg, features.*, quality.*
    # and every namespaced extension value (R1-11 A-01). Non-finite floats
    # also have no RFC 8259 wire form, so leaving one in means Python
    # consumers silently accept a coordinate that is not a coordinate while
    # Go/Rust/Jackson/browser consumers hard-reject the whole datagram - which
    # consumer sees what would be decided by the operator's output encoding,
    # not by the semantics.
    #
    # The traversal is the iterative pattern from _find_forbidden_key for the
    # same reason: recursing here would tie the process stack to
    # sender-controlled nesting depth. Unlike that one it carries parent links
    # instead of copying a path list per node - this runs on every event on
    # both the ingress and the egress gate, and per-node list copying is
    # quadratic in sender-controlled nesting depth, which would trade the
    # laundering defect for a cost-of-service one. The path is materialized
    # only on a hit. Map keys are walked as nodes in their own right (labelled
    # `<key>`) because a CBOR producer can send a float map key - which
    # json.dumps would launder into the string "NaN" - or a frozendict key
    # holding one further down.
    # Returns the dotted path of the shallowest offender, or None.
    #
    # It carries the seen-set for the same reason _find_forbidden_key does:
    # CBOR value-sharing tags make ingress structure possibly cyclic, and an
    # unbounded re-walk is a remote hang. Skipping an already-enqueued
    # container cannot hide an offender - the walk is breadth-first, so the
    # visit that is kept is the shallowest one, which is the path this
    # function is specified to report - and only CONTAINERS are skipped, never
    # a numeric leaf or a numeric key.
    #
    # Which types count as a container, and which as a non-finite leaf, is
    # decided by _child_entries / _is_non_finite_number rather than inline:
    # dispatching on dict/(list, tuple) and on `float` alone let four separate
    # cbor2-decoded shapes through (set, CBORTag, frozendict-as-map-key,
    # Decimal('NaN')), each of which was forwarded and each of which put the
    # NaN back on the CBOR wire.
    nodes = [(value, -1, None)]
    index = 0
    seen = set()
    while index < len(nodes):
        current = nodes[index][0]
        if _is_non_finite_number(current):
            return _path_of(nodes, index)
        if _is_traversable(current):
            marker = id(current)
            if marker in seen:
                index += 1
                continue
            seen.add(marker)
        for label, child in _child_entries(current):
            nodes.append((child, index, label))
        index += 1
    return None


_MAX_REPORTED_PATH_CHARS = 256


def _path_of(nodes, index, leaf=None):
    parts = [leaf] if leaf is not None else []
    while index >= 0:
        _value, parent, label = nodes[index]
        if label is not None:
            parts.append(label)
        index = parent
    parts.reverse()
    path = ".".join(parts) if parts else "<root>"
    if len(path) > _MAX_REPORTED_PATH_CHARS:
        # The path is sender-controlled and this string ships inside the
        # diagnostic. Truncate visibly rather than emitting a datagram-sized
        # reason - a marked truncation is honest, a silent one is not.
        path = path[:_MAX_REPORTED_PATH_CHARS] + "...<truncated>"
    return path


def _find_non_finite_confidence(event):
    # The two confidence sites keep their own, more specific diagnostic. This
    # is the candidate list that shipped with NON_FINITE_CONFIDENCE, unchanged
    # and in its original order, so that code keeps firing exactly where it
    # fired before; the value-scoped traversal above covers everything else.
    payload = event.get("payload") if isinstance(event, dict) else None
    candidates = [("confidence", event.get("confidence") if isinstance(event, dict) else None)]
    if isinstance(payload, dict):
        claim_block = payload.get("claim")
        if isinstance(claim_block, dict):
            candidates.append(("payload.claim.confidence", claim_block.get("confidence")))
    for conf_path, conf_value in candidates:
        if isinstance(conf_value, float) and not math.isfinite(conf_value):
            return conf_path
    return None


def _parse_utc_z(value):
    """Parse a trailing-Z UTC timestamp; None is the cannot-parse signal.

    A parse that yields a NAIVE datetime is a failed parse. Python's
    ``fromisoformat`` accepts date-only and ISO-week shapes and silently
    ignores the appended ``+00:00`` ("1969-12-31Z" and "2026-W01-1Z" satisfy
    the schema's ``Z$`` gate yet parse with ``tzinfo=None`` on 3.14). Letting
    a naive value out of this seam poisons every downstream comparison and
    subtraction with mixed naive/aware TypeError, which the receive loop's
    last-resort guard turns into a whole dropped datagram (VW-01). Refusing
    here routes gate-clean-but-naive shapes down the same arm every caller
    already has for an unparseable timestamp.
    """
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _format_utc_z(value):
    # A naive datetime is refused, not reinterpreted: .astimezone() on a
    # naive value asks the PLATFORM (silent host-local reinterpretation, or
    # OSError pre-epoch on Windows). tzinfo.utcoffset(None-returning) is the
    # stdlib definition of naive, so both shapes take the refusal arm.
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return None
    value = value.astimezone(timezone.utc)
    if value.microsecond:
        text = value.isoformat(timespec="milliseconds")
    else:
        text = value.isoformat(timespec="seconds")
    return text.replace("+00:00", "Z")


def _should_replace_timing_status(current, new_status):
    if not isinstance(current, dict):
        return True
    current_ts = _parse_utc_z(current.get("_event_ts"))
    new_ts = _parse_utc_z(new_status.get("_event_ts"))
    if current_ts is None or new_ts is None:
        return True
    return new_ts >= current_ts


def _profile_for_event(event, profile=None):
    if profile:
        return str(profile)
    event_profile = event.get("profile") if isinstance(event, dict) else None
    return str(event_profile or "H")


def _timing_freshness_enabled(policy):
    """Is the timing-freshness gate on?

    Only an explicit ``enabled: false`` turns it off. A block that is NOT a
    mapping cannot say ``enabled: false`` — it is a destroyed block, and
    reading a destroyed block as "the operator disabled this gate" is what
    silently switched the whole stale / negative-age gate off with no
    diagnostic anywhere (R1-11 B-02, runtime half).

    This was the sole outlier in its own family. Every other reader here
    already falls back to its built-in default when the policy is not a
    mapping — ``_timing_mode`` returns ``reject``, ``_max_timing_status_age_ms``
    and ``_max_negative_timing_status_age_ms`` return the per-profile
    defaults — and ``validate_timing_quality``'s own MISSING branch already
    refuses when the policy is unreadable. Absence stays legal and permissive
    the same way it always did: an absent ``timing-freshness.yaml`` loads as
    ``{}``, which is a mapping and takes the built-in defaults.
    """
    if not isinstance(policy, dict):
        return True
    return policy.get("enabled", True) is not False


def _timing_policy_block_error(policy):
    """Name a destroyed timing_freshness block so a refusal can cite it."""
    if isinstance(policy, dict):
        return None
    return (
        "the timing_freshness policy block must be a mapping; got "
        f"{type(policy).__name__}, so no freshness bound could be read and the "
        "built-in defaults were applied "
        "(policy/timing-freshness.yaml#timing_freshness)"
    )


def _timing_mode(policy, reason, profile=None):
    if not isinstance(policy, dict):
        return "reject"
    mode = None
    if profile:
        for key in (f"{reason}_mode_by_profile", "mode_by_profile"):
            configured = policy.get(key)
            if isinstance(configured, dict) and profile in configured:
                mode = configured.get(profile)
                break
    if mode is None:
        mode = policy.get(f"{reason}_mode", policy.get("mode", "reject"))
    mode = str(mode or "reject").strip().lower()
    if mode not in {"warn", "degrade", "reject"}:
        return "reject"
    return mode


def _timing_mode_severity(mode):
    return "fail" if mode == "reject" else "warn"


def _max_timing_status_age_ms(policy, profile):
    defaults = {"L": 60000, "M": 30000, "H": 10000}
    configured = policy.get("max_timing_status_age_ms", {}) if isinstance(policy, dict) else {}
    if not isinstance(configured, dict):
        configured = {}
    raw = configured.get(profile, defaults.get(profile, defaults["H"]))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = defaults.get(profile, defaults["H"])
    return max(0, value)


def _max_negative_timing_status_age_ms(policy, profile):
    defaults = {"L": 5000, "M": 2000, "H": 1000}
    configured = policy.get("max_negative_age_ms", {}) if isinstance(policy, dict) else {}
    if isinstance(configured, dict):
        raw = configured.get(profile, defaults.get(profile, defaults["H"]))
    else:
        raw = configured
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = defaults.get(profile, defaults["H"])
    return max(0, value)


_TIMING_DEGRADABLE_CODES = {
    "TIMING_STATUS_MISSING",
    "TIMING_STATUS_STALE",
    "TIMING_STATUS_AGE_NEGATIVE",
}


def _timing_policy_violation(
    code,
    message,
    mode,
    details,
    timing_freshness_policy=None,
    severity_map=None,
):
    details = _risk_details(
        details,
        "timing",
        mode,
        policy=timing_freshness_policy,
        policy_ref="policy/timing-freshness.yaml",
    )
    # A refusal caused by broken policy must name the policy, the same way the
    # routing and producer-authority refusals do (R1-11 B-02).
    block_error = _timing_policy_block_error(timing_freshness_policy)
    if block_error is not None:
        details["policy_error"] = block_error
    if mode == "degrade":
        details["action"] = "degrade"
        degradation = (
            timing_freshness_policy.get("degrade", {})
            if isinstance(timing_freshness_policy, dict)
            else {}
        )
        if not isinstance(degradation, dict):
            degradation = {}
        try:
            factor = float(degradation.get("confidence_reduction_factor", 2.0))
        except (TypeError, ValueError):
            factor = 2.0
        if factor <= 0:
            factor = 2.0
        details["effects"] = {"confidence_reduction_factor": factor}
    return _violation(
        code,
        message,
        details=details,
        severity_map=severity_map,
        severity=_timing_mode_severity(mode),
    )


def apply_timing_freshness_degradation(event, violations, timing_freshness_policy):
    if not isinstance(event, dict) or not isinstance(timing_freshness_policy, dict):
        return False
    if not any(
        violation.get("details", {}).get("action") == "degrade"
        and violation.get("code") in _TIMING_DEGRADABLE_CODES
        for violation in violations or []
    ):
        return False

    degradation = timing_freshness_policy.get("degrade", {})
    if not isinstance(degradation, dict):
        degradation = {}
    try:
        factor = float(degradation.get("confidence_reduction_factor", 2.0))
    except (TypeError, ValueError):
        factor = 2.0
    if factor <= 0:
        factor = 2.0

    confidence = event.get("confidence")
    if not isinstance(confidence, (int, float)) or _is_non_finite_number(confidence):
        # A non-finite confidence must be left exactly as it arrived. The
        # clamp below is `max(0.0, min(1.0, x))`, and `min(1.0, nan)` is 1.0
        # in Python - so degrading a NaN confidence rewrote it to MAXIMUM
        # confidence and the event was forwarded, the worst possible
        # direction for a degradation step (R1-11 residual against A-01).
        # This mutation runs at gateway.py's timing stage, ahead of the
        # value-honesty gate in validate_semantics, so overwriting the NaN
        # here also destroys the evidence the gate refuses on: the gate then
        # sees a clean 1.0 and passes it.
        #
        # Declining to degrade is not "accepting" it. The value is left
        # non-finite, so the gate downstream refuses the event under
        # NON_FINITE_CONFIDENCE - louder than any degraded forward - and the
        # timing violation is still reported by the caller either way.
        return False
    event["confidence"] = max(0.0, min(1.0, confidence / factor))
    changed = True
    for violation in violations or []:
        if (
            violation.get("details", {}).get("action") == "degrade"
            and violation.get("code") in _TIMING_DEGRADABLE_CODES
        ):
            changed = _append_risk_adjudication(
                event, violation, {"confidence_reduction_factor": factor}
            ) or changed
    return changed


def _normalize_pattern(value):
    return str(value or "").strip().lower()


def _matches_pattern(value, pattern):
    value_lc = _normalize_pattern(value)
    pattern_lc = _normalize_pattern(pattern)
    return bool(value_lc and pattern_lc and fnmatchcase(value_lc, pattern_lc))


def _matching_producer_rules(producer, producer_rules):
    if not isinstance(producer_rules, dict):
        return []
    matches = []
    for pattern, rule in producer_rules.items():
        if _matches_pattern(producer, pattern):
            matches.append((str(pattern), rule))
    return matches


def _list_values(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


# The kernel's own event vocabulary, DERIVED from the schemas rather than
# restated here (R1-11 A-05 residual c). A policy list whose entries are
# matched against `event.event_type` / `event.event_subtype` is disabled just
# as silently by a well-formed string that can never match (`STATE_EVEN`,
# `state_event`) as by a non-string entry: both stringify into a token no
# event carries. Checking those entries needs the vocabulary, and a copy of
# the vocabulary pasted into this module would drift the moment a governed
# schema change landed — so read every shipped schema and union what it
# actually allows.
_KERNEL_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schema"
_EVENT_VOCABULARY_CACHE = {}


def _collect_event_field_values(node, field, out):
    """Union every enum/const the schema attaches to ``event.<field>``."""
    if isinstance(node, dict):
        event_spec = node.get("event")
        if isinstance(event_spec, dict):
            properties = event_spec.get("properties")
            if isinstance(properties, dict) and isinstance(properties.get(field), dict):
                spec = properties[field]
                if isinstance(spec.get("enum"), list):
                    out.update(item for item in spec["enum"] if isinstance(item, str))
                if isinstance(spec.get("const"), str):
                    out.add(spec["const"])
        for value in node.values():
            _collect_event_field_values(value, field, out)
    elif isinstance(node, list):
        for value in node:
            _collect_event_field_values(value, field, out)


def _event_vocabulary(field, schema_dir=None):
    """Return the schema-declared vocabulary for ``event.<field>``.

    An empty result means the schemas could not be read at all. Callers must
    treat that as "this check could not run" and say so, never as "every
    entry is unknown" (which would refuse a correct policy) and never as
    "every entry is fine" (which would be a vacuous guard).
    """
    directory = Path(schema_dir) if schema_dir is not None else _KERNEL_SCHEMA_DIR
    cache_key = (str(directory), field)
    cached = _EVENT_VOCABULARY_CACHE.get(cache_key)
    if cached is not None:
        return cached
    values = set()
    try:
        candidates = sorted(directory.glob("*.schema.json"))
    except OSError:
        candidates = []
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        _collect_event_field_values(document, field, values)
    vocabulary = frozenset(values)
    if not vocabulary:
        # Never cache a FAILURE. An empty result means the schemas could not
        # be read on this call, which is a transient, environmental condition
        # (the directory not mounted yet, a read error) — caching it disables
        # the vocabulary check for the life of the process, so one unlucky
        # first call permanently turns the gate off (R1-11 R2-32).
        return vocabulary
    _EVENT_VOCABULARY_CACHE[cache_key] = vocabulary
    return vocabulary


def _unknown_event_tokens(values, field="event_type"):
    """Return the entries of ``values`` no event can ever carry."""
    vocabulary = _event_vocabulary(field)
    if not vocabulary:
        # Vocabulary underivable: the schemas are unreadable, in which case
        # nothing validates at all. Report nothing here rather than refuse a
        # correct policy; the deployment lint says so out loud instead.
        return []
    return sorted({str(item).strip() for item in values} - set(vocabulary))


def _require_match_types(block, key, policy_ref):
    """Read a require-match event-type allowlist, FAIL CLOSED if malformed.

    The two require-match gates (producer_authority.require_match_for_event_types
    and routing.producer_enforcement.require_allowlist_for_event_types) are the
    only control standing between an unregistered producer and the event types
    the deployment reserves. Before R1-11 A-05 both iterated the raw policy
    value: a bare YAML key (``None``) raised ``TypeError`` on every event, and
    a scalar (``STATE_EVENT``) was iterated character by character, producing a
    set that can never contain an event type and silently disabling the gate.

    Absence stays legal and permissive — that is the documented "no
    require-match" configuration. A value that is PRESENT but not a sequence is
    a policy defect, and a defective authorization policy must not be read as
    an empty allowlist: the caller applies the gate to every event type and
    reports ``policy_error`` in the diagnostic so the refusal names its cause.
    """
    if not isinstance(block, dict):
        # The enclosing block itself is malformed. Callers pass {} when the
        # block is absent, so this is present-but-wrong: it must not be
        # quieter than the AttributeError it replaces.
        return set(), (
            f"the block holding {key} must be a mapping; got "
            f"{type(block).__name__} ({policy_ref})"
        )
    if key not in block:
        return set(), None
    value = block[key]
    if isinstance(value, (list, tuple)):
        if all(isinstance(item, str) for item in value):
            types = {item.strip() for item in value if item.strip()}
            # A string entry that is not an event type is exactly as silent as
            # a non-string one: `STATE_EVEN` / `state_event` drops STATE_EVENT
            # out of the gate and the unregistered producer walks through
            # (R1-11 A-05 residual c). Same fail-closed answer as a wrong type.
            unknown = _unknown_event_tokens(types)
            if unknown:
                return set(), (
                    f"{key} entries must be event types the schema declares; "
                    f"{unknown} match nothing an event can carry, so each one "
                    f"silently drops out of the gate. A malformed authorization "
                    f"policy cannot disable the require-match gate ({policy_ref})"
                )
            return types, None
        return set(), (
            f"{key} entries must be event-type strings; got a non-string "
            f"entry. A malformed authorization policy cannot disable the "
            f"require-match gate ({policy_ref})"
        )
    return set(), (
        f"{key} must be a list of event types; got "
        f"{type(value).__name__}. A malformed authorization policy cannot "
        f"disable the require-match gate ({policy_ref})"
    )


_PRODUCER_RULE_LIST_KEYS = (
    "allowed_event_types",
    "allowed_event_subtypes",
    "forbidden_event_types",
)
# Of the per-producer list keys, the ones where an unmatchable token fails
# OPEN — and are therefore the ones a runtime refusal is proportionate for.
#
#   forbidden_event_types: `COMMAND_EVEN` silently DROPS a prohibition. The
#   extent of what is now un-prohibited is unknowable from the typo, so the
#   whole rule's adjudication is untrustworthy and the producer is refused.
#
#   allowed_event_types is deliberately NOT here. A typo there removes an
#   entry from an ALLOWLIST, which already fails closed by construction — the
#   producer's STATE_EVENTs stop being authorized on their own. Refusing the
#   producer wholesale on top of that discards the events the SURVIVING,
#   correctly-spelled entries explicitly authorize, buying no honesty: it
#   throws away good canonical data to re-close a door that is already shut
#   (R1-11 R2-17). The deployment lint still reports the token loudly through
#   _LIST_ENTRY_VOCABULARIES, so the operator is not left in the dark.
#
#   allowed_event_subtypes is not here either, for a different reason: the
#   subtype vocabulary is open — spec/extension-registry.yaml registers
#   subtypes that are not yet schema-valid — so "unknown token" is not
#   decidable from the schema at all (doctrine log R1-11-11, still open).
_FAIL_OPEN_ON_UNKNOWN_TOKEN = frozenset({"forbidden_event_types"})


def _producer_rule_policy_error(rule, policy_ref):
    """Return a message if a producer rule's event-type lists are unreadable.

    Same doctrine as ``_require_match_types``, one level down. ``_list_values``
    turns anything that is not a list or a non-empty string into ``[]``, which
    every caller reads as "no constraint on this axis" — so a bare
    ``allowed_event_types:`` key silently un-gates the producer and a bare
    ``forbidden_event_types:`` silently drops its prohibition, with every lint
    green (R1-11 A-05 residuals b and c).

    Only the LOSSY shapes are a defect. Absence is the documented "no
    constraint"; an empty list is the documented empty constraint; a bare
    scalar is read as a one-item list and loses nothing, so it stays working
    (the deployment lint still reports it as a shape defect). What refuses is
    the shape whose meaning is silently discarded.
    """
    if not isinstance(rule, dict):
        return (
            f"producer rule must be a mapping; got {type(rule).__name__}, so "
            f"every constraint on this producer is dropped while the gate "
            f"still looks configured ({policy_ref})"
        )
    for key in _PRODUCER_RULE_LIST_KEYS:
        if key not in rule:
            continue
        raw = rule[key]
        if isinstance(raw, str):
            if raw.strip():
                continue
            return (
                f"{key} is an empty string, which is read as 'no constraint' "
                f"and silently drops this rule from the gate ({policy_ref})"
            )
        if not isinstance(raw, (list, tuple)):
            return (
                f"{key} must be a list of event types; got "
                f"{type(raw).__name__}, which is read as 'no constraint' and "
                f"silently drops this rule from the gate ({policy_ref})"
            )
        bad = [
            index
            for index, item in enumerate(raw)
            if not isinstance(item, str) or not item.strip()
        ]
        if bad:
            return (
                f"{key} entries must be non-empty strings; entries {bad} are "
                f"not, and each is stringified into a token that can never "
                f"match ({policy_ref})"
            )
        if key not in _FAIL_OPEN_ON_UNKNOWN_TOKEN:
            continue
        unknown = _unknown_event_tokens(raw)
        if unknown:
            return (
                f"{key} entries must be event types the schema declares; "
                f"{unknown} match nothing an event can carry, so each one "
                f"silently drops out of this rule ({policy_ref})"
            )
    return None


def _is_blank(value):
    return value is None or value == "" or value == []


def _allowlist_contains(value, allowlist):
    """Is ``value`` a member of ``allowlist``, for a value we do not control?

    ``payload.extensions`` is free-form in both schemas — no type constraint on
    ``external_promotion`` or any of its members — so a producer may legally
    put a list or a dict where the promotion guard expects a scalar token.
    ``<list> in <set>`` raises ``TypeError: unhashable type`` straight out of
    the public ``validate_producer_authority`` API: inside the reference
    gateway the receive-loop backstop turns that into an ``INTERNAL_ERROR``
    drop, which tells the operator "gateway bug" instead of "promotion
    refused" and hides the laundering attempt; any embedder calling the API
    directly just gets the traceback (R1-11 A-14).

    An unhashable value is not a member of any allowlist, so answer that
    honestly and let the caller emit its normal refusal, naming the offending
    value in the diagnostic. This changes no answer for a hashable value: the
    membership test is unchanged, and where the allowlist is empty the caller
    still applies its documented "no constraint" reading.
    """
    try:
        return value in allowlist
    except TypeError:
        return False


def _risk_trigger_matches(value, triggers):
    """Does ``value`` trip a RISK/TRIGGER list, for a value we do not control?

    Same unhashable-input problem as :func:`_allowlist_contains`, opposite
    safety polarity, and the distinction is the whole point of this function
    existing separately.

    At an *allowlist* site the caller asks ``not _allowlist_contains(...)``, so
    answering ``False`` for an unhashable token produces a refusal — fail
    closed. At a *trigger* site the caller asks the question directly, so
    answering ``False`` means "this token did not trip the risk" and the event
    is ADMITTED — fail open. Reusing the allowlist helper here silently
    disabled the loop/reflection gate, ``always_reject_loop_risk`` included:
    a producer sending ``loop_status: ["REFLECTION_DETECTED"]`` as a list
    instead of a scalar went from a crash (which at least dropped the event)
    to a clean forward.

    An unhashable token is not a legal value for these fields, and a malformed
    token in a promotion-risk field is exactly the shape a laundering attempt
    takes. Treat it as tripping the trigger and let the caller emit its normal
    refusal naming the offending value. Hashable values are unaffected: the
    membership test is unchanged, and an empty trigger list still trips
    nothing.
    """
    try:
        return value in triggers
    except TypeError:
        return True


def _external_promotion_rules(matching_rules):
    rules = []
    for pattern, rule in matching_rules:
        if not isinstance(rule, dict):
            continue
        cfg = rule.get("external_state_promotion")
        if not isinstance(cfg, dict) or cfg.get("required", False) is not True:
            continue
        rules.append((pattern, cfg))
    return rules


def _union_rule_values(rules, key):
    values = set()
    for _pattern, cfg in rules:
        values.update(_list_values(cfg.get(key)))
    return values


_PROMOTION_MODES = {"reject", "warn", "quarantine", "degrade"}


def _normalize_promotion_mode(value, default="reject"):
    mode = str(value or default).strip().lower()
    if mode not in _PROMOTION_MODES:
        return default
    return mode


def _promotion_mode(global_cfg, promotion_rules, profile):
    if not isinstance(global_cfg, dict):
        return "reject"

    mode = global_cfg.get("mode", "reject")
    by_profile = global_cfg.get("mode_by_profile")
    if isinstance(by_profile, dict):
        mode = by_profile.get(profile, by_profile.get("default", mode))

    for _pattern, cfg in promotion_rules or []:
        if not isinstance(cfg, dict):
            continue
        rule_mode = cfg.get("mode")
        rule_by_profile = cfg.get("mode_by_profile")
        if isinstance(rule_by_profile, dict):
            rule_mode = rule_by_profile.get(profile, rule_by_profile.get("default", rule_mode))
        if rule_mode is not None:
            mode = rule_mode

    return _normalize_promotion_mode(mode)


def _promotion_mode_severity(mode):
    return "fail" if mode == "reject" else "warn"


def _promotion_violation(message, details=None, severity_map=None):
    details = dict(details or {})
    mode = _normalize_promotion_mode(details.get("policy_mode"), default="reject")
    details = _risk_details(
        details,
        "external_promotion",
        mode,
        policy_ref="policy/producer-authority.yaml#external_state_promotion",
    )
    if mode in {"degrade", "quarantine"}:
        details["action"] = mode
    return _violation(
        "PRODUCER_NOT_ALLOWED",
        message,
        details=details,
        severity_map=severity_map,
        severity=_promotion_mode_severity(mode),
    )


def _positive_float(value, default):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed <= 0:
        return default
    return parsed


def _bounded_float(value, default, low=0.0, high=1.0):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(low, min(high, parsed))


def _non_negative_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, parsed)


def _ensure_path_dict(value, dotted_path):
    if not isinstance(value, dict):
        return None
    target = value
    parts = [part for part in str(dotted_path).split(".") if part]
    for part in parts:
        if not isinstance(target, dict):
            return None
        child = target.get(part)
        if not isinstance(child, dict):
            child = {}
            target[part] = child
        target = child
    return target


# Every degradation/cap helper below refuses to compute on a non-finite
# operand, for the reason spelled out in apply_timing_freshness_degradation:
# `max(0.0, min(1.0, nan))` is 1.0, so clamping a NaN produces MAXIMUM
# confidence, and `int(nan)` / `int(inf)` raise ValueError / OverflowError
# straight out of the gateway instead of refusing. Today all four of these run
# downstream of the value-honesty gate in process_message and so cannot see a
# non-finite value; the guard is here so that stays true if the order ever
# changes, and because these are reachable directly. Declining to compute
# leaves the offending value intact for the gate to refuse - it never
# substitutes a cleaner one.
def _reduce_confidence(event, factor):
    confidence = event.get("confidence") if isinstance(event, dict) else None
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return False
    if _is_non_finite_number(confidence):
        return False
    event["confidence"] = max(0.0, min(1.0, float(confidence) / factor))
    return True


def _cap_confidence(event, cap):
    confidence = event.get("confidence") if isinstance(event, dict) else None
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return False
    if _is_non_finite_number(confidence):
        return False
    event["confidence"] = max(0.0, min(1.0, min(float(confidence), cap)))
    return True


def _reduce_valid_for_ms(event, factor):
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    if not isinstance(payload, dict):
        return False
    value = payload.get("valid_for_ms")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if _is_non_finite_number(value):
        return False
    payload["valid_for_ms"] = max(1, int(float(value) / factor))
    return True


def _cap_valid_for_ms(event, cap):
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    if not isinstance(payload, dict):
        return False
    value = payload.get("valid_for_ms")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if _is_non_finite_number(value):
        return False
    payload["valid_for_ms"] = max(0, int(min(float(value), cap)))
    return True


def apply_external_promotion_policy_action(event, violations, authority_policy):
    if not isinstance(event, dict) or not isinstance(authority_policy, dict):
        return False
    global_cfg = authority_policy.get("external_state_promotion", {})
    if not isinstance(global_cfg, dict):
        global_cfg = {}

    metadata_path = global_cfg.get("metadata_path", "payload.extensions.external_promotion")
    changed = False
    for violation in violations or []:
        if violation.get("code") != "PRODUCER_NOT_ALLOWED":
            continue
        details = violation.get("details", {})
        action = details.get("action") if isinstance(details, dict) else None
        if action not in {"degrade", "quarantine"}:
            continue

        metadata = _ensure_path_dict(event, metadata_path)
        if metadata is not None:
            metadata["policy_mode"] = action
            metadata["policy_reason_code"] = violation.get("code")
            metadata["policy_decision"] = _policy_decision_for_mode(action)
            changed = True

        if action == "degrade":
            degrade_cfg = global_cfg.get("degrade", {})
            if not isinstance(degrade_cfg, dict):
                degrade_cfg = {}
            confidence_factor = _positive_float(
                degrade_cfg.get("confidence_reduction_factor"), 2.0
            )
            valid_for_factor = _positive_float(
                degrade_cfg.get("valid_for_ms_reduction_factor"), confidence_factor
            )
            changed = _reduce_confidence(event, confidence_factor) or changed
            changed = _reduce_valid_for_ms(event, valid_for_factor) or changed
            changed = _append_risk_adjudication(
                event,
                violation,
                {
                    "confidence_reduction_factor": confidence_factor,
                    "valid_for_ms_reduction_factor": valid_for_factor,
                },
            ) or changed
            continue

        quarantine_cfg = global_cfg.get("quarantine", {})
        if not isinstance(quarantine_cfg, dict):
            quarantine_cfg = {}
        confidence_cap = _bounded_float(quarantine_cfg.get("confidence_cap"), 0.25)
        valid_for_cap = _non_negative_int(quarantine_cfg.get("valid_for_ms_cap"), 1000)
        changed = _cap_confidence(event, confidence_cap) or changed
        changed = _cap_valid_for_ms(event, valid_for_cap) or changed
        changed = _append_risk_adjudication(
            event,
            violation,
            {
                "confidence_cap": confidence_cap,
                "valid_for_ms_cap": valid_for_cap,
            },
        ) or changed

    return changed


def _validate_external_state_promotion(
    event,
    authority_policy,
    promotion_rules,
    matched_patterns,
    severity_map=None,
):
    if not promotion_rules:
        return None

    event_block = event.get("event", {}) if isinstance(event, dict) else {}
    event_type = event_block.get("event_type")
    if event_type != "STATE_EVENT":
        return None

    global_cfg = authority_policy.get("external_state_promotion", {})
    # Same class as the timing_freshness block, in the gate that exists to stop
    # laundering: a block that is NOT a mapping cannot say `enabled: false`.
    # Reading a destroyed block as "the operator disabled promotion checking"
    # turned the ENTIRE external-promotion gate off in silence — no trust
    # anchor, no lineage status, no loop check, no freshness bound — for every
    # producer whose rule requires promotion (R1-11 B-02 class, enumerated from
    # the code). An absent block is `{}`, which is a mapping and keeps the
    # built-in defaults; only a mangled one lands here.
    block_policy_error = None
    if not isinstance(global_cfg, dict):
        block_policy_error = (
            "the external_state_promotion policy block must be a mapping; got "
            f"{type(global_cfg).__name__}, so no promotion evidence could be "
            "required of this externally-promoted state "
            "(policy/producer-authority.yaml#producer_authority."
            "external_state_promotion)"
        )
        global_cfg = {}
    elif global_cfg.get("enabled", True) is False:
        return None

    source = event.get("source", {}) if isinstance(event, dict) else {}
    producer = (source.get("producer") or "").strip()
    profile = _profile_for_event(event)
    mode = _promotion_mode(global_cfg, promotion_rules, profile)
    metadata_path = global_cfg.get("metadata_path", "payload.extensions.external_promotion")
    metadata = _resolve_path(event, metadata_path)
    details = _risk_details(
        {
            "event_type": event_type,
            "producer": producer,
            "profile": profile,
            "matched_patterns": matched_patterns,
            "metadata_path": metadata_path,
            "policy_mode": mode,
        },
        "external_promotion",
        mode,
        policy=global_cfg,
        policy_ref="policy/producer-authority.yaml#external_state_promotion",
    )

    if block_policy_error is not None:
        # Refuse the PROMOTION, not some unrelated part of the event, and name
        # the file to fix. _promotion_mode returns "reject" for an unreadable
        # block, so this carries fail severity.
        return _promotion_violation(
            "external STATE_EVENT promotion policy is unreadable",
            details={**details, "policy_error": block_policy_error},
            severity_map=severity_map,
        )

    if not isinstance(metadata, dict):
        return _promotion_violation(
            "external STATE_EVENT promotion metadata missing",
            details=details,
            severity_map=severity_map,
        )

    required_by_profile = global_cfg.get("required_fields_by_profile", {})
    if not isinstance(required_by_profile, dict):
        required_by_profile = {}
    required_fields = _list_values(
        required_by_profile.get(profile, required_by_profile.get("default", []))
    )
    missing = [field for field in required_fields if _is_blank(metadata.get(field))]
    if missing:
        return _promotion_violation(
            "external STATE_EVENT promotion metadata missing required fields",
            details={**details, "missing": missing},
            severity_map=severity_map,
        )

    expected_category = global_cfg.get("required_state_category")
    if expected_category and metadata.get("state_category") != expected_category:
        return _promotion_violation(
            "external STATE_EVENT promotion category is not allowed",
            details={
                **details,
                "state_category": metadata.get("state_category"),
                "required_state_category": expected_category,
            },
            severity_map=severity_map,
        )

    allowed_origin_kinds = set(_list_values(global_cfg.get("allowed_origin_kinds")))
    origin_kind = metadata.get("origin_kind")
    if (
        origin_kind is not None
        and allowed_origin_kinds
        and not _allowlist_contains(origin_kind, allowed_origin_kinds)
    ):
        return _promotion_violation(
            "external STATE_EVENT promotion origin kind is not allowed",
            details={**details, "origin_kind": origin_kind, "allowed_origin_kinds": sorted(allowed_origin_kinds)},
            severity_map=severity_map,
        )

    lineage_by_profile = global_cfg.get("allowed_lineage_status_by_profile", {})
    if not isinstance(lineage_by_profile, dict):
        lineage_by_profile = {}
    allowed_lineage_status = set(
        _list_values(lineage_by_profile.get(profile, lineage_by_profile.get("default", [])))
    )
    lineage_status = metadata.get("lineage_status")
    if (
        lineage_status is not None
        and allowed_lineage_status
        and not _allowlist_contains(lineage_status, allowed_lineage_status)
    ):
        return _promotion_violation(
            "external STATE_EVENT promotion lineage status is not allowed for profile",
            details={
                **details,
                "lineage_status": lineage_status,
                "allowed_lineage_status": sorted(allowed_lineage_status),
            },
            severity_map=severity_map,
        )

    source_uid_statuses = set(_list_values(global_cfg.get("source_event_uid_required_statuses")))
    if _risk_trigger_matches(lineage_status, source_uid_statuses) and _is_blank(
        metadata.get("source_event_uid")
    ):
        return _promotion_violation(
            "external STATE_EVENT promotion requires source event identity",
            details={**details, "lineage_status": lineage_status, "missing": ["source_event_uid"]},
            severity_map=severity_map,
        )

    trust_ref = metadata.get("trust_ref")
    trust_prefixes = _list_values(global_cfg.get("required_trust_ref_prefixes"))
    if trust_ref is not None and trust_prefixes:
        trust_ref_text = str(trust_ref)
        if not any(trust_ref_text.startswith(prefix) for prefix in trust_prefixes):
            return _promotion_violation(
                "external STATE_EVENT promotion trust reference is not allowed",
                details={**details, "trust_ref": trust_ref, "required_prefixes": trust_prefixes},
                severity_map=severity_map,
            )

    current_event_id = event_block.get("event_id")
    lineage_ids = set(_lineage_based_on(event))
    source_zmeta_event_id = metadata.get("source_zmeta_event_id")
    loop_status = metadata.get("loop_status")
    loop_risk_statuses = set(_list_values(global_cfg.get("loop_risk_statuses")))
    if (
        _risk_trigger_matches(loop_status, loop_risk_statuses)
        or (source_zmeta_event_id and source_zmeta_event_id == current_event_id)
        or (current_event_id and _risk_trigger_matches(current_event_id, lineage_ids))
    ):
        loop_mode = mode
        if global_cfg.get("always_reject_loop_risk", True) is not False:
            loop_mode = "reject"
        loop_details_source = {
            key: value
            for key, value in details.items()
            if key not in {"allowed_uses", "prohibited_uses", "policy_decision"}
        }
        return _promotion_violation(
            "external STATE_EVENT promotion has loop/reflection risk",
            details=_risk_details(
                {
                    **loop_details_source,
                    "policy_mode": loop_mode,
                    "loop_status": loop_status,
                    "source_zmeta_event_id": source_zmeta_event_id,
                    "event_id": current_event_id,
                },
                "external_promotion",
                loop_mode,
                policy=global_cfg,
                policy_ref="policy/producer-authority.yaml#external_state_promotion",
            ),
            severity_map=severity_map,
        )

    allowed_loop_statuses = set(_list_values(global_cfg.get("allowed_loop_statuses")))
    if (
        loop_status is not None
        and allowed_loop_statuses
        and not _allowlist_contains(loop_status, allowed_loop_statuses)
    ):
        return _promotion_violation(
            "external STATE_EVENT promotion loop status is not allowed",
            details={**details, "loop_status": loop_status, "allowed_loop_statuses": sorted(allowed_loop_statuses)},
            severity_map=severity_map,
        )

    transform = event.get("lineage", {}).get("transform") if isinstance(event.get("lineage"), dict) else None
    transform_prefixes = _list_values(global_cfg.get("required_lineage_transform_prefixes"))
    if transform_prefixes and not any(str(transform or "").startswith(prefix) for prefix in transform_prefixes):
        return _promotion_violation(
            "external STATE_EVENT promotion lineage transform is not a promotion transform",
            details={**details, "transform": transform, "required_prefixes": transform_prefixes},
            severity_map=severity_map,
        )

    policy_id = metadata.get("promotion_policy_id")
    approved_policy_ids = _union_rule_values(promotion_rules, "approved_policy_ids")
    if (
        policy_id is not None
        and approved_policy_ids
        and not _allowlist_contains(policy_id, approved_policy_ids)
    ):
        return _promotion_violation(
            "external STATE_EVENT promotion policy is not approved for producer",
            details={**details, "promotion_policy_id": policy_id, "approved_policy_ids": sorted(approved_policy_ids)},
            severity_map=severity_map,
        )

    projection_id = metadata.get("projection_id")
    allowed_projection_ids = _union_rule_values(promotion_rules, "allowed_projection_ids")
    if (
        projection_id is not None
        and allowed_projection_ids
        and not _allowlist_contains(projection_id, allowed_projection_ids)
    ):
        return _promotion_violation(
            "external STATE_EVENT projection id is not approved for producer",
            details={**details, "projection_id": projection_id, "allowed_projection_ids": sorted(allowed_projection_ids)},
            severity_map=severity_map,
        )

    confidence_basis = metadata.get("confidence_basis")
    allowed_confidence_basis = _union_rule_values(promotion_rules, "allowed_confidence_basis")
    if (
        confidence_basis is not None
        and allowed_confidence_basis
        and not _allowlist_contains(confidence_basis, allowed_confidence_basis)
    ):
        return _promotion_violation(
            "external STATE_EVENT confidence basis is not approved for producer",
            details={
                **details,
                "confidence_basis": confidence_basis,
                "allowed_confidence_basis": sorted(allowed_confidence_basis),
            },
            severity_map=severity_map,
        )

    freshness_ms = metadata.get("freshness_ms")
    if freshness_ms is not None:
        try:
            freshness_value = float(freshness_ms)
        except (TypeError, ValueError):
            return _promotion_violation(
                "external STATE_EVENT promotion freshness is not numeric",
                details={**details, "freshness_ms": freshness_ms},
                severity_map=severity_map,
            )
        if freshness_value < 0:
            return _promotion_violation(
                "external STATE_EVENT promotion freshness is negative",
                details={**details, "freshness_ms": freshness_ms},
                severity_map=severity_map,
            )
        max_by_profile = global_cfg.get("max_freshness_ms_by_profile", {})
        if not isinstance(max_by_profile, dict):
            max_by_profile = {}
        max_freshness = max_by_profile.get(profile, max_by_profile.get("default"))
        if max_freshness is not None:
            try:
                max_freshness = float(max_freshness)
            except (TypeError, ValueError):
                max_freshness = None
        if max_freshness is not None and freshness_value > max_freshness:
            return _promotion_violation(
                "external STATE_EVENT promotion freshness exceeds policy",
                details={**details, "freshness_ms": freshness_ms, "max_freshness_ms": max_freshness},
                severity_map=severity_map,
            )

    return None


def _mode_for_profile(policy, key, profile, default="warn"):
    if not isinstance(policy, dict):
        return default
    value = policy.get(key, default)
    if isinstance(value, dict):
        value = value.get(profile, value.get("default", default))
    mode = str(value or default).strip().lower()
    if mode not in {"ignore", "warn", "reject"}:
        return default
    return mode


def _mode_severity(mode):
    return "fail" if mode == "reject" else "warn"


def _mode_violation(
    code,
    message,
    mode,
    details=None,
    severity_map=None,
    risk_dimension=None,
    policy=None,
    policy_ref=None,
):
    if mode == "ignore":
        return None
    details = dict(details or {})
    if risk_dimension:
        details = _risk_details(
            details,
            risk_dimension,
            mode,
            policy=policy,
            policy_ref=policy_ref,
        )
    else:
        details["policy_mode"] = mode
    return _violation(
        code,
        message,
        details=details,
        severity_map=severity_map,
        severity=_mode_severity(mode),
    )


_NON_MATERIAL_IGNORE_ALLOWLIST = {
    ("lineage", "unresolved_parent_mode", "L", "LINEAGE_PARENT_UNRESOLVED"),
}


def _policy_mode_entries(section, config, key, reason_codes, risk_dimension):
    if not isinstance(config, dict) or key not in config:
        return
    value = config.get(key)
    if isinstance(value, dict):
        for profile, mode in value.items():
            yield {
                "section": section,
                "path": f"{section}.{key}.{profile}",
                "key": key,
                "profile": str(profile),
                "mode": str(mode or "").strip().lower(),
                "risk_dimension": risk_dimension,
                "reason_codes": list(reason_codes),
            }
        return
    yield {
        "section": section,
        "path": f"{section}.{key}",
        "key": key,
        "profile": None,
        "mode": str(value or "").strip().lower(),
        "risk_dimension": risk_dimension,
        "reason_codes": list(reason_codes),
    }


def _ignore_is_allowlisted(entry):
    profile = entry.get("profile")
    if profile is None:
        return False
    for reason_code in entry.get("reason_codes", []):
        key = (entry.get("section"), entry.get("key"), profile, reason_code)
        if key not in _NON_MATERIAL_IGNORE_ALLOWLIST:
            return False
    return True


# Risk dimension and reason codes for each policy BLOCK this lint reads, so a
# destroyed block can be reported with the same fields as any other issue.
# Nothing minted: every dimension and every reason code below is already in
# use elsewhere in this module and in policy/violation-codes.yaml.
_POLICY_BLOCK_RISK = {
    "timing_freshness": (
        "timing",
        ["TIMING_STATUS_MISSING", "TIMING_STATUS_STALE", "TIMING_STATUS_AGE_NEGATIVE"],
    ),
    "timing_freshness.holdover_est_error_monotonic": (
        "timing",
        ["TIMING_STATUS_HOLDOVER_NON_MONOTONIC"],
    ),
    "lineage": ("lineage", ["LINEAGE_PARENT_UNRESOLVED"]),
    "command_evidence": (
        "lineage",
        ["LINEAGE_PARENT_UNRESOLVED", "LINEAGE_PARENT_TYPE_INVALID", "LINEAGE_MISMATCH"],
    ),
    "producer_authority": ("external_promotion", ["PRODUCER_NOT_ALLOWED"]),
    "producer_authority.external_state_promotion": (
        "external_promotion",
        ["PRODUCER_NOT_ALLOWED"],
    ),
}


def _mapping_or_empty(container, key, path, emit):
    """Read one policy block, coercing a mangled one to ``{}`` — and SAY SO.

    The coercion exists because an unhandled ``AttributeError`` out of the
    FIRST lint is not a diagnostic: it aborts the run before the structure
    lints get to name the defect (R1-11 A-05 residual d). But a coercion that
    reports nothing is worse than the crash it replaced — it substitutes a
    clean, empty, entirely legal-looking block for a destroyed one and prints
    ``policy risk mode lint ok``. That is exactly what happened to
    ``timing_freshness``: the gate was fully disabled with the operator-facing
    lint green (R1-11 B-02).

    So reporting is not optional here — ``emit`` and ``path`` are required
    arguments, and a caller cannot add a new block to this lint without
    deciding how a destroyed one is announced.

    ABSENCE stays legal and silent: a block that is not present at all is the
    documented "no policy of this kind" deployment, and ``load_policy`` gives
    an absent file an empty mapping rather than this shape.
    """
    if key not in container:
        return {}
    value = container[key]
    if isinstance(value, dict):
        return value
    emit(path, value)
    return {}


def lint_policy_risk_modes(policy):
    """Return policy lint issues for risk modes that can hide material risk."""
    issues = []
    if not isinstance(policy, dict):
        return issues

    def _block_issue(path, value):
        risk_dimension, reason_codes = _POLICY_BLOCK_RISK[path]
        issues.append(
            {
                # Existing lint code, reused rather than minted, exactly as
                # the routing structure lint reuses it. The path and
                # risk_dimension carry which block is broken.
                "code": "POLICY_PRODUCER_AUTHORITY_STRUCTURE",
                "path": path,
                "risk_dimension": risk_dimension,
                "reason_codes": list(reason_codes),
                "message": (
                    f"{path} must be a mapping; got {type(value).__name__}. A "
                    "bare key or wrong-typed value here is read as an empty "
                    "block, which switches every check this block configures "
                    "off while the rest of the lint stays green"
                ),
            }
        )

    entries = []
    timing = _mapping_or_empty(policy, "timing_freshness", "timing_freshness", _block_issue)
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "mode",
            ["TIMING_STATUS_MISSING", "TIMING_STATUS_STALE", "TIMING_STATUS_AGE_NEGATIVE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "mode_by_profile",
            ["TIMING_STATUS_MISSING", "TIMING_STATUS_STALE", "TIMING_STATUS_AGE_NEGATIVE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "missing_mode",
            ["TIMING_STATUS_MISSING"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "missing_mode_by_profile",
            ["TIMING_STATUS_MISSING"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "stale_mode",
            ["TIMING_STATUS_STALE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "stale_mode_by_profile",
            ["TIMING_STATUS_STALE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "negative_age_mode",
            ["TIMING_STATUS_AGE_NEGATIVE"],
            "timing",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness",
            timing,
            "negative_age_mode_by_profile",
            ["TIMING_STATUS_AGE_NEGATIVE"],
            "timing",
        )
    )
    holdover = _mapping_or_empty(
        timing,
        "holdover_est_error_monotonic",
        "timing_freshness.holdover_est_error_monotonic",
        _block_issue,
    )
    entries.extend(
        _policy_mode_entries(
            "timing_freshness.holdover_est_error_monotonic",
            holdover,
            "mode",
            ["TIMING_STATUS_HOLDOVER_NON_MONOTONIC"],
            "timing",
        )
    )

    lineage = _mapping_or_empty(policy, "lineage", "lineage", _block_issue)
    entries.extend(
        _policy_mode_entries(
            "lineage",
            lineage,
            "payload_based_on_subset_mode",
            ["LINEAGE_PAYLOAD_BASED_ON_NOT_SUBSET"],
            "lineage",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "lineage",
            lineage,
            "fusion_members_in_lineage_mode",
            ["LINEAGE_FUSION_MEMBERS_NOT_IN_BASED_ON"],
            "lineage",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "lineage",
            lineage,
            "unresolved_parent_mode",
            ["LINEAGE_PARENT_UNRESOLVED"],
            "lineage",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "lineage",
            lineage,
            "parent_type_mismatch_mode",
            ["LINEAGE_PARENT_TYPE_INVALID"],
            "lineage",
        )
    )

    # Command-evidence: the command-tier sibling of the lineage checks above.
    # ignore is never legal here — a command resting on unresolved, wrong-type,
    # or command-prohibited evidence is material command risk at every profile.
    command_evidence = _mapping_or_empty(
        policy, "command_evidence", "command_evidence", _block_issue
    )
    entries.extend(
        _policy_mode_entries(
            "command_evidence",
            command_evidence,
            "require_evidence_mode",
            ["LINEAGE_MISMATCH"],
            "lineage",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "command_evidence",
            command_evidence,
            "unresolved_parent_mode",
            ["COMMAND_EVIDENCE_UNRESOLVED"],
            "lineage",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "command_evidence",
            command_evidence,
            "parent_type_mismatch_mode",
            ["LINEAGE_PARENT_TYPE_INVALID"],
            "lineage",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "command_evidence",
            command_evidence,
            "prohibited_use_mode",
            ["COMMAND_EVIDENCE_PROHIBITED"],
            "lineage",
        )
    )

    # producer_authority is ALSO reported by lint_producer_authority_structure.
    # The duplicate is deliberate: "coerce only where another lint happens to
    # speak" is the arrangement that produced B-02, and it fails silently the
    # moment a block is added or a lint is moved. Every coercion here reports
    # for itself.
    producer_authority = _mapping_or_empty(
        policy, "producer_authority", "producer_authority", _block_issue
    )
    promotion = _mapping_or_empty(
        producer_authority,
        "external_state_promotion",
        "producer_authority.external_state_promotion",
        _block_issue,
    )
    entries.extend(
        _policy_mode_entries(
            "producer_authority.external_state_promotion",
            promotion,
            "mode",
            ["PRODUCER_NOT_ALLOWED"],
            "external_promotion",
        )
    )
    entries.extend(
        _policy_mode_entries(
            "producer_authority.external_state_promotion",
            promotion,
            "mode_by_profile",
            ["PRODUCER_NOT_ALLOWED"],
            "external_promotion",
        )
    )
    producers = producer_authority.get("producers", {})
    if isinstance(producers, dict):
        for producer, producer_rule in producers.items():
            if not isinstance(producer_rule, dict):
                continue
            rule = producer_rule.get("external_state_promotion", {})
            if not isinstance(rule, dict):
                continue
            section = f"producer_authority.producers.{producer}.external_state_promotion"
            entries.extend(
                _policy_mode_entries(
                    section,
                    rule,
                    "mode",
                    ["PRODUCER_NOT_ALLOWED"],
                    "external_promotion",
                )
            )
            entries.extend(
                _policy_mode_entries(
                    section,
                    rule,
                    "mode_by_profile",
                    ["PRODUCER_NOT_ALLOWED"],
                    "external_promotion",
                )
            )

    for entry in entries:
        if entry.get("mode") != "ignore" or _ignore_is_allowlisted(entry):
            continue
        issues.append(
            {
                "code": "POLICY_IGNORE_MATERIAL_RISK",
                "path": entry["path"],
                "risk_dimension": entry["risk_dimension"],
                "reason_codes": entry["reason_codes"],
                "message": (
                    "ignore is only allowed for explicitly non-material checks; "
                    "material timing, lineage, promotion, command, trust, or safety "
                    "risk must be rejected, warned, degraded, quarantined, or labeled"
                ),
            }
        )
    issues.extend(_lint_command_evidence_keys(command_evidence))
    return issues


# Every key the command-evidence enforcement reads. A knob the enforcement
# consults through .get() with a permissive default fails OPEN on a typo -
# `unresolved_parent_mod: reject` leaves the shipped `warn` in force with
# every lint green - which is the exact class this module already refuses to
# tolerate elsewhere ("a typo is the same fail-open as a wrong type").
_COMMAND_EVIDENCE_KEYS = {
    "enabled",
    "require_evidence",
    "require_evidence_task_types",
    "require_evidence_mode",
    "unresolved_parent_mode",
    "parent_type_mismatch_mode",
    "prohibited_use_mode",
    "motivating_parent_event_types",
    "command_basis_use_tokens",
    "evidence_index_max_entries",
    "use_limits",
}

_COMMAND_EVIDENCE_KEY_TYPES = {
    "enabled": bool,
    "require_evidence": bool,
    "require_evidence_task_types": list,
    "motivating_parent_event_types": list,
    "command_basis_use_tokens": list,
    "evidence_index_max_entries": int,
    "use_limits": dict,
}


def _lint_command_evidence_keys(block):
    """Report unknown or wrong-typed keys in the command-evidence block.

    Pre-cut review finding: the block had mode-VALUE and wrapper-KEY lints
    but nothing checking key NAMES or value TYPES, so a one-character typo
    in any knob silently reverted that knob to its permissive shipped
    default while `policy risk mode lint ok` still printed.
    """
    issues = []
    if not isinstance(block, dict) or not block:
        return issues
    for key in sorted(block):
        if key not in _COMMAND_EVIDENCE_KEYS:
            issues.append(
                {
                    "code": "POLICY_PRODUCER_AUTHORITY_STRUCTURE",
                    "path": f"command_evidence.{key}",
                    "risk_dimension": "lineage",
                    "reason_codes": ["LINEAGE_MISMATCH"],
                    "message": (
                        f"unknown command-evidence key {key!r}; the enforcement "
                        "never reads it, so a misspelled knob leaves the shipped "
                        "default in force with the rest of the lint green"
                    ),
                }
            )
            continue
        expected = _COMMAND_EVIDENCE_KEY_TYPES.get(key)
        if expected is None:
            continue
        value = block[key]
        if expected is bool:
            ok = isinstance(value, bool)
        elif expected is int:
            ok = isinstance(value, int) and not isinstance(value, bool)
        else:
            ok = isinstance(value, expected)
        if not ok:
            issues.append(
                {
                    "code": "POLICY_PRODUCER_AUTHORITY_STRUCTURE",
                    "path": f"command_evidence.{key}",
                    "risk_dimension": "lineage",
                    "reason_codes": ["LINEAGE_MISMATCH"],
                    "message": (
                        f"command_evidence.{key} must be {expected.__name__}; got "
                        f"{type(value).__name__}, which the enforcement reads as "
                        "its permissive default"
                    ),
                }
            )
    return issues


# Producer-authority structural vocabulary. validate_producer_authority
# reads these blocks with .get() defaults, so a typoed key or a deleted
# promotion sub-block silently disables enforcement while every gate stays
# green (R1-11 R11-05) — structural drift must fail the lint instead.
_PRODUCER_AUTHORITY_TOP_KEYS = frozenset(
    {"enabled", "producers", "require_match_for_event_types", "external_state_promotion"}
)
# allowed_event_subtypes is read and ENFORCED by validate_producer_authority
# ("event_subtype not authorized for producer") and is documented producer-rule
# vocabulary at policy/README.md, but was absent from this set — so the lint
# failed a legal, working policy and told the operator the control was a typo
# that "silently disables enforcement". The remedy that message prescribed —
# delete the key — removes a subtype restriction that was actually in force,
# turning a correct configuration into a weaker one (R1-11 A-15). Nothing is
# minted by listing it: the key already governs live traffic, and its ENTRY
# vocabulary stays unchecked (see _LIST_ENTRY_VOCABULARIES and the open
# question R1-11-11 in docs/zmeta_doctrine_review_log.md).
_PRODUCER_ENTRY_KEYS = frozenset(
    {
        "allowed_event_types",
        "allowed_event_subtypes",
        "forbidden_event_types",
        "external_state_promotion",
    }
)
# Keys the enforcement actually reads PER RULE (_external_promotion_rules,
# _promotion_mode, _union_rule_values). Nothing else has per-producer effect:
# every other promotion key is read only from the GLOBAL
# producer_authority.external_state_promotion block, so a per-producer copy is
# a silent no-op the lint must flag, not bless (R1-11 verification pass 2).
_PROMOTION_RULE_KEYS = frozenset(
    {
        "required",
        "mode",
        "mode_by_profile",
        "approved_policy_ids",
        "allowed_projection_ids",
        "allowed_confidence_basis",
    }
)
# Keys the enforcement reads from the GLOBAL external_state_promotion block
# (_validate_external_state_promotion, apply_external_promotion_policy_action,
# _promotion_mode, _risk_use_limits). A typo here silently reverts that gate
# to its .get() default while every lint stayed green — the exact R11-05
# failure mode, one block over.
_GLOBAL_PROMOTION_KEYS = frozenset(
    {
        "enabled",
        "mode",
        "mode_by_profile",
        "metadata_path",
        "required_fields_by_profile",
        "required_state_category",
        "allowed_origin_kinds",
        "allowed_lineage_status_by_profile",
        "source_event_uid_required_statuses",
        "required_trust_ref_prefixes",
        "loop_risk_statuses",
        "always_reject_loop_risk",
        "allowed_loop_statuses",
        "required_lineage_transform_prefixes",
        "max_freshness_ms_by_profile",
        "degrade",
        "quarantine",
        "use_limits",
    }
)
_PROMOTION_DEGRADE_KEYS = frozenset(
    {"confidence_reduction_factor", "valid_for_ms_reduction_factor"}
)
_PROMOTION_QUARANTINE_KEYS = frozenset({"confidence_cap", "valid_for_ms_cap"})
_PROMOTION_USE_LIMIT_MODES = frozenset({"warn", "degrade", "quarantine", "reject"})
_PROMOTION_USE_LIMIT_KEYS = frozenset({"allowed_uses", "prohibited_uses"})

# Declared VALUE SHAPE for every producer-authority key the enforcement reads
# (R1-11 A-05/A-07). The key-NAME diffs above catch a typo; they do not catch
# a key of the wrong TYPE, which is the same failure with a green light. The
# enforcement reads each of these through an isinstance guard or _list_values,
# so a wrong-typed value collapses to "no constraint" and the gate stops
# refusing (fail open) — or, where there is no guard at all, is iterated
# directly and raises on every event (total outage). Absence stays legal:
# a key that is not present is the documented "no constraint" configuration.
# A key that IS present, including present-with-null, must carry its shape.
_SHAPE_LIST = ("list", (list, tuple))
_SHAPE_MAPPING = ("mapping", (dict,))
_SHAPE_STRING = ("string", (str,))
_SHAPE_BOOL = ("boolean", (bool,))
_SHAPE_NUMBER = ("number", (int, float))

_PRODUCER_AUTHORITY_TOP_SHAPES = {
    "enabled": _SHAPE_BOOL,
    "producers": _SHAPE_MAPPING,
    "require_match_for_event_types": _SHAPE_LIST,
    "external_state_promotion": _SHAPE_MAPPING,
}
_PRODUCER_ENTRY_SHAPES = {
    "allowed_event_types": _SHAPE_LIST,
    # R1-11 A-15: same key, same collapse-to-"no constraint" reading through
    # _list_values as its routing twin in _ROUTING_PRODUCER_ENTRY_SHAPES.
    "allowed_event_subtypes": _SHAPE_LIST,
    "forbidden_event_types": _SHAPE_LIST,
    "external_state_promotion": _SHAPE_MAPPING,
}
_PROMOTION_RULE_SHAPES = {
    "required": _SHAPE_BOOL,
    "mode": _SHAPE_STRING,
    "mode_by_profile": _SHAPE_MAPPING,
    "approved_policy_ids": _SHAPE_LIST,
    "allowed_projection_ids": _SHAPE_LIST,
    "allowed_confidence_basis": _SHAPE_LIST,
}
_GLOBAL_PROMOTION_SHAPES = {
    "enabled": _SHAPE_BOOL,
    "mode": _SHAPE_STRING,
    "mode_by_profile": _SHAPE_MAPPING,
    "metadata_path": _SHAPE_STRING,
    "required_fields_by_profile": _SHAPE_MAPPING,
    "required_state_category": _SHAPE_STRING,
    "allowed_origin_kinds": _SHAPE_LIST,
    "allowed_lineage_status_by_profile": _SHAPE_MAPPING,
    "source_event_uid_required_statuses": _SHAPE_LIST,
    "required_trust_ref_prefixes": _SHAPE_LIST,
    "loop_risk_statuses": _SHAPE_LIST,
    "always_reject_loop_risk": _SHAPE_BOOL,
    "allowed_loop_statuses": _SHAPE_LIST,
    "required_lineage_transform_prefixes": _SHAPE_LIST,
    "max_freshness_ms_by_profile": _SHAPE_MAPPING,
    "degrade": _SHAPE_MAPPING,
    "quarantine": _SHAPE_MAPPING,
    "use_limits": _SHAPE_MAPPING,
}
# The same mangle one level down. Deleting the items under a by-profile key
# leaves "L:" -> None, which _list_values reads as the empty list and the
# freshness bound reads as "no bound" — the A-05 bare-key shape applied to a
# sub-key, and just as invisible to a key-name diff.
_GLOBAL_PROMOTION_VALUE_SHAPES = {
    "mode_by_profile": _SHAPE_STRING,
    "required_fields_by_profile": _SHAPE_LIST,
    "allowed_lineage_status_by_profile": _SHAPE_LIST,
    "max_freshness_ms_by_profile": _SHAPE_NUMBER,
    "degrade": _SHAPE_NUMBER,
    "quarantine": _SHAPE_NUMBER,
}
_PROMOTION_RULE_VALUE_SHAPES = {
    "mode_by_profile": _SHAPE_STRING,
}
_PROMOTION_USE_LIMIT_ENTRY_SHAPES = {
    "allowed_uses": _SHAPE_LIST,
    "prohibited_uses": _SHAPE_LIST,
}
# Routing carries the second member of the require-match family: the
# COMMAND_EVENT origin gate at validate_routing reads this key with the same
# unguarded iteration as producer_authority.require_match_for_event_types.
_ROUTING_PRODUCER_ENFORCEMENT_SHAPES = {
    "require_allowlist_for_event_types": _SHAPE_LIST,
}
# ...and the rest of the routing block, which had no shape table at all while
# the structurally identical producer-authority side had one for every key
# (R1-11 A-05 residual b). validate_routing reads routing.producers.<p>.* with
# the same _list_values collapse-to-"no constraint" semantics, and
# _is_comms_producer dereferences routing.command_event with no type guard.
_ROUTING_TOP_SHAPES = {
    "producers": _SHAPE_MAPPING,
    "producer_enforcement": _SHAPE_MAPPING,
    "command_event": _SHAPE_MAPPING,
}
_ROUTING_PRODUCER_ENTRY_SHAPES = {
    "allowed_event_types": _SHAPE_LIST,
    "allowed_event_subtypes": _SHAPE_LIST,
    "forbidden_event_types": _SHAPE_LIST,
}
# _is_comms_producer flattens these three into one origin allowlist. A
# wrong-typed value is skipped by its isinstance filter, so the entry drops
# out of the COMMAND_EVENT origin gate with no diagnostic anywhere.
_ROUTING_COMMAND_EVENT_SHAPES = {
    "allowed_producers": _SHAPE_LIST,
    "required_origin": _SHAPE_STRING,
    "must_pass_through": _SHAPE_STRING,
}
# Key NAMES, the other half of the treatment the producer-authority side
# already had. Measured: `producrs:` in routing.yaml linted green and admitted
# an event the shipped policy refuses — a typo is the same fail-open as a
# wrong type, and the shape tables cannot see it. Vocabulary documented at
# policy/README.md; nothing minted.
_ROUTING_TOP_KEYS = frozenset(_ROUTING_TOP_SHAPES)
_ROUTING_PRODUCER_ENTRY_KEYS = frozenset(_ROUTING_PRODUCER_ENTRY_SHAPES)
_ROUTING_COMMAND_EVENT_KEYS = frozenset(_ROUTING_COMMAND_EVENT_SHAPES)
# List keys whose ENTRIES are compared against an event field. A well-formed
# string that is not in the schema's vocabulary disables its entry exactly as
# silently as a non-string one, so the entry check has to know which field the
# entries are matched against (R1-11 A-05 residual c).
#
# event_type only. The event_subtype vocabulary is deliberately open —
# spec/extension-registry.yaml registers subtypes that are not yet
# schema-valid — so an unknown subtype token is not decidable from the schema
# and asserting one here would be a vocabulary claim this lint cannot make.
_LIST_ENTRY_VOCABULARIES = {
    "require_match_for_event_types": "event_type",
    "require_allowlist_for_event_types": "event_type",
    "allowed_event_types": "event_type",
    "forbidden_event_types": "event_type",
}


def _shape_ok(value, types):
    if types == (bool,):
        return isinstance(value, bool)
    if isinstance(value, bool):
        # A bare bool is never a list/mapping/string, and bool is an int
        # subclass, so reject it explicitly rather than by accident.
        return False
    return isinstance(value, types)


def _shape_problem(name, value, shape):
    """Return an operator-facing message if ``value`` is not ``shape``."""
    label, types = shape
    if types is _SHAPE_NUMBER[1] and isinstance(value, float) and not math.isfinite(value):
        # YAML .nan / .inf are legal floats. A NaN bound compares false
        # against everything, so the bound silently stops bounding.
        return (
            f"{name} must be a finite number: {value} disables this bound "
            "without disabling the key"
        )
    if not _shape_ok(value, types):
        return (
            f"{name} must be a {label}: a wrong-typed value here is read as "
            "'no constraint' and silently stops this check from refusing, or "
            "is iterated directly and fails every event, while the key-name "
            "checks stay green"
        )
    if types is not _SHAPE_LIST[1]:
        return None
    # A trailing colon turns a list ITEM into a one-key mapping
    # ("- STATE_EVENT:"), which every reader stringifies into a token that can
    # never match an event type or status — the same silent disablement one
    # level down.
    bad = [
        index
        for index, item in enumerate(value)
        if not isinstance(item, str) or not item.strip()
    ]
    if bad:
        return (
            f"{name} entries must be non-empty strings: entries {bad} are not, "
            "and a non-string entry is stringified into a token that can never "
            "match, silently dropping it from this check"
        )
    field = _LIST_ENTRY_VOCABULARIES.get(name)
    if field is None:
        return None
    # A STRING that can never match has the identical effect to the
    # stringified non-string above: one character (`STATE_EVEN`,
    # `state_event`) drops that entry out of the gate with every check green.
    vocabulary = _event_vocabulary(field)
    if not vocabulary:
        return (
            f"{name} entries could not be checked: the {field} vocabulary "
            "could not be derived from schema/*.schema.json, so this check "
            "did not run"
        )
    unknown = sorted({item.strip() for item in value} - set(vocabulary))
    if unknown:
        return (
            f"{name} entries must be {field} values the schema declares: "
            f"{unknown} match nothing an event can carry, so each one is "
            "silently dropped from this check"
        )
    return None


def _shape_issues(base, block, shapes, emit):
    """Emit one issue per present-but-wrong-shaped key in ``block``."""
    if not isinstance(block, dict):
        return
    for key in sorted(shapes):
        if key not in block:
            continue
        problem = _shape_problem(key, block[key], shapes[key])
        if problem:
            emit(f"{base}.{key}", problem)


def _value_shape_issues(base, block, value_shapes, emit):
    """Emit one issue per wrong-shaped VALUE inside a mapping-shaped key."""
    if not isinstance(block, dict):
        return
    for key in sorted(value_shapes):
        mapping = block.get(key)
        if not isinstance(mapping, dict):
            # Absent, or already reported by the key-level shape check.
            continue
        for sub_key in sorted(mapping, key=str):
            problem = _shape_problem(
                f"{key}.{sub_key}", mapping[sub_key], value_shapes[key]
            )
            if problem:
                emit(f"{base}.{key}.{sub_key}", problem)


def lint_producer_authority_structure(policy):
    """Return lint issues for structurally mangled producer-authority policy."""
    issues = []
    if not isinstance(policy, dict):
        return issues
    authority = policy.get("producer_authority")

    def _issue(path, message):
        issues.append(
            {
                "code": "POLICY_PRODUCER_AUTHORITY_STRUCTURE",
                "path": path,
                "risk_dimension": "external_promotion",
                "reason_codes": ["PRODUCER_NOT_ALLOWED"],
                "message": message,
            }
        )

    if not isinstance(authority, dict):
        # NOT a silent early return. `producer_authority:` truncated to a bare
        # key loads as None and switches the entire authority gate off; an
        # absent policy file loads as {} and is the documented "no authority
        # policy" deployment. Reporting the first is the whole point of this
        # function, one container up (R1-11 A-05 residual d).
        _issue(
            "producer_authority",
            "producer_authority must be a mapping: a bare key or wrong-typed "
            "value here switches the whole authority gate off, and an absent "
            "policy file is an empty mapping rather than this shape",
        )
        return issues

    for key in sorted(set(authority) - _PRODUCER_AUTHORITY_TOP_KEYS):
        _issue(
            f"producer_authority.{key}",
            "unknown producer-authority key: a typo here silently disables enforcement",
        )
    _shape_issues("producer_authority", authority, _PRODUCER_AUTHORITY_TOP_SHAPES, _issue)

    global_promotion = authority.get("external_state_promotion")
    if isinstance(global_promotion, dict):
        base = "producer_authority.external_state_promotion"
        for key in sorted(set(global_promotion) - _GLOBAL_PROMOTION_KEYS):
            _issue(
                f"{base}.{key}",
                "unknown global promotion key: a typo here silently reverts the "
                "gate to its default while every check stays green",
            )
        # A sub-block of the wrong TYPE is the same failure as a typo: the
        # enforcement reads it with .get() and falls back to its built-in
        # default, so it must fail the lint rather than be skipped over. The
        # type half is now table-driven for every key in the block; only the
        # sub-key vocabulary walk stays here.
        _shape_issues(base, global_promotion, _GLOBAL_PROMOTION_SHAPES, _issue)
        _value_shape_issues(
            base, global_promotion, _GLOBAL_PROMOTION_VALUE_SHAPES, _issue
        )
        for sub, allowed in (
            ("degrade", _PROMOTION_DEGRADE_KEYS),
            ("quarantine", _PROMOTION_QUARANTINE_KEYS),
        ):
            block = global_promotion.get(sub)
            if not isinstance(block, dict):
                # Absent is legal; present-but-wrong-shaped was already
                # reported by the shape check above.
                continue
            for key in sorted(set(block) - allowed):
                _issue(
                    f"{base}.{sub}.{key}",
                    f"unknown {sub} key: a typo here silently reverts the "
                    "action to its built-in default",
                )
        use_limits = global_promotion.get("use_limits")
        if isinstance(use_limits, dict):
            for mode in sorted(set(use_limits) - _PROMOTION_USE_LIMIT_MODES):
                _issue(
                    f"{base}.use_limits.{mode}",
                    "unknown use_limits mode: a typo here silently drops the "
                    "allowed/prohibited-use labels from that mode's diagnostics",
                )
            for mode in sorted(set(use_limits) & _PROMOTION_USE_LIMIT_MODES):
                limits = use_limits[mode]
                if not isinstance(limits, dict):
                    _issue(
                        f"{base}.use_limits.{mode}",
                        "use-limit entry must be a mapping: a non-mapping here "
                        "silently drops the label from promotion diagnostics",
                    )
                    continue
                for key in sorted(set(limits) - _PROMOTION_USE_LIMIT_KEYS):
                    _issue(
                        f"{base}.use_limits.{mode}.{key}",
                        "unknown use-limit key: a typo here silently drops the "
                        "label from promotion diagnostics",
                    )
                _shape_issues(
                    f"{base}.use_limits.{mode}",
                    limits,
                    _PROMOTION_USE_LIMIT_ENTRY_SHAPES,
                    _issue,
                )

    producers = authority.get("producers")
    if not isinstance(producers, dict):
        if "producers" not in authority and authority:
            # An EMPTY authority block is the documented "no producer-authority
            # policy" deployment — load_policy produces exactly {} for an
            # absent producer-authority.yaml — so demanding `producers` there
            # failed a legal configuration (R1-11 R2-24). A block that
            # configures something else but has no `producers` table is still
            # the drift this check exists to catch.
            _issue("producer_authority.producers", "producers must be a mapping")
        # A present-but-wrong-shaped producers block was already reported by
        # the top-level shape check; either way there is nothing to walk.
        return issues
    for name in sorted(producers):
        cfg = producers[name]
        base = f"producer_authority.producers.{name}"
        if not isinstance(cfg, dict):
            _issue(base, "producer entry must be a mapping")
            continue
        for key in sorted(set(cfg) - _PRODUCER_ENTRY_KEYS):
            _issue(
                f"{base}.{key}",
                "unknown producer entry key: a typo here silently disables enforcement",
            )
        _shape_issues(base, cfg, _PRODUCER_ENTRY_SHAPES, _issue)
        promotion = cfg.get("external_state_promotion")
        if not isinstance(promotion, dict):
            # Absent is legal; present-but-wrong-shaped was already reported.
            continue
        _shape_issues(
            f"{base}.external_state_promotion",
            promotion,
            _PROMOTION_RULE_SHAPES,
            _issue,
        )
        _value_shape_issues(
            f"{base}.external_state_promotion",
            promotion,
            _PROMOTION_RULE_VALUE_SHAPES,
            _issue,
        )
        for key in sorted(set(promotion) - _PROMOTION_RULE_KEYS):
            if key in _GLOBAL_PROMOTION_KEYS:
                _issue(
                    f"{base}.external_state_promotion.{key}",
                    "global-only promotion key: enforcement reads this key only "
                    "from producer_authority.external_state_promotion, so a "
                    "per-producer override here is a silent no-op",
                )
            else:
                _issue(
                    f"{base}.external_state_promotion.{key}",
                    "unknown promotion-rule key: a typo here silently disables enforcement",
                )
        if "required" not in promotion:
            # A present-but-non-bool value is reported by the shape check.
            _issue(
                f"{base}.external_state_promotion.required",
                "required must be an explicit boolean: absent or non-bool values "
                "silently disable promotion enforcement (cfg.get default)",
            )
    return issues


def lint_routing_producer_enforcement_structure(policy):
    """Return lint issues for a structurally mangled routing gate.

    ``routing.producer_enforcement.require_allowlist_for_event_types`` is the
    second member of the require-match family: validate_routing iterates it
    with no type guard, so a bare key raises on every event and a scalar
    silently empties the allowlist gate (R1-11 A-05 class).

    The rest of the routing block gets the same treatment the
    producer-authority side already had: the block that HOLDS the gate, the
    per-producer rules that carry the same collapse-to-"no constraint" list
    keys, and the command_event block ``_is_comms_producer`` dereferences
    (R1-11 A-05 residuals a and b).
    """
    issues = []
    if not isinstance(policy, dict):
        return issues
    routing = policy.get("routing")

    def _issue(path, message):
        issues.append(
            {
                # Existing lint code and reason code; `routing` is the
                # contract's own risk dimension for this gate
                # (spec/semantics-contract.md:317-319). Nothing minted.
                "code": "POLICY_PRODUCER_AUTHORITY_STRUCTURE",
                "path": path,
                "risk_dimension": "routing",
                "reason_codes": ["PRODUCER_NOT_ALLOWED"],
                "message": message,
            }
        )

    if not isinstance(routing, dict):
        # NOT a silent early return: this is the exact bare-key/wrong-type
        # mangle this function exists to catch, applied to the block that
        # holds the key. Measured before the fix: CLI exit 0 while every
        # event raised AttributeError (R1-11 A-05 residual a).
        _issue(
            "routing",
            "routing must be a mapping: a bare key or wrong-typed value here "
            "takes down every routing decision and leaves the allowlist gate "
            "with nothing to read",
        )
        return issues

    for key in sorted(set(routing) - _ROUTING_TOP_KEYS, key=str):
        _issue(
            f"routing.{key}",
            "unknown routing key: a typo here silently drops the whole block "
            "it renames, and the shape checks cannot see a key that is not "
            "there",
        )
    _shape_issues("routing", routing, _ROUTING_TOP_SHAPES, _issue)

    enforcement = routing.get("producer_enforcement")
    if "producer_enforcement" in routing:
        if not isinstance(enforcement, dict):
            _issue(
                "routing.producer_enforcement",
                "producer_enforcement must be a mapping: a wrong-typed value "
                "here silently empties the routing allowlist gate",
            )
        else:
            _shape_issues(
                "routing.producer_enforcement",
                enforcement,
                _ROUTING_PRODUCER_ENFORCEMENT_SHAPES,
                _issue,
            )

    command_event = routing.get("command_event")
    if isinstance(command_event, dict):
        for key in sorted(set(command_event) - _ROUTING_COMMAND_EVENT_KEYS, key=str):
            _issue(
                f"routing.command_event.{key}",
                "unknown command_event key: a typo here silently drops that "
                "origin from the COMMAND_EVENT allowlist",
            )
        _shape_issues(
            "routing.command_event",
            command_event,
            _ROUTING_COMMAND_EVENT_SHAPES,
            _issue,
        )

    producers = routing.get("producers")
    if isinstance(producers, dict):
        for name in sorted(producers, key=str):
            entry = producers[name]
            base = f"routing.producers.{name}"
            if not isinstance(entry, dict):
                _issue(
                    base,
                    "routing producer entry must be a mapping: a bare key here "
                    "drops every constraint on that producer while the gate "
                    "still looks configured",
                )
                continue
            for key in sorted(set(entry) - _ROUTING_PRODUCER_ENTRY_KEYS, key=str):
                _issue(
                    f"{base}.{key}",
                    "unknown routing producer entry key: a typo here silently "
                    "drops that constraint on the producer",
                )
            _shape_issues(base, entry, _ROUTING_PRODUCER_ENTRY_SHAPES, _issue)
    return issues


# load_policy unwraps each document with `.get("<wrapper>", <default>)`, so a
# MISSPELLED top-level key does not fail to load — it silently yields the
# permissive default. Measured: `routng:` in routing.yaml linted green while
# the routing producer allowlist failed OPEN (R1-11 A-05 residual a). The
# in-memory lints structurally cannot see this: by the time they run, a typoed
# wrapper and a legitimately empty block are the same object. Only a check
# that reads the DOCUMENT can tell them apart.
#
# The third element says whether load_policy treats an ABSENT file as a legal
# deployment. It has to, because load_policy makes an absent file and an
# empty/comment-only one byte-identical in memory: both become the permissive
# default. Reporting the empty file while skipping the absent one failed a
# deployment that the same function deliberately blesses one line up
# (R1-11 R2-24). routing.yaml is different — load_policy REQUIRES it, so an
# empty routing.yaml is not equivalent to anything legal: it silently empties
# every routing gate and must still be reported.
_POLICY_DOCUMENT_WRAPPERS = {
    # filename: (wrapper key, risk_dimension, absence_is_legal, reason codes
    # the gate this document configures refuses under — so a mangled wrapper
    # is filterable by the same codes as the enforcement it disables).
    "producer-authority.yaml": (
        "producer_authority",
        "external_promotion",
        True,
        ["PRODUCER_NOT_ALLOWED"],
    ),
    "routing.yaml": ("routing", "routing", False, ["PRODUCER_NOT_ALLOWED"]),
    "command-evidence.yaml": (
        "command_evidence",
        "lineage",
        True,
        ["LINEAGE_PARENT_UNRESOLVED", "LINEAGE_PARENT_TYPE_INVALID", "LINEAGE_MISMATCH"],
    ),
}


def lint_policy_document_structure(policy_dir):
    """Return lint issues for authorization documents with a mangled wrapper key."""
    issues = []
    directory = Path(policy_dir)

    def _issue(path, risk_dimension, message, reason_codes):
        issues.append(
            {
                "code": "POLICY_PRODUCER_AUTHORITY_STRUCTURE",
                "path": path,
                "risk_dimension": risk_dimension,
                "reason_codes": list(reason_codes),
                "message": message,
            }
        )

    for filename in sorted(_POLICY_DOCUMENT_WRAPPERS):
        wrapper, risk_dimension, absence_is_legal, reason_codes = _POLICY_DOCUMENT_WRAPPERS[
            filename
        ]
        path = directory / filename
        if not path.exists():
            # An absent document is the documented "no policy of this kind"
            # deployment for producer-authority, and load_policy raises
            # loudly for the ones it requires. Neither is silent.
            continue
        try:
            document = load_yaml(path)
        except yaml.YAMLError as exc:
            _issue(
                filename,
                risk_dimension,
                f"{filename} is not parseable YAML, so the whole gate it "
                f"carries is unreadable: {exc}",
                reason_codes,
            )
            continue
        if absence_is_legal and not document:
            # Empty or comment-only. load_policy cannot tell this from an
            # absent file, so neither may this check.
            continue
        if not isinstance(document, dict) or wrapper not in document:
            _issue(
                f"{filename}#{wrapper}",
                risk_dimension,
                f"{filename} has no top-level '{wrapper}:' key, so the policy "
                "loader falls back to its permissive default and the gate this "
                "file configures is not applied at all — a one-character typo "
                "in this key is invisible to every in-memory check",
                reason_codes,
            )
    return issues


def _ids_from_list(value):
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item.strip()]


# Every place a canonical `geo` / `bearing` block can sit in a payload.
# Derived from the two shipped schemas rather than restated per check:
# ObservationPayload and TrackStatePayload carry them at the payload root,
# FusionPayload carries them under `estimated_state`, and `claim` is an open
# object a producer can mirror either into. The zero-fill check walked two of
# these and the frame check walked exactly one, so the FUSED estimate — the
# promoted, downstream-consumed state, furthest from the sensor that knew the
# frame, and the one a consumer is most likely to act on — was invisible to
# both, while the check's PRESENCE on observations made its absence on fusion
# read as an assertion that the fused bearing was labeled (R1-11 A-16).
_SPATIAL_CONTAINERS = (("payload", None), ("payload.claim", "claim"),
                       ("payload.estimated_state", "estimated_state"))


def _spatial_candidates(payload, key):
    """Yield ``(path, value)`` for every canonical ``key`` block in a payload."""
    if not isinstance(payload, dict):
        return
    for prefix, container in _SPATIAL_CONTAINERS:
        block = payload if container is None else payload.get(container)
        if not isinstance(block, dict) or key not in block:
            continue
        yield f"{prefix}.{key}", block[key]


def _lineage_based_on(event):
    lineage = event.get("lineage", {}) if isinstance(event, dict) else {}
    if not isinstance(lineage, dict):
        return []
    return _ids_from_list(lineage.get("based_on"))


def validate_schema(event, schema, severity_map=None):
    errors = sorted(schema.iter_errors(event), key=lambda e: e.path)
    violations = []
    for err in errors:
        violations.append(
            _violation(
                "SCHEMA_INVALID",
                err.message,
                details={"path": "/".join(str(p) for p in err.path)},
                severity_map=severity_map,
            )
        )
    return not violations, violations


def validate_role(event, roles_policy, severity_map=None):
    event_block = event.get("event", {})
    source = event.get("source", {})
    event_type = event_block.get("event_type")
    node_role = source.get("node_role")
    producer = source.get("producer")

    roles = roles_policy.get("roles", {})
    role_cfg = roles.get(node_role)
    if not role_cfg:
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                "unknown node_role",
                details={"node_role": node_role},
                severity_map=severity_map,
            )
        ]

    allowed = role_cfg.get("allowed_event_types", [])
    if event_type not in allowed:
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                "event_type not allowed for role",
                details={"event_type": event_type, "node_role": node_role},
                severity_map=severity_map,
            )
        ]

    producer_lc = (producer or "").lower()
    for rule in roles_policy.get("deny", []):
        if "event_type" in rule and rule["event_type"] != event_type:
            continue
        if "node_role" in rule and rule["node_role"] != node_role:
            continue
        if "producer" in rule and rule["producer"].lower() != producer_lc:
            continue
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                "event_type explicitly denied",
                details={"event_type": event_type, "node_role": node_role, "producer": producer},
                severity_map=severity_map,
            )
        ]

    return True, []


def validate_profile(event, profile, profiles_policy, severity_map=None):
    event_type = event.get("event", {}).get("event_type")
    event_profile = event.get("profile")
    if event_profile is not None and event_profile != profile:
        return False, [
            _violation(
                "PROFILE_MISMATCH",
                "event profile does not match validation/export profile",
                details={"event_profile": event_profile, "profile": profile},
                severity_map=severity_map,
            )
        ]
    profile_cfg = profiles_policy.get(profile)
    if not profile_cfg:
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE",
                "unknown profile",
                details={"profile": profile},
                severity_map=severity_map,
            )
        ]
    allowed = profile_cfg.get("allowed_event_types", [])
    if event_type not in allowed:
        return False, [
            _violation(
                "EVENT_TYPE_NOT_ALLOWED_FOR_PROFILE",
                "event_type not allowed for profile",
                details={"event_type": event_type, "profile": profile},
                severity_map=severity_map,
            )
        ]
    return True, []


def _has_per_event_timing(event, timing_policy):
    required = [str(field) for field in timing_policy.get("required_fields", []) if str(field).strip()]
    if not required:
        required = ["time_source", "sync_state", "est_error_ms", "last_sync_ts"]
    for path in timing_policy.get("per_event_paths", []):
        value = _resolve_path(event, path)
        if isinstance(value, dict) and all(field in value for field in required):
            return True
    return False


def validate_timing_quality(
    event,
    semantics_policy,
    state=None,
    severity_map=None,
    timing_freshness_policy=None,
    profile=None,
):
    timing_policy = semantics_policy.get("timing_quality", {})
    if not timing_policy.get("required", False):
        return True, []

    event_type = event.get("event", {}).get("event_type")
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    system_type = payload.get("system_type") if isinstance(payload, dict) else None

    freshness_enabled = _timing_freshness_enabled(timing_freshness_policy)

    if event_type == "SYSTEM_EVENT" and system_type == "TIME_STATUS":
        if not freshness_enabled or state is None:
            return True, []
        # freshness_enabled is now True for a DESTROYED block as well as a
        # mapping (R1-11 B-02), so this dereference is reachable with a
        # non-mapping policy and must not raise into the receive-loop
        # backstop. Holdover monotonicity is opt-in, so an unreadable block
        # leaves it off - it is a corroboration check, not an authorization
        # gate, and the stale/negative-age gate below is the one that fails
        # closed on the same input.
        holdover_policy = (
            timing_freshness_policy.get("holdover_est_error_monotonic", {})
            if isinstance(timing_freshness_policy, dict)
            else {}
        )
        if not isinstance(holdover_policy, dict) or not holdover_policy.get("enabled", False):
            return True, []
        metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
        if not isinstance(metrics, dict) or metrics.get("sync_state") != "HOLDOVER":
            return True, []
        _key, previous = state.get_timing(event)
        if not isinstance(previous, dict) or previous.get("sync_state") != "HOLDOVER":
            return True, []
        try:
            current_error = float(metrics.get("est_error_ms"))
            previous_error = float(previous.get("est_error_ms"))
        except (TypeError, ValueError):
            return True, []
        if current_error >= previous_error:
            return True, []
        mode = str(holdover_policy.get("mode", "warn") or "warn").strip().lower()
        if mode not in {"warn", "reject"}:
            mode = "warn"
        violation = _violation(
            "TIMING_STATUS_HOLDOVER_NON_MONOTONIC",
            "HOLDOVER est_error_ms decreased compared with previous TIME_STATUS",
            details=_risk_details(
                {
                    "source": "/".join(_source_key(event)),
                    "previous_est_error_ms": previous_error,
                    "current_est_error_ms": current_error,
                    "previous_ts": previous.get("_event_ts"),
                    "current_ts": event.get("event", {}).get("ts"),
                    "policy_mode": mode,
                },
                "timing",
                mode,
                policy=timing_freshness_policy,
                policy_ref="policy/timing-freshness.yaml#holdover_est_error_monotonic",
            ),
            severity_map=severity_map,
            severity="fail" if mode == "reject" else "warn",
        )
        return mode != "reject", [violation]

    required_event_types = timing_policy.get("required_event_types", [])
    required_event_types = {str(value) for value in required_event_types if str(value).strip()}
    if required_event_types and event_type not in required_event_types:
        return True, []

    if _has_per_event_timing(event, timing_policy):
        return True, []

    timing_status = None
    timing_key = None
    if state is not None:
        timing_key, timing_status = state.get_timing(event)
    if timing_status is not None:
        if not freshness_enabled:
            return True, []

        event_ts = _parse_utc_z(event.get("event", {}).get("ts"))
        status_ts = _parse_utc_z(timing_status.get("_event_ts"))
        if event_ts is None or status_ts is None:
            return True, []
        raw_age_ms = (event_ts - status_ts).total_seconds() * 1000.0
        event_profile = _profile_for_event(event, profile)
        if raw_age_ms < 0:
            negative_age_ms = abs(raw_age_ms)
            max_negative_age_ms = _max_negative_timing_status_age_ms(
                timing_freshness_policy, event_profile
            )
            if negative_age_ms <= max_negative_age_ms:
                return True, []

            mode = _timing_mode(timing_freshness_policy, "negative_age", event_profile)
            violation = _timing_policy_violation(
                "TIMING_STATUS_AGE_NEGATIVE",
                "event timestamp is earlier than latest TIME_STATUS beyond policy tolerance",
                mode,
                {
                    "source": "/".join(timing_key or _source_key(event)),
                    "event_type": event_type,
                    "profile": event_profile,
                    "age_ms": raw_age_ms,
                    "negative_age_ms": negative_age_ms,
                    "max_negative_age_ms": max_negative_age_ms,
                    "timing_status_ts": timing_status.get("_event_ts"),
                    "event_ts": event.get("event", {}).get("ts"),
                },
                timing_freshness_policy=timing_freshness_policy,
                severity_map=severity_map,
            )
            return violation["severity"] != "fail", [violation]

        age_ms = raw_age_ms
        max_age_ms = _max_timing_status_age_ms(timing_freshness_policy, event_profile)
        if age_ms <= max_age_ms:
            return True, []

        mode = _timing_mode(timing_freshness_policy, "stale", event_profile)
        violation = _timing_policy_violation(
            "TIMING_STATUS_STALE",
            "latest TIME_STATUS is older than policy maximum age",
            mode,
            {
                "source": "/".join(timing_key or _source_key(event)),
                "event_type": event_type,
                "profile": event_profile,
                "age_ms": age_ms,
                "max_age_ms": max_age_ms,
                "timing_status_ts": timing_status.get("_event_ts"),
                "event_ts": event.get("event", {}).get("ts"),
            },
            timing_freshness_policy=timing_freshness_policy,
            severity_map=severity_map,
        )
        return violation["severity"] != "fail", [violation]

    event_profile = _profile_for_event(event, profile)
    mode = (
        _timing_mode(timing_freshness_policy, "missing", event_profile)
        if freshness_enabled
        else "reject"
    )
    violation = _timing_policy_violation(
        "TIMING_STATUS_MISSING",
        "node has not exposed timing quality for this event",
        mode,
        {
            "source": "/".join(_source_key(event)),
            "event_type": event_type,
            "profile": event_profile,
        },
        timing_freshness_policy=timing_freshness_policy,
        severity_map=severity_map,
    )
    return violation["severity"] != "fail", [violation]


def validate_deduplication(event, state=None, severity_map=None):
    if state is None:
        return True, []
    event_block = event.get("event", {}) if isinstance(event, dict) else {}
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    event_type = event_block.get("event_type")
    event_id = event_block.get("event_id")

    if event_id and event_id in state.event_ids:
        return False, [
            _violation(
                "EVENT_DUPLICATE",
                "event_id has already been applied",
                details={"event_id": event_id},
                severity_map=severity_map,
            )
        ]

    if event_type == "COMMAND_EVENT" and isinstance(payload, dict):
        task_id = payload.get("task_id")
        if task_id and task_id in state.command_task_ids:
            return False, [
                _violation(
                    "TASK_DUPLICATE",
                    "COMMAND_EVENT task_id has already been applied",
                    details={"task_id": task_id},
                    severity_map=severity_map,
                )
            ]

    if event_type == "SYSTEM_EVENT" and isinstance(payload, dict) and payload.get("system_type") == "TASK_ACK":
        metrics = payload.get("metrics", {})
        if isinstance(metrics, dict):
            key = (metrics.get("task_id"), metrics.get("original_event_id"), payload.get("state"))
            if all(key) and key in state.task_ack_keys:
                return False, [
                    _violation(
                        "TASK_ACK_DUPLICATE",
                        "TASK_ACK state transition has already been applied",
                        details={
                            "task_id": key[0],
                            "original_event_id": key[1],
                            "state": key[2],
                        },
                        severity_map=severity_map,
                    )
                ]

    return True, []


def validate_semantics(event, semantics_policy, severity_map=None):
    event_block = event.get("event", {})
    payload = event.get("payload", {})

    event_type = event_block.get("event_type")
    event_subtype = event_block.get("event_subtype")

    warnings = []

    # Contract 8.1 value honesty, first gate. NaN and +/-Infinity validate
    # clean at the schema layer (every minimum/maximum comparison against NaN
    # is vacuous) and reach the wire as `NaN`/`Infinity` tokens that are not
    # RFC 8259. This runs before every other semantic check for two reasons:
    # a value with no canonical form cannot be reasoned about by the checks
    # below, and several of those checks echo the offending value verbatim
    # into violation details - which would carry the non-finite float straight
    # into the gateway's own refusal event and back onto the wire. Refusing
    # first means the diagnostic names the path and never the value.
    #
    # Detection is value scoped (see _find_non_finite); only the reported code
    # is path sensitive, so the confidence fields keep their more specific
    # NON_FINITE_CONFIDENCE. Every other non-finite value is reported as
    # NON_FINITE_VALUE (R1-11-01: the general code was escalated as a
    # governed Class B change and minted by maintainer adjudication
    # 2026-08-09 at occurrence count 3): the datagram carries a token that
    # is not a JSON number, so the instance is not a valid instance of the
    # contract's data model, and the fault is the producer's. On a
    # v1.0-stamped wire diagnostic the code rides its documented fallback
    # SCHEMA_INVALID with the minted code in metrics.diagnostic_code
    # (diagnostic-first posture; policy/semantics.yaml
    # schema_violation_v1_0_wire_fallback). This diagnostic layer carries
    # the minted code natively, which is where the operator filters.
    #
    # Severity is pinned rather than resolved from the severity map. Every
    # other code is operator-tunable because "warn and forward" is a coherent
    # operating point for it; for a non-finite value it is not. Downgrading
    # this to warn forwards the event verbatim, so `"lat":NaN` goes on the
    # wire with a warning beside it - laundering by configuration. (The
    # `severity=` override is the same mechanism the risk-adjudication gate
    # below uses.)
    non_finite_path = _find_non_finite(event)
    if non_finite_path is not None:
        conf_path = _find_non_finite_confidence(event)
        if conf_path is not None:
            return False, [
                _violation(
                    "NON_FINITE_CONFIDENCE",
                    "confidence must be a finite number in [0, 1]; NaN/inf is not an honest claim",
                    details={"field": conf_path},
                    severity_map=severity_map,
                    severity="fail",
                )
            ]
        return False, [
            _violation(
                "NON_FINITE_VALUE",
                "non-finite number (NaN/inf) has no canonical value and no RFC 8259 "
                "wire form; refusing rather than forwarding a value that is not a value",
                details={"field": non_finite_path},
                severity_map=severity_map,
                severity="fail",
            )
        ]

    # Contract 6.4 frame provenance (version-agnostic, all event types).
    # quality.bearing_frame describes the canonical bearing and permits exactly
    # TRUE_NORTH; quality.heading_source is a free-form string naming the
    # heading reference. The v1.0 schema leaves quality free-form and the
    # locked schema cannot change, so this semantic check is the
    # lock-compatible enforcement route for v1.0 producers (and backstops
    # v1.1.0, where the schema also pins the enum).
    quality = payload.get("quality") if isinstance(payload, dict) else None
    if isinstance(quality, dict):
        if "bearing_frame" in quality and quality.get("bearing_frame") != "TRUE_NORTH":
            return False, [
                _violation(
                    "INVALID_QUALITY_BEARING_FRAME",
                    "quality.bearing_frame permits exactly TRUE_NORTH",
                    details={
                        "field": "quality.bearing_frame",
                        "value": quality.get("bearing_frame"),
                    },
                    severity_map=severity_map,
                )
            ]
        if "heading_source" in quality and not isinstance(quality.get("heading_source"), str):
            return False, [
                _violation(
                    "INVALID_QUALITY_HEADING_SOURCE",
                    "quality.heading_source must be a string",
                    details={
                        "field": "quality.heading_source",
                        "value": quality.get("heading_source"),
                    },
                    severity_map=severity_map,
                )
            ]

    # Contract 6.8 zero-fill heuristic (warn only, never reject). (0, 0) is a
    # legitimate coordinate (null island), so lat == 0.0 and lon == 0.0 cannot
    # be proven to be zero-fill - a hard check is impossible and warn severity
    # is the documented ceiling. The same ambiguity is handled at ingress by
    # the MAVLink adapter's refuse-to-fabricate rule
    # (adapters/ingress/mavlink/README.md).
    if isinstance(payload, dict):
        for geo_path, geo in _spatial_candidates(payload, "geo"):
            if (
                isinstance(geo, dict)
                and isinstance(geo.get("lat"), (int, float))
                and isinstance(geo.get("lon"), (int, float))
                and float(geo["lat"]) == 0.0
                and float(geo["lon"]) == 0.0
            ):
                warnings.append(
                    _violation(
                        "GEO_ZERO_FILL_SUSPECTED",
                        "geo sits at (0, 0); zero-filled position suspected (contract 6.8)",
                        details={"path": geo_path},
                        severity_map=severity_map,
                    )
                )

    # Contract 6.4 frame-provenance heuristic (warn only, never reject): a
    # canonical bearing with no frame provenance in either channel
    # (bearing.frame or quality.bearing_frame) passes every hard gate, yet
    # a mislabeled magnetic bearing consumed as true north is silent
    # geolocation corruption. v1.0 tolerates legacy-unlabeled bearings, so
    # warn is the ceiling - this makes the assertively-labeled vs
    # legacy-unlabeled distinction machine-visible (R1-11 R11-21).
    if isinstance(payload, dict):
        quality_block = payload.get("quality")
        if not isinstance(quality_block, dict):
            quality_block = {}
        for bearing_path, bearing in _spatial_candidates(payload, "bearing"):
            if not isinstance(bearing, dict) or bearing.get("az_deg") is None:
                continue
            if "frame" not in bearing and "bearing_frame" not in quality_block:
                warnings.append(
                    _violation(
                        "BEARING_FRAME_UNLABELED",
                        "canonical bearing carries no frame provenance "
                        "(bearing.frame or quality.bearing_frame) - contract 6.4 "
                        "frame assertion missing",
                        details={"path": bearing_path},
                        severity_map=severity_map,
                    )
                )

    # Contract 8.1 confidence honesty (R1-11 R11-04, validator side) is now
    # enforced by the value-scoped non-finite gate at the top of this
    # function, which reports NON_FINITE_CONFIDENCE for exactly these two
    # paths and SCHEMA_INVALID everywhere else.

    if event_type == "OBSERVATION_EVENT":
        forbidden = semantics_policy.get("observation_event", {}).get("payload_must_not_contain", [])
        forbidden_keys = {_normalize_key(key) for key in forbidden}
        found = _find_forbidden_key(payload, forbidden_keys)
        if found:
            found_key, path = found
            return False, [
                _violation(
                    "OBSERVATION_HAS_IDENTITY",
                    "observation payload contains identity fields",
                    details={"field": found_key, "path": "/".join(path)},
                    severity_map=severity_map,
                )
            ]

        if payload.get("modality") == "RF" and "t_start" in payload and "t_end" in payload:
            timestamp = _parse_utc_z(event_block.get("ts"))
            start = _parse_utc_z(payload.get("t_start"))
            end = _parse_utc_z(payload.get("t_end"))
            tolerance_ms = semantics_policy.get("observation_event", {}).get(
                "rf_window_midpoint_tolerance_ms", 1
            )
            try:
                tolerance_ms = float(tolerance_ms)
            except (TypeError, ValueError):
                tolerance_ms = 1.0
            if timestamp is not None and start is not None and end is not None:
                midpoint = start + ((end - start) / 2)
                delta_ms = abs((timestamp - midpoint).total_seconds() * 1000)
                if end < start or delta_ms > tolerance_ms:
                    return False, [
                        _violation(
                            "RF_WINDOW_MIDPOINT_MISMATCH",
                            "RF observation event.ts must equal the t_start/t_end midpoint",
                            details={
                                "ts": event_block.get("ts"),
                                "t_start": payload.get("t_start"),
                                "t_end": payload.get("t_end"),
                                "expected_midpoint": _format_utc_z(midpoint),
                                "delta_ms": delta_ms,
                                "tolerance_ms": tolerance_ms,
                            },
                            severity_map=severity_map,
                        )
                    ]

    if event_type == "INFERENCE_EVENT":
        forbidden = semantics_policy.get("inference_event", {}).get("payload_must_not_contain", [])
        forbidden_keys = {_normalize_key(key) for key in forbidden}
        found = _find_forbidden_key(payload, forbidden_keys)
        if found:
            found_key, path = found
            # Contract 7.5: payload and payload.claim MUST NOT contain
            # track_id, members, or estimated_state. track_id keeps its
            # historical code; the fused-state fields (members,
            # estimated_state) report INFERENCE_HAS_FUSION_STATE.
            if _normalize_key(found_key) == "track_id":
                code = "INFERENCE_HAS_TRACK_ID"
                message = "inference payload contains track identity"
            else:
                code = "INFERENCE_HAS_FUSION_STATE"
                message = "inference payload contains fused-state fields"
            return False, [
                _violation(
                    code,
                    message,
                    details={"field": found_key, "path": "/".join(path)},
                    severity_map=severity_map,
                )
            ]

    if event_type == "STATE_EVENT":
        forbidden = semantics_policy.get("state_event", {}).get("payload_must_not_contain", [])
        forbidden_keys = {_normalize_key(key) for key in forbidden}
        found = _find_forbidden_key(payload, forbidden_keys)
        if found:
            found_key, path = found
            return False, [
                _violation(
                    "STATE_HAS_RAW_FEATURES",
                    "state payload contains raw sensor features",
                    details={"field": found_key, "path": "/".join(path)},
                    severity_map=severity_map,
                )
            ]

    if event_type == "COMMAND_EVENT":
        requires_deconfliction = (
            semantics_policy.get("command_event", {}).get("requires_deconfliction", True)
        )
        if requires_deconfliction and payload.get("requires_deconfliction") is not True:
            return False, [
                _violation(
                    "COMMAND_NOT_DECONFLICTED",
                    "requires_deconfliction must be true",
                    details={"field": "requires_deconfliction"},
                    severity_map=severity_map,
                )
            ]
        forbidden = semantics_policy.get("command_event", {}).get("payload_must_not_contain", [])
        if not forbidden:
            forbidden = semantics_policy.get("command_event", {}).get("target_geo_must_not_include", [])
        forbidden_keys = {_normalize_key(key) for key in forbidden}
        found = _find_forbidden_key(payload, forbidden_keys) if forbidden_keys else None
        if found:
            found_key, path = found
            return False, [
                _violation(
                    "COMMAND_HAS_ALTITUDE",
                    "command payload must not include altitude",
                    details={"field": found_key, "path": "/".join(path)},
                    severity_map=severity_map,
                )
            ]

    if event_type == "SYSTEM_EVENT":
        system_policy = semantics_policy.get("system_event", {})
        system_type = payload.get("system_type")

        if system_type == "SCHEMA_VIOLATION":
            metrics = payload.get("metrics")
            required_fields = system_policy.get("schema_violation_required_metrics_fields", [])
            required_fields = [str(field) for field in required_fields if str(field).strip()]
            if not isinstance(metrics, dict):
                missing = required_fields or ["reason_code", "original_event_id"]
                if "reason_code" in missing:
                    code = "SCHEMA_VIOLATION_MISSING_REASON_CODE"
                elif "original_event_id" in missing:
                    code = "SCHEMA_VIOLATION_MISSING_ORIGINAL_EVENT_ID"
                else:
                    code = "SCHEMA_VIOLATION_MISSING_REASON_CODE"
                return False, [
                    _violation(
                        code,
                        "SCHEMA_VIOLATION metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]
            missing = [field for field in required_fields if field not in metrics]
            if missing:
                if "reason_code" in missing:
                    code = "SCHEMA_VIOLATION_MISSING_REASON_CODE"
                elif "original_event_id" in missing:
                    code = "SCHEMA_VIOLATION_MISSING_ORIGINAL_EVENT_ID"
                else:
                    code = "SCHEMA_VIOLATION_MISSING_REASON_CODE"
                return False, [
                    _violation(
                        code,
                        "SCHEMA_VIOLATION metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]

            reason_code = metrics.get("reason_code") if isinstance(metrics, dict) else None
            allowed_reason_codes = system_policy.get("schema_violation_allowed_reason_codes", [])
            allowed_reason_codes = [str(value) for value in allowed_reason_codes if str(value).strip()]
            if allowed_reason_codes and isinstance(reason_code, str) and reason_code.strip():
                if reason_code not in allowed_reason_codes:
                    return False, [
                        _violation(
                            "SCHEMA_VIOLATION_INVALID_REASON_CODE",
                            "SCHEMA_VIOLATION reason_code not allowed",
                            details={"reason_code": reason_code},
                            severity_map=severity_map,
                        )
                    ]

        if system_type == "LINK_STATUS":
            state = payload.get("state")
            allowed_states = system_policy.get("link_status_allowed_states", [])
            allowed_states = [str(value) for value in allowed_states if str(value).strip()]
            if allowed_states and state not in allowed_states:
                return False, [
                    _violation(
                        "LINK_STATUS_INVALID_STATE",
                        "LINK_STATUS state not allowed",
                        details={"state": state},
                        severity_map=severity_map,
                    )
                ]

            metrics = payload.get("metrics")
            required_fields = system_policy.get("link_status_required_metrics_fields", [])
            required_fields = [str(field) for field in required_fields if str(field).strip()]
            if not isinstance(metrics, dict):
                missing = required_fields or ["link_id"]
                return False, [
                    _violation(
                        "LINK_STATUS_MISSING_REQUIRED_FIELD",
                        "LINK_STATUS metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]
            missing = [field for field in required_fields if field not in metrics]
            if missing:
                return False, [
                    _violation(
                        "LINK_STATUS_MISSING_REQUIRED_FIELD",
                        "LINK_STATUS metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]

            reason_code = metrics.get("reason_code") if isinstance(metrics, dict) else None
            require_reason_states = system_policy.get("link_status_reason_code_required_states", [])
            require_reason_states = [str(value) for value in require_reason_states if str(value).strip()]
            if require_reason_states and state in require_reason_states:
                if not isinstance(reason_code, str) or not reason_code.strip():
                    return False, [
                        _violation(
                            "LINK_STATUS_MISSING_REASON_CODE",
                            "LINK_STATUS reason_code required for state",
                            details={"state": state},
                            severity_map=severity_map,
                        )
                    ]

            allowed_reason_codes = system_policy.get("link_status_allowed_reason_codes", [])
            allowed_reason_codes = [str(value) for value in allowed_reason_codes if str(value).strip()]
            if allowed_reason_codes and isinstance(reason_code, str) and reason_code.strip():
                if reason_code not in allowed_reason_codes:
                    return False, [
                        _violation(
                            "LINK_STATUS_INVALID_REASON_CODE",
                            "LINK_STATUS reason_code not allowed",
                            details={"reason_code": reason_code, "state": state},
                            severity_map=severity_map,
                        )
                    ]

        if event_subtype == "TASK_ACK" or system_type == "TASK_ACK":
            state = payload.get("state")
            allowed_states = system_policy.get("task_ack_allowed_states", [])
            allowed_states = [str(value) for value in allowed_states if str(value).strip()]
            if allowed_states and state not in allowed_states:
                return False, [
                    _violation(
                        "TASK_ACK_INVALID_STATE",
                        "TASK_ACK state not allowed",
                        details={"state": state},
                        severity_map=severity_map,
                    )
                ]

            metrics = payload.get("metrics")
            required_fields = system_policy.get("task_ack_required_metrics_fields")
            if not required_fields:
                required_fields = system_policy.get("task_ack_requires_metrics_fields", [])
            required_fields = [str(field) for field in required_fields if str(field).strip()]
            if not isinstance(metrics, dict):
                missing = required_fields or ["task_id"]
                if "task_id" in missing:
                    code = "TASK_ACK_MISSING_TASK_ID"
                elif "original_event_id" in missing:
                    code = "TASK_ACK_MISSING_ORIGINAL_EVENT_ID"
                else:
                    code = "TASK_ACK_MISSING_REQUIRED_FIELD"
                return False, [
                    _violation(
                        code,
                        "TASK_ACK metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]
            missing = [field for field in required_fields if field not in metrics]
            if missing:
                if "task_id" in missing:
                    code = "TASK_ACK_MISSING_TASK_ID"
                elif "original_event_id" in missing:
                    code = "TASK_ACK_MISSING_ORIGINAL_EVENT_ID"
                else:
                    code = "TASK_ACK_MISSING_REQUIRED_FIELD"
                return False, [
                    _violation(
                        code,
                        "TASK_ACK metrics missing required fields",
                        details={"missing": missing},
                        severity_map=severity_map,
                    )
                ]

            reason_code = metrics.get("reason_code") if isinstance(metrics, dict) else None
            require_reason_states = system_policy.get("task_ack_reason_code_required_states", [])
            require_reason_states = [str(value) for value in require_reason_states if str(value).strip()]
            if require_reason_states and state in require_reason_states:
                if not isinstance(reason_code, str) or not reason_code.strip():
                    return False, [
                        _violation(
                            "TASK_ACK_MISSING_REASON_CODE",
                            "TASK_ACK reason_code required for state",
                            details={"state": state},
                            severity_map=severity_map,
                        )
                    ]

            allowed_reason_codes = system_policy.get("task_ack_allowed_reason_codes", [])
            allowed_reason_codes = [str(value) for value in allowed_reason_codes if str(value).strip()]
            if allowed_reason_codes and isinstance(reason_code, str) and reason_code.strip():
                if reason_code not in allowed_reason_codes:
                    return False, [
                        _violation(
                            "TASK_ACK_INVALID_REASON_CODE",
                            "TASK_ACK reason_code not allowed",
                            details={"reason_code": reason_code, "state": state},
                            severity_map=severity_map,
                        )
                    ]

    return True, warnings


def validate_lineage(event, lineage_policy, state=None, profile=None, severity_map=None):
    # Third member of the destroyed-block family (R1-11 B-02 class). A
    # non-mapping block cannot say `enabled: false`, and reading it as
    # "lineage checking is switched off" silently drops every lineage
    # honesty signal. An absent lineage.yaml loads as `{}` — a mapping — and
    # keeps the built-in per-check defaults, so only a mangled block lands
    # here; run the checks on those defaults rather than skipping them.
    lineage_block_error = None
    if not isinstance(lineage_policy, dict):
        lineage_block_error = (
            "the lineage policy block must be a mapping; got "
            f"{type(lineage_policy).__name__}, so the built-in per-check "
            "defaults were applied (policy/lineage.yaml#lineage)"
        )
        lineage_policy = {}
    elif lineage_policy.get("enabled", True) is False:
        return True, []

    event_block = event.get("event", {}) if isinstance(event, dict) else {}
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    event_type = event_block.get("event_type")
    event_profile = _profile_for_event(event, profile)
    lineage_based_on = set(_lineage_based_on(event))
    violations = []

    payload_based_on = _ids_from_list(payload.get("based_on")) if isinstance(payload, dict) else []
    if payload_based_on:
        missing = sorted(item for item in payload_based_on if item not in lineage_based_on)
        if missing:
            mode = _mode_for_profile(
                lineage_policy, "payload_based_on_subset_mode", event_profile, default="reject"
            )
            violation = _mode_violation(
                "LINEAGE_PAYLOAD_BASED_ON_NOT_SUBSET",
                "payload.based_on must be equal to or a subset of lineage.based_on",
                mode,
                {
                    "event_id": event_block.get("event_id"),
                    "event_type": event_type,
                    "missing_from_lineage": missing,
                },
                severity_map=severity_map,
                risk_dimension="lineage",
                policy=lineage_policy,
                policy_ref="policy/lineage.yaml#payload_based_on_subset_mode",
            )
            if violation:
                violations.append(violation)

    if event_type == "FUSION_EVENT" and isinstance(payload, dict):
        members = _ids_from_list(payload.get("members"))
        if members:
            missing_members = sorted(item for item in members if item not in lineage_based_on)
            if missing_members:
                mode = _mode_for_profile(
                    lineage_policy, "fusion_members_in_lineage_mode", event_profile, default="warn"
                )
                violation = _mode_violation(
                    "LINEAGE_FUSION_MEMBERS_NOT_IN_BASED_ON",
                    "FUSION_EVENT payload.members should be represented in lineage.based_on",
                    mode,
                    {
                        "event_id": event_block.get("event_id"),
                        "missing_members": missing_members,
                    },
                    severity_map=severity_map,
                    risk_dimension="lineage",
                    policy=lineage_policy,
                    policy_ref="policy/lineage.yaml#fusion_members_in_lineage_mode",
                )
                if violation:
                    violations.append(violation)

    def _finish(collected):
        # A diagnostic produced under a destroyed policy block must name the
        # block, the same way the routing and producer-authority refusals do.
        if lineage_block_error is not None:
            for entry in collected:
                details = entry.get("details")
                if isinstance(details, dict):
                    details.setdefault("policy_error", lineage_block_error)
        return not any(v.get("severity") == "fail" for v in collected), collected

    if state is None or not hasattr(state, "get_event"):
        return _finish(violations)

    allowed_policy = lineage_policy.get("allowed_parent_event_types", {})
    if not isinstance(allowed_policy, dict):
        allowed_policy = {}
    allowed_parent_types = set(_list_values(allowed_policy.get(event_type)))

    unresolved = []
    invalid = []
    for parent_id in sorted(lineage_based_on):
        parent = state.get_event(parent_id)
        if not parent:
            unresolved.append(parent_id)
            continue
        parent_type = parent.get("event_type")
        if allowed_parent_types and parent_type not in allowed_parent_types:
            invalid.append({"event_id": parent_id, "event_type": parent_type})

    if unresolved:
        mode = _mode_for_profile(lineage_policy, "unresolved_parent_mode", event_profile, default="warn")
        violation = _mode_violation(
            "LINEAGE_PARENT_UNRESOLVED",
            "lineage parent references are not available in the local event store",
            mode,
            {
                "event_id": event_block.get("event_id"),
                "event_type": event_type,
                "profile": event_profile,
                "unresolved": unresolved,
            },
            severity_map=severity_map,
            risk_dimension="lineage",
            policy=lineage_policy,
            policy_ref="policy/lineage.yaml#unresolved_parent_mode",
        )
        if violation:
            violations.append(violation)

    if invalid:
        mode = _mode_for_profile(lineage_policy, "parent_type_mismatch_mode", event_profile, default="reject")
        violation = _mode_violation(
            "LINEAGE_PARENT_TYPE_INVALID",
            "lineage parent event_type is not allowed for this event_type",
            mode,
            {
                "event_id": event_block.get("event_id"),
                "event_type": event_type,
                "invalid_parents": invalid,
                "allowed_parent_event_types": sorted(allowed_parent_types),
            },
            severity_map=severity_map,
            risk_dimension="lineage",
            policy=lineage_policy,
            policy_ref="policy/lineage.yaml#parent_type_mismatch_mode",
        )
        if violation:
            violations.append(violation)

    return _finish(violations)


# Command-evidence lineage check (UxS command loop, GCS-originated tasking;
# maintainer record 2026-07-17). A COMMAND_EVENT may cite its motivating
# inference/fusion parents via the EXISTING lineage vocabulary
# (lineage.based_on); this check makes the citation auditable: the command
# provably rests on evidence the gateway saw and whose adjudicated use limits
# permitted command basis. Reason codes as updated by the R1-11-01/H1-08
# Class B batch (maintainer-adjudicated 2026-08-09; the escalation this
# comment used to record):
#   - never seen / evicted        -> COMMAND_EVIDENCE_UNRESOLVED (minted;
#     rode LINEAGE_PARENT_UNRESOLVED until the batch)
#   - type cannot motivate        -> LINEAGE_PARENT_TYPE_INVALID (kept: a
#     parent type that cannot motivate is honestly a lineage type fault)
#   - use limits prohibit command -> COMMAND_EVIDENCE_PROHIBITED (minted;
#     rode LINEAGE_MISMATCH until the batch)
#   - citations absent under require_evidence -> LINEAGE_MISMATCH (kept: a
#     policy-strictness refusal rather than an evidence adjudication;
#     filterable via policy_ref, and a third code was outside the
#     adjudicated pair)
# On a v1.0-stamped wire diagnostic the minted codes ride their documented
# legacy fallbacks with metrics.diagnostic_code carrying the specific
# condition (policy/semantics.yaml schema_violation_v1_0_wire_fallback).
# A bare command with NO citations stays legal unless the deployment enables
# the require_evidence knob: a human operator's direct tasking has no fused
# parent, and refusing it by default would break every fielded display loop.
_COMMAND_EVIDENCE_POLICY_REF = "policy/command-evidence.yaml"
# reject/warn/degrade only. "ignore" is not a legal mode for command risk —
# lint_policy_risk_modes flags it, and an illegal value falls back to the
# per-check default rather than silently widening acceptance.
_COMMAND_EVIDENCE_MODES = {"reject", "warn", "degrade"}
_COMMAND_EVIDENCE_CODES = {
    "COMMAND_EVIDENCE_UNRESOLVED",
    "COMMAND_EVIDENCE_PROHIBITED",
    "LINEAGE_PARENT_TYPE_INVALID",
    "LINEAGE_MISMATCH",
}
_DEFAULT_MOTIVATING_PARENT_EVENT_TYPES = ("INFERENCE_EVENT", "FUSION_EVENT", "STATE_EVENT")
# Same spelling as tools/filter_risk.py and the shipped policy packs — a
# parallel spelling here would split the use-token vocabulary.
_DEFAULT_COMMAND_BASIS_USE_TOKENS = ("COMMAND_BASIS", "AUTONOMY_TASKING")


def _command_evidence_mode(policy, key, profile, default):
    value = policy.get(key, default) if isinstance(policy, dict) else default
    if isinstance(value, dict):
        value = value.get(profile, value.get("default", default))
    mode = str(value or default).strip().lower()
    if mode not in _COMMAND_EVIDENCE_MODES:
        return default
    return mode


def validate_command_evidence(
    event, command_evidence_policy, state=None, profile=None, severity_map=None
):
    # Same destroyed-block posture as validate_lineage: a non-mapping block
    # cannot say `enabled: false`, so it runs the built-in per-check defaults
    # and every diagnostic names the broken policy. An absent file loads as
    # `{}` — a mapping — and keeps the same defaults silently (legal).
    block_error = None
    if not isinstance(command_evidence_policy, dict):
        block_error = (
            "the command_evidence policy block must be a mapping; got "
            f"{type(command_evidence_policy).__name__}, so the built-in "
            "per-check defaults were applied "
            "(policy/command-evidence.yaml#command_evidence)"
        )
        command_evidence_policy = {}
    elif command_evidence_policy.get("enabled", True) is False:
        return True, []

    event_block = event.get("event", {}) if isinstance(event, dict) else {}
    if event_block.get("event_type") != "COMMAND_EVENT":
        return True, []
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    if not isinstance(payload, dict):
        payload = {}
    event_profile = _profile_for_event(event, profile)
    task_id = payload.get("task_id")
    task_type = payload.get("task_type")
    cited = sorted(set(_lineage_based_on(event)))
    violations = []

    def _finish():
        if block_error is not None:
            for entry in violations:
                details = entry.get("details")
                if isinstance(details, dict):
                    details.setdefault("policy_error", block_error)
        return not any(v.get("severity") == "fail" for v in violations), violations

    def _emit(code, message, mode_key, default_mode, extra):
        mode = _command_evidence_mode(
            command_evidence_policy, mode_key, event_profile, default_mode
        )
        details = {
            "event_id": event_block.get("event_id"),
            "event_type": "COMMAND_EVENT",
            "task_id": task_id,
            "task_type": task_type,
            "profile": event_profile,
        }
        details.update(extra)
        if mode == "degrade":
            details["action"] = "degrade"
        violation = _mode_violation(
            code,
            message,
            mode,
            details,
            severity_map=severity_map,
            risk_dimension="lineage",
            policy=command_evidence_policy,
            policy_ref=f"{_COMMAND_EVIDENCE_POLICY_REF}#{mode_key}",
        )
        if violation:
            violations.append(violation)

    if not cited:
        # Bare commands are legal by default (direct operator tasking).
        # WHEN the strict knob is on, absence of citations mismatches the
        # lineage the policy requires.
        require = command_evidence_policy.get("require_evidence", False) is True
        scoped = set(_list_values(command_evidence_policy.get("require_evidence_task_types")))
        if require and (not scoped or str(task_type or "") in scoped):
            _emit(
                "LINEAGE_MISMATCH",
                "COMMAND_EVENT cites no motivating evidence in lineage.based_on "
                "and policy requires evidence for this task_type",
                "require_evidence_mode",
                "reject",
                {"require_evidence_task_types": sorted(scoped)},
            )
        return _finish()

    motivating = set(
        _list_values(command_evidence_policy.get("motivating_parent_event_types"))
    ) or set(_DEFAULT_MOTIVATING_PARENT_EVENT_TYPES)
    blocked_tokens = {
        token.upper()
        for token in (
            _list_values(command_evidence_policy.get("command_basis_use_tokens"))
            or _DEFAULT_COMMAND_BASIS_USE_TOKENS
        )
    }
    # Evidence whose risk labels could not be READ blocks the command path
    # regardless of which tokens a deployment configures: an unreadable
    # label set may say anything, and reading it as "says nothing" is the
    # laundering the whole check exists to prevent (pre-cut review). This
    # is an internal marker, never policy or event vocabulary.
    blocked_tokens.add(_UNADJUDICABLE_RISK_SHAPE)

    index = getattr(state, "command_evidence", None) if state is not None else None
    unresolved = []
    invalid = []
    prohibited = []
    for parent_id in cited:
        entry = index.get(parent_id) if index is not None else None
        if entry is None:
            # Never seen upstream, evicted from the bounded index, or no
            # index at all — every flavour is the same honest answer: this
            # citation cannot be resolved here.
            unresolved.append(parent_id)
            continue
        parent_type = entry.get("event_type")
        if parent_type not in motivating:
            invalid.append({"event_id": parent_id, "event_type": parent_type})
            continue
        blocking = sorted(set(entry.get("prohibited_uses") or ()) & blocked_tokens)
        if blocking:
            item = {
                "event_id": parent_id,
                "event_type": parent_type,
                "prohibited_command_uses": blocking,
            }
            codes = sorted(set(entry.get("risk_reason_codes") or ()))
            if codes:
                item["risk_reason_codes"] = codes
            prohibited.append(item)

    if unresolved:
        _emit(
            "COMMAND_EVIDENCE_UNRESOLVED",
            "COMMAND_EVENT cites motivating evidence that is not available in "
            "the gateway's bounded evidence index",
            "unresolved_parent_mode",
            "warn",
            {"unresolved": unresolved},
        )
    if invalid:
        _emit(
            "LINEAGE_PARENT_TYPE_INVALID",
            "COMMAND_EVENT cites a parent whose event_type cannot motivate a command",
            "parent_type_mismatch_mode",
            "reject",
            {
                "invalid_parents": invalid,
                "motivating_parent_event_types": sorted(motivating),
            },
        )
    if prohibited:
        _emit(
            "COMMAND_EVIDENCE_PROHIBITED",
            "COMMAND_EVENT cites evidence whose risk adjudication prohibits "
            "command basis",
            "prohibited_use_mode",
            "reject",
            {
                "prohibited_parents": prohibited,
                "command_basis_use_tokens": sorted(blocked_tokens),
            },
        )
    return _finish()


def apply_command_evidence_policy_action(event, violations, command_evidence_policy):
    """Stamp a degrade-accepted command with its risk adjudication.

    No confidence math: a command has no fused confidence to reduce, so the
    degradation IS the label — the risk_adjudication record carrying the
    policy's use limits (AUTONOMY_TASKING prohibited in the reference file),
    which downstream consumers (tools/filter_risk.py presets) act on. warn
    and reject dispositions stamp nothing: warn forwards the command
    unmodified beside its diagnostic, reject never forwards it.
    """
    if not isinstance(event, dict):
        return False
    changed = False
    for violation in violations or []:
        if not isinstance(violation, dict):
            continue
        if violation.get("code") not in _COMMAND_EVIDENCE_CODES:
            continue
        details = violation.get("details", {})
        if not isinstance(details, dict):
            continue
        if details.get("action") != "degrade":
            continue
        if not str(details.get("policy_ref") or "").startswith(_COMMAND_EVIDENCE_POLICY_REF):
            # The lineage codes are shared with validate_lineage; only this
            # check's own violations may stamp the command.
            continue
        changed = _append_risk_adjudication(event, violation) or changed
    return changed


def validate_producer_authority(event, authority_policy, severity_map=None):
    # The BLOCK, not just its keys. `producer_authority:` with nothing under
    # it loads as None, and reading that as "no authority policy" switched the
    # whole gate off in silence — the same mangle the key-level guards were
    # written for, one container up (R1-11 A-05 residual d). An absent policy
    # file is {} and stays permissive; a present-but-wrong-shaped block is a
    # defect and must not be quieter than the check it disables.
    block_policy_error = None
    if not isinstance(authority_policy, dict):
        block_policy_error = (
            "the producer_authority policy block must be a mapping; got "
            f"{type(authority_policy).__name__} "
            "(policy/producer-authority.yaml#producer_authority)"
        )
        authority_policy = {}
    elif authority_policy.get("enabled", True) is False:
        return True, []

    event_block = event.get("event", {}) if isinstance(event, dict) else {}
    source = event.get("source", {}) if isinstance(event, dict) else {}
    event_type = event_block.get("event_type")
    event_subtype = event_block.get("event_subtype")
    producer = (source.get("producer") or "").strip()

    producer_rules = authority_policy.get("producers", {})
    if "producers" in authority_policy and not isinstance(producer_rules, dict):
        # Same as the routing half: a destroyed rule table is not an absent
        # one (R1-11 A-05 residual b).
        block_policy_error = block_policy_error or (
            "producer_authority.producers must be a mapping; got "
            f"{type(producer_rules).__name__}, so every per-producer "
            "constraint is dropped "
            "(policy/producer-authority.yaml#producer_authority.producers)"
        )
        producer_rules = {}
    matching_rules = _matching_producer_rules(producer, producer_rules)
    matched_patterns = [pattern for pattern, _rule in matching_rules]
    require_match, require_match_error = _require_match_types(
        authority_policy,
        "require_match_for_event_types",
        "policy/producer-authority.yaml#producer_authority.require_match_for_event_types",
    )

    if require_match_error is None and block_policy_error is not None:
        require_match_error = block_policy_error

    if not matching_rules:
        if require_match_error is not None or event_type in require_match:
            details = {"event_type": event_type, "producer": producer}
            if require_match_error is not None:
                details["policy_error"] = require_match_error
            return False, [
                _violation(
                    "PRODUCER_NOT_ALLOWED",
                    # F8: this arm is also reached when the policy's producers
                    # table is malformed, in which case a correctly-named
                    # producer was being told to rename itself. The naming
                    # guidance only applies when the policy is intact.
                    (
                        "producer authority policy is malformed; the producer "
                        "name is not the problem -- see details.policy_error"
                    )
                    if require_match_error is not None
                    else (
                        "producer does not match producer authority policy "
                        "(policy/producer-authority.yaml); reference patterns "
                        "include rf-sensor-*, eo-sensor-*, acoustic-sensor-*, "
                        "classifier-*, detector-*, fusion-*, "
                        "mavlink-* -- see adapters/AUTHORING.md section 7"
                    ),
                    details=details,
                    severity_map=severity_map,
                )
            ]
        return True, []

    forbidden_types = set()
    allowed_types = set()
    allowed_subtypes = set()
    has_allowed_types = False
    has_allowed_subtypes = False
    rule_policy_error = None

    for pattern, rule in matching_rules:
        # A rule whose constraints collapsed to "no constraint" must not be
        # read as a rule that permits everything (R1-11 A-05 residuals b, c).
        # Scoped to the producer whose rule is broken, and named.
        rule_error = _producer_rule_policy_error(
            rule,
            "policy/producer-authority.yaml#producer_authority.producers."
            f"{pattern}",
        )
        if rule_error is not None:
            rule_policy_error = rule_policy_error or rule_error
            continue
        # Past this point the rule is a mapping: a non-mapping is one of the
        # defects _producer_rule_policy_error reports above. It is no longer
        # skipped over in silence, which is what it used to be.
        forbidden_types.update(_list_values(rule.get("forbidden_event_types")))
        rule_allowed_types = _list_values(rule.get("allowed_event_types"))
        if rule_allowed_types:
            has_allowed_types = True
            allowed_types.update(rule_allowed_types)
        rule_allowed_subtypes = _list_values(rule.get("allowed_event_subtypes"))
        if rule_allowed_subtypes:
            has_allowed_subtypes = True
            allowed_subtypes.update(rule_allowed_subtypes)

    if rule_policy_error is not None:
        return False, [
            _violation(
                "PRODUCER_NOT_ALLOWED",
                "producer authority rule is malformed",
                details={
                    "event_type": event_type,
                    "producer": producer,
                    "matched_patterns": matched_patterns,
                    "policy_error": rule_policy_error,
                },
                severity_map=severity_map,
            )
        ]

    if event_type in forbidden_types:
        return False, [
            _violation(
                "PRODUCER_NOT_ALLOWED",
                "event_type forbidden for producer",
                details={
                    "event_type": event_type,
                    "producer": producer,
                    "matched_patterns": matched_patterns,
                },
                severity_map=severity_map,
            )
        ]

    if has_allowed_types and event_type not in allowed_types:
        return False, [
            _violation(
                "PRODUCER_NOT_ALLOWED",
                "event_type not authorized for producer",
                details={
                    "event_type": event_type,
                    "producer": producer,
                    "matched_patterns": matched_patterns,
                },
                severity_map=severity_map,
            )
        ]

    if has_allowed_subtypes and event_subtype not in allowed_subtypes:
        return False, [
            _violation(
                "PRODUCER_NOT_ALLOWED",
                "event_subtype not authorized for producer",
                details={
                    "event_subtype": event_subtype,
                    "producer": producer,
                    "matched_patterns": matched_patterns,
                },
                severity_map=severity_map,
            )
        ]

    promotion_violation = _validate_external_state_promotion(
        event,
        authority_policy,
        _external_promotion_rules(matching_rules),
        matched_patterns,
        severity_map=severity_map,
    )
    if promotion_violation:
        return promotion_violation.get("severity") != "fail", [promotion_violation]

    return True, []


def _is_comms_producer(producer, routing_policy):
    cmd_cfg = routing_policy.get("command_event", {})
    if not isinstance(cmd_cfg, dict):
        # `command_event:` with nothing under it used to raise AttributeError
        # here on every COMMAND_EVENT. No comms origin can be established from
        # a destroyed block, so no producer is one (R1-11 A-05 residual a).
        return False
    allowlist = []
    for key in ("allowed_producers", "required_origin", "must_pass_through"):
        value = cmd_cfg.get(key)
        if isinstance(value, list):
            allowlist.extend(value)
        elif isinstance(value, str):
            allowlist.append(value)
    if not allowlist:
        allowlist = ["sensorops"]
    return any(_matches_pattern(producer, token) for token in allowlist)


def validate_routing(event, routing_policy, severity_map=None):
    event_type = event.get("event", {}).get("event_type")
    event_subtype = event.get("event", {}).get("event_subtype")
    producer = (event.get("source", {}).get("producer") or "").strip()
    # The BLOCK holding the routing gates. `routing:` truncated to a bare key
    # loads as None and raised AttributeError on EVERY event — a 100% outage
    # the receive-loop backstop reported as INTERNAL_ERROR, naming no policy
    # problem at all (R1-11 A-05 residual a). Refuse instead, and name it:
    # the same events are still not forwarded, but the refusal is loud,
    # filterable, and says which file to fix.
    block_policy_error = None
    if not isinstance(routing_policy, dict):
        block_policy_error = (
            "the routing policy block must be a mapping; got "
            f"{type(routing_policy).__name__} (policy/routing.yaml#routing)"
        )
        routing_policy = {}
    producer_rules = routing_policy.get("producers", {})
    if "producers" in routing_policy and not isinstance(producer_rules, dict):
        # `producers:` with nothing under it is not "no producer rules": it is
        # a rule table that was destroyed, and reading it as absent un-gates
        # every producer (R1-11 A-05 residual b).
        block_policy_error = block_policy_error or (
            "routing.producers must be a mapping; got "
            f"{type(producer_rules).__name__}, so every per-producer routing "
            "constraint is dropped (policy/routing.yaml#routing.producers)"
        )
        producer_rules = {}
    enforcement = routing_policy.get("producer_enforcement", {})
    require_allowlist, require_allowlist_error = _require_match_types(
        enforcement,
        "require_allowlist_for_event_types",
        "policy/routing.yaml#routing.producer_enforcement.require_allowlist_for_event_types",
    )
    if require_allowlist_error is None and block_policy_error is not None:
        require_allowlist_error = block_policy_error
    if producer_rules or require_allowlist_error is not None:
        matching_rules = _matching_producer_rules(producer, producer_rules)
        matched_patterns = [pattern for pattern, _rule in matching_rules]
        if not matching_rules and (
            require_allowlist_error is not None
            or (require_allowlist and event_type in require_allowlist)
        ):
            details = {"event_type": event_type, "producer": producer}
            if require_allowlist_error is not None:
                details["policy_error"] = require_allowlist_error
            return False, [
                _violation(
                    "PRODUCER_NOT_ALLOWED",
                    "producer not allowlisted for event_type",
                    details=details,
                    severity_map=severity_map,
                )
            ]
        if matching_rules:
            allowed_types = set()
            allowed_subtypes = set()
            forbidden = set()
            has_allowed_types = False
            has_allowed_subtypes = False
            rule_policy_error = None
            for pattern, rule in matching_rules:
                # Same collapse-to-"no constraint" fail-open as the
                # producer-authority half (R1-11 A-05 residuals b, c).
                rule_error = _producer_rule_policy_error(
                    rule, f"policy/routing.yaml#routing.producers.{pattern}"
                )
                if rule_error is not None:
                    rule_policy_error = rule_policy_error or rule_error
                    continue
                # Past this point the rule is a mapping; see the twin in
                # validate_producer_authority.
                rule_allowed_types = _list_values(rule.get("allowed_event_types"))
                if rule_allowed_types:
                    has_allowed_types = True
                    allowed_types.update(rule_allowed_types)
                rule_allowed_subtypes = _list_values(rule.get("allowed_event_subtypes"))
                if rule_allowed_subtypes:
                    has_allowed_subtypes = True
                    allowed_subtypes.update(rule_allowed_subtypes)
                forbidden.update(_list_values(rule.get("forbidden_event_types")))

            if rule_policy_error is not None:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "routing producer rule is malformed",
                        details={
                            "event_type": event_type,
                            "producer": producer,
                            "matched_patterns": matched_patterns,
                            "policy_error": rule_policy_error,
                        },
                        severity_map=severity_map,
                    )
                ]

            if has_allowed_types and event_type not in allowed_types:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "event_type not allowed for producer",
                        details={
                            "event_type": event_type,
                            "producer": producer,
                            "matched_patterns": matched_patterns,
                        },
                        severity_map=severity_map,
                    )
                ]
            if has_allowed_subtypes and event_subtype not in allowed_subtypes:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "event_subtype not allowed for producer",
                        details={
                            "event_subtype": event_subtype,
                            "producer": producer,
                            "matched_patterns": matched_patterns,
                        },
                        severity_map=severity_map,
                    )
                ]
            if event_type in forbidden:
                return False, [
                    _violation(
                        "EVENT_TYPE_NOT_ALLOWED_FOR_ROLE",
                        "event_type forbidden for producer",
                        details={
                            "event_type": event_type,
                            "producer": producer,
                            "matched_patterns": matched_patterns,
                        },
                        severity_map=severity_map,
                    )
                ]

    if event_type != "COMMAND_EVENT":
        return True, []
    if not _is_comms_producer(producer, routing_policy):
        details = {"producer": producer}
        command_cfg = routing_policy.get("command_event", {})
        if not isinstance(command_cfg, dict):
            details["policy_error"] = (
                "the command_event policy block must be a mapping; got "
                f"{type(command_cfg).__name__}, so no comms origin can be "
                "established (policy/routing.yaml#routing.command_event)"
            )
        return False, [
            _violation(
                "COMMAND_NOT_DECONFLICTED",
                "COMMAND_EVENT must originate from comms node",
                details=details,
                severity_map=severity_map,
            )
        ]
    return True, []
