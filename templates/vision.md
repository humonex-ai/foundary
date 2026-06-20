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
