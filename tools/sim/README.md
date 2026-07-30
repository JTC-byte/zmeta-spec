# Deployment simulation harnesses

Scripts that stand up real gateway nodes, push real traffic through them, and
report what actually arrived. They exist because reading the deployment path and
running it produced different answers: the 2026-07-30 reps found that a
containerized node could not deliver anything it produced, and that a documented
pre-event rehearsal passes while a real sensor feed shows nothing on the COP.
Neither was visible in the code or in a green test suite.

## What these are not

**These are not part of the standard, and nothing here may become load-bearing
for conformance.** ZMeta is a data standard. The tools that define and enforce
it are the schema, the policy files, the validators in `tools/`, and the
conformance corpora. A simulation harness is an operational convenience built on
top of those, and the moment a conformance claim depends on one, the standard has
quietly grown an implementation dependency it does not need.

That boundary is enforced rather than promised.
`gateway/tests/test_sim_boundary.py` asserts that no governed validator, no
kernel-gate tool and no conformance artifact imports anything from this
directory. If someone wires a sim harness into the gate, that test fails.

## The extraction question, deliberately left open

Whether this belongs in the standard's repository at all is undecided. It is
here because it costs nothing today and because the reps it enables are worth
more early than late, when adapters are being written against real sensors.

The criterion for moving it out, agreed 2026-07-30: **when these harnesses grow
their own configuration surface, their own dependencies, or an audience that is
not "someone integrating a sensor with ZMeta", they are a product and belong in
their own repository.** The boundary test above is what keeps that move cheap:
as long as nothing governed imports this directory, extraction is a directory
move and a README pointer, not a refactor.

Recorded as doctrine log **S1-04**, so the question comes back on a trigger
rather than drifting.

## `two_node.py` — the wire path

Runs an edge node and a GCS node, replays a corpus into the edge, and reports
what reached the far consumer and the CoT listener.

```
python tools/sim/two_node.py
python tools/sim/two_node.py --control
python tools/sim/two_node.py --corpus examples/zmeta-command-examples.jsonl
python tools/sim/two_node.py --edge-profile H --gcs-profile L
```

**Run `--control` first, and read its verdict before believing any other run.**
The control starts the GCS node and deliberately does not start the edge node,
so nothing can reach the downstream ports. It must report zero. If it reports
anything, some other process is feeding those ports and every non-control result
is meaningless. This is not ceremony: a clean run and a dead harness produce
identical output without it, which is the failure this whole directory exists to
avoid.

Exit codes are `0` pass, `1` fail, `2` invalid. Invalid means the run could not
establish the conditions it needed, and it is deliberately distinct from a
failure, so "the harness never ran" cannot be read as "the path is broken".

The harness runs child gateways with `python -u`, matching
`deploy/*/docker-compose.yml`. Without it the startup banner sits in a
block-buffered pipe and a live gateway is indistinguishable from a dead one.
That cost the first rep of the 2026-07-30 session a false negative.

## `throughput.py` — capacity

Pushes load through one node and reports four independent counts: offered, what
the gateway says it received, what it says it forwarded, and what a separate
socket actually got.

```
python tools/sim/throughput.py --events 2000 --rate 200
python tools/sim/throughput.py --events 5000 --rate 0
```

Agreeing counts are the only way to tell a clean run from a lossy one.
`sent > recv` is loss upstream of the process, in the kernel receive buffer,
which the gateway cannot see and does not count. `recv > fwd` is refusal, and
the violations counter says why. `fwd > sink` is loss downstream.

The generator mints a fresh `event_id` for every event, as a real producer does.
This matters more than it sounds: a gateway deduplicates on `event_id`, so a
generator that cycles a corpus verbatim measures duplicate suppression rather
than capacity. The first throughput run of the 2026-07-30 session reported 17%
delivery for exactly that reason, and it was a property of the generator, not of
the gateway. The same effect is why `tools/replay.py --loop` forwards nothing
after its first pass.

Reference figures from 2026-07-30, one x86 host, Profile H, JSON in and compact
out. These are a baseline for comparison, not a specification:

| Offered | Delivered | Note |
|---|---|---|
| 200 events/s | 100% | `drops=0 violations=0` |
| 400 events/s | 100% | still clean |
| 600 events/s | 74.5% | node saturates near 422/s |
| 1000 events/s | 44.4% | `drops=0` throughout, loss is upstream |

## Ports

Both harnesses use ports in the 155xx and 169xx range rather than the stock
5555/5556/6969, so a rep cannot collide with a running deployment or quietly
receive its traffic. Override them if those are in use.
