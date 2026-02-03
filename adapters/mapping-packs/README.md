## Mapping Packs

Overview: see `adapters/README.md`.

Mapping packs describe how to translate vendor payloads into ZMeta v1.0.

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
