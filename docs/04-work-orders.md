# Foundry — Work Orders

Work Orders to build Foundry V1 (Phase 1 of `03-roadmap.md`). Each is a discrete,
well-scoped unit of work that implements the architecture in `02-architecture.md`.
This is Foundry dogfooding its own artifact format.

## Format

Each Work Order has: an ID, a goal, scope (in / out), dependencies, a done-when
check, and metadata — **Complexity** (S/M/L) and **Risk** (Low/Medium/High). No
time estimates: for LLM-agent work they are fiction and mislead. Work Orders
trace upward to a Roadmap item and obey the principles. They describe *what* to
build, not *how* to code it.

A Work Order is a **shippable outcome**, not an implementation step
(`06-decisions.md` D-011, CTO compression). Tests, setup, and hardening fold into
*Done when*; decisions go to Open Questions; low-leverage units are merged. Prefer
the fewest, highest-leverage Work Orders that cover the Roadmap — vertical
capabilities over horizontal layers. WO-008 is the end-to-end loop test, not the
only testing.

---

## WO-001 — Services foundation

**Goal:** Thin shared layer the agents depend on.
**Roadmap link:** Phase 1, core artifact chain.
**In scope:** LLM client wrapper (Anthropic SDK), artifact file read/write,
config loading. Resolve the per-project output location: artifact IO targets
`projects/<name>/` (per `02-architecture.md`, Output Location), never Foundry's
own `docs/`.
**Out of scope:** Anything agent-specific, any orchestration.
**Depends on:** none. (Parallel with WO-002.)
**Done when:** an agent can call the LLM, and read/write a markdown artifact in
`projects/<name>/`, through `services/`.
**Complexity:** M. **Risk:** Low.

---

## WO-002 — Artifact templates

**Goal:** Section skeletons for the four artifacts.
**Roadmap link:** Phase 1.
**In scope:** A plain-markdown template each for Vision, Architecture, Roadmap,
Work Orders, defining the named section structure agents fill in (per
`02-architecture.md`, Template Strategy). Each template includes an
`## Assumptions` section.
**Out of scope:** Generation logic. Schema engines, databases (excluded by
design).
**Depends on:** none. (Parallel with WO-001.)
**Done when:** `templates/` holds one structured markdown template per artifact,
each with an Assumptions section, matching the shape of the docs in this repo.
**Complexity:** S. **Risk:** Medium (template strategy is the first thing agents
couple to).

---

## WO-002b — Product Input intake

**Goal:** Load and validate the Product Input that starts every project.
**Roadmap link:** Phase 1, "Capture a structured Product Input."
**In scope:** Read `projects/<name>/product-input.md`
(`08-product-input-template.md` shape), validate required sections are present,
make it available as the Vision agent's input.
**Out of scope:** Generating or improving the Product Input (the founder writes
it); any artifact generation.
**Depends on:** WO-001.
**Done when:** a filled Product Input is loaded and validated, ready for WO-003.
**Complexity:** S. **Risk:** Low.

---

## WO-003 — Vision agent

**Goal:** Produce a Vision from the Product Input.
**Roadmap link:** Phase 1, "Create a Vision from the Product Input."
**In scope:** Take the Product Input, fill the Vision template, write
`projects/<name>/00-vision.md`. **First agent — establishes the agent pattern**
(input assembly + template fill + LLM call + artifact write) that WO-004..006
reuse.
**Out of scope:** Any downstream artifact.
**Depends on:** WO-001, WO-002, WO-002b.
**Done when:** given a Product Input, the agent writes a coherent Vision artifact.
**Complexity:** L (carries the one-time cost of designing the agent pattern).
**Risk:** Medium (pattern spike; 004–006 inherit its decisions).

---

## WO-004 — Architecture agent

**Goal:** Derive Architecture from the Vision.
**Roadmap link:** Phase 1, "Derive Architecture from the Vision."
**In scope:** Read Vision, fill Architecture template, write
`projects/<name>/01-architecture.md`. Reuses the WO-003 agent pattern.
**Out of scope:** Reading any external codebase (that is Repo Intelligence,
deferred).
**Depends on:** WO-003.
**Done when:** given a Vision, the agent writes an Architecture that traces to it.
**Complexity:** S. **Risk:** Low.

---

## WO-005 — Roadmap agent

**Goal:** Derive a Roadmap from Vision + Architecture.
**Roadmap link:** Phase 1, "Derive a Roadmap."
**In scope:** Read Vision and Architecture, write `projects/<name>/02-roadmap.md`.
Reuses the WO-003 agent pattern.
**Out of scope:** Scheduling, estimation tooling.
**Depends on:** WO-004.
**Done when:** every Roadmap item traces back to the Vision.
**Complexity:** S. **Risk:** Low.

---

## WO-006 — Work Order agent

**Goal:** Break Roadmap items into Work Orders.
**Roadmap link:** Phase 1, "Break Roadmap items into Work Orders."
**In scope:** Read Roadmap, write `projects/<name>/03-work-orders.md` with scoped
Work Orders. Reuses the WO-003 agent pattern.
**Out of scope:** Executing Work Orders (no coding agents in V1).
**Depends on:** WO-005.
**Done when:** Roadmap items become Work Orders precise enough to act on without
re-deriving context.
**Complexity:** S. **Risk:** Low.

---

## WO-007 — Chain workflow

**Goal:** Orchestrate the full loop, Product Input → Work Orders.
**Roadmap link:** Phase 1, the core loop end to end.
**In scope:** Run intake + the four agents in order, pass each artifact
downstream, write all to `projects/<name>/`. Support re-running from a
**user-selected** entry stage downward (the V1 coherence mechanism per
`02-architecture.md`); no auto drift-detection. Plain-Python orchestration — no
agent framework (per `06-decisions.md`, D-010).
**Out of scope:** Targeted/automatic drift detection (deferred).
**Depends on:** WO-002b, WO-003..WO-006.
**Done when:** a founder goes from a Product Input to Work Orders in one run, and
can re-run from a chosen stage downward to remove drift.
**Complexity:** M. **Risk:** Medium (entry-stage selection + output paths).

---

## WO-008 — Loop tests

**Goal:** Verify the loop runs and produces correctly structured artifacts.
**Roadmap link:** Phase 1 "done when."
**In scope:** Test the chain workflow end to end; assert each artifact is produced
in its expected structure under `projects/<name>/`.
**Out of scope:** Quality grading of artifact content.
**Depends on:** WO-007.
**Done when:** tests confirm Product Input → four coherent artifacts.
**Complexity:** S. **Risk:** Low.

---

## Deferred (not Work Orders in V1)

Coding agents, GitHub integration, LLM Council, and Repo Intelligence are out of
V1 (`03-roadmap.md`). No Work Orders exist for them yet.
