## Mapping Packs

Mapping packs describe how to translate vendor payloads into ZMeta v1.0.

### schema_id naming convention

Use a stable, vendor-scoped identifier:

```
vendor:acme_rf:v1
```

### Pack contents

- `mapping.yaml` field-level map from vendor input to ZMeta
- `enums.yaml` enum translations (optional)
- `units.yaml` unit conversions and expectations
- `tests/` input samples + expected ZMeta output

### Structure example

```
adapters/mapping-packs/<schema_id>/
  mapping.yaml
  enums.yaml
  units.yaml
  tests/
    input.json
    expected.json
```
