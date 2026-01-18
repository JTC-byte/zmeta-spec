# ZMeta to KLV Tag Dict (Template)

Overview: see `adapters/README.md`.

Purpose: project ZMeta observations into a decoded KLV-style tag dictionary.

Notes:
- This is NOT a STANAG 4609 binary encoder.
- Output is a tag dict intended for external video pipelines to embed.
- Input is limited to ZMeta `OBSERVATION_EVENT`.
