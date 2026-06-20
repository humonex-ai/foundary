# Foundry — Principles

These principles govern how Foundry is built and how it behaves. When a decision
is unclear, these are the tiebreakers.

## 1. Direction leads

Direction — Vision, Architecture, Roadmap, Work Orders — is Foundry's center of
gravity, in every phase. Every feature is judged by whether it makes direction
clearer, not by whether it does more of the building. **In V1**, Foundry does
not write application code or touch a repository; it stops where direction
becomes implementation. Later phases may coordinate execution on top of
direction, but direction always leads — execution never comes before it.

## 2. The four artifacts are the V1 product

Vision, Architecture, Roadmap, and Work Orders are the whole V1 product, each
derived from a **Product Input** document. Everything else exists to create,
refine, or keep them coherent. In V1, if a feature does not serve one of these
four, it does not belong in Foundry.

## 3. Coherence flows downward

Each artifact derives from the one above it:

```
Product Input → Vision → Architecture → Roadmap → Work Orders
```

Vision must serve the Product Input. Architecture must serve the Vision. Roadmap
items must trace to the Vision. Work Orders must implement the Roadmap. When an
upper layer changes, the layers below it are re-checked for drift. Coherence
between layers matters more than detail within any one layer.

## 4. Keep V1 extremely simple

Prefer the smallest thing that proves the core loop. Defer every feature that is
not required to produce and connect the four artifacts. Simplicity now buys the
right to add power later; complexity now buys nothing.

## 5. Defer power until the loop is proven

Coding agents, GitHub integration, LLM Council, and Repo Intelligence are
deliberately not in V1. They are powerful but premature. None is worth building
until the core artifact chain demonstrably works. Resist pulling them forward.

## 6. Human owns intent

Foundry structures, sharpens, and connects intent — it does not replace the
founder's judgment about what to build. The human sets direction; Foundry makes
that direction explicit, coherent, and actionable.

## 7. Plain artifacts

Artifacts are written as plain, readable documents. They must be useful to a
human reader on their own, without special tooling to interpret them. Readability
is a feature, not a nicety.
