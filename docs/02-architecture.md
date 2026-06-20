# Foundry — Architecture

How Foundry V1 is shaped to deliver the vision. This follows from
`00-vision.md` and obeys `01-principles.md` (#3 coherence flows downward,
#4 keep V1 extremely simple).

## Shape in One Line

Foundry is a **pipeline of agents** that turns a structured **Product Input**
into four plain markdown artifacts, stage by stage, each stage reading the one
above it.

```
Product Input (08-product-input-template.md, filled per project)
  │
  ▼
[Vision agent] ──▶ 00-vision.md
  │
  ▼
[Architecture agent] ──▶ 01-architecture.md
  │
  ▼
[Roadmap agent] ──▶ 02-roadmap.md
  │
  ▼
[Work Order agent] ──▶ 03-work-orders.md
```

Each stage consumes the artifacts above it and produces the next. The Product
Input is the head of the chain: a founder fills it (see
`08-product-input-template.md`) and it is the Vision agent's input. This is the
core loop. Everything in V1 exists to run this loop.

## Components

The repository layout maps directly onto these components.

### `agents/`
One agent per artifact: Vision, Architecture, Roadmap, Work Order. An agent is a
prompt + the logic to assemble its inputs (the upstream artifacts) and emit one
artifact. Agents do not call each other; the workflow chains them.

### `workflows/`
Orchestration. A workflow runs the agents in order, passes each artifact
downstream, and writes results to disk. The full chain (intent → work orders) is
one workflow. Re-running from any stage is also a workflow.

### `templates/`
The skeleton of each artifact — the section structure an agent fills in. Keeps
output consistent and human-readable (principle #7, plain artifacts). Template
strategy is fixed and deliberately dumb: see "Template Strategy" below.

### `services/`
Shared low-level capabilities the agents depend on: the LLM client, file
read/write for artifacts, config. Thin by design.

### `projects/`
Generated output. Each project Foundry runs against gets its own directory under
`projects/<name>/`, holding that project's Product Input and the four generated
artifacts. See "Output Location" below.

### `docs/`
Foundry's **own** direction documents — vision, principles, this architecture,
roadmap, work orders, decisions, agent catalog. These are hand-authored project
documentation, not generated output. Foundry dogfoods its own format: its own
direction is stored as a project under `projects/foundry/`, in the same artifact
form Foundry produces for any project. `docs/` (the meta-documentation of how
Foundry is built) stays distinct from `projects/` (generated artifacts).

### `tests/`
Verifies the loop runs and artifacts are produced in the expected structure.

## Artifacts Are Files

Artifacts are **plain markdown files on disk**. No database, no proprietary
format. The file is the source of truth. This makes artifacts readable without
Foundry (principle #7) and keeps V1 simple (principle #4).

## Output Location

Generated artifacts never mix with Foundry's own documentation. Every project
gets its own directory:

```
projects/
  <project-name>/
    product-input.md      # the filled Product Input (chain head)
    00-vision.md
    01-architecture.md
    02-roadmap.md
    03-work-orders.md
```

Foundry's own direction lives at `projects/foundry/` (dogfooding); other projects
sit beside it (e.g. `projects/ai-investment-firm/`, `projects/humonex/`). The
`docs/` directory holds only Foundry's meta-documentation (how Foundry itself is
built) and is never a generation target. This removes the V1 collision risk where
a run could overwrite Foundry's own docs. See `06-decisions.md` (D-008).

## Template Strategy

Templates are **plain markdown files with named section headers** — nothing more.
A template is the section skeleton an agent fills in; the same headers also tell
the agent what structure to produce. Example (Vision template):

```markdown
# Vision — <project>

## Problem
## Users
## Goals
## Non-Goals
## Success Criteria
## Assumptions
```

Deliberately excluded: no schema engines, no database, no complex templating
system. Jinja2 is used only for trivial variable substitution (e.g. project
name) where helpful — not for logic. The template's value is consistent,
human-readable structure (principle #7), not machinery. Every artifact template
carries an `## Assumptions` section so hidden assumptions are visible and drift
is easier to detect later, and a `## Decision List` section — one triaged list of
decisions (an Open Question is a Decision with Status = Open), seeded from the
Product Input and carried forward through the chain. See `06-decisions.md`
(D-009, D-012).

## Coherence

Coherence flows downward (principle #3). Each agent's input is the set of
upstream artifacts, so an artifact cannot be generated without its parents. When
an upstream artifact changes, the downstream stages are re-run from that point to
remove drift. V1 handles coherence the simplest way that works: **re-run
downstream**. Smarter, targeted drift detection is deferred.

## Boundaries (What the Architecture Excludes)

The architecture stops where direction becomes implementation
(`00-vision.md`). V1 deliberately has **no** component for:

- **Coding agents** — nothing executes Work Orders into code.
- **GitHub / repository integration** — artifacts live in `projects/`, not in
  external issue trackers or repos.
- **LLM Council** — a single model produces each artifact; no multi-model
  deliberation layer.
- **Repo Intelligence** — agents read only the upstream artifacts, not any
  external codebase.

These absences are the architecture, not gaps in it. See `03-roadmap.md` for
when they may be added.

## Control Flow Summary

1. Founder fills a Product Input (`08-product-input-template.md`) under
   `projects/<name>/product-input.md`.
2. Workflow runs the Vision agent on the Product Input → writes Vision.
3. Workflow feeds Vision to the Architecture agent → writes Architecture.
4. Workflow feeds Vision + Architecture to the Roadmap agent → writes Roadmap.
5. Workflow feeds Roadmap to the Work Order agent → writes Work Orders.
6. On any upstream change, the founder re-runs from the chosen stage downward
   (V1 has no auto drift-detection; the entry stage is user-selected).

That is the whole system in V1.

## Interface

V1 is run as a **CLI**, not a service. There is no HTTP API in V1 — Foundry is a
pipeline you invoke, not a server you call. A web/API surface is deferred until a
real caller exists. See `06-decisions.md` (D-010).

## V1 Stack

Deliberately small (`06-decisions.md`, D-010):

- **Python 3.12** — language.
- **uv** — environment and dependency management.
- **pydantic** — config and Product Input validation.
- **jinja2** — trivial variable substitution in templates only.
- **Anthropic SDK** — the LLM client in `services/`.
- **pytest** — tests.

No FastAPI (no service surface in V1). No agent-orchestration framework
(LangGraph / CrewAI / AutoGen / Temporal) — the workflow is four sequential
calls in plain Python; a framework would be premature. See D-010.
