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

Store `schema_id` in `pack.json`. Directory names should be filesystem-safe
slugs such as `vendor__acme_rf__v1`.

### Pack contents

- `mapping.yaml` field-level map from vendor input to ZMeta
- `enums.yaml` enum translations (optional)
- `units.yaml` unit conversions and expectations
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
