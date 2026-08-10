# ZMeta Live-Test Checklist

**Standing artifact. Advisory / non-normative.**

Current release context: ZMeta v1.1.21.

## Why this file exists

Hardening something we have not observed failing is speculation, and
speculation has no natural stopping point. In one session it produced three
rounds of rework on a single guard before anyone noticed.

The rule this file implements, from the maintainer, 2026-07-28:

> **Validate the assumption live before hardening it.** If it cannot be
> live-validated, document it as an open question to check during the live
> test rather than acting on it. Proactive hardening stays available where the
> defect is certain or the cost of being wrong is high — but it is the
> exception, not the default.

Sections A, B and D are questions with a yes/no answer that a real deployment
can give. They are not tasks. Answering "no, nobody cared" is a complete and
valuable result: it closes the item and prevents work.

Section C is different and is labelled as such. Those are access-gated tasks
carried from earlier cycles, things that cannot be done without hardware or
live tooling. They are listed here because this is where a tester looks. They
are not discipline-10 deferrals.

Record the answer inline, dated. Items that turn out to matter graduate to the
handoff queue or the doctrine log with evidence attached.

---

## A. Alphabet gaps found by the ADS-B adapter (doctrine log cycle A1)

These are the highest-value questions here, because each one is a candidate
change to the standard and none should move without field evidence.

- [ ] **A1-01: does anyone need calibrated power?** `power_dbm` is a required
      RF minimum feature; every SDR reports uncalibrated relative power.
      *Question:* does a consumer ever compare power across two different
      sensors? If nobody does, the field is decorative and the gap is theory.
      *Sharper form:* the shipped `kraken` adapter writes uncalibrated "RSSI
      dB" into `power_dbm` and it translates, fuses and maps correctly in TAK
      today. Put a second RF sensor beside it in one consumer and see whether
      anything actually breaks.
- [x] **A1-02: does anyone miss the dropped 2-D positions?** ADS-B targets
      reporting only barometric altitude produce no canonical `geo`.
      *Question:* run the adapter against live traffic, count how many targets
      lose their position, then ask whether the operator or the COP notices.
      *Second leg:* AIS on the same dongle. A vessel never has an altitude, so
      that is where the answer is unambiguous.
      *Answered 2026-08-02, tick recorded 2026-08-09:* overtaken by promotion
      rather than settled in the field. The AIS adapter was the unambiguous
      second leg, the maintainer adjudicated the declared-dimensionality shape
      on 2026-08-02, and v1.1.20 shipped it end to end (doctrine log A1-02,
      CLOSED). What remains for the field is the render check, not this
      question: whether consumers show a declared 2-D position honestly
      (the section C TAK item's `<geo_dimensionality>` detail element).
- [ ] **A1-03: does anyone need translation provenance canonically?**
      `lineage` requires `based_on`, so an original observation cannot say what
      format it came from. It is expressible natively. *Question:* does any
      consumer actually read it?

## B. Deployment path

- [ ] **Stock profile choice.** Both nodes now ship Profile H so adapter
      observations flow. *Question:* does a real bandwidth-constrained link
      want L instead, and if so what does a team lose by having to choose?
- [ ] **The five-minute wire check as written.** The metrics line is emitted
      only after `metrics_interval_sec` has elapsed **on the datagram path**, so
      a short replay prints no metrics output at all, rather than a low count.
      **Reproduced 2026-07-30 and sharper than recorded:** the trigger is
      datagram arrival, not a timer, so shortening the interval does not help.
      Run at a one-second interval with seven seconds of idle, still nothing;
      the final window is never flushed on shutdown either. A team replaying any
      finite corpus will never see the line at any interval setting. The
      quickstart now says so and points at the far-consumer count as the real
      check. *Question that remains:* does a team hitting a 100% refusal in the
      field notice, given that neither channel says anything on the console?
- [x] **Two nodes on one host — FIXED 2026-07-30.** Both compose files published
      `5555:5555/udp` and the second one failed with `Bind for 0.0.0.0:5555
      failed: port is already allocated`. Host ports are now overridable
      (`ZMETA_EDGE_PORT`, `ZMETA_GATEWAY_PORT`) and the pair was run end to end
      on one machine. Closed rather than asked, because the answer did not
      depend on how teams deploy: the fix costs nothing and the failure was
      certain for anyone who tried.
- [x] **Containerized nodes could not deliver anything — FIXED 2026-07-30.**
      `forward.host` and `cot.host` are `127.0.0.1`, which inside a container is
      the container's own loopback, so both output streams were delivered to a
      namespace nothing can read, with no error. Measured before the fix: the
      container reported `recv=722 fwd=722` while a receiver on the host's
      `127.0.0.1:5556` saw zero. The Compose files now override both hosts on
      the command line. This was a real break of the shipped deployment path,
      not a question for the field.
- [ ] **CoT reaches TAK only for `STATE_EVENT`.** Five clean ADS-B observations
      traversed both nodes and produced zero CoT, while the example corpus
      produces one because it contains one `STATE_EVENT`. The documented
      rehearsal therefore passes and a real sensor then shows nothing.
      **Half-answered 2026-07-30 by building the missing half:**
      `adapters/projector/track/` closes it for sources whose subjects broadcast
      an identity, and the same snapshot that produced zero CoT now produces two
      tracks. A source whose identity must be inferred still needs a real
      tracker, which stays consumer-side by design. *Question that remains:* how
      many teams arrive with an inferred-identity sensor and no tracker? If most
      do, the ladder from observation to track needs to be far more prominent
      than one section of a quickstart.
- [ ] **Does anyone act differently on a known accuracy?** A v1.0
      `STATE_EVENT` has nowhere to carry positional uncertainty, so a track
      reaches TAK with `ce="9999999.0"` even when the ingress adapter measured a
      real ellipse (ADS-B derives 30 m from `nac_p: 9`). Observed end to end.
      Doctrine log SIM1-05. *Question:* does an operator treat a 30 m track
      differently from an unknown one, or is everything treated as approximate
      anyway? "Nobody acts on it" closes the item and the limit stays documented.
- [ ] **`drops=0` does not mean nothing was lost.** Loss from offered load above
      capacity happens in the kernel receive buffer, upstream of the gateway, so
      the gateway cannot count it. Measured on one x86 host: 100% delivery at
      400 events/s, saturation near 422/s, and at 1000/s offered only 44%
      arrived while the node still reported `drops=0 violations=0`. *Question:*
      does any deployment run near capacity, and if so is a receive-buffer
      overflow counter worth the platform-specific code it needs?
- [ ] **Adapter in about an hour.** *Question:* time a real author, cold, from
      `AUTHORING.md` to a green ladder. The producer-authority wall is closed;
      the remaining cost is the contract reading §0 routes them through.

## C. Integration items, decomposed by what is actually gated

**Re-tested 2026-07-28, and the section title was wrong.** These were carried as
"gated on hardware or access". Decomposing each one closed one item outright and
showed most of the rest are only partly gated. The prompt for the re-test came
from the fielded consumer: *"blocked" is a claim too*, and they had found their
own last audit criterion was seven sub-conditions, six of which closed the same
day on evidence already in hand. Three items here were first spotted as misfiled
by noticing; that is exactly the signal to re-test the whole list rather than the
ones that happened to catch the eye.

- [x] **Cross-platform hash agreement — ANSWERED 2026-07-28. No hardware
      needed.** `tools/compute_contract_hash.py` on Windows and in CI on ubuntu,
      over the same tree, produce byte-identical values for all four hashes
      (`contract_hash=3cafdd2705704b5dc5b1dc9efbb2e4840c40e1ff1f8437cb6f29ddd53c63e795`),
      confirmed by reading the CI job log rather than re-deriving locally. The
      item conflated two questions: whether the hash is platform-stable, which
      this answers, and whether a deployment pair is configured consistently,
      which was never a hash question. Note for anyone re-checking: the manifest
      records *bundle* hashes, which are a different computation — comparing
      those to this tool's output looks like a mismatch and proves nothing.
- [ ] **SITL end-to-end gate — never gated at all.** Software in the loop is
      software; no airframe is required. It is the stated precondition for live
      GCS-originated tasking and the only item here that exercises the command
      path against something with the authority to refuse.
      **Design precondition, adopted before the harness exists:** the telemetry
      must distinguish "delivered and refused" from "never delivered". A run
      reporting *no violations* must be structurally incapable of also meaning
      *the harness never delivered a command*. Learned from a consumer whose
      retention job returned `0` for both "ran, matched nothing" and "failed",
      producing six log lines that proved a query healthy against production
      when no eligible row had ever existed.
- [ ] **TAK / COP display — gated on a deploy step, not on access.**
      `takserver-docker 5.7-RELEASE-43` is already on hand locally. The
      `cot.config` pedigree knob that enables `<precisionlocation>` is shipped
      and pinned but has never rendered on a real COP.
- [ ] **ADS-B end to end — roughly five of seven links testable now.** The chain
      is RTL-SDR → `dump1090` → adapter → edge gateway → GCS gateway → CoT →
      TAK. Only the first two links need hardware; everything downstream runs
      today against a captured or synthetic `aircraft.json`. Combined with the
      TAK item above, the whole path except the RF front end is reachable.
- [ ] **SAPIENT — partly closed already.** Single-node Apex v4.2.0 validation
      was performed and recorded at v1.1.15. What remains is multi-node routing
      and the official C# BSI Flex 335 harness (no .NET SDK on the validation
      host). Narrower than the original item title implied.
- [ ] **Real-Pi throughput — genuinely hardware, and the only one.** Build,
      dependencies, startup and semantics are verified under ARM64 emulation;
      only the throughput number is unmeasured. The harness and metric can be
      built on x86 first so the Pi visit is a five-minute confirmation rather
      than a design exercise.

## D. Packaging

- [ ] **Does anyone use the dist bundle?** Its scope was contested twice in one
      session: the toolchain was removed, then restored on measurement.
      *Question:* do consumers take dist, or only the edge/gateway bundles and
      clones? If nobody takes dist, the argument cost nothing either way.
- [ ] **`--conformance-classes` from a bundle** reports missing process
      records by design. *Question:* does that read as a corrupt download to
      anyone who did not read `conformance/README.md` first?

## E. Pre-flight card and break-report card for live runs

Added 2026-08-03 for the v1.1.20 field deployments. The maintainer's
direction at hand-off: run the stack live as published and collect field
defects, rather than continuing internal hardening cycles. The two lists
below collect the known deployment failure modes from this file and the
release records into a sequence an operator can execute in order. Each
line cites recorded work; none of it is new doctrine.

**Pre-flight, in order, before the first live event:**

1. **Pin and verify the release.** Deploy from the v1.1.20 tag or bundle,
   then `sha256sum -c SHA256SUMS_v1.1.20.txt` against the published
   assets. Anyone verifying an older tag reads
   `docs/release_checksum_errata.md` first.
2. **Projector stage present.** CoT projects STATE_EVENT only. An ingress
   feed with no fusion or track stage shows nothing on TAK, and a
   rehearsal corpus that happens to contain a STATE_EVENT passes while the
   live feed then fails (doctrine SIM1-03). Confirm
   `adapters/projector/track/` or the team's own tracker is in the path,
   and rehearse with the live sensor's own output, never the example
   corpus alone.
3. **Host and port overrides when containerized.** `forward.host` and
   `cot.host` must be overridden off container loopback, and co-located
   nodes need `ZMETA_EDGE_PORT`/`ZMETA_GATEWAY_PORT` (both fixed
   2026-07-30; the deploy README's override path is the tested one).
4. **TIME_STATUS before the first command.** A node that has not published
   TIME_STATUS refuses every command with `TIMING_STATUS_MISSING`; a
   rehearsal lost four of four commands to this (2026-07-30).
5. **ts horizon for replayed data.** Replayed historical corpora trip the
   warn-only ts-plausibility window by design. Set
   `ts_plausibility_horizon_ms: 0` for sims and replays; keep the default
   for live sensors.
6. **Expect console silence on healthy idle nodes.** The metrics line is
   datagram-driven, so an idle or short-replay node prints nothing at any
   interval setting (section B). The delivery check is the far consumer's
   received count, not console output.
7. **Capacity margin.** Loss above capacity happens upstream of the
   process, so `drops=0` can accompany heavy loss (section B; saturation
   near 422 events/s, one x86 host, Profile H; no Pi datum exists yet,
   section C). Measure offered versus received at the far end.
8. **Complete the two open preconditions before the activities they
   gate:** SITL before any live GCS-originated tasking, with
   no-op-versus-failure telemetry built first, and the TAK render check
   of the `<geo_dimensionality>` detail element on a fielded client
   before relying on it operationally. Both are recorded in section C.

**Break report, captured at the moment of failure:**

- `metrics.jsonl` from every node in the path (violation details, clock
  health, truncation counts and CoT state are all present as of v1.1.20).
- Egress loss notes and counters.
- Ten raw input events around the failure, the exact configs in use, and
  the version or tag of every node.
- Record whether the failing event arrived and was refused (a violation
  record with a reason code exists) or never arrived (no record on any
  node). A report that does not answer this cannot be acted on, because
  "no violations" is also what a delivery failure looks like.
- Field reports are handled as telemetry under the contribution intake
  process; an issue carrying the artifacts above is a complete
  contribution.

---

## How to close an item

1. Run it. Record what happened, dated, inline.
2. If it did not matter, say so and strike it. That is the outcome this file
   is optimised for.
3. If it did matter, move it to `docs/zmeta_refinement_handoff.md` (work) or
   `docs/zmeta_doctrine_review_log.md` (standard), with the evidence.
