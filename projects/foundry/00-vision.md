# Vision — foundry

## Problem

Founders and small teams routinely lose coherence between why they are building something and what actually gets built. Vision lives in a single person's head, architecture is implied rather than written, roadmaps are flat feature lists with no rationale, and work is handed off as vague tickets. The gap between intent and execution compounds silently until what ships stops matching what was meant to exist.

Most small teams cannot afford a CTO to hold all four layers — vision, architecture, roadmap, and work — coherent as reality changes. The CTOs who do exist are too deep in execution to keep the picture current. Foundry exists to close that gap: giving a solo founder or small team a structured, traceable line from intent to actionable work, without requiring another person to maintain it.

## Users

**Primary:** A technical founder or solo builder who sets product direction but has no one to turn that direction into structured, coherent technical artifacts. They move fast, context-switch constantly, and need a system that makes their intent explicit and reviewable rather than ephemeral.

**Secondary:** Small engineering teams of two to ten people who need a written, traceable line from why to what before they begin building — teams where alignment is assumed but rarely documented.

## Goals

- A founder can go from a structured Product Input to four coherent, actionable artifacts — Vision, Architecture, Roadmap, Work Orders — in a single pass.
- Every downstream artifact traces demonstrably to the one above it, so drift is visible rather than hidden.
- Direction becomes explicit and reviewable, moving it out of one person's head and into shared, readable documents.
- Re-running from any stage downward refreshes all dependent artifacts, keeping the set coherent as intent evolves.
- The system stays simple enough that a solo founder can run and maintain it without operational overhead.

## Non-Goals

- **Not a coding platform:** Foundry does not write application code, open pull requests, or interact with a repository in V1.
- **Not a project manager:** No scheduling, time tracking, or integration with ticket boards.
- **Not a multi-model deliberation system:** No LLM Council or inter-agent debate in V1; one model backs each agent.
- **Not codebase-aware:** Foundry has no Repo Intelligence in V1 and does not read or analyze existing code.

## Constraints

- Python 3.12, managed with `uv`. Minimal dependencies: `pydantic`, `jinja2`, Anthropic SDK, `pytest`. No additional runtime dependencies without deliberate justification.
- CLI only — no web service, no HTTP API surface in V1.
- Artifacts are plain markdown files on disk; no database, no external storage.
- A single model backs each agent in V1; no multi-model routing.
- Built and maintained by one founder; low operational overhead is mandatory and non-negotiable.

## Success Criteria

- A founder who provides a structured Product Input receives four coherent markdown artifacts, each traceable to the artifact above it.
- Every artifact is readable and useful on its own, without requiring the tool to interpret it.
- Re-running Foundry from any stage downward produces refreshed, coherent dependent artifacts.
- Foundry successfully produces its own direction artifacts — dogfooding is a first-class validation of the system.

## Assumptions

- A structured Product Input yields markedly better artifacts than free-form intent; the quality of the input is the primary lever on output quality.
- A single LLM call per artifact, guided by a well-formed template, produces acceptable V1 quality without multi-step verification.
- Markdown with named sections provides sufficient structure for both human review and agent consumption downstream.
- One founder, one project at a time is the operative V1 usage shape; concurrent projects or multi-user workflows are out of scope.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | Should generated artifacts be version-controlled (history preserved) or is silent overwrite acceptable in V1? | Founder | Product | Open | — | Overwrite is simpler operationally, but version history changes the value proposition and affects re-run semantics materially. This is reversible in principle but has real blast radius on the re-run workflow design and user trust; warrants an explicit decision before Architecture. |
| D-002 | How strict should structural validation be on the founder's Product Input? | Product | Product | Assumed | — | Reversible and low-cost to tighten later. Default: validate that all required section headers are present and non-empty; emit a clear error and halt rather than proceeding on a malformed input. Deep semantic validation is deferred. |
| D-003 | When does coherence between artifacts require active verification rather than relying on each agent reading its upstream input? | Architect | Technical | Deferred | — | A real question but not blocking Vision or early Architecture. A passive read-upstream model is the V1 default; active coherence checking is a candidate for a post-V1 layer once the artifact pipeline is proven. |