# Overview figures

`generate_figures.py` produces the data-driven SVG figures embedded in
[`../zmeta_professional_overview.md`](../zmeta_professional_overview.md) and
[`../zmeta_ontology_reference.md`](../zmeta_ontology_reference.md). The
figures are intentionally vendor-neutral and reproducible: they are built only
from this repo's own example events, the policy pack, the governance
manifests, and the repo encoding modules. No third-party dependencies are
required (standard library only), and the output is plain SVG so it renders
inline on GitHub and scales cleanly.

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
| `d1-authority-stack.svg` | The six-tier authority stack | composite, mirrors `docs/zmeta_change_governance.md` |
| `d2-promotion-chain.svg` | Promotion chain + per-stage requirements | v1.0 schema allOf arms, `policy/lineage.yaml`, `policy/producer-authority.yaml` |
| `d3-true-today.svg` | Current-release counts ledger | conformance manifest, extension registry, `policy/violation-codes.yaml`, `adapters/`, roadmap, release manifest |
| `e1-adapt-once.svg` | Point-to-point bridges vs adapt-once | counted from `adapters/ingress/` and `adapters/egress/` |
| `e2-translation-pipeline.svg` | Native input -> normalize -> canonical -> projections | composite labels from `adapters/README.md`; sizes measured from `examples/zmeta-profile-H-examples.jsonl` |
| `e3-wire-matrix.svg` | Measured bytes: encodings x profiles | `examples/zmeta-profile-{H,M,L}-examples.jsonl` + repo encoders |
| `e4-proof-surface.svg` | Conformance proof-surface counts | fixture suites under `conformance/`, `KERNEL_GATE_CHECKS` |
| `f1-thin-waist.svg` | Replaceable products above and below one locked contract | `adapters/`, event-family enum in `schema/zmeta-event-1.0.schema.json` |
| `f2-behind-the-icon.svg` | One display icon decomposed into its real event chain | `examples/zmeta-eo-chain-examples.jsonl` |

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
