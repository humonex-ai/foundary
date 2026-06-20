# Foundry — Agent Catalog

The agents in Foundry V1. One agent per artifact, run in sequence by the chain
workflow (`02-architecture.md`). Each agent reads its upstream artifacts and
emits exactly one artifact.

Agents do not call each other (a V1 orchestration choice). The workflow chains
them and passes artifacts downstream. The chain head is the **Product Input**
(`08-product-input-template.md`), loaded and validated before the Vision agent
runs — that intake is WO-002b, not an agent.

Coherence in V1 is **structural**, not verified: each agent reads its upstream
artifacts as input, so an artifact cannot be produced without its parents. No
agent independently checks that the output actually traces to its parent. A
future critic/Council pass (deferred) is the natural home for verified coherence.

---

## Vision agent

- **Produces:** `00-vision.md`
- **Reads:** Product Input (`projects/<name>/product-input.md`)
- **Job:** Turn the Product Input into a clear statement of what we are building
  and why.
- **Boundary:** Does not propose architecture or work; vision only.
- **Work Order:** WO-003 (first pattern-establishing agent)

---

## Architecture agent

- **Produces:** `01-architecture.md`
- **Reads:** Vision
- **Job:** Shape a system that delivers the Vision. Define components and how the
  pieces fit.
- **Boundary:** Reads only the Vision — no external codebase (Repo Intelligence
  is deferred).
- **Work Order:** WO-004

---

## Roadmap agent

- **Produces:** `02-roadmap.md`
- **Reads:** Vision + Architecture
- **Job:** Sequence the work. Every item must trace back to the Vision.
- **Boundary:** Ordering and rationale, not detailed Work Orders.
- **Work Order:** WO-005

---

## Work Order agent

- **Produces:** `03-work-orders.md`
- **Reads:** Roadmap
- **Job:** Break Roadmap items into discrete, well-scoped Work Orders precise
  enough to act on.
- **Boundary:** Describes *what* to build, not *how* to code it. Does not execute
  Work Orders (no coding agents in V1).
- **Work Order:** WO-006

---

## Not in V1

No coding agents (execution) and no LLM Council (multi-model deliberation). A
single model backs each agent above. See `03-roadmap.md` and `06-decisions.md`
(D-005, D-006).
