# Foundry — Roadmap

The roadmap sequences how Foundry is built. The rule: prove the core artifact
loop first, then add power. Each phase must work before the next begins.

## Phase 1 — Core Artifact Chain (V1)

**Goal:** Produce the four artifacts from a Product Input and keep them coherent.
Nothing else.

- Capture a structured **Product Input** (`08-product-input-template.md`) as the
  start of every project.
- Create a **Vision** from the Product Input.
- Derive **Architecture** from the Vision.
- Derive a **Roadmap** from the Vision and Architecture.
- Break Roadmap items into **Work Orders**.
- Maintain the downward coherence link: a change upstream lets the founder re-run
  downstream to remove drift.

**Done when:** a founder can go from a Product Input to actionable Work Orders,
and the four artifacts stay coherent with each other.

**Explicitly not in V1:**

- No coding agents.
- No GitHub / repository integration.
- No LLM Council.
- No Repo Intelligence.

## Later Phases (Deferred)

Not scheduled. Listed only to record intent and keep them out of V1. Sequencing
and details are decided once Phase 1 is proven.

- **Repo Intelligence** — give Foundry awareness of an existing codebase so
  Architecture and Work Orders reflect reality on the ground.
- **GitHub Integration** — connect Work Orders to a real repository (issues,
  branches, references).
- **LLM Council** — multiple models deliberate on artifacts to raise the quality
  and rigor of direction.
- **Coding Agents** — execute Work Orders into code. This is the furthest-out
  capability and crosses Foundry's current boundary deliberately.

## Sequencing Principle

Each deferred capability is only worth building after the layer it depends on is
solid. Repo Intelligence and richer review (LLM Council) sharpen the artifacts;
GitHub and Coding Agents act on them. Direction must be trustworthy before we
automate acting on it. See `01-principles.md` (#5 Defer power until the loop is
proven).
