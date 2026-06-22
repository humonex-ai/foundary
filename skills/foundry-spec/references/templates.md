# Foundry artifact templates (authoritative, verbatim)

These are the exact template files Foundry validates against. Keep every `##` header verbatim and replace each _italic prompt_ with real content. Each file has a guidance block (Purpose / Required Sections / How To Use) and, below the `<!-- TEMPLATE BODY -->` marker, the skeleton you fill.

With the Foundry MCP connected, `get_templates` returns the live copies — prefer those. This file is the offline fallback (web / ChatGPT).

A complete plan = four required artifacts: **vision, architecture, roadmap, work-orders**. `product-input` is optional.


---

## `product-input.md`

# Product Input — Template

> Artifact file: `product-input.md` · Upstream: _none (chain head)_ · Filled by: the founder

## Purpose

The Product Input is the canonical starting point for every Foundry project
(`02-architecture.md`, Shape in One Line). It captures the founder's intent in
enough structure to remove ambiguity before any artifact is generated. It feeds
the Vision agent. Keep it to roughly one page — if it is longer than the Vision
it produces, it is doing the Vision's job.

## Required Sections

- **Problem** — what hurts today.
- **Users** — who has the problem.
- **Goals** — outcomes success enables.
- **Non-Goals** — what this explicitly will not do.
- **Constraints** — hard limits (tech, budget, timeline, team, regulatory).
- **Success Criteria** — how we know it worked.
- **Assumptions** — what is taken as true but unverified.
- **Open Questions** — known unknowns not yet resolved.

## How To Use

Humans fill each section directly. Keep every `##` header verbatim; replace each
italic prompt with real content. The document must read clearly on its own
(`01-principles.md` #7).

<!-- TEMPLATE BODY -->

# Product Input — {{ project }}

## Problem
_What hurts today. One paragraph, concrete, not aspirational._

## Users
_Who has this problem. Primary user first; be specific about role and context._

## Goals
_What success enables. 3–5 outcomes, not features._

## Non-Goals
_What this explicitly will not do. Scope discipline starts here._

## Constraints
_Hard limits: technology, budget, timeline, team size, regulatory, existing systems._

## Success Criteria
_How we will know it worked. Measurable where possible._

## Assumptions
_What is taken as true but not yet verified. Surfacing these makes garbage-in
visible and aids later drift detection._

## Open Questions
_Known unknowns the founder has not resolved yet. The Vision agent triages these
into the project's Decision List (each becomes a Decision, most as Status = Open)._


---

## `vision.md`

# Vision — Template

> Artifact file: `00-vision.md` · Upstream: `product-input.md` · Produced by: Vision agent (WO-003)

## Purpose

The Vision states what we are building and why, derived from the Product Input
(`00-vision.md`). It is the first generated artifact and the parent every
downstream artifact traces back to (`01-principles.md` #3). It does not propose
architecture or work — vision only.

## Required Sections

- **Problem** — the pain being solved, in product terms.
- **Users** — who it is for.
- **Goals** — what success looks like.
- **Non-Goals** — what this product is deliberately not.
- **Constraints** — hard limits carried from the Product Input (technology,
  interface, storage, budget, team, regulatory). These must survive to the
  Architecture stage.
- **Success Criteria** — how the vision is judged met.
- **Assumptions** — what the vision takes as true.
- **Decision List** — the single, triaged list of decisions (an Open Question is
  a Decision with Status = Open). Seeded from the Product Input's Open Questions
  and carried forward to every later artifact.

## How To Use

Agents fill each section from the upstream Product Input, keeping every `##`
header verbatim and replacing each italic prompt with real content. No section
should contradict the Product Input; surface tensions under Assumptions or as
Decision List rows. Preserve the Product Input's hard Constraints faithfully — do
not drop the stack, interface, or storage limits. Stay at the vision altitude —
no components, no roadmap.

Build the **Decision List** from the Product Input's Open Questions, one triaged
row each (see "Decision List" below for the format and triage rules). It is the
single home for unresolved choices — there is no separate free-prose Open
Questions section.

<!-- TEMPLATE BODY -->

# Vision — {{ project }}

## Problem
_The core pain this product exists to solve, in one or two paragraphs._

## Users
_Who this is for. Primary user first._

## Goals
_What success enables. Outcomes, not features._

## Non-Goals
_What this product is deliberately not. The boundary that prevents scope creep._

## Constraints
_Hard limits carried faithfully from the Product Input: technology, interface,
storage, budget, team, regulatory. Do not drop or soften them — the Architecture
stage depends on these surviving._

## Success Criteria
_How we know the vision is being met. Measurable where possible._

## Assumptions
_What the vision takes as true but has not verified. When one breaks, downstream
artifacts are re-checked for drift. Do not put real, unresolved decisions here —
those go in the Decision List._

## Decision List
_One row per real decision. An Open Question is a Decision with Status = Open.
Triage by **reversibility and blast radius**, not by Type label: reversible +
low-cost + obvious default → Assumed (state the default), even if Type = Product;
Open only when it changes scope or target users, incurs material/irreversible
cost, or carries compliance/legal/data-safety risk; Deferred for real but
non-blocking; Decided when upstream context already resolves it. Never
auto-decide compliance, legal, or genuinely strategic (high-blast-radius) items —
keep those Open. Stable IDs (D-001, D-002, …) carry forward to every later
artifact._

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | _the decision or question_ | _Founder / Product / Architect / Engineer / Compliance / Legal_ | _Product / Technical / Compliance / Legal / Operational_ | _Open / Assumed / Deferred / Decided / Superseded_ | _WO id, or —_ | _why it matters; for Assumed, state the chosen default_ |


---

## `architecture.md`

# Architecture — Template

> Artifact file: `01-architecture.md` · Upstream: `00-vision.md` · Produced by: Architecture agent (WO-004)

## Purpose

The Architecture shapes a system that delivers the Vision (`02-architecture.md`).
It defines the components and how they fit, and states what is deliberately
excluded. It must trace to the Vision — every component serves a Vision goal — and
reads only the Vision, no external codebase (Repo Intelligence is deferred).

## Required Sections

- **Overview** — the shape of the system in a few sentences.
- **Components** — the parts and each part's responsibility.
- **Data & Control Flow** — how the parts interact and where state lives.
- **Boundaries** — what the architecture deliberately excludes.
- **Tech Stack** — technologies named by the Vision's Constraints, with reasons;
  any unspecified choice left explicitly unresolved.
- **Assumptions** — what the architecture takes as true.
- **Decision List** — the Vision's Decision List carried forward and extended
  with any architecture decisions (an Open Question is a Decision with Status =
  Open).

## How To Use

Agents fill each section from the upstream Vision, keeping every `##` header
verbatim and replacing each italic prompt with real content. Prefer the simplest
shape that delivers the Vision; record excluded options under Boundaries rather
than silently dropping them. Use only technologies named in the Vision's
Constraints — never invent a stack. If a technology choice is unspecified, state
the requirement in Tech Stack and add it to the Decision List (a trivial,
low-risk default as Assumed; a genuine, blocking fork as Open).

Carry the Vision's **Decision List** forward verbatim (preserving IDs and any
Decided/Assumed/Deferred status — never reopen a resolved row) and append new
architecture decisions with fresh IDs. Triage per the rules in the Decision List
section below.

<!-- TEMPLATE BODY -->

# Architecture — {{ project }}

## Overview
_The shape of the system in a few sentences. How it delivers the Vision._

## Components
_The parts of the system and each part's single responsibility._

## Data & Control Flow
_How the components interact, the order of operations, and where state lives._

## Boundaries
_What the architecture deliberately excludes, and why. Absences are the
architecture, not gaps in it._

## Tech Stack
_Only technologies named in the Vision's Constraints, each with its reason. Keep
it minimal. Do not invent a NEW tool/vendor/framework the upstream never named.
A default PARAMETER of an already-named technology (a model id when the provider
is named, a default path, a file format) is NOT inventing — state a sensible
default and record it in the Decision List as Assumed/override-able. Only a
genuinely new, unnamed tool is left unresolved (Decision List, Open)._

## Assumptions
_What the architecture takes as true but has not verified (scale, load, available
services, team capability). Do not put real, unresolved decisions here — those go
in the Decision List._

## Decision List
_The Vision's Decision List carried forward (same IDs, same statuses — never
reopen a resolved row), plus new architecture decisions. An Open Question is a
Decision with Status = Open. Triage by **reversibility and blast radius**, not
Type label: reversible + obvious default → Assumed (state the default); a default
parameter of an already-named technology → Assumed; scope/target-user change,
material/irreversible cost, or compliance/legal/data-safety risk → Open; real but
non-blocking → Deferred; already resolved upstream → Decided. Never auto-decide
compliance, legal, or genuinely strategic items. Set Blocks when known._

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | _the decision or question_ | _Founder / Product / Architect / Engineer / Compliance / Legal_ | _Product / Technical / Compliance / Legal / Operational_ | _Open / Assumed / Deferred / Decided / Superseded_ | _WO id, or —_ | _why it matters; for Assumed, state the chosen default_ |


---

## `roadmap.md`

# Roadmap — Template

> Artifact file: `02-roadmap.md` · Upstream: `00-vision.md` + `01-architecture.md` · Produced by: Roadmap agent (WO-005)

## Purpose

The Roadmap sequences the work that delivers the Vision (`03-roadmap.md`). Every
item must trace back to the Vision, and each phase must be worth doing before the
next begins. A phase is a **founder-visible outcome** — a usable increment of the
product — not a bucket of engineering tasks. It records ordering and rationale,
not detailed Work Orders.

## Required Sections

- **Goal** — what the roadmap as a whole achieves.
- **Phases** — ordered phases, each a usable outcome with a goal and a done-when.
- **Sequencing Principle** — why this order, what each phase depends on.
- **Deferred** — capabilities intentionally left for later phases.
- **Assumptions** — what the sequencing takes as true.
- **Decision List** — upstream Decision List carried forward, extended with any
  sequencing decisions (an Open Question is a Decision with Status = Open).

## How To Use

Agents fill each section from the upstream Vision and Architecture, keeping every
`##` header verbatim and replacing each italic prompt with real content. Think
like a CTO, not an engineer.

- Phases represent **founder-visible outcomes** — usable increments a founder
  would recognize, each leaving the product more useful than before.
- **Do not enumerate implementation tasks** inside a phase. Describe the
  capability the phase delivers, not the files, modules, libraries, or tests
  needed to build it.
- Prefer **2–4 phases** for a typical V1. Minimize phase count while preserving
  clarity.
- Phases are ordered; nothing in a later phase may be required by an earlier one.
  Keep deferred items visible so they are not silently dropped or pulled forward.
- Treat Non-Goals as hard limits — do not invent features beyond the stated Goals.
- Carry the upstream **Decision List** forward (same IDs and statuses — never
  reopen a resolved row); append sequencing decisions, triaged per the rules in
  the Decision List section.

<!-- TEMPLATE BODY -->

# Roadmap — {{ project }}

## Goal
_What sequencing the work achieves overall._

## Phases
_Ordered phases, each a founder-visible outcome (a usable increment). For each:
the capability it delivers and a done-when check. Describe what the founder can
do after the phase, not the build steps. The first phase proves the core before
any power is added. Prefer 2–4 phases._

## Sequencing Principle
_Why this order. What each phase depends on being solid first._

## Deferred
_Capabilities intentionally not scheduled yet, recorded to keep them out of the
current phase without losing the intent._

## Assumptions
_What the sequencing takes as true but has not verified (dependencies, capacity,
external readiness). Do not put real, unresolved decisions here — those go in the
Decision List._

## Decision List
_Upstream Decision List carried forward (same IDs, same statuses — never reopen a
resolved row), plus new sequencing decisions. An Open Question is a Decision with
Status = Open. Triage: trivial defaults → Assumed; genuine, blocking forks →
Open; real but non-blocking → Deferred; already resolved upstream → Decided. Never
auto-decide compliance, legal, or major product-strategy items._

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | _the decision or question_ | _Founder / Product / Architect / Engineer / Compliance / Legal_ | _Product / Technical / Compliance / Legal / Operational_ | _Open / Assumed / Deferred / Decided / Superseded_ | _WO id, or —_ | _why it matters; for Assumed, state the chosen default_ |


---

## `work-orders.md`

# Work Orders — Template

> Artifact file: `03-work-orders.md` · Upstream: `02-roadmap.md` · Produced by: Work Order agent (WO-006)

## Purpose

Work Orders break Roadmap items into well-scoped units of work precise enough to
act on without re-deriving context (`04-work-orders.md`). A Work Order is a
**shippable outcome** — something a founder or user can observe once it is done —
not an implementation step. They describe *what* to build, not *how* to code it,
and trace upward to a Roadmap item.

### What a Work Order is — and is not

- A Work Order is **one shippable outcome**. If finishing it changes nothing a
  founder or user can observe, it is not a Work Order — fold it into one.
- **Tests** belong in *Done when*, never as their own Work Order.
- **Decisions** (which language, library, vendor, format) belong in the
  *Decision List*, never as a "select/settle/confirm" Work Order.
- **Setup and scaffolding** fold into the first capability that needs them.
- **Hardening and edge-cases** fold into the capability they harden.
- Prefer **vertical slices** (a thin end-to-end capability) over horizontal
  layers (build component A, then B, then C).
- **Minimize the count.** Aim for the fewest Work Orders that cover the Roadmap —
  typically a handful per phase. Mostly-Small Work Orders is a sign of
  over-decomposition; merge upward.
- **Name by outcome**, not by module touched. Optimize for leverage, not
  completeness.

## Required Sections

- **Format** — the fields every Work Order carries.
- **Work Orders** — the ordered list of Work Orders.
- **Deferred** — work intentionally not yet broken into Work Orders.
- **Assumptions** — what the breakdown takes as true.
- **Decision List** — the canonical, consolidated decision list for the project
  (an Open Question is a Decision with Status = Open). This terminal artifact
  holds the complete list, with the **Blocks** field linking each blocking
  decision to the Work Order it gates.

Each Work Order carries: ID, Goal, In scope, Out of scope, Depends on, Done when,
Complexity (S/M/L), Risk (Low/Medium/High). No time estimates.

## How To Use

Agents fill each section from the upstream Roadmap, keeping every `##` header
verbatim and replacing each italic prompt with real content. Use the
per-Work-Order field block once per **outcome** (see "What a Work Order is"
above), not once per implementation step. Fold tests, setup, and hardening into
Done when. Route decisions to the Decision List. Merge any Work Order that has no
observable founder/user outcome into the one it serves. Dependencies must point
only at earlier Work Orders. Treat Non-Goals as hard limits — do not invent work
beyond the stated Roadmap.

Carry the upstream **Decision List** forward (same IDs and statuses — never reopen
a resolved row) and set each row's **Blocks** field to the Work Order it gates (or
"—" if none). This is the canonical, consolidated list for the project.

<!-- TEMPLATE BODY -->

# Work Orders — {{ project }}

## Format
_Each Work Order has: an ID, a goal, scope (in/out), dependencies, a done-when
check, and metadata — Complexity (S/M/L) and Risk (Low/Medium/High). No time
estimates._

## Work Orders
_One block per shippable outcome, in dependency order. Not one per
implementation step — fold tests, setup, and hardening into Done when, and route
decisions to Open Questions._

### WO-NNN — _outcome-first title_
- **Goal:** _the founder/user-visible outcome this unit produces._
- **In scope:** _the capability built here, end to end (including its tests,
  setup, and hardening)._
- **Out of scope:** _what is explicitly excluded._
- **Depends on:** _earlier Work Order IDs, or none._
- **Done when:** _the check that proves the outcome works, tests included._
- **Complexity:** _S / M / L._ **Risk:** _Low / Medium / High._

## Deferred
_Work intentionally not yet broken into Work Orders, with the reason._

## Assumptions
_What the breakdown takes as true but has not verified (scope stability,
dependency correctness, available tooling). Do not put real, unresolved decisions
here — those go in the Decision List._

## Decision List
_The canonical, consolidated decision list for the project: every upstream row
carried forward (same IDs, same statuses — never reopen a resolved row) plus any
new ones. An Open Question is a Decision with Status = Open. Set Blocks to the
Work Order each decision gates. Triage: trivial defaults → Assumed (state the
default); genuine, blocking forks → Open; real but non-blocking → Deferred;
already resolved upstream → Decided. Never auto-decide compliance, legal, or major
product-strategy items — keep those Open._

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | _the decision or question_ | _Founder / Product / Architect / Engineer / Compliance / Legal_ | _Product / Technical / Compliance / Legal / Operational_ | _Open / Assumed / Deferred / Decided / Superseded_ | _WO id, or —_ | _why it matters; for Assumed, state the chosen default_ |
