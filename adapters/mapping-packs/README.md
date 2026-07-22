## Mapping Packs

Overview: see `adapters/README.md`.

Mapping packs describe how to translate vendor payloads into ZMeta v1.0.

### What a mapping pack is (and is not)

A mapping pack is a *declarative description plus test evidence*: field maps,
enum translations, unit conversions, and input/expected-output samples. This
repository does **not** ship a runtime engine that executes `mapping.yaml`
automatically — translation runs in adapter code (see
`adapters/ingress/template/`), and the pack's `tests/` samples are the
conformance evidence that the adapter implements the pack faithfully.
`tools/install_mapping_pack.py` copies and registers a pack; it does not make
the pack executable by itself. Plan adapter implementation effort
accordingly.

### schema_id naming convention

Use a stable, vendor-scoped identifier:

```
vendor:acme_rf:v1
```

Store `schema_id` in `pack.json`. The directory name is the `pack_slug`: a
filesystem-safe, lowercase, hyphenated slug — the shipped exemplar
`example-vendor-pack` (`schema_id: vendor:example_rf:v1`,
`pack_slug: example-vendor-pack`) is the pattern to copy. Keep slugs to
lowercase letters, digits, and hyphens; the colon-separated `schema_id` is
an identifier, not a directory name, and never appears on the filesystem.

### Pack contents

- `mapping.yaml` field-level map from vendor input to ZMeta
- `enums.yaml` enum translations (optional)
- `units.yaml` unit conversions and expectations (optional when the format
  declares units elsewhere, e.g. a registration codex or fixed-unit wire)
- `pack.json` manifest with `schema_id`, `pack_slug`, and version (recommended)
- `tests/` input samples + expected ZMeta output

### Structure example

```
adapters/mapping-packs/<pack_slug>/
  mapping.yaml
  enums.yaml
  units.yaml
  pack.json
  tests/
    input.json
    expected.json
```

### Install

Copy the pack folder into `adapters/mapping-packs/<pack_slug>`, or use:

```
python tools/install_mapping_pack.py --pack <path>
```

### Real edge-comms corpus

`edge-comms-bladerf/` ships two real bladeRF / ROS2 EW `rf_detection`
inputs from a flight blackbox with schema-valid RF `OBSERVATION_EVENT`
expected outputs. Use it when validating a new RF adapter against governed
shape and honesty rules. See that pack's README for provenance and
validation commands.

### SAPIENT / BSI Flex 335 pack

`sapient-bsi-flex-335/` (`vendor:sapient_bsi335:v2`) maps SapientMessage
protobuf-JSON to ZMeta both directions, with reference adapters under
`adapters/ingress/sapient/` and `adapters/egress/sapient/`. It is the
worked example for registration-declared formats (units/error codex from
Registration, refuse-when-unregistered) and for split fact/opinion
reports. See that pack's README for the wire-validation record.
