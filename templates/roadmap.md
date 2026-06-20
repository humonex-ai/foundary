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
