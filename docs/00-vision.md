# Foundry — Vision

## What Foundry Is

Foundry is an **AI CTO Office**.

It does the thinking work a CTO does: it turns a founder's intent into clear,
structured technical direction. Direction is Foundry's center of gravity — what
to build and in what order — and that does not change across phases. Future
phases may extend Foundry to coordinate engineering execution on top of that
direction (see "The Long-Term Vs. V1" below), but direction always leads.

Every project starts from a **Product Input** document (problem, users, goals,
constraints — see `08-product-input-template.md`). From that input Foundry
produces four artifacts and keeps them coherent with each other:

1. **Vision** — what we are building and why.
2. **Architecture** — how the system is shaped to deliver the vision.
3. **Roadmap** — the sequence of work that gets us there.
4. **Work Orders** — discrete, well-scoped units of work ready to be executed.

The artifact chain is therefore:

```
Product Input → Vision → Architecture → Roadmap → Work Orders
```

## The Long-Term Vs. V1

Foundry the **long-term product** is the AI CTO Office. Its center of gravity is
direction, and later phases may add engineering coordination and even autonomous
execution on top of that direction. The roadmap records this arc deliberately
(`03-roadmap.md`).

**Foundry V1 stops before implementation.** V1 is **not a coding platform**: it
does not write application code, open pull requests, or manage a repository. It
stops at the boundary where direction becomes implementation. The output of
Foundry V1 is the input a human (or, in a later phase, a coding agent) uses to
build.

This V1 boundary is deliberate. The hardest, highest-leverage part of building
software is deciding *what* to build and *in what order* — not typing the code.
Foundry owns that part first and proves it before crossing into execution.

## The Problem

Founders and small teams move fast but lose the thread. Vision lives in one
person's head. Architecture is implied, never written. The roadmap is a list of
features with no rationale. Work gets handed off as vague tickets. The result is
drift: what gets built stops matching why it was supposed to exist.

A CTO holds all four layers — vision, architecture, roadmap, work — in one
coherent picture and keeps them aligned as reality changes. Most teams cannot
afford a CTO, or their CTO is too deep in execution to keep the picture current.

## The Outcome

With Foundry, a team always has:

- A written vision everyone can point to.
- An architecture that follows from the vision, not from habit.
- A roadmap where every item traces back to the vision.
- Work orders precise enough to act on without re-deriving context.

When intent changes, Foundry propagates the change down through the layers so
the artifacts stay coherent instead of stale.

## V1 Scope

V1 is **extremely simple**. It establishes the core artifact chain — Product
Input → Vision → Architecture → Roadmap → Work Orders — and nothing more.

Explicitly **out of scope for V1**:

- No coding agents.
- No GitHub / repository integration.
- No LLM Council.
- No Repo Intelligence.

These are deferred deliberately. V1 must prove the core loop works before any of
them are worth building. See `03-roadmap.md` for sequencing.
