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
