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
