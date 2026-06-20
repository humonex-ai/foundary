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
