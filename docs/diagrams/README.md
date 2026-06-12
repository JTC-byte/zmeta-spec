# Overview figures

`generate_figures.py` produces the data-driven SVG figures embedded in
[`../zmeta_professional_overview.md`](../zmeta_professional_overview.md). The
figures are intentionally vendor-neutral and reproducible: they are built only
from this repo's own example events, the policy pack, and the repo encoding
modules. No third-party dependencies are required (standard library only), and
the output is plain SVG so it renders inline on GitHub and scales cleanly.

## Regenerate

```bash
python docs/diagrams/generate_figures.py
```

Outputs are written to `docs/img/`:

| File | Figure | Source of truth |
| --- | --- | --- |
| `c1-zmeta-at-a-glance.svg` | One-glance pipeline + retask loop | composite, vendor-neutral |
| `b1-event-anatomy.svg` | Anatomy of a ZMeta event | `examples/zmeta-profile-H-examples.jsonl` |
| `b2-lineage-chain.svg` | `based_on` lineage chain | `examples/zmeta-profile-H-examples.jsonl` |
| `b3-encoding-sizes.svg` | Wire-size comparison | `examples/zmeta-profile-L-examples.jsonl` + `zmeta_cbor` / `zmeta_compact` / `zmeta_proto` |
| `b4-profile-matrix.svg` | Profiles vs allowed event families | `policy/profiles.yaml` |
| `b5-triangulation.svg` | Multi-LOB triangulation + error ellipse | synthetic, vendor-neutral geometry |

The architecture, sequence, and flow diagrams in the overview are inline
[Mermaid](https://mermaid.js.org/) blocks (rendered by GitHub), not files in this
directory.

## Conventions

- Figures draw on a white card with dark ink so they stay legible in both light
  and dark GitHub themes.
- Encoding byte counts are measured at generation time, so they stay honest if
  the example events or encoders change.
- Keep figures vendor-neutral; program- or vendor-specific evidence does not
  belong in the public spec overview.
