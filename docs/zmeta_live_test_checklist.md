# ZMeta Live-Test Checklist

**Standing artifact. Advisory / non-normative.**

Current release context: ZMeta v1.1.19.

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
- [ ] **A1-02: does anyone miss the dropped 2-D positions?** ADS-B targets
      reporting only barometric altitude produce no canonical `geo`.
      *Question:* run the adapter against live traffic, count how many targets
      lose their position, then ask whether the operator or the COP notices.
      *Second leg:* AIS on the same dongle. A vessel never has an altitude, so
      that is where the answer is unambiguous.
- [ ] **A1-03: does anyone need translation provenance canonically?**
      `lineage` requires `based_on`, so an original observation cannot say what
      format it came from. It is expressible natively. *Question:* does any
      consumer actually read it?

## B. Deployment path

- [ ] **Stock profile choice.** Both nodes now ship Profile H so adapter
      observations flow. *Question:* does a real bandwidth-constrained link
      want L instead, and if so what does a team lose by having to choose?
- [ ] **The five-minute wire check as written.** The metrics line is emitted
      only after `metrics_interval_sec` (30 s in the stock configs) has elapsed
      on the datagram path, so a short replay prints no metrics output at all,
      rather than a low count. The quickstart's `recv=N ... fwd=N` line will
      not appear, and the documented check replays four events in under a
      second. *Question:* does the absence mislead a real team, or does the
      far-consumer count suffice?
- [ ] **Two nodes on one host.** Both compose files publish `5555:5555/udp`, so
      the pair cannot come up unmodified on a single machine. *Question:* do
      teams actually co-host, or is the two-machine assumption fine?
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

---

## How to close an item

1. Run it. Record what happened, dated, inline.
2. If it did not matter, say so and strike it. That is the outcome this file
   is optimised for.
3. If it did matter, move it to `docs/zmeta_refinement_handoff.md` (work) or
   `docs/zmeta_doctrine_review_log.md` (standard), with the evidence.
