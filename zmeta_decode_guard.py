"""Decode guards shared by the reference decoders (contract 3.4; doctrine F7-01).

A decode that chose between two values for one name, or dropped a member it
could not type, produces an event the producer never sent. Forwarding it would
make every consumer behind the gateway agree on the gateway's choice. The
reference decoders refuse such input under the governed diagnostic code
DECODE_AMBIGUOUS instead of repairing it:

- JSON: an object with a duplicate key. `json.loads` keeps the last value
  silently; `pairs_refusing_duplicates` is the `object_pairs_hook` that raises.
- protobuf: an unknown field number, a known field number carrying a wire
  type the schema does not use for it, or a non-repeatable field that appears
  twice, at any message level (zmeta_proto; `lineage.based_on` is the one
  repeated field).

The exception is a ValueError, so every caller that already refuses malformed
input keeps refusing; `decode_ambiguous` lets the gateway name the code.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple


class DecodeAmbiguousError(ValueError):
    """The wire bytes admit more than one canonical reading; refused, never repaired."""

    decode_ambiguous = True


def pairs_refusing_duplicates(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
    """`object_pairs_hook` for `json.loads`: a duplicate key is refused, not resolved."""
    out: Dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise DecodeAmbiguousError(
                f"ambiguous JSON: duplicate key {key!r} in one object; "
                "the decoder will not choose between its values"
            )
        out[key] = value
    return out


def is_decode_ambiguous(exc: BaseException) -> bool:
    return bool(getattr(exc, "decode_ambiguous", False))
